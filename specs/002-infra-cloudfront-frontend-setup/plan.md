# Implementation Plan: CloudFront フロントエンド配信基盤

**Branch**: `001-cloudfront-frontend-setup` | **Date**: 2025-11-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-cloudfront-frontend-setup/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

loanpedia.jpドメインでHTTPS接続によるフロントエンドコンテンツ配信基盤を構築します。CloudFrontディストリビューション、S3バケット、WAF、Route53 DNSレコードを組み合わせ、セキュアで監視可能なCDN環境を提供します。

## Technical Context

**Language/Version**: TypeScript 5.6.3 (AWS CDKによるインフラ定義)
**Primary Dependencies**: aws-cdk-lib 2.215.0, aws-cdk/aws-cloudfront, aws-cdk/aws-s3, aws-cdk/aws-wafv2, aws-cdk/aws-route53
**Storage**: Amazon S3 (静的コンテンツ: ap-northeast-1, アクセスログ: ap-northeast-1)
**Testing**: CDK integration tests, manual deployment verification
**Target Platform**: AWS Cloud (CloudFront: us-east-1, WAF: us-east-1, S3: ap-northeast-1, Route53: グローバル)
**Project Type**: Infrastructure as Code (AWS CDK)
**Performance Goals**: 3秒以内のページ表示、CloudFront edge locationからの配信
**Constraints**: ACM証明書は既存のものを使用、Route53ホストゾーンは既存、バックエンドALBは未実装のため/apiビヘイビアはTODO
**Scale/Scope**: 単一ドメイン (loanpedia.jp)、単一環境、基本的なWAFルール
**Region Strategy**: CloudFront/WAFはus-east-1（要件）、S3バケットはap-northeast-1（データ保管場所の最適化）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 要件 | 本機能での遵守状況 | 判定 |
|------|------|-------------------|------|
| **I. 日本語優先** | 全ての仕様書、計画書、タスクリスト、ドキュメント、およびユーザーとのコミュニケーションは日本語で記述 | ✅ 仕様書、計画書は日本語で記述。CDKコード内のコメントも日本語で記述予定 | ✅ PASS |
| **V. セキュリティ基本原則** | API キー、認証情報は`.env`で管理し、リポジトリにコミットしない | ✅ ACM証明書ARNは環境変数またはCDK Contextで管理。機密情報はコミットしない | ✅ PASS |
| **Git運用ルール** | feature/* ブランチ使用、コミットメッセージ日本語 | ✅ `001-cloudfront-frontend-setup` ブランチで実装 | ✅ PASS |

**特記事項**:
- 本機能はインフラストラクチャ定義であり、バッチ処理やAI処理には該当しないため、憲章のII、III、IV、VI、VIIの原則は適用外
- セキュリティ原則（V）は、ACM証明書ARN、Route53ホストゾーンIDなどの機密情報管理で遵守

**Phase 1設計後の再チェック**: ✅ 完了

Phase 1設計の完了後、以下を確認しました：

1. **データモデル（data-model.md）**:
   - すべてのAWSリソースがセキュリティベストプラクティスに準拠
   - S3バケットはプライベート設定、OAC経由のみアクセス可能
   - 暗号化設定（SSE-S3）が有効

2. **API契約（contracts/）**:
   - CloudFormation Outputsに機密情報を含めない
   - Export名は適切に設定され、他のスタックから参照可能

3. **クイックスタートガイド（quickstart.md）**:
   - すべてのドキュメントが日本語で記述
   - セキュリティ考慮事項が明記されている

**再チェック結果**: すべての原則に準拠していることを確認 ✅

## Project Structure

### Documentation (this feature)

```text
specs/001-cloudfront-frontend-setup/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
infrastructure/
├── lib/
│   ├── stacks/
│   │   ├── s3-stack.ts                         # S3バケットスタック (ap-northeast-1)
│   │   └── frontend-stack.ts                   # CloudFrontスタック (us-east-1)
│   └── constructs/
│       ├── frontend-distribution.ts            # CloudFrontディストリビューションのConstruct
│       ├── frontend-s3-bucket.ts               # フロントエンド用S3バケットのConstruct
│       └── waf-cloudfront.ts                   # WAFのConstruct
├── bin/
│   └── loanpedia-app.ts                        # CDKアプリケーションエントリーポイント
└── test/
    ├── s3-stack.test.ts                        # S3スタックのテスト
    └── frontend-stack.test.ts                  # CloudFrontスタックのテスト

.github/
└── workflows/
    └── deploy-infrastructure.yml               # 既存のCI/CDワークフロー（更新不要）
```

**Structure Decision**: AWS CDKを使用したインフラストラクチャ定義。S3バケットとCloudFront/WAFを異なるリージョンに配置するため、2つのスタックに分離:
- **S3Stack (ap-northeast-1)**: フロントエンド用S3バケット、ログ用S3バケット
- **FrontendStack (us-east-1)**: CloudFrontディストリビューション、WAF、Route53レコード

FrontendStackはS3Stackのバケットをクロスリージョン参照(`Fn.importValue`)で使用。Route53スタック（001-route53-hosted-zone）との依存関係を考慮し、既存のホストゾーンとACM証明書を参照する形で実装。

## Complexity Tracking

本機能は憲章違反なしのため、このセクションは不要です。
