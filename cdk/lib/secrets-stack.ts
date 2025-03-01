import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ssm from 'aws-cdk-lib/aws-ssm';

export interface SecretsStackProps extends cdk.StackProps {
    environmentName: string;
}

export class SecretsStack extends cdk.Stack {
    public readonly anthropicApiKeySecret: secretsmanager.Secret;

    constructor(scope: Construct, id: string, props: SecretsStackProps) {
        super(scope, id, props);

        // Hardcoded Anthropic API key - for development purposes only
        // In production, this should be managed more securely
        const hardcodedApiKey = <ANTHROPIC_API_KEY>;

        // Create a secret for the Anthropic API key
        const secretName = `anthropic-api-key-${props.environmentName}`;

        // Create a new secret with the hardcoded API key
        this.anthropicApiKeySecret = new secretsmanager.Secret(this, 'AnthropicApiKey', {
            secretName: secretName,
            description: 'API key for Anthropic Claude',
            secretStringValue: cdk.SecretValue.unsafePlainText(hardcodedApiKey),
        });

        // Store the secret ARN in SSM Parameter Store for cross-stack reference
        new ssm.StringParameter(this, 'AnthropicApiKeySecretArn', {
            parameterName: `/personal-assistant/${props.environmentName}/anthropic-api-key-secret-arn`,
            description: 'ARN of the Anthropic API key secret',
            stringValue: this.anthropicApiKeySecret.secretArn,
        });

        // Output the secret ARN
        new cdk.CfnOutput(this, 'AnthropicApiKeySecretArnOutput', {
            value: this.anthropicApiKeySecret.secretArn,
            description: 'ARN of the Anthropic API key secret',
            exportName: `AnthropicApiKeySecretArn-${props.environmentName}`,
        });
    }
} 