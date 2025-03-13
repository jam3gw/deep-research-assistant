"""
Knowledge base management for the research generator.
"""
import os
import json
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import PyPDF2
from io import BytesIO
from datetime import datetime

class KnowledgeBaseManager:
    def __init__(self, rag_engine):
        self.rag_engine = rag_engine
        
        # Use /tmp directory for Lambda environments, which is writable
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            # We're running in Lambda, use /tmp directory
            self.sources_file = os.path.join('/tmp', 'sources.json')
        else:
            # Local development environment
            self.sources_file = os.path.join(os.path.dirname(__file__), 'data/sources.json')
            os.makedirs(os.path.dirname(self.sources_file), exist_ok=True)
        
        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(self.sources_file), exist_ok=True)
    
    def populate_from_brave_search(self, query: str, api_key: str, num_results: int = 3) -> List[Dict[str, Any]]:
        """Populate knowledge base with content from Brave Search results."""
        print(f"\nFetching search results for: {query}")
        
        headers = {
            'X-Subscription-Token': api_key,
            'Accept': 'application/json',
        }
        
        # Make Brave Search API request
        search_url = 'https://api.search.brave.com/res/v1/web/search'
        params = {
            'q': query,
            'count': num_results,
            'text_format': 'raw',
            'search_lang': 'en'
        }
        
        try:
            print(f"Making Brave Search API request to {search_url}...")
            print(f"Query parameters: {params}")
            response = requests.get(search_url, headers=headers, params=params)
            print(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response from Brave Search: {response.text}")
                return []
                
            response.raise_for_status()
            search_results = response.json()
            
            results_count = len(search_results.get('web', {}).get('results', []))
            print(f"Received {results_count} search results from Brave Search")
            
            if results_count == 0:
                print("No results found in the response")
                if 'web' not in search_results:
                    print("No 'web' field in response")
                print(f"Response structure: {json.dumps(search_results.keys(), indent=2)}")
                return []
            
            documents = []
            for i, result in enumerate(search_results.get('web', {}).get('results', []), 1):
                print(f"\nProcessing result {i}/{results_count}:")
                print(f"Title: {result.get('title', 'No title')}")
                print(f"URL: {result.get('url', 'No URL')}")
                
                # Create document from Brave Search result
                content = [
                    result.get('title', ''),
                    result.get('description', ''),
                    result.get('content', {}).get('text', '')
                ]
                
                # Filter out empty content
                content = [c for c in content if c]
                print(f"Content length: {sum(len(c) for c in content)} characters")
                
                document = {
                    'content': '\n\n'.join(content),
                    'metadata': {
                        'source': result['url'],
                        'type': 'web',
                        'title': result.get('title', ''),
                        'description': result.get('description', ''),
                        'query': query,
                        'fetched_at': str(datetime.now())
                    }
                }
                documents.append(document)
            
            # Add documents to the knowledge base
            if documents:
                print(f"\nAdding {len(documents)} documents to knowledge base...")
                self.rag_engine.add_documents(documents)
                self._save_sources(documents)
                print("Documents added successfully")
            else:
                print("No valid documents to add to knowledge base")
            
            return documents
            
        except requests.exceptions.RequestException as e:
            print(f"Network error making Brave Search API request: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing Brave Search response as JSON: {str(e)}")
            print(f"Raw response: {response.text[:500]}...")  # Print first 500 chars
            return []
        except Exception as e:
            print(f"Unexpected error in populate_from_brave_search: {str(e)}")
            return []
    
    def add_web_content(self, urls: List[str]):
        """Add content from web pages to the knowledge base."""
        documents = []
        for url in urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract main content (customize based on website structure)
                content = ' '.join([p.get_text() for p in soup.find_all('p')])
                
                documents.append({
                    'content': content,
                    'metadata': {
                        'source': url,
                        'type': 'web',
                        'title': soup.title.string if soup.title else url
                    }
                })
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
        
        if documents:
            self.rag_engine.add_documents(documents)
            self._save_sources(documents)
    
    def add_pdf_documents(self, pdf_paths: List[str]):
        """Add content from PDF files to the knowledge base."""
        documents = []
        for path in pdf_paths:
            try:
                with open(path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    content = ''
                    for page in pdf_reader.pages:
                        content += page.extract_text() + '\n'
                    
                    documents.append({
                        'content': content,
                        'metadata': {
                            'source': path,
                            'type': 'pdf',
                            'title': os.path.basename(path)
                        }
                    })
            except Exception as e:
                print(f"Error processing {path}: {str(e)}")
        
        if documents:
            self.rag_engine.add_documents(documents)
            self._save_sources(documents)
    
    def add_text_content(self, text: str, metadata: Dict[str, Any]):
        """Add raw text content to the knowledge base."""
        document = {
            'content': text,
            'metadata': {
                **metadata,
                'type': 'text'
            }
        }
        self.rag_engine.add_documents([document])
        self._save_sources([document])
    
    def _save_sources(self, documents: List[Dict[str, Any]]):
        """Save source information to track what's in the knowledge base."""
        sources = []
        if os.path.exists(self.sources_file):
            with open(self.sources_file, 'r') as f:
                sources = json.load(f)
        
        # Add new sources
        for doc in documents:
            source_info = {
                'title': doc['metadata'].get('title', ''),
                'source': doc['metadata'].get('source', ''),
                'type': doc['metadata'].get('type', ''),
                'added_at': str(datetime.now())
            }
            sources.append(source_info)
        
        # Save updated sources
        with open(self.sources_file, 'w') as f:
            json.dump(sources, f, indent=2)
    
    def list_sources(self) -> List[Dict[str, Any]]:
        """List all sources in the knowledge base."""
        if os.path.exists(self.sources_file):
            with open(self.sources_file, 'r') as f:
                return json.load(f)
        return []
    
    def clear_knowledge_base(self):
        """Clear all documents from the knowledge base."""
        if os.path.exists(self.rag_engine.VECTOR_DB_PATH):
            import shutil
            shutil.rmtree(self.rag_engine.VECTOR_DB_PATH)
        if os.path.exists(self.sources_file):
            os.remove(self.sources_file)
        self.rag_engine.initialize_vector_db() 