"""
Configuration settings and constants for the research generator.
"""
import os

# Maximum allowed values for user-configurable parameters
MAX_ALLOWED_RECURSION_DEPTH = 4
MAX_ALLOWED_SUB_QUESTIONS = 5

# Default values
DEFAULT_RECURSION_DEPTH = 2
DEFAULT_SUB_QUESTIONS = 3
DEFAULT_RECURSION_THRESHOLD = 1

# Vector database settings
VECTOR_DB_TYPE = "faiss"  # Options: faiss, milvus, pinecone
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI's embedding model
VECTOR_DB_PATH = "/tmp/vector_db"  # Use Lambda's writable /tmp directory
TOP_K_RESULTS = 3  # Number of most relevant documents to retrieve

# Model configuration
DEFAULT_MODEL = "claude-3-5-sonnet-20240620"  # Using Sonnet for better quality
DEFAULT_SYNTHESIS_MAX_TOKENS = 1500  # Increased from 1200 to accommodate sources
DEFAULT_ANSWER_MAX_TOKENS = 1200  # Restored to original value for comprehensive final answer
DEFAULT_EVALUATION_MAX_TOKENS = 400  # Keep unchanged

# RAG configuration
CHUNK_SIZE = 150  # Reduced from 250 to prevent potential memory issues
CHUNK_OVERLAP = 15  # Reduced from 25 to maintain proportion
SIMILARITY_THRESHOLD = 0.45  # Reduced from 0.55 to ensure more sources are included

# Validation
if CHUNK_SIZE <= CHUNK_OVERLAP:
    raise ValueError("CHUNK_SIZE must be greater than CHUNK_OVERLAP")
if CHUNK_SIZE <= 0 or CHUNK_OVERLAP < 0:
    raise ValueError("CHUNK_SIZE must be positive and CHUNK_OVERLAP must be non-negative")

# Additional token limits
DEFAULT_SUB_QUESTION_MAX_TOKENS = 500 