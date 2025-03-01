# Research Generator

This component generates structured research questions and outlines for any given topic using the Anthropic Claude API.

## Features

- Analyzes a user-provided topic and breaks it down into key subtopics
- Generates specific research questions for each subtopic
- Assigns confidence scores to each question
- Returns a structured JSON response with the analysis results
- Includes error handling for vague or extremely broad topics

## Architecture

The Research Generator consists of:

1. A Python Lambda function that processes requests and calls the Anthropic API
2. An API Gateway endpoint that exposes the Lambda function
3. Integration with AWS Secrets Manager to securely store the Anthropic API key

## Local Testing

To test the function locally before deployment:

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set your Anthropic API key as an environment variable:
   ```
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

3. Run the test script with a sample topic:
   ```
   python test_locally.py "climate change impacts on agriculture"
   ```

4. Check the output in the console and in the generated `research_output.json` file

## API Usage

Once deployed, you can call the API with a POST request:

```bash
curl -X POST \
  https://your-api-gateway-url/research \
  -H 'Content-Type: application/json' \
  -d '{
    "topic": "climate change impacts on agriculture"
  }'
```

### Request Format

```json
{
  "topic": "your research topic here"
}
```

### Response Format

```json
{
  "topic": "climate change impacts on agriculture",
  "subtopics": [
    {
      "name": "Crop Yields and Production",
      "description": "How climate change affects agricultural productivity",
      "questions": [
        {
          "question": "How will rising temperatures affect global wheat production by 2050?",
          "confidence": 0.92,
          "rationale": "Wheat is a temperature-sensitive crop grown globally, making it an important indicator of climate impacts"
        },
        {
          "question": "What adaptation strategies can maintain crop yields in regions experiencing increased drought?",
          "confidence": 0.88,
          "rationale": "Drought adaptation is critical for food security in many agricultural regions"
        }
      ]
    },
    // Additional subtopics...
  ],
  "metadata": {
    "model": "claude-3-sonnet-20240229",
    "generated_at": "msg_01234abcd",
    "token_count": 1234
  }
}
```

## Deployment

The Research Generator is deployed as part of the CDK stack. To deploy:

```bash
cd cdk
npm run deploy:dev
```

This will deploy the Research Generator stack along with other stacks in the project.

## Error Handling

The API returns appropriate HTTP status codes:

- 200: Success
- 400: Invalid input (e.g., topic too short or too long)
- 500: Server error (e.g., issue with the Anthropic API)

Error responses include a descriptive message:

```json
{
  "error": "Topic is too short. Please provide a more descriptive topic."
}
``` 