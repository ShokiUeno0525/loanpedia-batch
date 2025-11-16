#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { GitHubOidcStack } from '../lib/github-oidc-stack';

const app = new cdk.App();

// GitHub OIDC認証スタック
new GitHubOidcStack(app, 'GitHubOidcStack', {
  repositoryName: 'ShokiUeno0525/loanpedia-batch',
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});

// TODO: Add other stacks here

app.synth();
