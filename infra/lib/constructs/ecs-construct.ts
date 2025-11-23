import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import { Construct } from 'constructs';

export interface EcsConstructProps {
  /**
   * VPC
   */
  readonly vpc: ec2.IVpc;

  /**
   * プライベートサブネット（AZ-a）
   */
  readonly privateSubnet: ec2.ISubnet;

  /**
   * ECS用セキュリティグループ
   */
  readonly securityGroup: ec2.ISecurityGroup;

  /**
   * ALBターゲットグループ
   */
  readonly targetGroup: elbv2.ApplicationTargetGroup;

  /**
   * RDS認証情報Secret
   */
  readonly rdsSecret: secretsmanager.ISecret;

  /**
   * Cognito認証情報Secret
   */
  readonly cognitoSecret: secretsmanager.ISecret;

  /**
   * API用ロググループ
   */
  readonly apiLogGroup: logs.ILogGroup;

  /**
   * マイグレーション用ロググループ
   */
  readonly migrationLogGroup: logs.ILogGroup;

  /**
   * ECR APIリポジトリ
   */
  readonly ecrApiRepository: ecr.IRepository;

  /**
   * ECRマイグレーションリポジトリ
   */
  readonly ecrMigrationRepository: ecr.IRepository;
}

/**
 * ECS Fargateコンストラクト
 *
 * ECSクラスター、タスク定義（API、マイグレーション）、Web APIサービスを作成します。
 *
 * 構成:
 * - クラスター: loanpedia-cluster（Container Insights無効）
 * - Web APIタスク定義: CPU 512、メモリ1024 MB、コンテナポート80
 * - マイグレーションタスク定義: CPU 256、メモリ512 MB
 * - Web APIサービス: タスク数1、プライベートサブネット配置、ALB統合
 */
export class EcsConstruct extends Construct {
  /**
   * 作成されたECSクラスター
   */
  public readonly cluster: ecs.Cluster;

  /**
   * Web APIタスク定義
   */
  public readonly apiTaskDefinition: ecs.FargateTaskDefinition;

  /**
   * マイグレーションタスク定義
   */
  public readonly migrationTaskDefinition: ecs.FargateTaskDefinition;

  /**
   * Web APIサービス
   */
  public readonly apiService: ecs.FargateService;

