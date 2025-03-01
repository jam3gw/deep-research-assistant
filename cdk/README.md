# Personal Assistant CDK Project

This project deploys an S3-backed, CloudFront-distributed web application with separate development and production environments.

## Architecture

- **S3**: Hosts the static website files
- **CloudFront**: Distributes the website globally with HTTPS
- **Route53**: Manages DNS records for the domains (A and AAAA records for IPv4/IPv6 support)
- **ACM**: Provides SSL/TLS certificates

## Security Features

- **HTTPS Only**: All traffic is redirected to HTTPS
- **Domain Allowlisting**: CloudFront distribution is configured to only serve content to specified domains
- **Security Headers**: Implements best practice security headers including:
  - Content-Security-Policy
  - X-Frame-Options
  - X-Content-Type-Options
  - X-XSS-Protection
  - Strict-Transport-Security (HSTS)

## Environments

The application supports multiple environments defined in the `config/environments.ts` file:

- **Development**: Deployed at `personal-assistant.dev.jake-moses.com`
- **Production**: Deployed at `personal-assistant.jake-moses.com`

## Prerequisites

- AWS CLI configured with appropriate credentials
- Node.js and npm installed
- AWS CDK installed globally (`npm install -g aws-cdk`)

## Setup

1. Install dependencies:
   ```
   npm install
   ```

2. Bootstrap your AWS environment (if not already done):
   ```
   cdk bootstrap
   ```

## Deployment

The project includes npm scripts for easy deployment:

### Deploy Environments

```bash
# Deploy development environment
npm run deploy:dev

# Deploy production environment
npm run deploy:prod

# Deploy all environments
npm run deploy:all
```

### Compare Changes

```bash
# Compare development environment changes
npm run diff:dev

# Compare production environment changes
npm run diff:prod
```

### Generate CloudFormation Templates

```bash
# Synthesize development environment template
npm run synth:dev

# Synthesize production environment template
npm run synth:prod
```

## Adding a New Environment

To add a new environment:

1. Edit the `config/environments.ts` file to add a new environment configuration
2. Add corresponding npm scripts to package.json
3. Deploy the new environment using the npm script

## Website Structure

The website is a simple static site with:
- HTML/CSS/JavaScript
- Responsive design
- Environment indicator (shows whether you're in dev or prod)

## Customization

To customize the website:
1. Modify files in the `website/` directory
2. Redeploy the stacks

## Cleanup

```bash
# Remove development environment
npm run destroy:dev

# Remove production environment
npm run destroy:prod

# Remove all environments
npm run destroy:all
```

## Notes

- The hosted zone `jake-moses.com` must already exist in your AWS account
- Certificates are created in the us-east-1 region for CloudFront compatibility
- S3 buckets are configured with removal policies to clean up resources when stacks are destroyed
- Both IPv4 (A records) and IPv6 (AAAA records) are supported
