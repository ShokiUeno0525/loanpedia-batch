import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { RdsConstruct } from '../../lib/constructs/rds-construct';

describe('RdsConstruct', () => {
  test('RDS MySQLインスタンスが正しく作成される', () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'TestStack', {
      env: {
        account: '123456789012',
        region: 'ap-northeast-1',
      },
    });

    const vpc = new ec2.Vpc(stack, 'TestVpc', {
      ipAddresses: ec2.IpAddresses.cidr('10.16.0.0/16'),
      maxAzs: 2,
      subnetConfiguration: [],
    });

    const securityGroup = new ec2.SecurityGroup(stack, 'TestSg', {
      vpc,
      description: 'Test security group',
    });

    const isolatedSubnetA = new ec2.PrivateSubnet(stack, 'IsolatedSubnetA', {
      vpcId: vpc.vpcId,
      cidrBlock: '10.16.64.0/20',
      availabilityZone: 'ap-northeast-1a',
    });

    const isolatedSubnetC = new ec2.PrivateSubnet(stack, 'IsolatedSubnetC', {
      vpcId: vpc.vpcId,
      cidrBlock: '10.16.80.0/20',
      availabilityZone: 'ap-northeast-1c',
    });

    new RdsConstruct(stack, 'TestRdsConstruct', {
      vpc,
      securityGroup,
      isolatedSubnets: [isolatedSubnetA, isolatedSubnetC],
    });

    const template = Template.fromStack(stack);

    // RDSインスタンスが作成される
    template.resourceCountIs('AWS::RDS::DBInstance', 1);

    // RDSインスタンスのプロパティ確認
    template.hasResourceProperties('AWS::RDS::DBInstance', {
      Engine: 'mysql',
      EngineVersion: '8.0',
      DBInstanceClass: 'db.t3.micro',
      AllocatedStorage: '20',
      StorageType: 'gp3',
      MultiAZ: false,
      DBName: 'loanpedia',
    });

    // サブネットグループが作成される
    template.resourceCountIs('AWS::RDS::DBSubnetGroup', 1);

    // パラメータグループが作成される
    template.resourceCountIs('AWS::RDS::DBParameterGroup', 1);

    // パラメータグループにutf8mb4設定がある
    template.hasResourceProperties('AWS::RDS::DBParameterGroup', {
      Parameters: {
        character_set_server: 'utf8mb4',
        collation_server: 'utf8mb4_unicode_ci',
        character_set_client: 'utf8mb4',
        character_set_connection: 'utf8mb4',
        character_set_database: 'utf8mb4',
        character_set_results: 'utf8mb4',
      },
    });
  });

  test('複数のアイソレートサブネットがサブネットグループに設定される', () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'TestStack', {
      env: {
        account: '123456789012',
        region: 'ap-northeast-1',
      },
    });

    const vpc = new ec2.Vpc(stack, 'TestVpc', {
      ipAddresses: ec2.IpAddresses.cidr('10.16.0.0/16'),
      maxAzs: 2,
      subnetConfiguration: [],
    });

    const securityGroup = new ec2.SecurityGroup(stack, 'TestSg', {
      vpc,
      description: 'Test security group',
    });

    const isolatedSubnetA = new ec2.PrivateSubnet(stack, 'IsolatedSubnetA', {
      vpcId: vpc.vpcId,
      cidrBlock: '10.16.64.0/20',
      availabilityZone: 'ap-northeast-1a',
    });

    const isolatedSubnetC = new ec2.PrivateSubnet(stack, 'IsolatedSubnetC', {
      vpcId: vpc.vpcId,
      cidrBlock: '10.16.80.0/20',
      availabilityZone: 'ap-northeast-1c',
    });

    new RdsConstruct(stack, 'TestRdsConstruct', {
      vpc,
      securityGroup,
      isolatedSubnets: [isolatedSubnetA, isolatedSubnetC],
    });

    const template = Template.fromStack(stack);

    // サブネットグループが作成され、2つのサブネットが含まれる
    template.resourceCountIs('AWS::RDS::DBSubnetGroup', 1);

    // サブネットグループに2つのサブネットが含まれることを確認
    const subnetGroups = template.findResources('AWS::RDS::DBSubnetGroup');
    const subnetGroup = Object.values(subnetGroups)[0];
    expect(subnetGroup.Properties.SubnetIds).toHaveLength(2);
  });
});
