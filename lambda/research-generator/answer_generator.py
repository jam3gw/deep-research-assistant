"""
Functions for generating answers to questions.
"""
from utils import extract_content
from config import DEFAULT_MODEL, DEFAULT_ANSWER_MAX_TOKENS, get_token_limit_for_depth

def get_answer_for_question(question, client, parent_question=None, depth=0, original_question=None):
    """
    Use Anthropic to get an answer for a specific question
    """
    context_prompt = ""
    if parent_question:
        context_prompt = f"""
This question is part of a larger research question: "{parent_question}"
Your answer should be relevant to this broader context while focusing specifically on the sub-question.
"""
    
    # Add original question context if available and different from parent
    if original_question and original_question != parent_question:
        context_prompt += f"""
This is part of research on the original question: "{original_question}"
Ensure your answer contributes to understanding this original research question.
"""
    
    # Adjust token limit based on depth
    token_limit = get_token_limit_for_depth(DEFAULT_ANSWER_MAX_TOKENS, depth)
    
    # Adjust the prompt based on depth to encourage brevity at deeper levels
    brevity_guidance = ""
    if depth >= 1:
        brevity_guidance = "Be concise and focus only on the most important points."
    if depth >= 2:
        brevity_guidance = "Be very brief and focus only on the essential information."
    if depth >= 3:
        brevity_guidance = "Provide only the most critical information in a highly condensed format."
    
    prompt = f"""You are a research assistant.
    
    Please provide a detailed answer to the following question: {question}
    
    {context_prompt}
    
    Your answer should be comprehensive but focused specifically on this question.
    Be concise and direct in your response while covering the key points.
    {brevity_guidance}
    """
    
    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=token_limit,
        temperature=0.5,
        system="You are a helpful and friendly research assistant that explains complex concepts in simple terms. Format your response with HTML tags for better readability: use <h3> for section titles, <p> for paragraphs, <ol> and <li> for numbered steps, <strong> for emphasis, and <hr> for section dividers. Be concise and direct.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return extract_content(message)

def get_concise_summary_for_broad_question(question, client, depth=0):
    """
    Get a concise summary for a question that has reached maximum recursion depth
    """
    # Adjust token limit based on depth
    token_limit = get_token_limit_for_depth(DEFAULT_ANSWER_MAX_TOKENS, depth)
    
    prompt = f"""You are a research assistant.
    
    The following question is very broad and has reached the maximum recursion depth in our system:
    
    {question}
    
    Please provide a CONCISE summary (no more than {300 - depth * 50} words) that:
    1. Provides a high-level overview of the key points related to this question
    2. Focuses only on the most essential information
    
    Format your response with HTML tags for better readability.
    """
    
    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=token_limit,
        temperature=0.5,
        system="You are a helpful research assistant that provides concise summaries of broad topics. Format your response with HTML tags for better readability: use <h3> for section titles, <p> for paragraphs, <strong> for emphasis.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return extract_content(message)

def get_vanilla_response_for_vague_question(question, client, depth=0):
    """
    Provide a response for questions that have a broad scope.
    """
    # Adjust token limit based on depth
    token_limit = get_token_limit_for_depth(DEFAULT_ANSWER_MAX_TOKENS, depth)
    
    prompt = f"""You are a research assistant.
    
    The following question has a broad scope that would benefit from a high-level overview:
    
    {question}
    
    Please provide a response that:
    1. Provides general information about the topic
    2. Focuses on the most common aspects or interpretations
    3. Gives a balanced overview of the main considerations
    
    Format your response with HTML tags for better readability.
    """
    
    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=token_limit,
        temperature=0.5,
        system="You are a helpful research assistant that provides informative overviews for broad topics. Format your response with HTML tags for better readability: use <h3> for section titles, <p> for paragraphs, <strong> for emphasis.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    content = extract_content(message)
    
    # Add a simple disclaimer at the beginning
    disclaimer = """<div class="note" style="background-color: #e6f7ff; border-left: 4px solid #1890ff; padding: 15px; margin-bottom: 20px;">
    <strong>Broad Topic Response</strong>
    </div>"""
    
    return disclaimer + content 