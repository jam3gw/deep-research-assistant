import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as path from 'path';

export interface ResearchStackProps extends cdk.StackProps {
    environmentName: string;
    secretsStackName?: string; // Optional: Name of the secrets stack to reference
}

export class ResearchStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: ResearchStackProps) {
        super(scope, id, props);

        // Get the Anthropic API key secret from SSM Parameter Store
        const secretArnParam = ssm.StringParameter.fromStringParameterAttributes(this, 'AnthropicApiKeySecretArnParam', {
            parameterName: `/personal-assistant/${props.environmentName}/anthropic-api-key-secret-arn`,
        });

        // Import the secret using the ARN from SSM
        const anthropicApiKey = secretsmanager.Secret.fromSecretAttributes(this, 'AnthropicApiKey', {
            secretCompleteArn: secretArnParam.stringValue,
        });

        // Create a Lambda function for the research generator
        const researchGenerator = new lambda.Function(this, 'ResearchGenerator', {
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: 'lambda_function.lambda_handler',
            code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/research-generator')),
            timeout: cdk.Duration.minutes(5),
            memorySize: 512,
            environment: {
                ANTHROPIC_API_KEY_SECRET_NAME: anthropicApiKey.secretName,
                ENVIRONMENT: props.environmentName,
            },
            logRetention: logs.RetentionDays.ONE_WEEK,
        });

        // Grant the Lambda function permission to read the Anthropic API key
        anthropicApiKey.grantRead(researchGenerator);

        // Create an API Gateway REST API
        const api = new apigateway.RestApi(this, 'ResearchAPI', {
            restApiName: `research-generator-api-${props.environmentName}`,
            description: 'API for generating research questions and outlines',
            defaultCorsPreflightOptions: {
                allowOrigins: apigateway.Cors.ALL_ORIGINS,
                allowMethods: apigateway.Cors.ALL_METHODS,
            },
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
    }
} 