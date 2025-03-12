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

def get_token_limit_for_depth(base_limit: int, depth: int) -> int:
    """
    Calculate the token limit based on the depth of the question.
    
    Args:
        base_limit (int): The base token limit (e.g., DEFAULT_ANSWER_MAX_TOKENS)
        depth (int): The depth of the current question in the tree
        
    Returns:
        int: The adjusted token limit for the given depth
    """
    # For depth 0 (root), use the full base limit
    if depth == 0:
        return base_limit
        
    # For deeper levels, reduce the token limit to keep responses more focused
    # Use a linear reduction strategy
    reduction_factor = max(0.25, 1 - (depth * 0.25))  # Reduce by 25% for each level, minimum 25% of base
    return int(base_limit * reduction_factor)

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
        if VECTOR_DB_TYPE == "faiss":
            # Ensure the /tmp/vector_db directory exists
            os.makedirs(VECTOR_DB_PATH, exist_ok=True)
            
            index_path = os.path.join(VECTOR_DB_PATH, "index.faiss")
            documents_path = os.path.join(VECTOR_DB_PATH, "documents.npy")
            
            if os.path.exists(index_path):
                # Load existing index
                self.index = faiss.read_index(index_path)
                # Load documents
                with open(documents_path, 'rb') as f:
                    self.documents = np.load(f, allow_pickle=True).tolist()
            else:
                # Create new index
                self.index = faiss.IndexFlatL2(1536)  # OpenAI embedding dimension
                self.documents = []
                # Save empty index and documents
                faiss.write_index(self.index, index_path)
                np.save(documents_path, np.array(self.documents))
                
            print(f"Vector DB initialized at {VECTOR_DB_PATH}")
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
            print("Saving FAISS index...")
            faiss.write_index(self.index, f"{VECTOR_DB_PATH}/index.faiss")
            print("Saving documents...")
            np.save(f"{VECTOR_DB_PATH}/documents.npy", np.array(self.documents))
            print("Successfully saved all updates")
        except Exception as e:
            print(f"Error saving updates: {str(e)}")
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
        
        # Filter by similarity threshold and return relevant documents
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if dist < SIMILARITY_THRESHOLD:
                results.append(self.documents[idx])
        
        return results
    
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
        
        system_message = """You are a research assistant tasked with breaking down complex questions into focused sub-questions.
Your responses should contain ONLY the sub-questions, one per line, with no additional text, prefixes, or explanations."""
        
        prompt = f"""Context from knowledge base:
{context}

Main question: {question}

Break this question down into 2-3 focused sub-questions that will help provide a comprehensive answer.
Each sub-question should:
1. Address a specific aspect of the main question
2. Be more specific than the main question
3. Be answerable using the provided context or general knowledge

IMPORTANT: Return ONLY the sub-questions, one per line. Do not include any other text, numbering, or explanations."""

        message = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=DEFAULT_EVALUATION_MAX_TOKENS,
            temperature=0,
            system=system_message,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract sub-questions from response and clean up
        response = extract_content(message)
        sub_questions = [q.strip() for q in response.split('\n') if q.strip() and not q.lower().startswith(("here are", "question", "-", "•", "*", "1.", "2.", "3."))]
        return sub_questions[:3]  # Limit to 3 sub-questions
    
    def generate_answer_with_tree(self, question: str, client, brave_api_key: str, depth: int = 0) -> Dict[str, Any]:
        """Generate an answer with question tree structure using RAG with dynamic knowledge base."""
        # Create node for current question
        node = {
            'id': str(uuid.uuid4()),
            'question': question,
            'depth': depth,
            'children': []
        }
        
        # For deeper levels or if question is specific enough, don't generate sub-questions
        if depth >= 2:
            node['needs_breakdown'] = False
            node['answer'] = self.generate_answer(question, client, brave_api_key, depth)
            return node
        
        # Generate sub-questions using dynamic knowledge base
        sub_questions = self.generate_sub_questions(question, client, brave_api_key)
        
        if len(sub_questions) <= 1:
            # If no meaningful breakdown, treat as leaf node
            node['needs_breakdown'] = False
            node['answer'] = self.generate_answer(question, client, brave_api_key, depth)
        else:
            # Process sub-questions recursively
            node['needs_breakdown'] = True
            for sub_q in sub_questions:
                sub_node = self.generate_answer_with_tree(sub_q, client, brave_api_key, depth + 1)
                sub_node['parent_question'] = question
                node['children'].append(sub_node)
        
        return node
    
    def generate_answer(self, query: str, client, brave_api_key: str, depth: int = 0) -> str:
        """Generate an answer using RAG approach with dynamic knowledge base."""
        # First, populate knowledge base with relevant content
        self.kb_manager.populate_from_brave_search(query, brave_api_key, num_results=3)
        
        # Retrieve relevant documents
        relevant_docs = self.retrieve(query)
        
        # Prepare context from retrieved documents
        context = "\n\n".join([doc['content'] for doc in relevant_docs])
        
        # Generate answer using Claude
        system_message = """You are a helpful research assistant that provides well-structured answers based on provided context.
Format your response with semantic HTML tags for optimal readability and structure:

1. Document Structure:
- Use <h1> for the main title/topic
- Use <h2> for major sections
- Use <h3> for subsections if needed

2. Content Sections:
- Wrap each major section in <div class="section technology"> or <div class="section limitation"> based on content type
- Use <p> for regular paragraphs
- Use <strong> only for emphasizing specific terms or phrases, not entire paragraphs
- Use <ul> and <li> for lists

3. Formatting Guidelines:
- Keep paragraphs concise and focused
- Use lists for multiple related points
- Maintain consistent heading hierarchy
- Add appropriate spacing for readability

Example structure:
<h1>Main Topic</h1>
<p>Introduction paragraph...</p>

<div class="section technology">
    <h2>Technology Section</h2>
    <p>Overview of the technology, with <strong>key terms</strong> emphasized.</p>
    <ul>
        <li>Key point 1</li>
        <li>Key point 2</li>
    </ul>
</div>

<div class="section limitation">
    <h2>Limitations</h2>
    <p>Discussion of limitations...</p>
</div>"""

        prompt = f"""Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information,
you can use your general knowledge but clearly indicate when you're doing so.

Structure your response following these guidelines:
1. Start with a clear title using <h1>
2. Begin with a brief overview paragraph
3. Organize content into logical sections using appropriate HTML tags
4. Use <strong> sparingly - only for emphasizing specific terms, not entire paragraphs
5. Use lists when presenting multiple related points
6. Wrap each major section in an appropriate div with semantic class names

Make the content visually appealing and easy to scan while maintaining a professional tone."""

        message = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=get_token_limit_for_depth(DEFAULT_ANSWER_MAX_TOKENS, depth),
            temperature=0,
            system=system_message,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return extract_content(message) 