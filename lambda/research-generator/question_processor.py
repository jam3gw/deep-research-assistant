"""
Functions for processing questions and building the question tree.
"""
import json
import uuid
import asyncio
import concurrent.futures
from utils import extract_content
from config import (
    DEFAULT_MODEL, DEFAULT_EVALUATION_MAX_TOKENS, DEFAULT_ANSWER_MAX_TOKENS,
    DEFAULT_RECURSION_DEPTH, DEFAULT_SUB_QUESTIONS, DEFAULT_RECURSION_THRESHOLD,
    get_token_limit_for_depth
)
from answer_generator import (
    get_answer_for_question, 
    get_concise_summary_for_broad_question,
    get_vanilla_response_for_vague_question,
    get_answer_for_question_async,
    get_concise_summary_for_broad_question_async,
    get_vanilla_response_for_vague_question_async
)

# Main entry point that will be called by the Lambda handler
def process_question_node(node, client, max_recursion_depth=DEFAULT_RECURSION_DEPTH, 
                         max_sub_questions=DEFAULT_SUB_QUESTIONS, recursion_threshold=DEFAULT_RECURSION_THRESHOLD,
                         original_question=None):
    """
    Entry point for processing a question node. This function sets up the event loop
    and calls the async version of the processing function.
    """
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the async function in the event loop
        return loop.run_until_complete(
            process_question_node_async(node, client, max_recursion_depth, 
                                      max_sub_questions, recursion_threshold, original_question)
        )
    finally:
        # Clean up the event loop
        loop.close()

