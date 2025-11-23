# Implementation Plan: バックエンドインフラストラクチャ

**Branch**: `001-backend-stack` | **Date**: 2025-11-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-backend-stack/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

金融機関ローン情報集約システムのバックエンドインフラをAWS CDKで構築する。既存のVPCネットワーク（シングルAZ）をマルチAZ構成に拡張し、ALB、ECS Fargate、RDS MySQL、Cognito User Pool、ECR、CloudWatch Logs、Secrets Managerを統合したAPI基盤を提供する。CloudFrontの`/api/*`ビヘイビアを追加してエンドツーエンドのHTTPSアクセスを実現する。

**技術アプローチ**:
- AWS CDKによるInfrastructure as Code（TypeScript）
- マルチAZアーキテクチャ（ap-northeast-1a、1c）による高可用性
- CloudFrontとALBの統合によるセキュアなAPI配信
- ECS FargateでコンテナベースのAPI実行
- RDS MySQLでデータ永続化
- Cognito User Poolでユーザー認証基盤
- Secrets Managerで機密情報管理

## Technical Context

**Language/Version**: TypeScript 5.6.3（AWS CDK）
**Primary Dependencies**:
- aws-cdk-lib 2.215.0
- aws-cdk/aws-ec2（VPC、サブネット、セキュリティグループ）
- aws-cdk/aws-elasticloadbalancingv2（ALB、ターゲットグループ）
- aws-cdk/aws-ecs（Fargate、クラスター、タスク定義、サービス）
- aws-cdk/aws-rds（MySQL、パラメータグループ、サブネットグループ）
- aws-cdk/aws-cognito（User Pool、アプリクライアント）
- aws-cdk/aws-ecr（リポジトリ）
- aws-cdk/aws-secretsmanager（Secrets Manager）
- aws-cdk/aws-certificatemanager（ACM証明書）
- aws-cdk/aws-route53（DNSレコード）
- aws-cdk/aws-cloudfront（CloudFrontディストリビューション更新）
- aws-cdk/aws-logs（CloudWatch Logs）
- aws-cdk/aws-iam（IAMロール、ポリシー）

**Storage**:
- RDS MySQL 8.0（db.t3.micro、gp3 20GB、シングルAZ）
- Secrets Manager（RDS認証情報、Cognitoクライアントシークレット）
- CloudWatch Logs（ECSタスクログ、保持期間7日間）

**Testing**:
- CDK内蔵テスト（`@aws-cdk/assertions`）
- CDKスタックの単体テスト
- インテグレーションテスト（CloudFormation変更セット検証）
- AWS Console/CLI での手動検証（デプロイ後）

**Target Platform**: AWS（ap-northeast-1リージョン、us-east-1リージョン for CloudFront）

**Project Type**: Infrastructure as Code（AWS CDK）

**Performance Goals**:
- インフラ全体のデプロイ時間: 初回60分以内、更新30分以内（ACM DNS検証時間を除く）
- ACM証明書発行: 30分以内
- RDSインスタンス起動: 10分以内
- ECS Fargateタスク起動: 5分以内
- ALBヘルスチェック成功: タスク起動後2分以内

**Constraints**:
- ALBは最低2AZ必須（ap-northeast-1a、1c）
- RDSはシングルAZ構成（コスト削減）
- RDSサブネットグループは2AZ必須（AWS仕様）
- ECSはシングルAZ配置（タスク数1、ALBが冗長性提供）
- NAT Gatewayは1AZのみ（コスト削減）
- CloudFront SGはマネージドプレフィックスリスト使用（CloudFront IPレンジ）
- Cognitoメール送信は標準（50通/日制限）
- ECS Auto Scaling未実装
- CloudWatch Alarms未実装

**Scale/Scope**:
- VPCサブネット: 6サブネット（パブリック×2、プライベート×2、アイソレート×2）
- ALB: 1個（internet-facing、2AZ）
- ECS Fargate: 1クラスター、2タスク定義、1サービス（初期タスク数1）
- RDS MySQL: 1インスタンス（db.t3.micro）
- Cognito User Pool: 1個
- ECR: 2リポジトリ
- Secrets Manager: 2シークレット
- CloudWatch Logs: 2ロググループ
- ACM証明書: 1個（`api.loanpedia.jp`）
- Route53レコード: 1個（Aレコード、Alias）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. 日本語優先

- **適合**: 本計画書は日本語で記述され、仕様書（spec.md）も日本語で記述されている
- **適合**: コミットメッセージは日本語で記述される予定
- **適合**: コード内コメントは日本語で記述される予定
- **例外**: AWS CDKコード（TypeScript）の変数名、関数名は英語（言語仕様）
- **例外**: AWS CloudFormationリソース名は英語（AWSベストプラクティス）

### ✅ V. セキュリティ基本原則

