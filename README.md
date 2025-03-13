# Deep Research Assistant

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
- **API Gateway**: Provides a REST API endpoint
- **Web Interface**: Static HTML/JS/CSS for user interaction
- **CloudFront**: Distributes the web interface globally
- **Route53**: Manages DNS records for the domains

## Environments

The application supports two environments:

- **Development**: Deployed at `deep-research-assistant.dev.jake-moses.com`
- **Production**: Deployed at `deep-research-assistant.jake-moses.com`

## Configuration

### Environment Variables

The Lambda function requires different environment variables depending on the environment:

#### Development
- `ANTHROPIC_API_KEY`: Development environment API key

#### Production
- `DEEP_RESEARCH_PROD_ANTHROPIC_KEY`: Production environment API key

### AWS Resources

Resources are created for each environment with the following naming pattern:

#### Development
- **Lambda Function**: `personal-assistant-dev-research-question-generator`
- **API Gateway**: `research-generator-api-dev`
- **SSM Parameter**: `/personal-assistant/dev/anthropic-api-key-secret-arn`

#### Production
- **Lambda Function**: `personal-assistant-prod-research-question-generator`
- **API Gateway**: `research-generator-api-prod`
- **SSM Parameter**: `/personal-assistant/prod/anthropic-api-key-secret-arn`

### Local Development

1. Clone the repository
2. Set up your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```
3. Install dependencies:
   ```bash
   cd lambda/research-generator
   ./setup_local_env.sh
   ```
4. Run the local web server:
   ```bash
   cd website
   python -m http.server 8000
   ```
5. Access the application at `http://localhost:8000`

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

# Control recursion behavior
python test_locally.py --threshold 0 "Your question"  # More aggressive breakdown
python test_locally.py --threshold 1 "Your question"  # Default
python test_locally.py --threshold 2 "Your question"  # More conservative

# Skip visualization to save time
python test_locally.py --skip-visualization "Your research question"
```

## Deployment

The application is deployed using AWS CDK. Different commands are available for each environment:

### Development Environment
```bash
cd cdk
npm install
export ANTHROPIC_API_KEY=your_dev_key
npm run deploy:dev
```

### Production Environment
```bash
cd cdk
npm install
export DEEP_RESEARCH_PROD_ANTHROPIC_KEY=your_prod_key
npm run deploy:prod
```

### Other Useful Commands
```bash
# Compare changes before deployment
npm run diff:dev    # For development
npm run diff:prod   # For production

# Generate CloudFormation templates
npm run synth:dev   # For development
npm run synth:prod  # For production

# Remove resources
npm run destroy:dev    # Remove development environment
npm run destroy:prod   # Remove production environment
npm run destroy:all    # Remove all environments
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
  "explanation": "HTML-formatted comprehensive answer with source citations",
  "tree_visualization": "Interactive HTML visualization of the question tree with sources",
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
        "sources": [
          {
            "title": "Source document title",
            "url": "Source URL",
            "relevance_score": 0.95
          }
        ],
        "children": []
      }
    ]
  },
  "parameters_used": {
    "max_recursion_depth": 3,
    "max_sub_questions": 3,
    "recursion_threshold": 1,
    "token_reserve": 1000
  },
  "success": true,
  "formatted": true
}
```

## Security

- All traffic is served over HTTPS
- API keys are stored securely in SSM Parameter Store
- CORS is configured to allow requests from specific domains
- CloudFront distribution is configured with security best practices

## License

[MIT License](LICENSE)

### Key Features

- **Question Breakdown**: Decomposes complex questions into manageable sub-questions
- **Source Attribution**: Provides detailed source information for answers using RAG and BRAVE technologies
- **Token Management**: Efficiently manages token usage to ensure comprehensive answers with proper source citations
- **Interactive Visualization**: Shows the question breakdown tree with source information
- **Recursive Processing**: Handles nested questions with configurable depth 