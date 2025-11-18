# Research: VPCネットワーク基盤の構築

**Feature**: 003-infra-vpc-network-setup
**Date**: 2025-11-18
**Phase**: Phase 0 - Technical Research

## 目的

AWS CDK を使用したVPCネットワーク基盤構築における技術的な選択肢、ベストプラクティス、および実装方針を調査・決定する。

## 調査項目

### 1. AWS CDK VPC構築パターン

#### 調査内容
AWS CDK で VPC を構築する際の推奨パターンと、カスタムサブネット構成の実装方法。

#### 決定事項

**選択**: aws-cdk-lib の `aws-ec2.Vpc` コンストラクトを使用

**理由**:
- AWS の公式 CDK ライブラリで、ベストプラクティスがデフォルトで適用される
- サブネット、ルートテーブル、ゲートウェイの関連付けが自動化される
- 高レベル API と低レベル API の両方をサポートし、カスタマイズ性が高い
- CloudFormation テンプレート生成により、インフラ変更の追跡が容易

**代替案**:
1. **aws-ec2.CfnVPC (低レベル CloudFormation リソース)**
   - より細かい制御が可能
   - 却下理由: 冗長な記述が必要で、ルーティングテーブルの関連付けなどを手動で管理する必要がある

2. **Terraform CDK**
   - Terraform エコシステムとの統合
   - 却下理由: プロジェクトは既に AWS CDK を採用しており（Route53, CloudFront）、一貫性を保つべき

3. **AWS CloudFormation YAML/JSON**
   - 宣言的な定義
   - 却下理由: TypeScript による型安全性、再利用性、テスタビリティに劣る

#### 実装方針

```typescript
// 高レベル API を使用した VPC 作成（推奨）
const vpc = new ec2.Vpc(this, 'LoanpediaVpc', {
  ipAddresses: ec2.IpAddresses.cidr('10.16.0.0/16'),
  maxAzs: 1, // シングル AZ
  natGateways: 1,
  subnetConfiguration: [
    {
      cidrMask: 20,
      name: 'Public',
      subnetType: ec2.SubnetType.PUBLIC,
    },
    {
      cidrMask: 20,
      name: 'Private',
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
    },
    {
      cidrMask: 20,
      name: 'Isolated',
      subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
    },
  ],
});
```

### 2. サブネット CIDR 割り当て戦略

#### 調査内容
指定された CIDR ブロック（10.16.0.0/20, 10.16.32.0/20, 10.16.64.0/20）を AWS CDK でどのように設定するか。

#### 決定事項

**選択**: `subnetConfiguration` で `cidrMask: 20` を指定し、AWS CDK に自動割り当てさせる

**理由**:
- AWS CDK は VPC の CIDR ブロックを均等に分割してサブネットを作成する
- `/16` の VPC で `/20` のサブネットを3つ作成すると、自動的に 10.16.0.0/20, 10.16.16.0/20, 10.16.32.0/20 が割り当てられる
- 仕様書の要件（10.16.0.0/20, 10.16.32.0/20, 10.16.64.0/20）とは若干異なるが、機能的には同等

**代替案**:
1. **手動で CIDR を指定（低レベル API）**
   - `ec2.CfnSubnet` を使用して CIDR を明示的に指定
   - 選択理由: 仕様書通りの正確な CIDR 配置が必要な場合はこちらを採用
   - 実装例:
   ```typescript
   const publicSubnet = new ec2.CfnSubnet(this, 'PublicSubnet', {
     vpcId: vpc.vpcId,
     cidrBlock: '10.16.0.0/20',
     availabilityZone: 'ap-northeast-1a',
   });
   ```

2. **VPC IP アドレスマネージャー (IPAM) の使用**
   - 組織全体で IP アドレスを一元管理
   - 却下理由: 小規模プロジェクトには過剰で、追加コストが発生

#### 実装方針

**最終決定**: 仕様書の CIDR ブロック要件を厳密に満たすため、低レベル API を併用する

```typescript
// VPC は高レベル API で作成
const vpc = new ec2.Vpc(this, 'LoanpediaVpc', {
  ipAddresses: ec2.IpAddresses.cidr('10.16.0.0/16'),
  maxAzs: 1,
  natGateways: 0, // 手動で NAT Gateway を作成するため 0
  subnetConfiguration: [], // サブネットも手動作成
});

// サブネットを手動で作成し、正確な CIDR を指定
const publicSubnet = new ec2.PublicSubnet(this, 'PublicSubnet', {
  availabilityZone: vpc.availabilityZones[0],
  cidrBlock: '10.16.0.0/20',
  vpcId: vpc.vpcId,
  mapPublicIpOnLaunch: true,
});
```

