/**
 * Lambda Function URL Configuration
 * This file contains the configuration for direct Lambda invocation
 */

// Lambda Function URL Configuration
const lambdaConfig = {
    // Default Lambda Function URL - replace with your actual Lambda Function URL from CDK output
    // You can get this URL after deploying your CDK stack with:
    // aws cloudformation describe-stacks --stack-name PersonalAssistantDevResearchStack --query "Stacks[0].Outputs[?OutputKey=='ResearchGeneratorFunctionUrl'].OutputValue" --output text
    // For Prod:
    // functionUrl: 'https://qekzfmhc3bwg4rqqyh3dyiujza0bstto.lambda-url.us-west-2.on.aws/',
    // for dev
    functionUrl: 'https://3wfy3gdqgpf3xjqkb2kurxiufa0wypxt.lambda-url.us-west-2.on.aws/',

    // Default function name (used for display purposes only)
    // You can get this name after deploying your CDK stack with:
    // aws cloudformation describe-stacks --stack-name PersonalAssistantDevResearchStack --query "Stacks[0].Outputs[?OutputKey=='ResearchGeneratorFunctionName'].OutputValue" --output text
    // For Prod:
    // functionName: 'personal-assistant-prod-research-question-generator'
    // For Dev:
    functionName: 'personal-assistant-dev-research-question-generator'
};

// Function to invoke Lambda directly via Function URL
async function invokeLambda(params) {
    try {
        console.log('Invoking Lambda with params:', params);

        const response = await fetch(lambdaConfig.functionUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });

        if (!response.ok) {
            let errorMessage = `Lambda invocation failed: ${response.status} ${response.statusText}`;

            try {
                // Try to parse the error response as JSON
                const errorData = await response.json();
                console.error('Lambda error details:', errorData);

                if (errorData && errorData.error) {
                    errorMessage += `. ${errorData.error}`;
                }
            } catch (parseError) {
                // If we can't parse as JSON, get the text
                try {
                    const errorText = await response.text();
                    errorMessage += `. ${errorText}`;
                } catch (textError) {
                    console.error('Could not read error response text:', textError);
                }
            }

            throw new Error(errorMessage);
        }

        const result = await response.json();
        console.log('Lambda response:', result);
        return result;
    } catch (error) {
        console.error('Error invoking Lambda:', error);

        // Provide a more user-friendly error message
        if (error.message.includes("'answer'")) {
            throw new Error('The research engine encountered an issue generating an answer. Please try again with a more specific question.');
        } else {
            throw error;
        }
    }
} 