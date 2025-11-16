import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export interface GitHubOidcStackProps extends cdk.StackProps {
  /**
   * GitHubリポジトリ名（例: "ユーザー名/リポジトリ名"）
   */
  readonly repositoryName: string;
}

/**
 * GitHub Actions用のOIDC認証スタック
 *
 * @remarks
 * このスタックはGitHub ActionsからAWSリソースにアクセスするための
 * OIDC認証基盤を構築します。長期的なAWS認証情報を使用せず、
 * 一時的な認証情報をOIDCトークン交換により取得します。
 *
 * 作成されるリソース:
 * - GitHub OIDC Provider
 * - GitHub Actions用IAM Role (GitHubActionsDeployRole)
 *
 * @see {@link https://docs.github.com/ja/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect | GitHub Actions OIDC}
 */
export class GitHubOidcStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: GitHubOidcStackProps) {
    super(scope, id, props);

    // GitHub OIDC Provider作成
    const provider = new iam.OpenIdConnectProvider(this, 'GitHubProvider', {
      url: 'https://token.actions.githubusercontent.com',
      clientIds: ['sts.amazonaws.com'],
    });

    // GitHub Actions用IAM Role作成
    const githubRole = new iam.Role(this, 'GitHubActionsRole', {
      assumedBy: new iam.WebIdentityPrincipal(
        provider.openIdConnectProviderArn,
        {
          StringEquals: {
            'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com',
          },
          StringLike: {
            // 指定されたリポジトリからのみアクセスを許可
            'token.actions.githubusercontent.com:sub': `repo:${props.repositoryName}:*`,
          },
        }
      ),
      description: 'Role for GitHub Actions to deploy CDK stacks',
      roleName: 'GitHubActionsDeployRole',
      maxSessionDuration: cdk.Duration.hours(1),
    });

    // 管理者権限を付与
    // Note: 本当はデプロイに必要な権限だけにしておく方が良い(最小権限の原則)
    githubRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('AdministratorAccess')
    );

    // GitHubシークレットに設定するため出力
    new cdk.CfnOutput(this, 'GitHubActionsRoleArn', {
      value: githubRole.roleArn,
      description: 'GitHub Actions用IAM RoleのARN（GitHub Secretsに設定してください）',
      exportName: 'GitHubActionsRoleArn',
    });
  }
}