### 3. NAT Gateway 配置とコスト最適化

#### 調査内容
NAT Gateway の配置方法と、コスト最適化のベストプラクティス。

#### 決定事項

**選択**: パブリックサブネットに NAT Gateway を1つ配置（シングル AZ 構成）

**理由**:
- 仕様書で「コスト最適化を優先」と明示されている
- 開発・検証環境であり、高可用性は求められていない
- NAT Gateway のコストは以下の通り:
  - 時間料金: $0.062/時間（ap-northeast-1）
  - データ転送料金: $0.062/GB
  - 月額約 $45 + データ転送料（1個の場合）

**代替案**:
1. **マルチAZ構成（各AZにNAT Gateway）**
   - 高可用性を実現
   - 却下理由: シングルAZ構成のため不要、コストが2倍以上になる

2. **NAT Instance（EC2ベース）**
   - t4g.nano を使用すれば月額約$3と低コスト
   - 却下理由:
     - 管理オーバーヘッド（パッチ適用、スケーリング）
     - パフォーマンスが NAT Gateway より劣る
     - AWS が NAT Gateway を推奨

3. **VPC Endpoints（PrivateLink）**
   - S3, DynamoDB は Gateway Endpoint で無料
   - その他は Interface Endpoint で $0.01/時間/AZ
   - 採用検討: 後続フェーズで S3/DynamoDB を使用する場合は追加を推奨

#### 実装方針

```typescript
// Elastic IP を作成
const eip = new ec2.CfnEIP(this, 'NatGatewayEIP', {
  domain: 'vpc',
});

// NAT Gateway を作成
const natGateway = new ec2.CfnNatGateway(this, 'NatGateway', {
  subnetId: publicSubnet.subnetId,
  allocationId: eip.attrAllocationId,
});
```

### 4. ルートテーブル設計

#### 調査内容
各サブネットタイプに対する最適なルートテーブル設計。

#### 決定事項

**選択**: サブネットタイプごとに専用のルートテーブルを作成

**理由**:
- セキュリティの明確化: 各サブネットの通信経路が明示的に定義される
- 将来的な拡張性: 追加のルートやルールを個別に適用可能
- AWS ベストプラクティスに準拠

**ルート設計**:

| サブネットタイプ | デフォルトルート (0.0.0.0/0) | VPC ローカル (10.16.0.0/16) | 備考 |
|------------------|------------------------------|------------------------------|------|
| パブリック       | Internet Gateway             | 自動（VPC作成時）           | 外部からの受信・送信可能 |
| プライベート     | NAT Gateway                  | 自動（VPC作成時）           | 外部への送信のみ可能 |
| アイソレート     | なし                         | 自動（VPC作成時）           | VPC内通信のみ |

**代替案**:
1. **共有ルートテーブル**
   - プライベートとアイソレートで同じルートテーブルを共有
   - 却下理由: セキュリティリスク、意図しない通信が発生する可能性

2. **カスタムルート（ブラックホールルート）**
   - 特定の CIDR への通信を明示的にブロック
   - 却下理由: 現時点では不要、必要に応じて後から追加可能

#### 実装方針

```typescript
// パブリックサブネット用ルートテーブル
const publicRouteTable = new ec2.CfnRouteTable(this, 'PublicRouteTable', {
  vpcId: vpc.vpcId,
});

new ec2.CfnRoute(this, 'PublicRoute', {
  routeTableId: publicRouteTable.ref,
  destinationCidrBlock: '0.0.0.0/0',
  gatewayId: internetGateway.ref,
});

// プライベートサブネット用ルートテーブル
const privateRouteTable = new ec2.CfnRouteTable(this, 'PrivateRouteTable', {
  vpcId: vpc.vpcId,
});

new ec2.CfnRoute(this, 'PrivateRoute', {
  routeTableId: privateRouteTable.ref,
  destinationCidrBlock: '0.0.0.0/0',
  natGatewayId: natGateway.ref,
});

// アイソレートサブネット用ルートテーブル（デフォルトルートなし）
const isolatedRouteTable = new ec2.CfnRouteTable(this, 'IsolatedRouteTable', {
  vpcId: vpc.vpcId,
});
```

### 5. タグ戦略とリソース命名

#### 調査内容
AWS リソースに適用すべきタグと命名規則。

#### 決定事項

