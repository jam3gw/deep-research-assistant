# Research Question Generator Frontend

This is the frontend for the Research Question Generator, a tool that uses AI to break down complex research questions into manageable sub-questions and provide comprehensive answers.

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

- The frontend connects to the Research Generator Lambda function via API Gateway.
- The API endpoint is currently hardcoded to: `https://ow5zhzdho1.execute-api.us-west-2.amazonaws.com/prod/`
- The frontend is built with vanilla HTML, CSS, and JavaScript (no frameworks).

## Deployment

To deploy this frontend:

1. Upload all files in the `website` directory to your web hosting service.
2. No build process is required as this is a static website.

## Local Development

To run the frontend locally:

1. Clone the repository.
2. Navigate to the `website` directory.
3. Open `index.html` in your browser.

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

To change the API endpoint:
1. Open `js/main.js`
2. Update the `API_ENDPOINT` constant at the top of the file. 