- **適合**: API キー、データベース認証情報はSecrets Managerで管理（リポジトリにコミットしない）
- **適合**: `.gitignore`で機密ファイル（`.env`、`cdk.context.json`の機密情報部分）を除外
- **適合**: データベースアクセスは最小権限（ECS SGからRDS SGへのポート3306のみ）
- **適合**: ログ出力時は機密情報をマスキング（Secrets Managerの値は自動的にマスキング）
- **適合**: CloudFront→ALB間のアクセスはCloudFront IPレンジのみ許可（セキュリティグループ制限）
- **適合**: ALB→ECS間はHTTP（内部通信、VPC内）
- **適合**: CloudFront→ALB、クライアント→CloudFrontはHTTPS必須

### ✅ その他の原則

**II. バッチ処理の信頼性**: 本フィーチャーはインフラ定義のみで、バッチ処理ロジックは含まない（別タスク）。インフラレベルでは、ECS Fargateのタスク定義とマイグレーションタスクが冪等性を持つように設計される。

**III. データ品質の保証**: 本フィーチャーはインフラ定義のみで、データ収集・検証ロジックは含まない（別タスク）。インフラレベルでは、RDSのutf8mb4文字セット設定により文字化けを防止。

**IV. AI処理の透明性**: 本フィーチャーはインフラ定義のみで、AI処理ロジックは含まない（別タスク）。インフラレベルでは、CloudWatch Logsによる処理ログの保存（保持期間7日間）。

**VI. スクレイピングマナーと倫理**: 本フィーチャーはインフラ定義のみで、スクレイピングロジックは含まない（別タスク）。

**VII. 段階的データ保存**: 本フィーチャーはインフラ定義のみで、データ保存ロジックは含まない（別タスク）。インフラレベルでは、RDS MySQLの提供によりデータ保存基盤を提供。

### 🚨 技術スタック制約との整合性

**憲章記載の技術スタック**:
- バッチ処理: Python 3.12+（本フィーチャー対象外、別タスク）
- AI処理: Amazon BedRock API（本フィーチャー対象外、別タスク）
- **データベース**: MySQL 8.0+（✅ 本フィーチャーで対応: RDS MySQL 8.0）
- **API**: PHP 8.2+ + Laravel 10+（⚠️ 本フィーチャーではECS Fargateのインフラのみ提供、アプリケーションコードは別タスク）
- **フロントエンド**: React 18+（本フィーチャー対象外、既存CloudFrontスタックで提供済み）

**注記**: 本フィーチャーはインフラストラクチャ定義（AWS CDK）のみを対象とし、アプリケーションコード（バッチ処理、AI処理、Laravel API、React フロントエンド）は実装対象外。憲章の技術スタック制約はインフラレイヤーでの準備として、対応するAWSリソース（RDS MySQL、ECS Fargate、CloudFront）を提供する。

### ✅ パフォーマンス要件

**憲章記載のパフォーマンス要件**:
- バッチ処理: 4金融機関の全ローン情報を6時間以内に収集完了（本フィーチャー対象外、別タスク）
- AI処理: 1商品あたり平均5秒以内（本フィーチャー対象外、別タスク）
- **API応答**: 検索APIは95パーセンタイルで500ms以内、データ取得APIは95パーセンタイルで200ms以内（✅ 本フィーチャーでALB、ECS Fargate、RDSのインフラ提供により実現可能）

**本フィーチャーのパフォーマンス目標**:
- インフラデプロイ時間: 初回60分以内、更新30分以内（✅ 目標に含む）
- ACM証明書発行: 30分以内（✅ 目標に含む）
- RDSインスタンス起動: 10分以内（✅ 目標に含む）
- ECS Fargateタスク起動: 5分以内（✅ 目標に含む）

### ✅ Git運用ルール

- **適合**: フィーチャーブランチ`001-backend-stack`を使用
- **適合**: コミットメッセージは日本語で記述予定（種別: 概要）
- **適合**: `main`ブランチへの直接プッシュ禁止
- **適合**: 強制プッシュ禁止
- **適合**: 機密情報のコミット禁止

### ✅ Gate判定

**Phase 0研究開始前**: ✅ **PASS** - 憲章のコア原則に違反なし

**Phase 1設計完了後の再チェック対象**:
- セキュリティグループ構成の妥当性検証
- Secrets Managerによる機密情報管理の実装確認
- CloudWatch Logsの設定確認

## Project Structure

### Documentation (this feature)

