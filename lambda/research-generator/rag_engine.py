"""
RAG (Retrieval-Augmented Generation) engine for the research generator.
"""
import os
import uuid
import faiss
import numpy as np
from typing import List, Dict, Any
from openai import OpenAI
from config import (
    VECTOR_DB_TYPE, EMBEDDING_MODEL, VECTOR_DB_PATH,
    TOP_K_RESULTS, CHUNK_SIZE, CHUNK_OVERLAP,
    SIMILARITY_THRESHOLD, DEFAULT_MODEL, DEFAULT_ANSWER_MAX_TOKENS,
    DEFAULT_EVALUATION_MAX_TOKENS
)
from utils import extract_content
from knowledge_base import KnowledgeBaseManager
import time
import traceback
import random

def retry_with_exponential_backoff(initial_delay=1, exponential_base=2, jitter=True, max_retries=10, errors=(Exception,)):
    """Retry a function with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            num_retries = 0
            delay = initial_delay
            
            while True:
                try:
                    return func(*args, **kwargs)
                except errors as e:
                    num_retries += 1
                    if num_retries > max_retries:
                        print(f"Maximum retries ({max_retries}) exceeded.")
                        raise e
                    
                    delay *= exponential_base * (1 + jitter * random.random())
                    print(f"Retrying in {delay:.2f} seconds... (Attempt {num_retries}/{max_retries})")
                    print(f"Error: {str(e)}")
                    time.sleep(delay)
        return wrapper
    return decorator

def get_token_limit_for_depth(base_limit: int, depth: int) -> int:
    """
    Adjust token limit based on depth in the question tree.
    
    For leaf nodes (depth >= 2), we want more concise answers, so we reduce the token limit.
    For intermediate nodes (depth 1), we want moderate detail.
    For the root node (depth 0), we want the most comprehensive answer.
    
    Args:
        base_limit: The base token limit from config
        depth: The depth in the question tree
        
    Returns:
        Adjusted token limit
    """
    if depth >= 2:
        # Leaf nodes - more concise (60% of base)
        return 500
    elif depth == 1:
        # Intermediate nodes - moderate detail (80% of base)
        return 800
    else:
        # Root node - full detail
        return base_limit

def estimate_sources_tokens(sources: List[Dict[str, str]]) -> int:
    """
    Estimate the number of tokens needed for the sources section.
    
    Args:
        sources (List[Dict[str, str]]): List of source dictionaries with 'url' and 'title'
        
    Returns:
        int: Estimated number of tokens needed for sources
    """
    if not sources:
        return 0
    
    # Base tokens for the sources section header and structure
    base_tokens = 30  # <div class="sources"><h2>Sources</h2><ol></ol></div>
    
    # Estimate tokens per source (title, URL, and HTML structure)
    tokens_per_source = 0
    for source in sources:
        # Estimate ~1 token per 4 characters for URLs and titles
        url_tokens = len(source['url']) // 4 + 1
        title_tokens = len(source['title']) // 4 + 1
        # HTML structure: <li><a href="...">...</a></li>
        structure_tokens = 10
        tokens_per_source += url_tokens + title_tokens + structure_tokens
    
    return base_tokens + tokens_per_source

def deduplicate_sources(sources: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Deduplicate sources based on URL to avoid listing the same source multiple times.
    
    Args:
        sources (List[Dict[str, str]]): List of source dictionaries with 'url' and 'title'
        
    Returns:
        List[Dict[str, str]]: Deduplicated list of sources
    """
    if not sources:
        return []
    
    # Use a dictionary to track unique sources by URL
    unique_sources = {}
    
    for source in sources:
        url = source.get('url', '')
        if url and url not in unique_sources:
            unique_sources[url] = source
    
    # Return the list of unique sources
    return list(unique_sources.values())

