import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as connect from 'aws-cdk-lib/aws-connect';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as path from 'path';

export interface ConnectStackProps extends cdk.StackProps {
    environmentName: string;
    phoneNumber?: string; // Optional: If you want to provision a phone number
    secretsStackName?: string; // Optional: Name of the secrets stack to reference
}

export class ConnectStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: ConnectStackProps) {
        super(scope, id, props);

        // Get the Anthropic API key secret from SSM Parameter Store
        const secretArnParam = ssm.StringParameter.fromStringParameterAttributes(this, 'AnthropicApiKeySecretArnParam', {
            parameterName: `/personal-assistant/${props.environmentName}/anthropic-api-key-secret-arn`,
        });

        // Import the secret using the ARN from SSM
        const anthropicApiKey = secretsmanager.Secret.fromSecretAttributes(this, 'AnthropicApiKey', {
            secretCompleteArn: secretArnParam.stringValue,
        });

        // Create a Lambda function for handling the conversation with Anthropic
        const conversationHandler = new lambda.Function(this, 'ConversationHandler', {
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: 'lambda_function.lambda_handler',
            code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/conversation-handler')),
            timeout: cdk.Duration.minutes(15), // Longer timeout for conversations
            memorySize: 1024,
            environment: {
                ANTHROPIC_API_KEY_SECRET_NAME: anthropicApiKey.secretName,
                ENVIRONMENT: props.environmentName,
            },
            logRetention: logs.RetentionDays.ONE_WEEK,
        });

        // Grant the Lambda function permission to read the Anthropic API key
        anthropicApiKey.grantRead(conversationHandler);

        // Create an AWS Connect instance
        const connectInstance = new connect.CfnInstance(this, 'ConnectInstance', {
            instanceAlias: `personal-assistant-${props.environmentName}`,
            identityManagementType: 'CONNECT_MANAGED', // Use Connect's built-in user management
            attributes: {
                inboundCalls: true,
                outboundCalls: true,
                contactflowLogs: true
            }
        });

        // Create a Lambda function integration for AWS Connect
        const connectLambdaIntegration = new lambda.Function(this, 'ConnectLambdaIntegration', {
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: 'lambda_function.lambda_handler',
            code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/connect-integration')),
            timeout: cdk.Duration.minutes(5),
            memorySize: 512,
            environment: {
                CONVERSATION_HANDLER_FUNCTION_NAME: conversationHandler.functionName,
                ENVIRONMENT: props.environmentName,
            },
            logRetention: logs.RetentionDays.ONE_WEEK,
        });

        // Grant the Connect Lambda integration permission to invoke the conversation handler
        conversationHandler.grantInvoke(connectLambdaIntegration);

        // Create an IAM role for the AWS Connect instance to invoke the Lambda function
        const connectLambdaRole = new iam.Role(this, 'ConnectLambdaRole', {
            assumedBy: new iam.ServicePrincipal('connect.amazonaws.com'),
            managedPolicies: [
                iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonConnect_FullAccess'),
            ],
        });

        // Grant the Connect Lambda role permission to invoke the Lambda function
        connectLambdaIntegration.grantInvoke(connectLambdaRole);

        // If a phone number is provided, provision it for the Connect instance
        if (props.phoneNumber) {
            // Note: Phone number provisioning requires additional setup and may need manual steps
            // This is a placeholder for the phone number provisioning logic
            new cdk.CfnOutput(this, 'PhoneNumberInfo', {
                value: `Phone number ${props.phoneNumber} needs to be manually provisioned in the AWS Connect console`,
                description: 'Information about phone number provisioning',
            });
        }

        // Output the Connect instance ARN
        new cdk.CfnOutput(this, 'ConnectInstanceArn', {
            value: connectInstance.attrArn,
            description: 'The ARN of the AWS Connect instance',
        });

        // Output the Connect instance URL
        new cdk.CfnOutput(this, 'ConnectInstanceUrl', {
            value: `https://${connectInstance.attrId}.awsapps.com/connect/`,
            description: 'The URL of the AWS Connect instance',
        });

        // Output the Lambda function ARNs
        new cdk.CfnOutput(this, 'ConversationHandlerArn', {
            value: conversationHandler.functionArn,
            description: 'The ARN of the conversation handler Lambda function',
        });

        new cdk.CfnOutput(this, 'ConnectLambdaIntegrationArn', {
            value: connectLambdaIntegration.functionArn,
            description: 'The ARN of the Connect Lambda integration function',
        });
    }
} 