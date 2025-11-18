#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { GitHubOidcStack } from '../lib/github-oidc-stack';
import { Route53Stack } from '../lib/route53-stack';
import { AcmCertificateStack } from '../lib/acm-certificate-stack';
import { FrontendStack } from '../lib/frontend-stack';

const app = new cdk.App();

// GitHub OIDC認証スタック
new GitHubOidcStack(app, 'GitHubOidcStack', {
  repositoryName: 'ShokiUeno0525/loanpedia-batch',
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});

// Route53 パブリックホストゾーンスタック
new Route53Stack(app, 'Route53Stack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});

// ACM証明書スタック
// CloudFront用の証明書はus-east-1リージョンで作成する必要がある
new AcmCertificateStack(app, 'AcmCertificateStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'us-east-1', // CloudFront用証明書は必ずus-east-1
  },
  description: 'Loanpedia ACM Certificate Stack for CloudFront (us-east-1)',
});

// T030: CloudFrontフロントエンド配信基盤スタック
// CloudFront用WAFは必ずus-east-1リージョンで作成する必要がある
new FrontendStack(app, 'FrontendStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'us-east-1', // CloudFront用WAFは必ずus-east-1
  },
  description: 'Loanpedia CloudFront Frontend Distribution Stack (us-east-1)',
});

app.synth();
