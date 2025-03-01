# Deep Research Assistant Frontend

This is the frontend for the Deep Research Assistant, a tool that uses AI to break down complex research questions into manageable sub-questions and provide comprehensive answers.

## Features

1. **User-friendly Interface**: Simple and intuitive design for asking research questions.
2. **Configurable Parameters**: Adjust how the AI processes your questions with these options:
   - **Maximum Recursion Depth**: Controls how many levels deep the question can be broken down (0-4).
   - **Maximum Sub-Questions**: Limits the number of sub-questions generated at each level (1-5).
   - **Recursion Threshold**: Determines how aggressive the system is about breaking down questions.
3. **Interactive Results**: View your results in three formats:
   - **Answer**: A comprehensive response to your research question.
   - **Question Tree**: Visual representation of how your question was broken down.
   - **Raw Data**: The complete JSON response from the API.

## How It Works

1. **Enter Your Question**: Type in a complex research question you want to explore.
2. **Configure Parameters** (Optional): Adjust the parameters or use the default values.
3. **Submit**: Click "Generate Research" to process your question.
4. **View Results**: Explore the comprehensive answer and the question breakdown tree.

## Technical Details

- The frontend can connect to the Research Generator Lambda function in two ways:
  1. Via API Gateway (original method)
  2. Directly via Lambda Function URL (new method, recommended for longer-running requests)
- The Lambda Function URL allows for longer execution times (up to 15 minutes) compared to API Gateway (max 30 seconds)
- The frontend is built with vanilla HTML, CSS, and JavaScript (no frameworks).

## Using Lambda Function URL

The website now uses direct invocation of the Lambda function using Lambda Function URLs, which bypasses the 30-second timeout limitation of API Gateway.

### Setting Up Lambda Function URL

1. Deploy your CDK stack with the Lambda Function URL enabled:
   ```bash
   cd cdk
   npm run deploy:dev  # or deploy:prod for production
   ```

### Testing with Lambda Function URL

When testing locally:

1. Start your local server using one of the methods below
2. Open the website in your browser
3. Submit your research question

The request will go directly to the Lambda function, bypassing API Gateway and its 30-second timeout limitation.

## Local Development and Testing

### Using Python's Built-in HTTP Server (Recommended)

1. Make sure you have Python installed (Python 3.x recommended)
2. Open a terminal and navigate to the website directory:
   ```bash
   cd /Users/Macbook/Github-Projects/personal-assistant/website
   ```
3. Start the HTTP server:
   ```bash
   python -m http.server 8000
   ```
4. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```
5. To stop the server, press `Ctrl+C` in the terminal

### Alternative Methods

#### Using Node.js and http-server

If you have Node.js installed:

1. Install http-server globally:
   ```bash
   npm install -g http-server
   ```
2. Navigate to the website directory:
   ```bash
   cd /Users/Macbook/Github-Projects/personal-assistant/website
   ```
3. Start the server:
   ```bash
   http-server -p 8000
   ```
4. Access the site at `http://localhost:8000`

#### Using VS Code Live Server Extension

1. Install the "Live Server" extension in VS Code
2. Open the website directory in VS Code
3. Right-click on `index.html` and select "Open with Live Server"

## Deployment

To deploy this frontend:

1. Upload all files in the `website` directory to your web hosting service.
2. No build process is required as this is a static website.

## API Parameters

The frontend sends the following parameters to the API:

- `expression`: The research question (required).
- `max_recursion_depth`: Maximum depth for breaking down questions (0-4, default: 2).
- `max_sub_questions`: Maximum number of sub-questions per level (1-5, default: 3).
- `recursion_threshold`: How conservative the system is about breaking down questions (0-2, default: 1).

## Response Format

The API returns a JSON object with the following properties:

- `explanation`: HTML-formatted comprehensive answer.
- `tree_visualization`: HTML for the interactive question tree visualization.
- `question_tree`: The complete question tree data structure.
- `parameters_used`: The parameters that were used for processing.

## Customization

To customize the appearance:
- Edit `css/styles.css` to change the styling.
- Modify `js/main.js` to alter the behavior.
- Update `index.html` to change the structure.

## API Endpoint Configuration

The Lambda Function URL is configured in the `js/aws-config.js` file. After deploying your CDK stack, run the `get-lambda-url.sh` script to automatically update this file with the correct URL. 