```text
specs/001-backend-stack/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── cloudformation-outputs.json  # スタック出力定義
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
infra/                                    # AWS CDKプロジェクトルート
├── bin/
│   └── infra.ts                         # CDK アプリエントリーポイント
├── lib/
│   ├── stacks/
│   │   ├── vpc-network-stack.ts         # 既存（更新対象: マルチAZ対応）
│   │   ├── route53-stack.ts             # 既存（参照のみ）
│   │   ├── acm-certificate-stack.ts     # 既存（参照のみ: CloudFront用）
│   │   ├── alb-acm-certificate-stack.ts # 新規: ALB用ACM証明書
│   │   ├── backend-stack.ts             # 新規: ECR、ECS、ALB、RDS、Cognito、Secrets Manager
│   │   └── frontend-stack.ts            # 既存（更新対象: /api/* ビヘイビア追加）
│   └── constructs/
│       ├── alb-construct.ts             # 新規: ALB、ターゲットグループ、リスナー
│       ├── ecs-construct.ts             # 新規: ECSクラスター、タスク定義、サービス
│       ├── rds-construct.ts             # 新規: RDS MySQL、サブネットグループ、パラメータグループ
│       ├── cognito-construct.ts         # 新規: Cognito User Pool、アプリクライアント
│       ├── security-groups-construct.ts # 新規: ALB SG、ECS SG、RDS SG
│       └── secrets-construct.ts         # 新規: Secrets Manager統合
├── test/
│   ├── vpc-network-stack.test.ts        # 更新: マルチAZ対応テスト
│   ├── alb-acm-certificate-stack.test.ts # 新規
│   ├── backend-stack.test.ts            # 新規
│   └── frontend-stack.test.ts           # 更新: /api/* ビヘイビアテスト
├── cdk.json                             # CDK設定
├── tsconfig.json                        # TypeScript設定
└── package.json                         # 依存関係管理

api/                                      # アプリケーションコード（別タスク、本フィーチャー対象外）
└── (Laravel PHPアプリケーション)

.github/
└── workflows/
    ├── infra_cd.yml                     # 既存（更新対象: Backend Stack追加）
    └── api_cd.yml                       # 新規（別タスク: ECSデプロイ）
```

**Structure Decision**:

本フィーチャーは**Infrastructure as Code（AWS CDK）**プロジェクトであり、既存の`infra/`ディレクトリ構造を拡張する。

**既存構造**:
- `infra/lib/stacks/`: CloudFormationスタック定義（既存: VPC、Route53、ACM、Frontend）
- `infra/lib/constructs/`: 再利用可能なCDK Construct（既存構造を活用）
- `infra/test/`: CDKスタックの単体テスト

**新規追加**:
- `alb-acm-certificate-stack.ts`: ALB用ACM証明書スタック（ap-northeast-1）
- `backend-stack.ts`: バックエンドリソース統合スタック（ECR、ECS、ALB、RDS、Cognito、Secrets Manager）
- `alb-construct.ts`、`ecs-construct.ts`、`rds-construct.ts`、`cognito-construct.ts`、`security-groups-construct.ts`、`secrets-construct.ts`: 各リソースのConstruct
- テストファイル

**更新対象**:
- `vpc-network-stack.ts`: マルチAZ対応（サブネット追加）
- `frontend-stack.ts`: CloudFront `/api/*` ビヘイビア追加

**依存関係**:
- Backend Stack → VPC Stack（VPC、サブネット、セキュリティグループ参照）
- Backend Stack → Route53 Stack（ホストゾーン参照）
- Backend Stack → ALB ACM Certificate Stack（証明書参照）
- Frontend Stack → Backend Stack（ALBのDNS名参照）

**デプロイ順序**:
1. VPC Stack更新（マルチAZ対応）
2. ALB ACM Certificate Stack作成
3. Backend Stack作成
4. Frontend Stack更新（`/api/*` ビヘイビア追加）

## Complexity Tracking

本フィーチャーは憲章のコア原則に違反する複雑性は導入しない。インフラストラクチャ定義（AWS CDK）として標準的な構成であり、以下の理由で正当化される:

| 検討項目 | 判定 | 理由 |
|---------|------|------|
| マルチAZ構成 | ✅ 必須 | ALBは最低2AZ必須（AWS仕様）。高可用性の標準構成。 |
| シングルAZ RDS | ✅ 許容 | コスト削減のため、開発環境ではシングルAZ。本番環境ではマルチAZに変更可能。 |
| Secrets Manager使用 | ✅ 推奨 | 憲章V（セキュリティ基本原則）に準拠。機密情報をリポジトリにコミットしない。 |
| CloudFront→ALB統合 | ✅ 必須 | エンドユーザーからのHTTPSアクセスを実現するために必須。CloudFront IPレンジのみ許可でセキュリティ強化。 |
| ECS Fargate使用 | ✅ 推奨 | サーバーレスコンテナ実行により運用コスト削減。オートスケーリングは将来追加可能。 |
| Cognito User Pool | ✅ 必須 | ユーザー認証基盤として必須。マネージドサービスにより運用コスト削減。 |

**複雑性の正当化は不要**: 憲章違反なし、標準的なAWSインフラ構成。
