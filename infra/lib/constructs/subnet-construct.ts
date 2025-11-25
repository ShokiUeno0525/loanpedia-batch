import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { Tags } from 'aws-cdk-lib';

export interface SubnetConstructProps {
  /**
   * サブネットを作成するVPC
   */
  readonly vpc: ec2.IVpc;

  /**
   * サブネットを配置するアベイラビリティゾーン
   */
  readonly availabilityZone: string;

  /**
   * パブリックサブネットのCIDRブロック
   * @default '10.16.0.0/20'
   */
  readonly publicCidr?: string;

  /**
   * プライベートサブネットのCIDRブロック
   * @default '10.16.32.0/20'
   */
  readonly privateCidr?: string;

  /**
   * アイソレートサブネットのCIDRブロック
   * @default '10.16.64.0/20'
   */
  readonly isolatedCidr?: string;
}

/**
 * サブネットコンストラクト
 *
 * パブリック、プライベート、アイソレートサブネットを作成します。
 */
export class SubnetConstruct extends Construct {
  /**
   * パブリックサブネット (CIDR: 10.16.0.0/20)
   * インターネットからの直接アクセスを受け付けるリソース用
   */
  public readonly publicSubnet: ec2.PublicSubnet;

  /**
   * プライベートサブネット (CIDR: 10.16.32.0/20)
   * ECS や Lambda など、外部通信が必要なリソース用
   */
  public readonly privateSubnet: ec2.PrivateSubnet;

  /**
   * アイソレートサブネット (CIDR: 10.16.64.0/20)
   * RDS など、外部通信が不要なリソース用
   */
  public readonly isolatedSubnet: ec2.PrivateSubnet;

  constructor(scope: Construct, id: string, props: SubnetConstructProps) {
    super(scope, id);

    const {
      vpc,
      availabilityZone,
      publicCidr = '10.16.0.0/20',
      privateCidr = '10.16.32.0/20',
      isolatedCidr = '10.16.64.0/20',
    } = props;

    // パブリックサブネット
    this.publicSubnet = new ec2.PublicSubnet(this, 'PublicSubnet', {
      vpcId: vpc.vpcId,
      cidrBlock: publicCidr,
      availabilityZone: availabilityZone,
      mapPublicIpOnLaunch: true, // パブリックIPの自動割り当てを有効化
    });

    Tags.of(this.publicSubnet).add('Name', 'Loanpedia-Dev-Subnet-Public');
    Tags.of(this.publicSubnet).add('aws-cdk:subnet-type', 'Public');

    // プライベートサブネット
    this.privateSubnet = new ec2.PrivateSubnet(this, 'PrivateSubnet', {
      vpcId: vpc.vpcId,
      cidrBlock: privateCidr,
      availabilityZone: availabilityZone,
    });

    Tags.of(this.privateSubnet).add('Name', 'Loanpedia-Dev-Subnet-Private');
    Tags.of(this.privateSubnet).add('aws-cdk:subnet-type', 'Private');

    // アイソレートサブネット
    this.isolatedSubnet = new ec2.PrivateSubnet(this, 'IsolatedSubnet', {
      vpcId: vpc.vpcId,
      cidrBlock: isolatedCidr,
      availabilityZone: availabilityZone,
    });

    Tags.of(this.isolatedSubnet).add('Name', 'Loanpedia-Dev-Subnet-Isolated');
    Tags.of(this.isolatedSubnet).add('aws-cdk:subnet-type', 'Isolated');
  }
}
