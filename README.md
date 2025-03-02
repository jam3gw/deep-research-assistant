# Personal Research Assistant

A sophisticated AI-powered research assistant that breaks down complex questions into simpler sub-questions, answers them, and synthesizes the results into comprehensive explanations.

## Overview

This application uses Claude AI (via Anthropic's API) to create a hierarchical approach to answering complex research questions. Instead of treating all questions the same way, the system:

1. Analyzes the complexity of the question
2. For simple questions, provides direct answers
3. For complex questions:
   - Breaks them down into simpler sub-questions
   - Recursively processes these sub-questions
   - Synthesizes the answers into a comprehensive explanation
   - Provides an interactive visualization of the question breakdown

## Deep Research Assistant: Under the Hood

The Deep Research Assistant uses a sophisticated recursive approach to handle complex research questions:

### How It Works

1. **Question Analysis**: When a question is submitted, the system first analyzes its complexity to determine if it needs to be broken down.
2. **Recursive Breakdown**: Complex questions are intelligently divided into simpler sub-questions, which may be further broken down if needed (up to the maximum recursion depth).
3. **Parallel Processing**: The system processes multiple sub-questions simultaneously to provide faster results.
4. **Individual Answers**: Each leaf question (one that doesn't need further breakdown) receives its own detailed answer.
5. **Answer Synthesis**: All individual answers are combined into a comprehensive, well-structured response to the original question.
6. **Visualization**: The question tree visualization shows exactly how the question was broken down and answered.

### Technical Implementation

- **Recursive Algorithm**: The core of the system is a recursive algorithm that breaks down questions and processes them in a tree-like structure.
- **Intelligent Validation**: The system validates that sub-questions are genuinely simpler than their parent questions and relevant to the original query.
- **Parallel Processing**: Multiple sub-questions are processed concurrently using async/await patterns for efficiency.
- **Exponential Backoff**: API calls include retry logic with exponential backoff to handle rate limiting and service overloads.
- **Adaptive Response Generation**: Different types of questions receive different treatment (e.g., vague questions, broad topics, specific inquiries).

### Example Questions to Try

The system excels at handling complex, multi-faceted questions such as:

1. "What are the economic and environmental impacts of renewable energy adoption globally?"
2. "How has artificial intelligence influenced modern healthcare systems, and what ethical concerns have emerged?"
3. "What are the psychological and sociological factors that contribute to the spread of misinformation on social media?"
4. "How do different educational approaches affect childhood development and future career success?"
5. "What are the most promising technologies for addressing climate change, and what are their limitations?"

## Architecture

The application consists of:

- **AWS Lambda Function**: Handles the question processing logic
- **Web Interface**: Allows users to submit questions and view results
- **AWS CDK Infrastructure**: Manages deployment and configuration

### Key Components

- **Lambda Function**: Processes questions using the Anthropic API
- **SSM Parameter Store**: Securely stores the Anthropic API key
- **Function URL**: Provides a serverless HTTP endpoint for the Lambda
- **Web Interface**: Static HTML/JS/CSS for user interaction

## How It Works

### AI Agent Workflow

1. **Question Analysis**: The system first determines if a question is simple or complex
2. **Question Breakdown**: Complex questions are recursively broken down into simpler sub-questions
3. **Answer Generation**: Each leaf question is answered individually
4. **Answer Synthesis**: The individual answers are combined into a comprehensive explanation
5. **Visualization**: An interactive tree visualization shows the question breakdown

### Intelligent Features

- **Complexity Detection**: Automatically determines if a question needs to be broken down
- **Recursion Control**: Limits the depth of question breakdown to prevent infinite recursion
- **Simplicity Validation**: Ensures sub-questions are genuinely simpler than their parent questions
- **Vagueness Detection**: Identifies and handles vague questions differently
- **Adaptive Response**: Adjusts the level of detail based on question complexity

## Configuration

### Environment Variables

The Lambda function requires the following environment variables:

- `ANTHROPIC_API_KEY_SECRET_NAME`: SSM parameter name containing the Anthropic API key

### AWS Resources

- **Lambda Function**: `personal-assistant-dev-research-question-generator`
- **API Endpoint**: Lambda Function URL (no API Gateway required)
- **SSM Parameter**: `/personal-assistant/dev/anthropic-api-key-secret-arn`

### Local Development

1. Clone the repository
2. Set up your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```
3. Run the local web server:
   ```bash
   cd website
   python -m http.server 8000
   ```
4. Access the application at `http://localhost:8000`

### Testing Locally

You can test the research generator locally using the provided test script:

```bash
cd lambda/research-generator
python test_locally.py "Your research question here"
```

Additional options:
```bash
# Set recursion depth and max sub-questions
python test_locally.py --depth 3 --sub-questions 4 "Your research question"

# Skip visualization to save time
python test_locally.py --skip-visualization "Your research question"
```

## Deployment

The application is deployed using AWS CDK:

```bash
cd cdk
npm install
cdk deploy
```

## API Reference

### Request Format

```json
{
  "expression": "Your research question here",
  "max_recursion_depth": 3,
  "max_sub_questions": 3,
  "recursion_threshold": 1
}
```

### Response Format

```json
{
  "explanation": "HTML-formatted comprehensive answer",
  "tree_visualization": "Interactive HTML visualization of the question tree",
  "question_tree": {
    "id": "uuid",
    "question": "Original question",
    "depth": 0,
    "children": [
      {
        "id": "uuid",
        "question": "Sub-question 1",
        "depth": 1,
        "answer": "Answer to sub-question 1",
        "children": []
      },
      // More sub-questions...
    ]
  },
  "parameters_used": {
    "max_recursion_depth": 3,
    "max_sub_questions": 3,
    "recursion_threshold": 1
  },
  "success": true,
  "formatted": true
}
```

## CORS Configuration

The Lambda function includes CORS headers to allow cross-origin requests from web browsers. The `Access-Control-Allow-Origin` header is set to `*` to allow requests from any origin.

## License

[MIT License](LICENSE) 