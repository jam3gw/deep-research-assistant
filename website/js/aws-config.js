/**
 * Lambda Function URL Configuration
 * This file contains the configuration for direct Lambda invocation
 */

// Lambda Function URL Configuration
const lambdaConfig = {
    // Default Lambda Function URL - replace with your actual Lambda Function URL from CDK output
    // You can get this URL after deploying your CDK stack with:
    // aws cloudformation describe-stacks --stack-name PersonalAssistantDevResearchStack --query "Stacks[0].Outputs[?OutputKey=='ResearchGeneratorFunctionUrl'].OutputValue" --output text
    functionUrl: 'https://3wfy3gdqgpf3xjqkb2kurxiufa0wypxt.lambda-url.us-west-2.on.aws/',

    // Default function name (used for display purposes only)
    // You can get this name after deploying your CDK stack with:
    // aws cloudformation describe-stacks --stack-name PersonalAssistantDevResearchStack --query "Stacks[0].Outputs[?OutputKey=='ResearchGeneratorFunctionName'].OutputValue" --output text
    functionName: 'personal-assistant-dev-research-question-generator'
};

// Function to invoke Lambda directly via Function URL
async function invokeLambda(params) {
    try {
        const response = await fetch(lambdaConfig.functionUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Lambda invocation failed: ${response.status} ${response.statusText}. ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error invoking Lambda:', error);
        throw error;
    }
} 