import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as path from 'path';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';

export interface ResearchStackProps extends cdk.StackProps {
    environmentName: string;
}

export class ResearchStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: ResearchStackProps) {
        super(scope, id, props);

        // Get the Anthropic API key secret from SSM Parameter Store
        const anthropicApiParam = new ssm.StringParameter(this, 'AnthropicApiParameter', {
            parameterName: `/personal-assistant/${props.environmentName}/anthropic-api-key-secret-arn`,
            stringValue: process.env.ANTHROPIC_API_KEY ?? (() => { throw new Error('ANTHROPIC_API_KEY not set in environment') })(),
            description: 'API Key for Anthropic Claude API',
            tier: ssm.ParameterTier.STANDARD,
        });

        // Create a Lambda function for the research generator
        const researchGenerator = new PythonFunction(this, 'ResearchGenerator', {
            entry: path.join(__dirname, '../../lambda/research-generator'),
            index: 'lambda_function.py',
            handler: 'lambda_handler',
            timeout: cdk.Duration.minutes(5),
            runtime: lambda.Runtime.PYTHON_3_9,
            memorySize: 2048,
            environment: {
                ANTHROPIC_API_KEY_SECRET_NAME: anthropicApiParam.parameterName,
                ENVIRONMENT: props.environmentName,
            },
            logRetention: logs.RetentionDays.ONE_WEEK,
            bundling: {
                assetExcludes: [
                    'venv',
                    '__pycache__',
                    'research_output.json',
                    'test_locally.py',
                    'test_setup.py',
                    'test_deployed.py',
                    'setup_local_env.sh'
                ]
            }
        });

        // Grant the Lambda function permission to read the Anthropic API key
        researchGenerator.addToRolePolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: ['ssm:GetParameter'],
            resources: [anthropicApiParam.parameterArn],
        }));

        // Add a Lambda Function URL with CORS enabled
        const functionUrl = researchGenerator.addFunctionUrl({
            authType: lambda.FunctionUrlAuthType.NONE, // No authentication required
            cors: {
                allowedOrigins: ['*'], // Allow all origins
                allowedMethods: [lambda.HttpMethod.ALL], // Allow all HTTP methods
                allowedHeaders: ['*'], // Allow all headers
                allowCredentials: true, // Allow credentials
            },
        });

        // Create an API Gateway REST API
        const api = new apigateway.RestApi(this, 'ResearchAPI', {
            restApiName: `research-generator-api-${props.environmentName}`,
            description: 'API for generating research questions and outlines',
            defaultCorsPreflightOptions: {
                allowOrigins: apigateway.Cors.ALL_ORIGINS, // Or specify domains: ['https://deep-research-assistant.dev.jake-moses.com']
                allowMethods: apigateway.Cors.ALL_METHODS,
                allowHeaders: ['Content-Type'],
            }
        });

        // Create a resource and method for the API
        const researchResource = api.root.addResource('research');
        researchResource.addMethod('POST', new apigateway.LambdaIntegration(researchGenerator), {
            apiKeyRequired: false, // Set to true if you want to require an API key
        });

        // Output the API endpoint URL
        new cdk.CfnOutput(this, 'ResearchAPIEndpoint', {
            value: api.url,
            description: 'The URL of the Research Generator API',
        });

        // Output the Lambda function ARN
        new cdk.CfnOutput(this, 'ResearchGeneratorArn', {
            value: researchGenerator.functionArn,
            description: 'The ARN of the Research Generator Lambda function',
        });

        // Output the Lambda Function URL
        new cdk.CfnOutput(this, 'ResearchGeneratorFunctionUrl', {
            value: functionUrl.url,
            description: 'The URL of the Research Generator Lambda Function URL',
        });

        // Output the Lambda function name
        new cdk.CfnOutput(this, 'ResearchGeneratorFunctionName', {
            value: researchGenerator.functionName,
            description: 'The name of the Research Generator Lambda function',
        });
    }
} 