#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { WebsiteStack } from '../lib/website-stack';
import { ConnectStack } from '../lib/connect-stack';
import { SecretsStack } from '../lib/secrets-stack';
import config from '../config/environments';

const app = new cdk.App();

// Get AWS account and region from environment variables
const account = process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID;
const region = process.env.CDK_DEFAULT_REGION || 'us-east-1';

// Get environment parameter from context or default to all environments
const targetEnv = app.node.tryGetContext('env');

// Function to create stacks for a specific environment
const createStacksForEnvironment = (envKey: string) => {
  const envConfig = config.environments[envKey];

  if (!envConfig) {
    console.warn(`Environment '${envKey}' not found in configuration. Skipping.`);
    return;
  }

  const baseStackId = `PersonalAssistant${envConfig.name.charAt(0).toUpperCase() + envConfig.name.slice(1)}`;
  const secretsStackId = `${baseStackId}SecretsStack`;
  const websiteStackId = `${baseStackId}WebsiteStack`;
  const connectStackId = `${baseStackId}ConnectStack`;

  // Create the secrets stack first
  const secretsStack = new SecretsStack(app, secretsStackId, {
    environmentName: envConfig.name,
    env: {
      account: account,
      region: region
    },
    tags: envConfig.tags
  });

  // Create the website stack
  new WebsiteStack(app, websiteStackId, {
    domainName: envConfig.domainName,
    hostedZoneName: config.hostedZoneName,
    environmentName: envConfig.name,
    env: {
      account: account,
      region: region
    },
    tags: envConfig.tags
  });

  // Create the Connect stack with a dependency on the secrets stack
  const connectStack = new ConnectStack(app, connectStackId, {
    environmentName: envConfig.name,
    secretsStackName: secretsStackId, // Pass the secrets stack name for reference
    env: {
      account: account,
      region: region
    },
    tags: envConfig.tags
  });

  // Add explicit dependency on the secrets stack
  connectStack.addDependency(secretsStack);

  console.log(`Created stacks: ${secretsStackId}, ${websiteStackId}, ${connectStackId}`);
};

// If a specific environment is specified, create only that stack
// Otherwise, create stacks for all environments
if (targetEnv) {
  createStacksForEnvironment(targetEnv);
} else {
  // Create stacks for all environments
  Object.keys(config.environments).forEach(envKey => {
    createStacksForEnvironment(envKey);
  });
}