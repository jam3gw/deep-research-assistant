"""
Functions for aggregating answers from the question tree.
"""
import asyncio
from utils import extract_content
from config import DEFAULT_MODEL, DEFAULT_SYNTHESIS_MAX_TOKENS

async def aggregate_answers_async(question_tree, client):
    """
    Async version of aggregate_answers
    """
    return await asyncio.to_thread(aggregate_answers, question_tree, client)

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

I've broken down a complex question into sub-questions and found answers to each. Now I need you to synthesize this information into a concise, well-structured answer to the original question.

Original question: {question_tree['question']}

{special_notes}

Here is the breakdown of questions and answers:

{tree_representation}

Please synthesize all this information into a concise, well-structured answer to the original question. Focus on clarity and brevity while ensuring all key points are covered.

IMPORTANT FORMATTING GUIDELINES:
1. Use a clear hierarchical structure with headings and subheadings
2. Keep paragraphs short and focused (3-4 sentences maximum)
3. Use bullet points for lists whenever possible
4. Avoid unnecessary repetition or filler text
5. Include a very brief introduction and conclusion
6. Use HTML formatting for better readability

Your response should be approximately 30-40% shorter than a typical comprehensive explanation while maintaining all key information.
"""

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_SYNTHESIS_MAX_TOKENS,
        temperature=0.0,
        system="""You are a helpful research assistant that synthesizes information from multiple sources into concise, well-structured responses.

FORMAT YOUR RESPONSE WITH THESE HTML ELEMENTS:
- <div class="research-answer"> as the main container
- <h2> for the main title
- <h3> for section titles
- <p> for paragraphs (keep them short)
- <ul> and <li> for unordered lists
- <ol> and <li> for ordered lists
- <strong> for emphasis
- <hr> for section dividers
- <div class="summary"> for the conclusion

STYLING GUIDELINES:
- Be concise and direct
- Prioritize clarity over comprehensiveness
- Use bullet points liberally
- Avoid unnecessary words and phrases
- Structure information hierarchically
- Make the content scannable

Your goal is to create a response that is both informative and easy to quickly digest.""",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    content = extract_content(message)
    
    # Add CSS styling for better presentation
    css_styling = """
<style>
.research-answer {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    color: #333;
}
h2 {
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
    margin-top: 30px;
}
h3 {
    color: #2980b9;
    margin-top: 25px;
    font-weight: 600;
}
p {
    margin-bottom: 15px;
}
ul, ol {
    margin-bottom: 20px;
    padding-left: 25px;
}
li {
    margin-bottom: 8px;
}
.summary {
    background-color: #f8f9fa;
    border-left: 4px solid #3498db;
    padding: 15px;
    margin: 25px 0;
}
hr {
    border: 0;
    height: 1px;
    background: #e0e0e0;
    margin: 25px 0;
}
.note {
    background-color: #e6f7ff;
    border-left: 4px solid #1890ff;
    padding: 15px;
    margin-bottom: 20px;
}
</style>
"""
    
    # Ensure content is wrapped in the main container if not already
    if "<div class=\"research-answer\">" not in content:
        content = f"<div class=\"research-answer\">{content}</div>"
    
    # Add disclaimers at the beginning if needed
    disclaimers = ""
    if has_vague_questions:
        disclaimers += """<div class="note">
        <strong>Note:</strong> Some topics include broader responses due to their wide scope.
        </div>"""
    
    # Combine everything
    final_output = css_styling + disclaimers + content
    
    return final_output

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