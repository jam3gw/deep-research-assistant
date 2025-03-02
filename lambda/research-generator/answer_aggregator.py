"""
Functions for aggregating answers from the question tree.
"""
from utils import extract_content
from config import DEFAULT_MODEL, DEFAULT_SYNTHESIS_MAX_TOKENS

def aggregate_answers(question_tree, client):
    """
    Aggregate the answers from the question tree into a comprehensive final answer
    """
    # First, ensure all branches have been answered
    if not has_complete_answers(question_tree):
        return "Error: Not all questions have been answered. Please try again."
    
    # Create a structured representation of the question tree for Claude
    tree_representation = format_tree_for_aggregation(question_tree)
    
    # Check if any nodes were too vague
    has_vague_questions = has_vague_question_nodes(question_tree)
    
    special_notes = ""
    if has_vague_questions:
        special_notes += """
Note: Some questions in this research were addressed with broader topic responses due to their scope.
"""
    
    prompt = f"""You are a research assistant tasked with synthesizing information from multiple sources.

I've broken down a complex question into sub-questions and found answers to each. Now I need you to synthesize this information into a comprehensive answer to the original question.

Original question: {question_tree['question']}

{special_notes}

Here is the breakdown of questions and answers:

{tree_representation}

Please synthesize all this information into a comprehensive, well-structured answer to the original question. Use HTML formatting for better readability.
Be concise and direct while ensuring all key points are covered.
"""

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_SYNTHESIS_MAX_TOKENS,
        temperature=0.0,
        system="You are a helpful research assistant that synthesizes information from multiple sources. Format your response with HTML tags for better readability: use <h3> for section titles, <p> for paragraphs, <ol> and <li> for numbered steps, <strong> for emphasis, and <hr> for section dividers. Be concise and direct in your explanations.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    content = extract_content(message)
    
    # Add disclaimers at the beginning if needed
    disclaimers = ""
    if has_vague_questions:
        disclaimers += """<div class="note" style="background-color: #e6f7ff; border-left: 4px solid #1890ff; padding: 15px; margin-bottom: 20px;">
        <strong>Note:</strong> Some topics include broader responses due to their wide scope.
        </div>"""
    
    if disclaimers:
        return disclaimers + content
    
    return content

def has_complete_answers(node):
    """
    Check if all leaf nodes in the tree have answers
    """
    if node['needs_breakdown']:
        # This is not a leaf node, check all children
        return all(has_complete_answers(child) for child in node['children'])
    else:
        # This is a leaf node, check if it has an answer
        return 'answer' in node and node['answer']

def format_tree_for_aggregation(node, indent=0):
    """
    Format the question tree for aggregation, with proper indentation
    """
    result = "  " * indent + f"Question: {node['question']}\n"
    
    if node['needs_breakdown']:
        result += "  " * indent + "Sub-questions and answers:\n"
        for child in node['children']:
            result += format_tree_for_aggregation(child, indent + 1)
    else:
        result += "  " * indent + f"Answer: {node['answer']}\n\n"
    
    return result

def has_max_depth_nodes(node):
    """
    Check if the tree has any nodes that reached maximum depth
    """
    if node.get('max_depth_reached', False):
        return True
    
    if node.get('needs_breakdown', False):
        # Check children
        for child in node['children']:
            if has_max_depth_nodes(child):
                return True
    
    return False

def has_vague_question_nodes(node):
    """
    Check if the tree has any nodes that were identified as too vague
    """
    if node.get('is_vague', False):
        return True
    
    if node.get('needs_breakdown', False):
        # Check children
        for child in node['children']:
            if has_vague_question_nodes(child):
                return True
    
    return False 