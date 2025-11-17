#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AuroraStack } from '../lib/aurora-stack';

const app = new cdk.App();

// Aurora Serverless v2 + Data API スタック
new AuroraStack(app, 'LoanpediaAuroraStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'ap-northeast-1',
  },
  description: 'Loanpedia Aurora Serverless v2 Database Stack with Data API',
});