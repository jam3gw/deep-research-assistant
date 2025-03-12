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
DEFAULT_MODEL = "claude-3-haiku-20240307"  # Fastest Claude model
DEFAULT_SYNTHESIS_MAX_TOKENS = 1000
DEFAULT_ANSWER_MAX_TOKENS = 500
DEFAULT_EVALUATION_MAX_TOKENS = 400

# RAG configuration
CHUNK_SIZE = 150  # Reduced from 250 to prevent potential memory issues
CHUNK_OVERLAP = 15  # Reduced from 25 to maintain proportion
SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score for retrieved documents

# Validation
if CHUNK_SIZE <= CHUNK_OVERLAP:
    raise ValueError("CHUNK_SIZE must be greater than CHUNK_OVERLAP")
if CHUNK_SIZE <= 0 or CHUNK_OVERLAP < 0:
    raise ValueError("CHUNK_SIZE must be positive and CHUNK_OVERLAP must be non-negative")

def get_token_limit_for_depth(base_limit, depth):
    """
    Calculate token limit based on depth - deeper nodes get fewer tokens
    """
    if depth == 0:
        return base_limit
    elif depth == 1:
        return int(base_limit * 0.75)  # 75% of base limit
    elif depth == 2:
        return int(base_limit * 0.5)   # 50% of base limit
    else:
        return int(base_limit * 0.25)   # 25% of base limit for depth 3+ 