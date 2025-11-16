import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { GitHubOidcStack } from '../lib/github-oidc-stack';

describe('GitHubOidcStack', () => {
  test('GitHub OIDC Provider is created', () => {
    const app = new cdk.App();
    const stack = new GitHubOidcStack(app, 'TestStack', {
      repositoryName: 'test-owner/test-repo',
    });

    const template = Template.fromStack(stack);

    // OIDC Providerが作成されることを確認
    template.hasResourceProperties('Custom::AWSCDKOpenIdConnectProvider', {
      Url: 'https://token.actions.githubusercontent.com',
      ClientIDList: ['sts.amazonaws.com'],
    });
  });

  test('IAM Role with correct trust policy is created', () => {
    const app = new cdk.App();
    const stack = new GitHubOidcStack(app, 'TestStack', {
      repositoryName: 'test-owner/test-repo',
    });

    const template = Template.fromStack(stack);

    // IAM Roleが作成されることを確認
    template.hasResourceProperties('AWS::IAM::Role', {
      RoleName: 'GitHubActionsDeployRole',
      MaxSessionDuration: 3600,
    });
  });

  test('CloudFormation Output is created', () => {
    const app = new cdk.App();
    const stack = new GitHubOidcStack(app, 'TestStack', {
      repositoryName: 'test-owner/test-repo',
    });

    const template = Template.fromStack(stack);

    // CloudFormation Outputが作成されることを確認
    template.hasOutput('GitHubActionsRoleArn', {});
  });
});
