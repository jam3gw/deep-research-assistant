"""
Configuration settings and constants for the research generator.
"""

# Maximum allowed values for user-configurable parameters
MAX_ALLOWED_RECURSION_DEPTH = 4
MAX_ALLOWED_SUB_QUESTIONS = 5

# Default values
DEFAULT_RECURSION_DEPTH = 2
DEFAULT_SUB_QUESTIONS = 3
DEFAULT_RECURSION_THRESHOLD = 1

# Model configuration
DEFAULT_MODEL = "claude-3-haiku-20240307"  # Fastest Claude model
DEFAULT_SYNTHESIS_MAX_TOKENS = 1500  # Reduced from 2000
DEFAULT_ANSWER_MAX_TOKENS = 800  # Reduced from 1000
DEFAULT_EVALUATION_MAX_TOKENS = 600  # Reduced from 1000

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