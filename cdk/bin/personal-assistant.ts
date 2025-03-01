#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { WebsiteStack } from '../lib/website-stack';
import config from '../config/environments';

const app = new cdk.App();

// Get AWS account and region from environment variables
const account = process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID;
const region = process.env.CDK_DEFAULT_REGION || 'us-east-1';

// Get environment parameter from context or default to all environments
const targetEnv = app.node.tryGetContext('env');

// Function to create a stack for a specific environment
const createStackForEnvironment = (envKey: string) => {
  const envConfig = config.environments[envKey];

  if (!envConfig) {
    console.warn(`Environment '${envKey}' not found in configuration. Skipping.`);
    return;
  }

  const stackId = `PersonalAssistant${envConfig.name.charAt(0).toUpperCase() + envConfig.name.slice(1)}Stack`;

  new WebsiteStack(app, stackId, {
    domainName: envConfig.domainName,
    hostedZoneName: config.hostedZoneName,
    environmentName: envConfig.name,
    env: {
      account: account,
      region: region
    },
    tags: envConfig.tags
  });

  console.log(`Created stack: ${stackId}`);
};

// If a specific environment is specified, create only that stack
// Otherwise, create stacks for all environments
if (targetEnv) {
  createStackForEnvironment(targetEnv);
} else {
  // Create stacks for all environments
  Object.keys(config.environments).forEach(envKey => {
    createStackForEnvironment(envKey);
  });
}