**選択**: 統一された命名規則とタグ付けルールを適用

**命名規則**:
```
{Project}-{Environment}-{ResourceType}-{Purpose}
例: Loanpedia-Dev-VPC-Main
    Loanpedia-Dev-Subnet-Public
    Loanpedia-Dev-NatGateway-Main
```

**必須タグ**:
- `Project`: Loanpedia
- `Environment`: Development / Staging / Production
- `ManagedBy`: CDK
- `Feature`: 003-infra-vpc-network-setup
- `CostCenter`: Loanpedia-Infrastructure

**理由**:
- コスト管理: タグベースのコスト配分が可能
- リソース追跡: 複数環境でリソースを識別可能
- 自動化: タグベースの自動バックアップ、削除ポリシー適用が可能
- コンプライアンス: リソースの所有者と目的を明確化

**代替案**:
1. **最小限のタグのみ（Name タグのみ）**
   - シンプルで管理しやすい
   - 却下理由: コスト管理や自動化に不利

2. **詳細すぎるタグ（CreatedBy, LastModifiedDate など）**
   - 完全なトレーサビリティ
   - 却下理由: 管理オーバーヘッドが大きく、AWS の標準タグ（CreatedBy など）で十分

#### 実装方針

```typescript
// CDK スタックレベルでデフォルトタグを適用
import { Tags } from 'aws-cdk-lib';

Tags.of(this).add('Project', 'Loanpedia');
Tags.of(this).add('Environment', 'Development');
Tags.of(this).add('ManagedBy', 'CDK');
Tags.of(this).add('Feature', '003-infra-vpc-network-setup');
Tags.of(this).add('CostCenter', 'Loanpedia-Infrastructure');

// 個別リソースに Name タグを追加
const vpc = new ec2.Vpc(this, 'LoanpediaVpc', {
  // ...
});
Tags.of(vpc).add('Name', 'Loanpedia-Dev-VPC-Main');
```

### 6. セキュリティグループ設計（スコープ外だが将来検討）

#### 調査内容
VPC 作成後に必要となるセキュリティグループの設計方針。

#### 決定事項

**現フェーズの方針**: セキュリティグループは作成しない（スコープ外）

**理由**:
- 仕様書で「VPC とサブネット構成のみを準備」と明記
- ECS, Lambda, RDS などのリソースは後続フェーズで作成予定
- セキュリティグループは各リソースに特化した設計が必要

**将来の推奨事項**（後続フェーズで考慮）:

1. **ALB セキュリティグループ**
   - インバウンド: HTTP (80), HTTPS (443) from 0.0.0.0/0
   - アウトバウンド: ECS タスクへの通信

2. **ECS タスクセキュリティグループ**
   - インバウンド: ALB からのみ許可
   - アウトバウンド: RDS, インターネット (NAT Gateway 経由)

3. **Lambda セキュリティグループ**
   - インバウンド: なし（Lambda は受信しない）
   - アウトバウンド: RDS, インターネット (NAT Gateway 経由)

4. **RDS セキュリティグループ**
   - インバウンド: ECS, Lambda からのみ MySQL (3306)
   - アウトバウンド: なし（外部通信不要）

### 7. AWS CDK プロジェクト構造

#### 調査内容
既存の CDK プロジェクト（Route53, CloudFront）との統合方法。

#### 決定事項

**選択**: 既存の `infrastructure/` ディレクトリに新しいスタックとして追加

**理由**:
- 既存プロジェクトとの一貫性を保つ
- 単一の CDK アプリで複数スタックを管理できる
- スタック間の依存関係（例: VPC → ECS）を明示的に定義可能
- デプロイの一元管理（`cdk deploy --all` で全スタックをデプロイ）

**ディレクトリ構造**:
```
infrastructure/
├── bin/
│   └── app.ts                          # 既存: 全スタックのエントリーポイント
├── lib/
│   ├── stacks/
│   │   ├── route53-stack.ts            # 既存
│   │   ├── cloudfront-stack.ts         # 既存
│   │   └── vpc-network-stack.ts        # 新規: このフェーズで追加
│   └── constructs/
│       ├── vpc-construct.ts            # 新規
│       ├── subnet-construct.ts         # 新規
│       └── gateway-construct.ts        # 新規
├── test/
│   ├── route53-stack.test.ts           # 既存
│   ├── cloudfront-stack.test.ts        # 既存
│   └── vpc-network-stack.test.ts       # 新規
├── cdk.json
├── tsconfig.json
└── package.json
```

