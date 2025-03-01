import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as targets from 'aws-cdk-lib/aws-route53-targets';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as path from 'path';

export interface WebsiteStackProps extends cdk.StackProps {
    domainName: string;
    hostedZoneName: string;
    environmentName: string;
}

export class WebsiteStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: WebsiteStackProps) {
        super(scope, id, props);

        // Get the hosted zone
        const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
            domainName: props.hostedZoneName,
        });
        const wwwDomainName = props.domainName.indexOf('www.') === 0 ? props.domainName : `www.${props.domainName}`;

        // Create an S3 bucket for website content
        const websiteBucket = new s3.Bucket(this, 'WebsiteBucket', {
            bucketName: `${props.domainName.replace(/\./g, '-')}-${props.environmentName}`,
            websiteIndexDocument: 'index.html',
            publicReadAccess: true,
            blockPublicAccess: s3.BlockPublicAccess.BLOCK_ACLS,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
            autoDeleteObjects: true,
        });

        // Get the website endpoint URL with the correct region
        const websiteEndpoint = `${websiteBucket.bucketName}.s3-website-us-west-2.amazonaws.com`;

        // Create a certificate for the domain
        const certificate = new acm.DnsValidatedCertificate(this, 'SiteCertificate', {
            domainName: props.domainName,
            subjectAlternativeNames: [wwwDomainName],
            hostedZone,
            region: 'us-east-1', // CloudFront requires certificates in us-east-1
        });

        // Define allowed domains for the CloudFront distribution
        const allowedDomains = [props.domainName, wwwDomainName];

        // Create a CloudFront distribution with domain allowlisting
        const distribution = new cloudfront.Distribution(this, 'SiteDistribution', {
            defaultBehavior: {
                origin: new origins.HttpOrigin(websiteEndpoint, {
                    protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY
                }),
                viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                compress: true,
            },
            domainNames: allowedDomains,
            certificate,
            defaultRootObject: 'index.html',
            errorResponses: [
                {
                    httpStatus: 403,
                    responseHttpStatus: 200,
                    responsePagePath: '/index.html',
                },
                {
                    httpStatus: 404,
                    responseHttpStatus: 200,
                    responsePagePath: '/index.html',
                },
            ],
        });

        // Create Route53 A record (IPv4) for main domain
        new route53.ARecord(this, 'SiteAliasRecord', {
            recordName: props.domainName,
            target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
            zone: hostedZone,
        });

        // Create Route53 AAAA record (IPv6) for main domain
        new route53.AaaaRecord(this, 'SiteAliasRecordIPv6', {
            recordName: props.domainName,
            target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
            zone: hostedZone,
        });

        // Create Route53 A record (IPv4) for www subdomain
        new route53.ARecord(this, 'WwwSiteAliasRecord', {
            recordName: wwwDomainName,
            target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
            zone: hostedZone,
        });

        // Create Route53 AAAA record (IPv6) for www subdomain
        new route53.AaaaRecord(this, 'WwwSiteAliasRecordIPv6', {
            recordName: wwwDomainName,
            target: route53.RecordTarget.fromAlias(new targets.CloudFrontTarget(distribution)),
            zone: hostedZone,
        });

        // Deploy website content to S3
        new s3deploy.BucketDeployment(this, 'DeployWebsite', {
            sources: [s3deploy.Source.asset(path.join(__dirname, '../../website'))],
            destinationBucket: websiteBucket,
            distribution,
            distributionPaths: ['/*'],
        });

        // Output the CloudFront URL
        new cdk.CfnOutput(this, 'DistributionDomainName', {
            value: distribution.distributionDomainName,
            description: 'The CloudFront distribution domain name',
        });

        // Output the website URL
        new cdk.CfnOutput(this, 'WebsiteURL', {
            value: `https://${props.domainName}`,
            description: 'The website URL',
        });

        // Output the allowed domains
        new cdk.CfnOutput(this, 'AllowedDomains', {
            value: allowedDomains.join(', '),
            description: 'Domains allowed to access the CloudFront distribution',
        });
    }
} 