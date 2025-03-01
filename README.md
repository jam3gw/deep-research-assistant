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