class RAGEngine:
    def __init__(self):
        self.index = None
        self.documents = []
        self.initialize_vector_db()
        self.kb_manager = KnowledgeBaseManager(self)
        # Initialize without API key - it will be set later
        self.openai_client = None
    
    def set_openai_key(self, api_key: str):
        """Set the OpenAI API key and initialize the client."""
        self.openai_client = OpenAI(api_key=api_key)
    
    def initialize_vector_db(self):
        """Initialize the vector database based on configuration."""
        # Ensure we're using the /tmp directory in Lambda environments
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            # We're running in Lambda, ensure we're using /tmp
            vector_db_path = "/tmp/vector_db"
        else:
            # Use the configured path
            vector_db_path = VECTOR_DB_PATH
            
        # Ensure the vector_db directory exists
        os.makedirs(vector_db_path, exist_ok=True)
        
        if VECTOR_DB_TYPE == "faiss":
            index_path = os.path.join(vector_db_path, "index.faiss")
            documents_path = os.path.join(vector_db_path, "documents.npy")
            
            if os.path.exists(index_path):
                try:
                    # Load existing index
                    self.index = faiss.read_index(index_path)
                    # Load documents
                    with open(documents_path, 'rb') as f:
                        self.documents = np.load(f, allow_pickle=True).tolist()
                    print(f"Loaded existing vector DB from {vector_db_path}")
                except Exception as e:
                    print(f"Error loading existing vector DB: {str(e)}")
                    print("Creating new vector DB...")
                    # Create new index
                    self.index = faiss.IndexFlatL2(1536)  # OpenAI embedding dimension
                    self.documents = []
                    # Save empty index and documents
                    try:
                        faiss.write_index(self.index, index_path)
                        np.save(documents_path, np.array(self.documents))
                    except Exception as e2:
                        print(f"Error saving new vector DB: {str(e2)}")
            else:
                # Create new index
                self.index = faiss.IndexFlatL2(1536)  # OpenAI embedding dimension
                self.documents = []
                # Save empty index and documents
                try:
                    faiss.write_index(self.index, index_path)
                    np.save(documents_path, np.array(self.documents))
                except Exception as e:
                    print(f"Error saving new vector DB: {str(e)}")
                
            print(f"Vector DB initialized at {vector_db_path}")
            print(f"Number of documents: {len(self.documents)}")
            print(f"Index size: {self.index.ntotal} vectors")
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts using OpenAI's API."""
        try:
            print(f"Starting embedding generation for {len(texts)} texts at {time.strftime('%H:%M:%S')}")
            start_time = time.time()
            
            response = self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts
            )
            
            end_time = time.time()
            duration = end_time - start_time
            print(f"Embedding generation completed in {duration:.2f} seconds")
            
            embeddings = np.array([r.embedding for r in response.data])
            print(f"Successfully processed {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            print(f"Error in get_embeddings: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add new documents to the vector database."""
        print("\nProcessing documents for vector database...")
        
        # Determine the vector_db_path
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            # We're running in Lambda, ensure we're using /tmp
            vector_db_path = "/tmp/vector_db"
        else:
            # Use the configured path
            vector_db_path = VECTOR_DB_PATH
        
        # Process documents into chunks
        print("Chunking documents...")
        chunks = []
        for i, doc in enumerate(documents, 1):
            print(f"\nChunking document {i}/{len(documents)}:")
            print(f"Document length: {len(doc['content'])} characters")
            doc_chunks = self._chunk_text(doc['content'])
            print(f"Created {len(doc_chunks)} chunks")
            for chunk in doc_chunks:
                chunks.append({
                    'content': chunk,
                    'metadata': doc.get('metadata', {})
                })
        
        print(f"\nTotal chunks created: {len(chunks)}")
        
        # Get embeddings for chunks
        print("\nGenerating embeddings using OpenAI API...")
        try:
            chunk_texts = [c['content'] for c in chunks]
            print(f"Getting embeddings for {len(chunk_texts)} chunks")
            embeddings = self.get_embeddings(chunk_texts)
            print(f"Successfully generated {len(embeddings)} embeddings")
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            raise
        
        # Add to FAISS index
        print("\nAdding embeddings to FAISS index...")
        try:
            self.index.add(embeddings)
            print("Successfully added embeddings to FAISS index")
        except Exception as e:
            print(f"Error adding to FAISS index: {str(e)}")
            raise
        
        # Update documents list
        print("\nUpdating documents list...")
        try:
            self.documents.extend(chunks)
            print(f"Documents list updated, new total: {len(self.documents)}")
        except Exception as e:
            print(f"Error updating documents list: {str(e)}")
            raise
        
        # Save updated index and documents
        print("\nSaving updated index and documents...")
        try:
            print(f"Saving FAISS index to {vector_db_path}...")
            index_path = os.path.join(vector_db_path, "index.faiss")
            documents_path = os.path.join(vector_db_path, "documents.npy")
            
            faiss.write_index(self.index, index_path)
            print(f"Saving documents to {vector_db_path}...")
            np.save(documents_path, np.array(self.documents))
            print("Successfully saved all updates")
        except Exception as e:
            print(f"Error saving updates: {str(e)}")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception traceback: {traceback.format_exc()}")
            raise
    
    def retrieve(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
        """Retrieve most relevant documents for a query."""
        # Get query embedding
        query_embedding = self.get_embeddings([query])[0]
        
        # Search in FAISS
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1),
            top_k
        )
        
        # Enhanced logging for similarity scores
        print(f"Retrieved {len(indices[0])} potential documents for query")
        if len(indices[0]) > 0:
            print(f"Similarity scores (lower is better): {distances[0]}")
            print(f"Current similarity threshold: {SIMILARITY_THRESHOLD}")
        
        # Filter by similarity threshold and return relevant documents
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):  # Safety check
                if dist < SIMILARITY_THRESHOLD:
                    results.append(self.documents[idx])
                    print(f"Including document with score {dist:.4f}: {self.documents[idx].get('metadata', {}).get('title', 'Untitled')[:50]}...")
                else:
                    print(f"Excluding document with score {dist:.4f} (above threshold): {self.documents[idx].get('metadata', {}).get('title', 'Untitled')[:50]}...")
            else:
                print(f"Warning: Index {idx} out of bounds for documents array of length {len(self.documents)}")
        
        print(f"Final result: {len(results)} documents passed the similarity threshold")
        return results
    
    def retrieve_with_fallback(self, query: str, depth: int) -> List[Dict[str, Any]]:
        """Retrieve documents with fallback mechanism if no results are found."""
        print(f"  Retrieving relevant documents for question at depth {depth}...")
        relevant_docs = self.retrieve(query)
        print(f"  Retrieved {len(relevant_docs)} relevant documents.")
        
        # First fallback: If no sources found, try with a higher threshold
        if len(relevant_docs) == 0:
            print(f"  No sources found with standard threshold. Trying first fallback retrieval...")
            # Temporarily increase the threshold by 100% (double) for this query only
            fallback_threshold = SIMILARITY_THRESHOLD * 2.0
            print(f"  Using fallback threshold: {fallback_threshold:.4f}")
            
            # Search in FAISS with the same query embedding but higher threshold
            query_embedding = self.get_embeddings([query])[0]
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1),
                TOP_K_RESULTS
            )
            
            # Filter with higher threshold
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(self.documents) and dist < fallback_threshold:
                    relevant_docs.append(self.documents[idx])
                    print(f"  Fallback 1: Including document with score {dist:.4f}")
            
            print(f"  First fallback retrieval found {len(relevant_docs)} documents")
            
            # Second fallback: If still no sources found, just take the top 2 closest documents
            if len(relevant_docs) == 0 and len(indices[0]) > 0:
                print(f"  Still no sources found. Using second fallback: taking top 2 closest documents regardless of threshold.")
                # Take at most 2 documents to avoid too much irrelevant content
                for i in range(min(2, len(indices[0]))):
                    idx = indices[0][i]
                    dist = distances[0][i]
                    if idx < len(self.documents):
                        relevant_docs.append(self.documents[idx])
                        print(f"  Fallback 2: Including document with score {dist:.4f} (above threshold but closest available)")
                
                print(f"  Second fallback retrieval found {len(relevant_docs)} documents")
        
        return relevant_docs
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        print(f"\nChunking text of length {len(text)} with chunk size {CHUNK_SIZE} and overlap {CHUNK_OVERLAP}")
        
        if not text:
            print("Warning: Empty text provided to _chunk_text")
            return []
            
        chunks = []
        start = 0
        iteration = 0
        max_iterations = (len(text) // (CHUNK_SIZE - CHUNK_OVERLAP)) + 2  # Safety limit
        
        try:
            while start < len(text):
                iteration += 1
                if iteration > max_iterations:
                    print(f"Warning: Maximum iterations ({max_iterations}) reached. Breaking loop.")
                    break
                    
                print(f"Iteration {iteration}: Processing chunk starting at position {start}")
                
                end = start + CHUNK_SIZE
                if end > len(text):
                    end = len(text)
                    
                chunk = text[start:end]
                chunk_len = len(chunk)
                print(f"Created chunk of length {chunk_len}")
                
                chunks.append(chunk)
                start = end - CHUNK_OVERLAP
                
                print(f"Next start position: {start}")
                
            print(f"Chunking completed. Created {len(chunks)} chunks.")
            return chunks
            
        except Exception as e:
            print(f"Error in _chunk_text: {str(e)}")
            return chunks  # Return any chunks we managed to create
    
    def generate_sub_questions(self, question: str, client, brave_api_key: str) -> List[str]:
        """Generate sub-questions for a given question using RAG with dynamic knowledge base."""
        # First, populate knowledge base with relevant content
        self.kb_manager.populate_from_brave_search(question, brave_api_key, num_results=3)
        
        # Now retrieve relevant documents and generate sub-questions
        relevant_docs = self.retrieve(question)
        context = "\n\n".join([doc['content'] for doc in relevant_docs])
        
        # First, assess the complexity of the question
        system_message_complexity = """You are an AI assistant that analyzes questions to determine their complexity.
Your task is to categorize questions as 'simple', 'medium', or 'complex' based on:
1. The number of distinct concepts or topics involved
2. The depth of knowledge required to answer comprehensively
3. Whether the question has multiple facets or dimensions
4. The scope of the question (narrow vs. broad)
5. The level of specificity vs. generality

Respond with ONLY ONE of these three words: 'simple', 'medium', or 'complex'."""
        
        complexity_prompt = f"""Question: {question}

Analyze this question and determine if it is 'simple', 'medium', or 'complex'.

A 'simple' question:
- Focuses on a single, well-defined concept
- Can be answered directly and concisely
- Doesn't require breaking down into sub-questions
- Example: "What is the capital of France?"

A 'medium' question:
- Involves 2-3 related concepts
- Benefits from some structured breakdown
- Requires moderate explanation
- Example: "How does climate change affect agriculture?"

A 'complex' question:
- Involves multiple interconnected concepts
- Has several distinct facets or dimensions
- Requires comprehensive explanation
- Benefits from being broken into 3-5 sub-questions
- Example: "What are the economic, social, and environmental impacts of artificial intelligence on global development, and how might these change over the next decade?"

Respond with ONLY ONE of these three words: 'simple', 'medium', or 'complex'."""

        # Get complexity assessment
        try:
            @retry_with_exponential_backoff(
                initial_delay=2,
                exponential_base=2,
                jitter=True,
                max_retries=5,
                errors=(Exception,)
            )
            def assess_complexity_with_retry():
                return client.messages.create(
                    model=DEFAULT_MODEL,
                    max_tokens=10,  # Very short response needed
                    temperature=0,
                    system=system_message_complexity,
                    messages=[
                        {"role": "user", "content": complexity_prompt}
                    ]
                )
            
            # Call the function with retry logic
            complexity_message = assess_complexity_with_retry()
            
            complexity = extract_content(complexity_message).strip().lower()
            print(f"  Question complexity assessed as: {complexity}")
        except Exception as e:
            print(f"ERROR during complexity assessment: {str(e)}. Using standard comprehensive prompt.")
            # Fall back to standard comprehensive prompt
            system_message_complexity = """You are a helpful research assistant that provides comprehensive, well-structured answers based on provided context.
Format your response with semantic HTML tags for optimal readability and structure:

1. Document Structure:
- Use <h1> for the main title/topic
- Use <h2> for major sections
- Use <h3> for subsections when needed

2. Content Sections:
- Wrap each major section in <div class="section technology"> or <div class="section limitation"> based on content type
- Use <p> for regular paragraphs
- Use <strong> for emphasizing important terms or concepts
- Use <ul> and <li> for lists
- Use <blockquote> for notable quotes or definitions

3. Formatting Guidelines:
- Be comprehensive but clear
- Use bullet points for lists of features, benefits, or steps
- Break down complex topics into digestible sections
- Use examples to illustrate concepts when helpful
- DO NOT use numbered citations like [1], [2], etc. in your response

Example structure:
<h1>Comprehensive Topic Overview</h1>
<p>Thorough introduction with <strong>key terms</strong> highlighted.</p>

<div class="section technology">
    <h2>Major Section</h2>
    <p>Detailed explanation.</p>
    
    <h3>Subsection</h3>
    <ul>
        <li>Detailed point 1</li>
        <li>Detailed point 2</li>
    </ul>
</div>"""

            complexity_prompt = f"""Context:
{context}

Question: {question}

Please provide a comprehensive answer to this question based on the provided context.

Guidelines:
1. Be thorough and well-structured
2. Use appropriate HTML formatting for readability
3. DO NOT include a sources section at the end - this will be handled separately
4. DO NOT use numbered citations like [1], [2], etc. in your response"""

        # Determine number of sub-questions based on complexity
        if complexity == "simple":
            # For simple questions, we might not need sub-questions at all
            # Return an empty list to indicate no breakdown needed
            print("  Simple question detected. No sub-questions needed.")
            return []
        elif complexity == "medium":
            num_sub_questions = "2-3"
            print("  Medium complexity question. Generating 2-3 sub-questions.")
        else:  # complex or any other response
            num_sub_questions = "3-5"
            print("  Complex question detected. Generating 3-5 sub-questions.")
        
        # Now generate the appropriate number of sub-questions
        system_message = """You are a research assistant tasked with breaking down complex questions into focused, concise sub-questions.
Your responses should contain ONLY the sub-questions, one per line, with no additional text, prefixes, or explanations.
Each sub-question should be specific, focused, and directly answerable."""
        
        prompt = f"""Context from knowledge base:
{context}

Main question: {question}

Break this question down into {num_sub_questions} highly focused, concise sub-questions that will help provide a comprehensive answer.
Each sub-question should:
1. Address a specific aspect of the main question
2. Be more specific and narrower in scope than the main question
3. Be directly answerable with a concise response
4. Be clear and self-contained
5. Avoid overlapping too much with other sub-questions

IMPORTANT: 
- Return ONLY the sub-questions, one per line
- Make each sub-question as focused and specific as possible
- Ensure sub-questions can be answered concisely
- Do not include any other text, numbering, or explanations"""

        @retry_with_exponential_backoff(
            initial_delay=2,
            exponential_base=2,
            jitter=True,
            max_retries=5,
            errors=(Exception,)
        )
        def generate_sub_questions_with_retry():
            return client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=DEFAULT_EVALUATION_MAX_TOKENS,
                temperature=0,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
        
        # Call the function with retry logic
        message = generate_sub_questions_with_retry()
        
        # Extract sub-questions from response and clean up
        response = extract_content(message)
        sub_questions = [q.strip() for q in response.split('\n') if q.strip() and not q.lower().startswith(("here are", "question", "-", "•", "*", "1.", "2.", "3."))]
        
        # For complex questions, return up to 5 sub-questions
        # For medium questions, return up to 3 sub-questions
        max_questions = 5 if complexity == "complex" else 3
        return sub_questions[:max_questions]
    
    def generate_answer_with_tree(self, question: str, client, brave_api_key: str, depth: int = 0) -> Dict[str, Any]:
        """Generate an answer with question tree structure using RAG with dynamic knowledge base."""
        print(f"Generating tree node for question at depth {depth}: {question[:50]}...")
        
        start_time = time.time()
        
        try:
            # Create node for current question
            node = {
                'id': str(uuid.uuid4()),
                'question': question,
                'depth': depth,
                'children': []
            }
            
            # For deeper levels or if question is specific enough, don't generate sub-questions
            if depth >= 2:
                print(f"  Reached max depth ({depth}). Generating answer without breakdown.")
                node['needs_breakdown'] = False
                
                try:
                    # First retrieve relevant documents to get sources
                    relevant_docs = self.retrieve_with_fallback(question, depth)
                    
                    sources = []
                    for doc in relevant_docs:
                        if 'metadata' in doc and 'source' in doc['metadata']:
                            source_url = doc['metadata']['source']
                            source_title = doc['metadata'].get('title', 'Untitled Source')
                            sources.append({
                                'url': source_url,
                                'title': source_title
                            })
                    
                    # If no sources found, add a placeholder source
                    if not sources:
                        print(f"  WARNING: No sources found for node at depth {depth}. Adding a placeholder source.")
                        sources.append({
                            'url': "https://example.com/no-sources-found",
                            'title': "No specific sources found for this question"
                        })
                    
                    # Deduplicate sources
                    sources = deduplicate_sources(sources)
                    print(f"  Found {len(sources)} unique sources for node at depth {depth}")
                    
                    # Add sources to the node
                    node['sources'] = sources
                except Exception as e:
                    print(f"ERROR retrieving sources at depth {depth}: {str(e)}")
                    node['sources_error'] = str(e)
                
                try:
                    # Generate answer with sources - use concise mode for leaf nodes
                    print(f"  Generating answer for leaf node at depth {depth}...")
                    answer = self.generate_answer(question, client, brave_api_key, depth, concise=True)
                    print(f"  Generated answer of length {len(answer)} characters.")
                    node['answer'] = answer
                except Exception as e:
                    print(f"ERROR generating answer at depth {depth}: {str(e)}")
                    node['answer_error'] = str(e)
                    # Provide a fallback answer
                    node['answer'] = f"Error generating answer: {str(e)}"
                
                return node
            
            try:
                # Generate sub-questions using dynamic knowledge base
                print(f"  Generating sub-questions for depth {depth}...")
                sub_questions = self.generate_sub_questions(question, client, brave_api_key)
                print(f"  Generated {len(sub_questions)} sub-questions.")
            except Exception as e:
                print(f"ERROR generating sub-questions at depth {depth}: {str(e)}")
                # If we can't generate sub-questions, treat as leaf node
                node['needs_breakdown'] = False
                node['sub_questions_error'] = str(e)
                
                try:
                    # First retrieve relevant documents to get sources
                    relevant_docs = self.retrieve_with_fallback(question, depth)
                    
                    sources = []
                    for doc in relevant_docs:
                        if 'metadata' in doc and 'source' in doc['metadata']:
                            source_url = doc['metadata']['source']
                            source_title = doc['metadata'].get('title', 'Untitled Source')
                            sources.append({
                                'url': source_url,
                                'title': source_title
                            })
                    
                    # If no sources found, add a placeholder source
                    if not sources:
                        print(f"  WARNING: No sources found for node at depth {depth}. Adding a placeholder source.")
                        sources.append({
                            'url': "https://example.com/no-sources-found",
                            'title': "No specific sources found for this question"
                        })
                    
                    # Deduplicate sources
                    sources = deduplicate_sources(sources)
                    print(f"  Found {len(sources)} unique sources for node at depth {depth}")
                    
                    # Add sources to the node
                    node['sources'] = sources
                except Exception as e:
                    print(f"ERROR retrieving sources at depth {depth}: {str(e)}")
                    node['sources_error'] = str(e)
                
                try:
                    # Generate answer with sources - use concise mode for leaf nodes
                    print(f"  Generating answer for node with insufficient sub-questions at depth {depth}...")
                    answer = self.generate_answer(question, client, brave_api_key, depth, concise=True)
                    print(f"  Generated answer of length {len(answer)} characters.")
                    node['answer'] = answer
                except Exception as e:
                    print(f"ERROR generating answer at depth {depth}: {str(e)}")
                    node['answer_error'] = str(e)
                    node['answer'] = f"Error generating answer: {str(e)}"
                
                return node
            
            if len(sub_questions) <= 0:
                # For simple questions that don't need breakdown
                print(f"  Simple question detected. No breakdown needed.")
                node['needs_breakdown'] = False
                
                try:
                    # First retrieve relevant documents to get sources
                    relevant_docs = self.retrieve_with_fallback(question, depth)
                    
                    sources = []
                    for doc in relevant_docs:
                        if 'metadata' in doc and 'source' in doc['metadata']:
                            source_url = doc['metadata']['source']
                            source_title = doc['metadata'].get('title', 'Untitled Source')
                            sources.append({
                                'url': source_url,
                                'title': source_title
                            })
                    
                    # If no sources found, add a placeholder source
                    if not sources:
                        print(f"  WARNING: No sources found for node at depth {depth}. Adding a placeholder source.")
                        sources.append({
                            'url': "https://example.com/no-sources-found",
                            'title': "No specific sources found for this question"
                        })
                    
                    # Deduplicate sources
                    sources = deduplicate_sources(sources)
                    print(f"  Found {len(sources)} unique sources for node at depth {depth}")
                    
                    # Add sources to the node
                    node['sources'] = sources
                except Exception as e:
                    print(f"ERROR retrieving sources at depth {depth}: {str(e)}")
                    node['sources_error'] = str(e)
                
                try:
                    # Generate answer with sources - use concise mode for leaf nodes
                    print(f"  Generating direct answer for simple question at depth {depth}...")
                    answer = self.generate_answer(question, client, brave_api_key, depth, concise=False)
                    print(f"  Generated answer of length {len(answer)} characters.")
                    node['answer'] = answer
                except Exception as e:
                    print(f"ERROR generating answer at depth {depth}: {str(e)}")
                    node['answer_error'] = str(e)
                    node['answer'] = f"Error generating answer: {str(e)}"
                
                return node
            elif len(sub_questions) <= 1:
                # If no meaningful breakdown, treat as leaf node
                print(f"  Insufficient sub-questions ({len(sub_questions)}). Treating as leaf node.")
                node['needs_breakdown'] = False
                
                try:
                    # First retrieve relevant documents to get sources
                    relevant_docs = self.retrieve_with_fallback(question, depth)
                    
                    sources = []
                    for doc in relevant_docs:
                        if 'metadata' in doc and 'source' in doc['metadata']:
                            source_url = doc['metadata']['source']
                            source_title = doc['metadata'].get('title', 'Untitled Source')
                            sources.append({
                                'url': source_url,
                                'title': source_title
                            })
                    
                    # If no sources found, add a placeholder source
                    if not sources:
                        print(f"  WARNING: No sources found for node at depth {depth}. Adding a placeholder source.")
                        sources.append({
                            'url': "https://example.com/no-sources-found",
                            'title': "No specific sources found for this question"
                        })
                    
                    # Deduplicate sources
                    sources = deduplicate_sources(sources)
                    print(f"  Found {len(sources)} unique sources for node at depth {depth}")
                    
                    # Add sources to the node
                    node['sources'] = sources
                except Exception as e:
                    print(f"ERROR retrieving sources at depth {depth}: {str(e)}")
                    node['sources_error'] = str(e)
                
                try:
                    # Generate answer with sources - use concise mode for leaf nodes
                    print(f"  Generating answer for node with insufficient sub-questions at depth {depth}...")
                    answer = self.generate_answer(question, client, brave_api_key, depth, concise=True)
                    print(f"  Generated answer of length {len(answer)} characters.")
                    node['answer'] = answer
                except Exception as e:
                    print(f"ERROR generating answer at depth {depth}: {str(e)}")
                    node['answer_error'] = str(e)
                    node['answer'] = f"Error generating answer: {str(e)}"
            else:
                # Process sub-questions recursively
                print(f"  Processing {len(sub_questions)} sub-questions recursively.")
                node['needs_breakdown'] = True
                
                for i, sub_q in enumerate(sub_questions):
                    try:
                        print(f"  Processing sub-question {i+1}/{len(sub_questions)} at depth {depth+1}")
                        # Ensure consistent depth by explicitly passing the expected depth
                        sub_node = self.generate_answer_with_tree(sub_q, client, brave_api_key, depth + 1)
                        
                        # Validate and fix sub-node structure if needed
                        if 'depth' not in sub_node or sub_node['depth'] != depth + 1:
                            print(f"WARNING: Sub-node has incorrect depth. Expected {depth+1}, got {sub_node.get('depth')}. Fixing.")
                            sub_node['depth'] = depth + 1
                        
                        sub_node['parent_question'] = question
                        node['children'].append(sub_node)
                    except Exception as e:
                        print(f"ERROR processing sub-question {i+1} at depth {depth+1}: {str(e)}")
                        # Create an error node
                        error_node = {
                            'id': str(uuid.uuid4()),
                            'question': sub_q,
                            'depth': depth + 1,
                            'error': str(e),
                            'parent_question': question,
                            'answer': f"Error processing this question: {str(e)}",
                            'children': [],  # Add empty children list
                            'needs_breakdown': False  # Mark as not needing breakdown
                        }
                        node['children'].append(error_node)
                
                # Generate a summary answer for the parent node
                try:
                    print(f"  Generating summary answer for parent node at depth {depth}...")
                    # Check if we have any successful child nodes with answers
                    has_successful_children = any('answer' in child and not child.get('answer', '').startswith('Error') 
                                                for child in node['children'])
                    
                    if has_successful_children:
                        # Generate a summary based on child answers
                        child_answers = [f"Q: {child['question']}\nA: {child.get('answer', 'No answer')}" 
                                        for child in node['children'] if 'answer' in child]
                        
                        # Use the generate_answer method to create a summary
                        summary_prompt = f"Based on the following information about {question}, provide a comprehensive summary:\n\n"
                        summary_prompt += "\n\n".join(child_answers)
                        
                        answer = self.generate_answer(summary_prompt, client, brave_api_key, depth, concise=False)
                        node['answer'] = answer
                    else:
                        # If all children failed, generate a direct answer
                        print("  All child nodes failed. Generating direct answer.")
                        answer = self.generate_answer(question, client, brave_api_key, depth, concise=False)
                        node['answer'] = answer
                except Exception as e:
                    print(f"ERROR generating summary answer at depth {depth}: {str(e)}")
                    node['answer_error'] = str(e)
                    # Provide a fallback answer
                    node['answer'] = f"Error generating summary: {str(e)}"
            
            # Final validation of node structure
            print(f"Completed node at depth {depth} with {len(node.get('children', []))} children.")
            
            # Ensure the node has an answer
            if 'answer' not in node:
                print(f"WARNING: Node at depth {depth} is missing an answer. Adding a placeholder.")
                node['answer'] = "No answer was generated for this question."
            
            processing_time = time.time() - start_time
            print(f"Node at depth {depth} completed in {processing_time:.2f} seconds.")
            
            return node
            
        except Exception as e:
            print(f"CRITICAL ERROR in generate_answer_with_tree at depth {depth}: {str(e)}")
            print(f"Exception traceback: {traceback.format_exc()}")
            
            # Return a minimal error node
            error_node = {
                'id': str(uuid.uuid4()),
                'question': question,
                'depth': depth,
                'error': str(e),
                'answer': f"Error processing this question: {str(e)}"
            }
            return error_node
    
    def generate_answer(self, query: str, client, brave_api_key: str, depth: int = 0, concise: bool = False) -> str:
        """Generate an answer using RAG with dynamic knowledge base."""
        print(f"Generating answer for query at depth {depth}: {query[:50]}...")
        
        start_time = time.time()
        
        try:
            # First, try to retrieve relevant documents from the existing knowledge base
            print(f"  Retrieving documents from existing knowledge base...")
            relevant_docs = self.retrieve_with_fallback(query, depth)
            print(f"  Retrieved {len(relevant_docs)} documents from existing knowledge base.")
            
            # If not enough relevant documents, populate knowledge base with web search results
            if len(relevant_docs) < 1:
                print(f"  Insufficient documents ({len(relevant_docs)}). Performing web search...")
                try:
                    # Initialize knowledge base manager
                    kb_manager = KnowledgeBaseManager(self)
                    
                    # Populate knowledge base with web search results
                    search_docs = kb_manager.populate_from_brave_search(query, brave_api_key)
                    print(f"  Added {len(search_docs)} documents from web search.")
                    
                    # Retrieve again with the updated knowledge base
                    relevant_docs = self.retrieve_with_fallback(query, depth)
                    print(f"  Retrieved {len(relevant_docs)} documents after knowledge base update.")
                except Exception as e:
                    print(f"ERROR during web search: {str(e)}")
                    print(f"Exception type: {type(e).__name__}")
                    print(f"Exception traceback: {traceback.format_exc()}")
                    # Continue with whatever documents we have
            
            # Extract content from relevant documents
            context = ""
            sources = []
            
            print(f"  Processing {len(relevant_docs)} relevant documents...")
            for i, doc in enumerate(relevant_docs):
                try:
                    # Extract content and add to context
                    content = extract_content(doc)
                    if content:
                        # Add source to context without numbered references
                        context += f"\n\nSource Information:\n{content}"
                        
                        # Add source information
                        if 'metadata' in doc:
                            source_url = doc['metadata'].get('source', 'Unknown source')
                            source_title = doc['metadata'].get('title', 'Untitled')
                            sources.append({
                                'url': source_url,
                                'title': source_title
                            })
                except Exception as e:
                    print(f"ERROR processing document {i}: {str(e)}")
            
            # If we still have no sources, create a placeholder source
            if not sources:
                print("  WARNING: No sources found. Adding a placeholder source.")
                sources.append({
                    'number': 1,
                    'url': "https://example.com/no-sources-found",
                    'title': "No specific sources found for this query"
                })
            
            print(f"  Prepared context with {len(sources)} sources and {len(context)} characters.")
            
            # Adjust token limit based on depth
            token_limit = get_token_limit_for_depth(DEFAULT_ANSWER_MAX_TOKENS, depth)
     
            # First, check if this is a simple question at depth 0 (root level)
            # For simple questions at root level, we want a direct but comprehensive answer
            if depth == 0 and not concise:
                # Assess if this is a simple question
                system_message_complexity = """You are an AI assistant that analyzes questions to determine their complexity.
Your task is to categorize questions as 'simple', 'medium', or 'complex' based on:
1. The number of distinct concepts or topics involved
2. The depth of knowledge required to answer comprehensively
3. Whether the question has multiple facets or dimensions
4. The scope of the question (narrow vs. broad)
5. The level of specificity vs. generality

Respond with ONLY ONE of these three words: 'simple', 'medium', or 'complex'."""
                
                complexity_prompt = f"""Question: {query}

Analyze this question and determine if it is 'simple', 'medium', or 'complex'.

A 'simple' question:
- Focuses on a single, well-defined concept
- Can be answered directly and concisely
- Doesn't require breaking down into sub-questions
- Example: "What is the capital of France?"

A 'medium' question:
- Involves 2-3 related concepts
- Benefits from some structured breakdown
- Requires moderate explanation
- Example: "How does climate change affect agriculture?"

A 'complex' question:
- Involves multiple interconnected concepts
- Has several distinct facets or dimensions
- Requires comprehensive explanation
- Benefits from being broken into 3-5 sub-questions
- Example: "What are the economic, social, and environmental impacts of artificial intelligence on global development, and how might these change over the next decade?"

Respond with ONLY ONE of these three words: 'simple', 'medium', or 'complex'."""

                # Get complexity assessment
                try:
                    @retry_with_exponential_backoff(
                        initial_delay=2,
                        exponential_base=2,
                        jitter=True,
                        max_retries=5,
                        errors=(Exception,)
                    )
                    def assess_complexity_with_retry():
                        return client.messages.create(
                            model=DEFAULT_MODEL,
                            max_tokens=10,  # Very short response needed
                            temperature=0,
                            system=system_message_complexity,
                            messages=[
                                {"role": "user", "content": complexity_prompt}
                            ]
                        )
                    
                    # Call the function with retry logic
                    complexity_message = assess_complexity_with_retry()
                    
                    complexity = extract_content(complexity_message).strip().lower()
                    print(f"  Question complexity assessed as: {complexity}")
                    
                    # For simple questions, use a more direct approach
                    if complexity == "simple":
                        print("  Using direct answer approach for simple question.")
                        system_message = """You are a helpful research assistant that provides clear, direct answers to simple questions.
Format your response with semantic HTML tags for optimal readability and structure:

1. Document Structure:
- Use <h1> for the main title/topic
- Use <p> for regular paragraphs
- Use <strong> for emphasizing important terms or concepts
- Use <ul> and <li> for lists when appropriate

2. Formatting Guidelines:
- Be direct and to the point
- Provide a complete answer without unnecessary elaboration
- Use clear, simple language
- Include the most important information first

Example structure:
<h1>Direct Answer to Question</h1>
<p>Clear explanation with <strong>key terms</strong> highlighted.</p>
<p>Additional relevant information if needed.</p>"""

                        prompt = f"""Context:
{context}

Question: {query}

Please provide a direct, clear answer to this simple question based on the provided context.

Guidelines:
1. Be direct and to the point
2. Provide a complete answer
3. Use appropriate HTML formatting for readability
4. DO NOT include a sources section at the end - this will be handled separately
5. DO NOT use numbered citations like [1], [2], etc. in your response"""
                    else:
                        # Use standard comprehensive prompt for non-simple questions
                        system_message = """You are a helpful research assistant that provides comprehensive, well-structured answers based on provided context.
Format your response with semantic HTML tags for optimal readability and structure:

1. Document Structure:
- Use <h1> for the main title/topic
- Use <h2> for major sections
- Use <h3> for subsections when needed

2. Content Sections:
- Wrap each major section in <div class="section technology"> or <div class="section limitation"> based on content type
- Use <p> for regular paragraphs
- Use <strong> for emphasizing important terms or concepts
- Use <ul> and <li> for lists
- Use <blockquote> for notable quotes or definitions

3. Formatting Guidelines:
- Be comprehensive but clear
- Use bullet points for lists of features, benefits, or steps
- Break down complex topics into digestible sections
- Use examples to illustrate concepts when helpful
- DO NOT use numbered citations like [1], [2], etc. in your response

Example structure:
<h1>Comprehensive Topic Overview</h1>
<p>Thorough introduction with <strong>key terms</strong> highlighted.</p>

<div class="section technology">
    <h2>Major Section</h2>
    <p>Detailed explanation.</p>
    
    <h3>Subsection</h3>
    <ul>
        <li>Detailed point 1</li>
        <li>Detailed point 2</li>
    </ul>
</div>"""

                        prompt = f"""Context:
{context}

Question: {query}

Please provide a comprehensive answer to this question based on the provided context.

Guidelines:
1. Be thorough and well-structured
2. Use appropriate HTML formatting for readability
3. DO NOT include a sources section at the end - this will be handled separately
4. DO NOT use numbered citations like [1], [2], etc. in your response"""
                except Exception as e:
                    print(f"ERROR during complexity assessment: {str(e)}. Using standard comprehensive prompt.")
                    # Fall back to standard comprehensive prompt
                    system_message = """You are a helpful research assistant that provides comprehensive, well-structured answers based on provided context.
Format your response with semantic HTML tags for optimal readability and structure:

1. Document Structure:
- Use <h1> for the main title/topic
- Use <h2> for major sections
- Use <h3> for subsections when needed

2. Content Sections:
- Wrap each major section in <div class="section technology"> or <div class="section limitation"> based on content type
- Use <p> for regular paragraphs
- Use <strong> for emphasizing important terms or concepts
- Use <ul> and <li> for lists
- Use <blockquote> for notable quotes or definitions

3. Formatting Guidelines:
- Be comprehensive but clear
- Use bullet points for lists of features, benefits, or steps
- Break down complex topics into digestible sections
- Use examples to illustrate concepts when helpful
- DO NOT use numbered citations like [1], [2], etc. in your response

Example structure:
<h1>Comprehensive Topic Overview</h1>
<p>Thorough introduction with <strong>key terms</strong> highlighted.</p>

<div class="section technology">
    <h2>Major Section</h2>
    <p>Detailed explanation.</p>
    
    <h3>Subsection</h3>
    <ul>
        <li>Detailed point 1</li>
        <li>Detailed point 2</li>
    </ul>
</div>"""

                    prompt = f"""Context:
{context}

Question: {query}

Please provide a comprehensive answer to this question based on the provided context.

Guidelines:
1. Be thorough and well-structured
2. Use appropriate HTML formatting for readability
3. DO NOT include a sources section at the end - this will be handled separately
4. DO NOT use numbered citations like [1], [2], etc. in your response"""
            # Determine which prompt to use based on depth and conciseness for non-root questions
            elif concise or depth >= 1:
                # Use a more concise prompt for leaf nodes
                system_message = """You are a helpful research assistant that provides concise, focused answers based on provided context.
Format your response with semantic HTML tags for optimal readability and structure:

1. Document Structure:
- Use <h1> for the main title/topic (keep it brief)
- Use <h2> for major sections (only if necessary)
- Avoid using <h3> unless absolutely necessary

2. Content Sections:
- Wrap each major section in <div class="section technology"> or <div class="section limitation"> based on content type
- Use <p> for regular paragraphs (keep paragraphs short and focused)
- Use <strong> only for emphasizing specific terms or phrases
- Use <ul> and <li> for lists (prefer lists over long paragraphs)

3. Formatting Guidelines:
- Be extremely concise and focused
- Prioritize brevity over comprehensiveness
- Use bullet points whenever possible
- Limit to 1-2 short paragraphs per section
- Avoid repetition and unnecessary details
- Focus on making your answer as concise and informative as possible
- DO NOT use numbered citations like [1], [2], etc. in your response

Example structure:
<h1>Main Topic</h1>
<p>Brief introduction with <strong>key term</strong> highlighted.</p>

<div class="section technology">
    <h2>Key Points</h2>
    <ul>
        <li>Concise point 1</li>
        <li>Concise point 2</li>
    </ul>
</div>"""

                prompt = f"""Context:
{context}

Question: {query}

Please provide a VERY CONCISE answer to this specific question. Focus only on the most relevant information.

Guidelines:
1. Keep your answer brief and to the point
2. Use bullet points and short paragraphs
3. Include only the most essential information
4. DO NOT include a sources section at the end - this will be handled separately
5. DO NOT use numbered citations like [1], [2], etc. in your response"""
            else:
                # Use a more comprehensive prompt for root node
                system_message = """You are a helpful research assistant that provides comprehensive, well-structured answers based on provided context.
Format your response with semantic HTML tags for optimal readability and structure:

1. Document Structure:
- Use <h1> for the main title/topic
- Use <h2> for major sections
- Use <h3> for subsections when needed

2. Content Sections:
- Wrap each major section in <div class="section technology"> or <div class="section limitation"> based on content type
- Use <p> for regular paragraphs
- Use <strong> for emphasizing important terms or concepts
- Use <ul> and <li> for lists
- Use <blockquote> for notable quotes or definitions

3. Formatting Guidelines:
- Be comprehensive but clear
- Use bullet points for lists of features, benefits, or steps
- Break down complex topics into digestible sections
- Use examples to illustrate concepts when helpful
- DO NOT use numbered citations like [1], [2], etc. in your response

Example structure:
<h1>Comprehensive Topic Overview</h1>
<p>Thorough introduction with <strong>key terms</strong> highlighted.</p>

<div class="section technology">
    <h2>Major Section</h2>
    <p>Detailed explanation.</p>
    
    <h3>Subsection</h3>
    <ul>
        <li>Detailed point 1</li>
        <li>Detailed point 2</li>
    </ul>
</div>"""

                prompt = f"""Context:
{context}

Question: {query}

Please provide a comprehensive answer to this question based on the provided context.

Guidelines:
1. Be thorough and well-structured
2. Use appropriate HTML formatting for readability
3. DO NOT include a sources section at the end - this will be handled separately"""
            
            print(f"  Sending request to Anthropic Claude with prompt length {len(prompt)} characters...")
            
            try:
                # Generate answer using Anthropic Claude with retry logic
                @retry_with_exponential_backoff(
                    initial_delay=2,
                    exponential_base=2,
                    jitter=True,
                    max_retries=5,
                    errors=(Exception,)
                )
                def call_anthropic_with_retry():
                    return client.messages.create(
                        model=DEFAULT_MODEL,
                        max_tokens=token_limit,
                        system=system_message,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    )
                
                # Call the function with retry logic
                response = call_anthropic_with_retry()
                
                answer = response.content[0].text
                print(f"  Received answer from Claude with length {len(answer)} characters.")
                
                # Check if the answer already has a sources section and remove it
                if "<h2>Sources</h2>" in answer or "<h3>Sources</h3>" in answer:
                    print("  Answer contains a sources section. Removing it...")
                    answer = self._remove_sources_section(answer)
                
                # We're no longer adding the sources section at the bottom
                # The sources are still tracked and available in the node data
                # but we don't append them to the HTML output
                
                processing_time = time.time() - start_time
                print(f"Answer generation completed in {processing_time:.2f} seconds.")
                
                return answer
                
            except Exception as e:
                print(f"ERROR during Claude API call: {str(e)}")
                print(f"Exception type: {type(e).__name__}")
                print(f"Exception traceback: {traceback.format_exc()}")
                raise ValueError(f"Failed to generate answer with Claude: {str(e)}")
                
        except Exception as e:
            print(f"CRITICAL ERROR in generate_answer: {str(e)}")
            print(f"Exception traceback: {traceback.format_exc()}")
            raise ValueError(f"Failed to generate answer: {str(e)}")
    
    def _generate_sources_html(self, sources: List[Dict[str, str]]) -> str:
        """Generate HTML for the sources section."""
        html = "<div class=\"sources\"><h2>Sources</h2><ol>"
        for source in sources:
            html += f"<li>{source['title']} - <a href=\"{source['url']}\">{source['url']}</a></li>"
        html += "</ol></div>"
        return html
    
    def _remove_sources_section(self, html_content):
        """Remove any sources section from the HTML content."""
        # Check for sources section with double quotes
        if "<div class=\"sources\">" in html_content:
            parts = html_content.split("<div class=\"sources\">")
            html_content = parts[0].strip()
        
        # Check for sources section with single quotes
        elif "<div class='sources'>" in html_content:
            parts = html_content.split("<div class='sources'>")
            html_content = parts[0].strip()
        
        return html_content 