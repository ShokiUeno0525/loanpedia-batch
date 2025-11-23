import * as cdk from 'aws-cdk-lib';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';

/**
 * Cognito User Poolコンストラクト
 *
 * ユーザー認証基盤としてCognito User Poolを作成します。
 *
 * 構成:
 * - ユーザー名属性: email
 * - 必須属性: email
 * - 自動検証: email
 * - MFA: REQUIRED（EMAIL_OTP方式）
 * - パスワードポリシー: 8文字以上、大小英数記号
 * - アプリクライアント: クライアントシークレット必須
 * - トークン有効期限: アクセス/ID 1時間、リフレッシュ 30日
 */
export class CognitoConstruct extends Construct {
  /**
   * 作成されたUser Pool
   */
  public readonly userPool: cognito.UserPool;

  /**
   * 作成されたアプリクライアント
   */
  public readonly appClient: cognito.UserPoolClient;

  /**
   * アプリクライアントシークレットを格納するSecrets Manager
   */
  public readonly clientSecret: secretsmanager.Secret;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    // Cognito User Pool作成
    this.userPool = new cognito.UserPool(this, 'UserPool', {
      userPoolName: 'loanpedia-user-pool',
      signInAliases: {
        email: true, // emailをユーザー名として使用
      },
      autoVerify: {
        email: true, // メールアドレスの自動検証
      },
      standardAttributes: {
        email: {
          required: true,
          mutable: true,
        },
      },
      mfa: cognito.Mfa.REQUIRED, // MFA必須
      mfaSecondFactor: {
        sms: false,
        otp: true, // EMAIL_OTP
      },
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      removalPolicy: cdk.RemovalPolicy.RETAIN, // 本番データ保護のため保持
    });

    // アプリクライアント作成
    this.appClient = this.userPool.addClient('AppClient', {
      userPoolClientName: 'loanpedia-app-client',
      generateSecret: true, // クライアントシークレット生成
      authFlows: {
        userPassword: true, // USER_PASSWORD_AUTH
        userSrp: true, // USER_SRP_AUTH
        custom: false,
        adminUserPassword: false,
      },
      refreshTokenValidity: cdk.Duration.days(30),
      accessTokenValidity: cdk.Duration.hours(1),
      idTokenValidity: cdk.Duration.hours(1),
      enableTokenRevocation: true,
      preventUserExistenceErrors: true, // セキュリティ強化
    });

    // アプリクライアントシークレットをSecrets Managerに保存
    // 注: UserPoolClientのシークレットはCDKから直接取得できないため、
    //     デプロイ後にAWS CLIまたはカスタムリソースで取得してSecrets Managerに保存する必要がある
    //     ここでは仮のSecretを作成し、後で手動またはCI/CDで値を設定する想定
    this.clientSecret = new secretsmanager.Secret(this, 'ClientSecret', {
      secretName: 'loanpedia/cognito/client-secret',
      description: 'Cognitoアプリクライアントシークレット',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({
          userPoolId: this.userPool.userPoolId,
          clientId: this.appClient.userPoolClientId,
        }),
        generateStringKey: 'clientSecret',
      },
    });

    // CloudFormation Output: User Pool ID
    new cdk.CfnOutput(scope, 'CognitoUserPoolId', {
      value: this.userPool.userPoolId,
      description: 'Cognito User Pool ID',
      exportName: 'LoanpediaCognitoUserPoolId',
    });

    // CloudFormation Output: App Client ID
    new cdk.CfnOutput(scope, 'CognitoAppClientId', {
      value: this.appClient.userPoolClientId,
      description: 'Cognito App Client ID',
      exportName: 'LoanpediaCognitoAppClientId',
    });

    // CloudFormation Output: Client Secret ARN
    new cdk.CfnOutput(scope, 'CognitoSecretArn', {
      value: this.clientSecret.secretArn,
      description: 'Cognitoクライアントシークレット Secrets Manager ARN',
      exportName: 'LoanpediaCognitoSecretArn',
    });
  }
}