**代替案**:
1. **別の CDK プロジェクトとして作成**
   - 完全に独立した管理
   - 却下理由: スタック間の依存関係管理が複雑になる、デプロイが煩雑

2. **モノレポ構造（Nx, Lerna）**
   - 複数の CDK プロジェクトを統合管理
   - 却下理由: プロジェクト規模に対して過剰、単一 CDK アプリで十分

#### 実装方針

```typescript
// infrastructure/bin/app.ts（既存ファイルを更新）
import { VpcNetworkStack } from '../lib/stacks/vpc-network-stack';

const app = new cdk.App();

// 既存スタック
new Route53Stack(app, 'Route53Stack', { /* ... */ });
new CloudFrontStack(app, 'CloudFrontStack', { /* ... */ });

// 新規スタック
new VpcNetworkStack(app, 'VpcNetworkStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'ap-northeast-1',
  },
});
```

### 8. テスト戦略

#### 調査内容
CDK スタックのテスト方法とベストプラクティス。

#### 決定事項

**選択**: スナップショットテスト + 細かいアサーション（Fine-Grained Assertions）

**理由**:
- **スナップショットテスト**: CloudFormation テンプレート全体の変更を検出
- **Fine-Grained Assertions**: 特定リソースの存在と設定を検証
- AWS CDK 公式推奨のテスト戦略
- リファクタリング時の回帰テスト

**テストケース**:
1. VPC が正しい CIDR ブロックで作成されること
2. 3つのサブネット（Public, Private, Isolated）が存在すること
3. Internet Gateway が VPC にアタッチされていること
4. NAT Gateway がパブリックサブネットに作成されていること
5. ルートテーブルが正しく設定されていること

**代替案**:
1. **スナップショットテストのみ**
   - シンプルだが、何が変わったか不明確
   - 却下理由: 特定の要件（CIDR ブロックなど）を検証できない

2. **統合テスト（実際にAWSにデプロイ）**
   - 最も正確な検証
   - 却下理由: コストと時間がかかる、CIパイプラインに不向き

#### 実装方針

```typescript
import { Template } from 'aws-cdk-lib/assertions';
import { VpcNetworkStack } from '../lib/stacks/vpc-network-stack';

test('VPC created with correct CIDR', () => {
  const stack = new VpcNetworkStack(app, 'TestStack');
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::EC2::VPC', {
    CidrBlock: '10.16.0.0/16',
  });
});

test('NAT Gateway exists in public subnet', () => {
  const template = Template.fromStack(stack);
  template.resourceCountIs('AWS::EC2::NatGateway', 1);
});
```

## まとめ

### 技術スタック最終決定

| カテゴリ | 技術 | バージョン |
|----------|------|------------|
| IaC | AWS CDK | 2.215.0 |
| 言語 | TypeScript | 5.6.3 |
| VPC 構築 | aws-cdk-lib/aws-ec2 | 2.215.0 |
| テスト | Jest + aws-cdk-lib/assertions | - |
| AWS リージョン | ap-northeast-1 | - |

### 主要な設計決定

1. **VPC 構築パターン**: aws-ec2.Vpc の低レベル API を使用し、CIDR ブロックを正確に指定
2. **NAT Gateway**: シングル構成でコスト最適化
3. **ルートテーブル**: サブネットタイプごとに専用テーブルを作成
4. **タグ戦略**: プロジェクト、環境、コスト管理のための統一タグ
5. **プロジェクト構造**: 既存 CDK プロジェクトに新規スタックとして統合
6. **テスト**: スナップショットテスト + Fine-Grained Assertions

### 次フェーズへの準備

Phase 1 では以下を実装します:
- `vpc-network-stack.ts`: メインスタック定義
- `vpc-construct.ts`, `subnet-construct.ts`, `gateway-construct.ts`: 再利用可能なコンストラクト
- `vpc-network-stack.test.ts`: ユニットテスト
- `quickstart.md`: デプロイ手順とクイックスタートガイド

### リスクと緩和策

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| NAT Gateway 単一障害点 | プライベートサブネットからの外部通信停止 | 開発環境のため許容、本番環境ではマルチAZ化を検討 |
| CIDR ブロックの拡張不可 | IP アドレス枯渇 | 各サブネット 4,096 IP で十分な余裕を確保 |
| Elastic IP 割り当て制限 | NAT Gateway 作成失敗 | デプロイ前に AWS サポートで上限確認 |
| CDK バージョン不一致 | デプロイ失敗 | package.json で固定バージョンを指定 |