  constructor(scope: Construct, id: string, props: EcsConstructProps) {
    super(scope, id);

    const {
      vpc,
      privateSubnet,
      securityGroup,
      targetGroup,
      rdsSecret,
      cognitoSecret,
      apiLogGroup,
      migrationLogGroup,
      ecrApiRepository,
      ecrMigrationRepository,
    } = props;

    // ECSクラスター作成
    this.cluster = new ecs.Cluster(this, 'Cluster', {
      clusterName: 'loanpedia-cluster',
      vpc,
      containerInsights: false, // Container Insights無効（コスト削減）
    });

    // IAMタスク実行ロール作成
    const taskExecutionRole = new iam.Role(this, 'TaskExecutionRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy'),
      ],
    });

    // Secrets Manager参照権限を追加
    rdsSecret.grantRead(taskExecutionRole);
    cognitoSecret.grantRead(taskExecutionRole);

    // IAMタスクロール作成（アプリケーション実行用）
    const taskRole = new iam.Role(this, 'TaskRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });

    // Cognito権限を追加
    taskRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['cognito-idp:*'],
        resources: ['*'], // 必要に応じて特定のUser Pool ARNに制限
      })
    );

    // Web APIタスク定義作成
    this.apiTaskDefinition = new ecs.FargateTaskDefinition(this, 'ApiTaskDefinition', {
      cpu: 512, // 0.5 vCPU
      memoryLimitMiB: 1024, // 1 GB
      executionRole: taskExecutionRole,
      taskRole,
    });

    // Web APIコンテナ追加
    this.apiTaskDefinition.addContainer('ApiContainer', {
      containerName: 'loanpedia-api',
      image: ecs.ContainerImage.fromEcrRepository(ecrApiRepository, 'latest'),
      portMappings: [
        {
          containerPort: 80,
          protocol: ecs.Protocol.TCP,
        },
      ],
      logging: ecs.LogDriver.awsLogs({
        logGroup: apiLogGroup,
        streamPrefix: 'api',
      }),
      environment: {
        APP_ENV: 'production',
        APP_DEBUG: 'false',
      },
      secrets: {
        DB_HOST: ecs.Secret.fromSecretsManager(rdsSecret, 'host'),
        DB_PORT: ecs.Secret.fromSecretsManager(rdsSecret, 'port'),
        DB_DATABASE: ecs.Secret.fromSecretsManager(rdsSecret, 'dbname'),
        DB_USERNAME: ecs.Secret.fromSecretsManager(rdsSecret, 'username'),
        DB_PASSWORD: ecs.Secret.fromSecretsManager(rdsSecret, 'password'),
        COGNITO_CLIENT_SECRET: ecs.Secret.fromSecretsManager(cognitoSecret, 'clientSecret'),
      },
    });

    // マイグレーションタスク定義作成
    this.migrationTaskDefinition = new ecs.FargateTaskDefinition(this, 'MigrationTaskDefinition', {
      cpu: 256, // 0.25 vCPU
      memoryLimitMiB: 512, // 512 MB
      executionRole: taskExecutionRole,
      taskRole,
    });

    // マイグレーションコンテナ追加
    this.migrationTaskDefinition.addContainer('MigrationContainer', {
      containerName: 'loanpedia-migration',
      image: ecs.ContainerImage.fromEcrRepository(ecrMigrationRepository, 'latest'),
      logging: ecs.LogDriver.awsLogs({
        logGroup: migrationLogGroup,
        streamPrefix: 'migration',
      }),
      environment: {
        APP_ENV: 'production',
      },
      secrets: {
        DB_HOST: ecs.Secret.fromSecretsManager(rdsSecret, 'host'),
        DB_PORT: ecs.Secret.fromSecretsManager(rdsSecret, 'port'),
        DB_DATABASE: ecs.Secret.fromSecretsManager(rdsSecret, 'dbname'),
        DB_USERNAME: ecs.Secret.fromSecretsManager(rdsSecret, 'username'),
        DB_PASSWORD: ecs.Secret.fromSecretsManager(rdsSecret, 'password'),
      },
      command: ['php', 'artisan', 'migrate', '--force'],
    });

    // Web APIサービス作成
    this.apiService = new ecs.FargateService(this, 'ApiService', {
      cluster: this.cluster,
      taskDefinition: this.apiTaskDefinition,
      desiredCount: 1,
      vpcSubnets: {
        subnets: [privateSubnet],
      },
      securityGroups: [securityGroup],
      assignPublicIp: false,
    });

    // Web APIサービスをALBターゲットグループに登録
    this.apiService.attachToApplicationTargetGroup(targetGroup);

    // CloudFormation Outputs
    new cdk.CfnOutput(scope, 'EcsClusterName', {
      value: this.cluster.clusterName,
      description: 'ECSクラスター名',
      exportName: 'LoanpediaEcsClusterName',
    });

    new cdk.CfnOutput(scope, 'EcsClusterArn', {
      value: this.cluster.clusterArn,
      description: 'ECSクラスターARN',
      exportName: 'LoanpediaEcsClusterArn',
    });

    new cdk.CfnOutput(scope, 'ApiServiceName', {
      value: this.apiService.serviceName,
      description: 'Web APIサービス名',
      exportName: 'LoanpediaApiServiceName',
    });

    new cdk.CfnOutput(scope, 'ApiTaskDefinitionArn', {
      value: this.apiTaskDefinition.taskDefinitionArn,
      description: 'Web APIタスク定義ARN',
      exportName: 'LoanpediaApiTaskDefinitionArn',
    });

    new cdk.CfnOutput(scope, 'MigrationTaskDefinitionArn', {
      value: this.migrationTaskDefinition.taskDefinitionArn,
      description: 'マイグレーションタスク定義ARN',
      exportName: 'LoanpediaMigrationTaskDefinitionArn',
    });
  }
}
