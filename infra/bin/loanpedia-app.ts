#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { GitHubOidcStack } from '../lib/stacks/github-oidc-stack';
import { Route53Stack } from '../lib/stacks/route53-stack';
import { AcmCertificateStack } from '../lib/stacks/acm-certificate-stack';
import { S3Stack } from '../lib/stacks/s3-stack';
import { FrontendStack } from '../lib/stacks/frontend-stack';
import { VpcNetworkStack } from '../lib/stacks/vpc-network-stack';

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

// S3バケットスタック（東京リージョン）
// フロントエンド用S3バケットとログバケットを作成
const s3Stack = new S3Stack(app, 'S3Stack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'ap-northeast-1', // S3バケットは東京リージョンに作成
  },
  description: 'Loanpedia S3 Storage Stack (ap-northeast-1)',
});

// T030: CloudFrontフロントエンド配信基盤スタック
// CloudFront用WAFは必ずus-east-1リージョンで作成する必要がある
const frontendStack = new FrontendStack(app, 'FrontendStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'us-east-1', // CloudFront用WAFは必ずus-east-1
  },
  description: 'Loanpedia CloudFront Frontend Distribution Stack (us-east-1)',
});

// 依存関係: FrontendStackはS3Stackのバケットを参照する
frontendStack.addDependency(s3Stack);

// VPCネットワーク基盤スタック
// シングルAZ構成のVPC、パブリック・プライベート・アイソレートサブネットを作成
new VpcNetworkStack(app, 'VpcNetworkStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'ap-northeast-1', // VPCはap-northeast-1に作成
  },
  description: 'Loanpedia VPC Network Infrastructure Stack (ap-northeast-1)',
});

app.synth();
