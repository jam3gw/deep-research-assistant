#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { WebsiteStack } from '../lib/website-stack';
import { ResearchStack } from '../lib/research-stack';
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
  const websiteStackId = `${baseStackId}WebsiteStack`;
  const researchStackId = `${baseStackId}ResearchStack`;

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

  // Create the Research stack with a dependency on the secrets stack
  const researchStack = new ResearchStack(app, researchStackId, {
    environmentName: envConfig.name,
    env: {
      account: account,
      region: region
    },
    tags: envConfig.tags
  });
};

// If a specific environment is specified, create stacks for that environment only
if (targetEnv && targetEnv !== 'all') {
  createStacksForEnvironment(targetEnv);
} else {
  // Otherwise, create stacks for all environments
  Object.keys(config.environments).forEach(createStacksForEnvironment);
}