async def process_question_node_async(node, client, max_recursion_depth=DEFAULT_RECURSION_DEPTH, 
                                    max_sub_questions=DEFAULT_SUB_QUESTIONS, recursion_threshold=DEFAULT_RECURSION_THRESHOLD,
                                    original_question=None):
    """
    Async version of process_question_node that processes sub-questions in parallel.
    """
    depth = node['depth']
    question = node['question']
    
    # Track the original question for context
    if original_question is None:
        original_question = question  # The root question is the original question
    
    print(f"Processing question at depth {depth}: {question}")
    
    # Check if we've reached the maximum recursion depth
    if depth >= max_recursion_depth:
        print(f"WARNING: Maximum recursion depth ({max_recursion_depth}) reached for question: {question}")
        
        # Instead of error message, get a concise summary
        node['answer'] = await get_concise_summary_for_broad_question_async(question, client, depth)
        node['needs_breakdown'] = False
        node['max_depth_reached'] = True
        return
    
    # For questions at deeper levels, be more conservative about breaking them down
    if depth > 1:
        # At deeper levels, we should be more conservative about breaking down questions
        print(f"At depth {depth}, being more conservative about breaking down: {question}")
    
    # Determine if the question needs to be broken down
    needs_breakdown, sub_questions = await asyncio.to_thread(
        should_break_down_question, question, client, recursion_threshold, max_sub_questions, depth
    )
    
    # Additional check: if we're at depth > 0 and have no sub-questions or only one, don't break down
    if needs_breakdown and depth > 0 and (not sub_questions or len(sub_questions) <= 1):
        print(f"Overriding breakdown decision at depth {depth} because only {len(sub_questions)} sub-questions were generated")
        needs_breakdown = False
    
    # Validate that sub-questions are actually simpler than the parent question and stay on topic
    if needs_breakdown and depth > 0 and sub_questions:
        validated_sub_questions = await asyncio.to_thread(
            validate_sub_questions_simplicity, question, sub_questions, client, depth
        )
        if not validated_sub_questions:
            print(f"Overriding breakdown decision at depth {depth} because sub-questions were not valid (not simpler or off-topic)")
            needs_breakdown = False
        else:
            sub_questions = validated_sub_questions
    
    # Additional check: ensure sub-questions are relevant to the original question
    if needs_breakdown and depth > 0 and sub_questions:
        relevant_sub_questions = await asyncio.to_thread(
            validate_sub_questions_relevance, original_question, sub_questions, client
        )
        if not relevant_sub_questions:
            print(f"Overriding breakdown decision at depth {depth} because sub-questions were not relevant to the original question")
            needs_breakdown = False
        else:
            sub_questions = relevant_sub_questions
    
    node['needs_breakdown'] = needs_breakdown
    
    if needs_breakdown:
        print(f"Breaking down question into {len(sub_questions)} sub-questions")
        # Process each sub-question recursively in parallel
        node['children'] = []  # Ensure children is initialized as an empty list
        
        # Create sub-nodes first
        sub_nodes = []
        for sub_q in sub_questions:
            sub_node = {
                'id': str(uuid.uuid4()),
                'question': sub_q,
                'depth': depth + 1,  # Explicitly set depth as parent depth + 1
                'children': [],
                'parent_question': question,  # Store the parent question for context
                'original_question': original_question  # Store the original question for context
            }
            node['children'].append(sub_node)
            sub_nodes.append(sub_node)
        
        # Process all sub-nodes in parallel
        tasks = []
        for sub_node in sub_nodes:
            task = asyncio.create_task(
                process_question_node_async(
                    sub_node, client, max_recursion_depth, 
                    max_sub_questions, recursion_threshold, original_question
                )
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
    else:
        # This is a leaf node, check if it's too vague
        is_vague = await asyncio.to_thread(is_question_too_vague, question, client)
        
        if is_vague:
            print(f"Question is too vague, providing vanilla response: {question}")
            node['answer'] = await get_vanilla_response_for_vague_question_async(question, client, depth)
            node['is_vague'] = True
        else:
            # Get a detailed answer for a specific question
            print(f"Getting answer for leaf question: {question}")
            # Pass parent context if available
            parent_question = node.get('parent_question', None)
            # Also pass the original question for broader context
            node['answer'] = await get_answer_for_question_async(question, client, parent_question, depth, original_question)

def validate_sub_questions_simplicity(parent_question, sub_questions, client, depth):
    """
    Validate that sub-questions are actually simpler than the parent question.
    Returns a filtered list of sub-questions that are simpler, or an empty list if none are simpler.
    """
    if depth == 0 or not sub_questions:
        return sub_questions  # At depth 0, no simplification check needed
    
    prompt = f"""You are a research assistant tasked with evaluating whether sub-questions are simpler than their parent question and stay on topic.

Parent question: {parent_question}

Sub-questions:
{json.dumps(sub_questions, indent=2)}

For each sub-question, determine if it meets BOTH of these criteria:
1. It is GENUINELY SIMPLER than the parent question (more specific, narrower scope, less complex)
2. It STAYS ON TOPIC and is directly relevant to the parent question (not tangential or introducing unrelated topics)

A good sub-question:
- Is more specific and narrower in scope
- Focuses on a single, well-defined aspect of the parent question
- Is answerable with less complexity
- Does not introduce new complexity or broaden the scope
- Remains directly relevant to the parent question
- Does not deviate into tangential topics

Your response should be in JSON format:
{{
  "evaluations": [
    {{
      "sub_question": "sub-question 1",
      "is_valid": true/false,
      "reasoning": "Brief explanation focusing on simplicity and topic relevance"
    }},
    ...
  ]
}}
"""

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_EVALUATION_MAX_TOKENS,
        temperature=0.0,  # Zero temperature for maximum consistency
        system="You are a helpful research assistant that evaluates the quality of sub-questions. Always respond in valid JSON format. Be strict about ensuring sub-questions are both simpler AND stay on topic.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the JSON response
    content = extract_content(message)
    
    try:
        # Find JSON in the response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            result = json.loads(json_str)
            
            # Filter sub-questions to only include those that are simpler and on topic
            valid_sub_questions = []
            for eval_item in result.get('evaluations', []):
                if eval_item.get('is_valid', False):
                    valid_sub_questions.append(eval_item.get('sub_question'))
                else:
                    print(f"Removing invalid sub-question: {eval_item.get('sub_question')}")
                    print(f"Reasoning: {eval_item.get('reasoning')}")
            
            return valid_sub_questions
        else:
            print(f"Could not find JSON in response: {content}")
            return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response content: {content}")
        return []

def should_break_down_question(question, client, recursion_threshold=DEFAULT_RECURSION_THRESHOLD, max_sub_questions=DEFAULT_SUB_QUESTIONS, depth=0):
    """
    Use Anthropic to determine if a question should be broken down into sub-questions.
    Returns a tuple of (needs_breakdown, sub_questions)
    """
    # Adjust the prompt based on the recursion threshold and depth
    conservative_guidance = ""
    simplification_guidance = ""
    topic_focus_guidance = ""
    
    # Add depth-based guidance to ensure questions get simpler
    if depth > 0:
        simplification_guidance = f"""
CRITICAL: You are at recursion depth {depth}. At this depth, it is ESSENTIAL that any sub-questions you generate are SIGNIFICANTLY SIMPLER than the parent question.
Each sub-question MUST:
1. Be more specific and narrower in scope than the parent question
2. Focus on a single, well-defined aspect of the parent question
3. Be answerable with less complexity than the parent question
4. Avoid introducing new complexity or broadening the scope

DO NOT create sub-questions that:
- Are as complex as the original question
- Introduce new topics not directly related to the parent question
- Require their own complex breakdown
- Are vague or general in nature
"""
    else:
        # At depth 0 (root question), be more aggressive about breaking down
        simplification_guidance = """
ROOT QUESTION GUIDANCE: This is the original user question. For root questions, breaking down is STRONGLY PREFERRED unless the question is already very specific.
For broad questions at the root level, almost always break them down into more manageable sub-questions.
"""

    # Add topic focus guidance to ensure sub-questions stay on topic
    topic_focus_guidance = """
EXTREMELY IMPORTANT: All sub-questions MUST be directly related to the original question and should not deviate from the main topic.
Each sub-question should:
1. Explore a specific aspect of the ORIGINAL question
2. Maintain clear relevance to the main topic
3. Not introduce tangential or only loosely related topics
4. Together with other sub-questions, comprehensively cover the original question.

The goal is to break down the question into more manageable parts while ensuring all parts remain focused on answering the original question.
"""

    # Make the guidance less conservative for broad questions
    conservative_guidance = """
IMPORTANT: For broad, multi-faceted questions, breaking them down is STRONGLY PREFERRED.
Break down a question if ANY of these criteria are met:
1. The question covers multiple distinct topics or aspects
2. The question is broad enough that a direct answer would be superficial
3. Breaking it down would lead to more precise and valuable answers
4. The question would be better answered by exploring its components separately

SPECIAL CASES THAT SHOULD ALMOST ALWAYS BE BROKEN DOWN:
- Questions about "impacts" or "effects" (e.g., "How has X impacted Y?")
- Questions about trends or developments over time
- Questions involving comparisons between multiple things
- Questions about advantages/disadvantages or pros/cons
- Questions about historical developments or evolution of topics

For these special cases, assume breakdown is needed unless there's a compelling reason not to.
"""

    if recursion_threshold >= 1:
        conservative_guidance += """
For questions at deeper levels, be more selective about further breakdown, but still favor breaking down broad questions.
"""
    if recursion_threshold >= 2:
        conservative_guidance += """
At the deepest levels, only break down questions if absolutely necessary for comprehensive understanding.
"""

    prompt = f"""You are a research assistant tasked with breaking down complex questions into simpler sub-questions.

Given the following question, determine if it should be broken down into sub-questions for more thorough research.
{conservative_guidance}
{simplification_guidance}
{topic_focus_guidance}
If the question is already specific, focused on a single aspect, or can be answered comprehensively in one go, do NOT break it down.

Question: {question}

Your response should be in JSON format:
{{
  "needs_breakdown": true/false,
  "reasoning": "Brief explanation of why this question should or should not be broken down",
  "sub_questions": ["sub-question 1", "sub-question 2", ...]
}}

If needs_breakdown is false, sub_questions can be an empty array.
"""

    # Set temperature to 0 for maximum consistency
    temperature = 0.0
    
    system_message = "You are a research assistant that breaks down complex questions into simpler sub-questions when appropriate."
    system_message += " For broad questions covering multiple aspects, STRONGLY prefer to break them down into more specific sub-questions."
    system_message += " Questions about impacts, trends, comparisons, or historical developments should almost always be broken down."
    if depth > 0:
        system_message += f" At depth {depth}, you MUST ensure that sub-questions are SIGNIFICANTLY SIMPLER than their parent question."
    else:
        system_message += " For root questions (depth 0), be very aggressive about breaking them down unless they are already very specific."
    system_message += " Always respond in valid JSON format."
    system_message += " Ensure all sub-questions remain directly focused on the original topic and don't introduce tangential subjects."

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_EVALUATION_MAX_TOKENS,
        temperature=temperature,
        system=system_message,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the JSON response
    content = extract_content(message)
    
    try:
        # Find JSON in the response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            result = json.loads(json_str)
            
            # Log the reasoning for debugging
            if 'reasoning' in result:
                print(f"Breakdown decision reasoning: {result['reasoning']}")
            
            # Apply additional threshold-based filtering
            needs_breakdown = result.get('needs_breakdown', False)
            
            # Remove the random factor that could override breakdown decisions
            # Commented out to ensure consistency
            # if needs_breakdown:
            #     import random
            #     # 40% chance to override to false - more balanced approach
            #     if random.random() < 0.4:
            #         print("Moderate mode: Overriding breakdown decision to false")
            #         needs_breakdown = False
            
            # Ensure we don't exceed the maximum number of sub-questions
            if needs_breakdown:
                sub_questions = result.get('sub_questions', [])
                if len(sub_questions) > max_sub_questions:
                    sub_questions = sub_questions[:max_sub_questions]
                
                # Additional filter: if we have fewer than 2 sub-questions, don't break down
                # But make an exception for questions about impacts, trends, etc.
                if len(sub_questions) < 2:
                    # Check if this is a special case question that should be broken down even with just one sub-question
                    impact_keywords = ["impact", "effect", "influence", "change", "transform", "revolution"]
                    is_impact_question = any(keyword in question.lower() for keyword in impact_keywords)
                    
                    if is_impact_question and len(sub_questions) == 1:
                        # For impact questions, allow even a single good sub-question
                        print("Impact-related question with one sub-question, allowing breakdown")
                        return True, sub_questions
                    else:
                        print("Not enough sub-questions generated, overriding breakdown decision to false")
                        needs_breakdown = False
                        return False, []
                
                return needs_breakdown, sub_questions
            return False, []
        else:
            print(f"Could not find JSON in response: {content}")
            return False, []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response content: {content}")
        return False, []

def validate_sub_questions_relevance(original_question, sub_questions, client):
    """
    Validate that sub-questions are relevant to the original question.
    Returns a filtered list of sub-questions that are relevant, or an empty list if none are relevant.
    """
    if not sub_questions:
        return []
    
    prompt = f"""You are a research assistant tasked with evaluating whether sub-questions are relevant to the original research question.

Original research question: {original_question}

Sub-questions:
{json.dumps(sub_questions, indent=2)}

For each sub-question, determine if it is DIRECTLY RELEVANT to the original research question. A relevant sub-question:
1. Addresses a specific aspect of the original question
2. Helps answer the original question when combined with other sub-questions
3. Does not introduce topics that are tangential or unrelated to the original question
4. Maintains the same general subject matter as the original question

Your response should be in JSON format:
{{
  "evaluations": [
    {{
      "sub_question": "sub-question 1",
      "is_relevant": true/false,
      "reasoning": "Brief explanation of why this sub-question is or is not relevant to the original question"
    }},
    ...
  ]
}}
"""

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_EVALUATION_MAX_TOKENS,
        temperature=0.0,  # Zero temperature for maximum consistency
        system="You are a helpful research assistant that evaluates the relevance of sub-questions to the original research question. Always respond in valid JSON format. Be strict about ensuring sub-questions are directly relevant to the original question.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the JSON response
    content = extract_content(message)
    
    try:
        # Find JSON in the response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            result = json.loads(json_str)
            
            # Filter sub-questions to only include those that are relevant
            relevant_sub_questions = []
            for eval_item in result.get('evaluations', []):
                if eval_item.get('is_relevant', False):
                    relevant_sub_questions.append(eval_item.get('sub_question'))
                else:
                    print(f"Removing irrelevant sub-question: {eval_item.get('sub_question')}")
                    print(f"Reasoning: {eval_item.get('reasoning')}")
            
            return relevant_sub_questions
        else:
            print(f"Could not find JSON in response: {content}")
            return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response content: {content}")
        return []

def is_question_too_vague(question, client):
    """
    Determine if a question is too vague to provide a detailed answer.
    Returns True if the question is too vague, False otherwise.
    """
    prompt = f"""You are a research assistant tasked with evaluating questions.

Given the following question, determine if it is too vague to provide a detailed, specific answer:

Question: {question}

A question is too vague if:
1. It lacks specific context or parameters
2. It could be interpreted in many different ways
3. It's overly broad without clear focus
4. It uses ambiguous terms without clarification

Your response should be in JSON format:
{{
  "is_vague": true/false,
  "reasoning": "Brief explanation of why this question is or is not too vague"
}}
"""

    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=500,
        temperature=0.0,  # Zero temperature for maximum consistency
        system="You are a helpful research assistant that evaluates the specificity of questions. Always respond in valid JSON format.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the JSON response
    content = extract_content(message)
    
    try:
        # Find JSON in the response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            result = json.loads(json_str)
            
            # Log the reasoning for debugging
            if 'reasoning' in result:
                print(f"Vagueness evaluation reasoning: {result['reasoning']}")
            
            return result.get('is_vague', False)
        else:
            print(f"Could not find JSON in response: {content}")
            return False
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response content: {content}")
        return False 