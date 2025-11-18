# Feature Specification: Route53 パブリックホストゾーン作成

**Feature Branch**: `001-route53-hosted-zone`
**Created**: 2025-11-16
**Status**: Draft
**Input**: User description: "Route53 スタックファイルの作成 - loanpedia.jp のパブリックホストゾーンを定義し、ネームサーバー情報を CloudFormation Output で出力"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - DNS管理基盤の確立 (Priority: P1)

DevOpsエンジニアが、loanpedia.jpドメインのDNS管理をAWS Route53で行えるようにする必要があります。これにより、お名前.comで取得したドメインをAWSインフラと統合し、今後のサービスデプロイメント（フロントエンド、API、SSL証明書など）の基盤を整えます。

**Why this priority**: DNS基盤はすべてのWebサービスの基礎インフラです。ホストゾーンがなければ、ドメインレコードの追加、SSL証明書の検証、CloudFrontやALBとの連携ができません。これは最優先で実装すべき基盤機能です。

**Independent Test**: Route53コンソールでloanpedia.jpのホストゾーンが作成され、4つのネームサーバーが割り当てられ、CloudFormation Outputsから取得できることを確認できれば完了です。

**Acceptance Scenarios**:

1. **Given** AWS環境とお名前.comで取得済みのloanpedia.jpドメイン、**When** CDKスタックをデプロイする、**Then** Route53にloanpedia.jpのパブリックホストゾーンが作成される
2. **Given** ホストゾーンが作成された状態、**When** CloudFormation Outputsを確認する、**Then** 4つのネームサーバー（ns-xxxx.awsdns-xx.com形式）が出力として表示される
3. **Given** ネームサーバー情報が出力された状態、**When** お名前.comの管理画面でネームサーバーを変更する、**Then** DNS解決がAWS Route53経由で行われるようになる
4. **Given** ホストゾーンが作成された状態、**When** nslookupやdigコマンドでloanpedia.jpを照会する、**Then** AWS Route53のネームサーバーが応答する

---

### Edge Cases

- ホストゾーン作成後にスタックを削除した場合、ホストゾーンも正しく削除されるか？
- 同じドメイン名でホストゾーンを複数作成しようとした場合、どう動作するか？
- ネームサーバー変更前にDNSレコードを追加した場合、変更後に正しく反映されるか？
- DNS浸透中にアクセスした場合、旧DNSと新DNSが混在する期間の挙動は？

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは loanpedia.jp のパブリックホストゾーンを作成しなければならない
- **FR-002**: システムは作成したホストゾーンのネームサーバー情報（4つのNSレコード）をCloudFormation Outputsとして出力しなければならない
- **FR-003**: ネームサーバー情報は、お名前.comでの設定変更に使用できる形式（例: ns-1234.awsdns-12.com）で提供されなければならない
- **FR-004**: ホストゾーンはパブリックタイプ（インターネットからアクセス可能）として作成されなければならない
- **FR-005**: インフラ構成は再現可能であり、スタックの削除と再作成が可能でなければならない

### Key Entities

- **ホストゾーン**: loanpedia.jpドメインのDNS管理を担当するRoute53リソース。NSレコード、SOAレコードを含み、将来的にA、CNAME、Aliasレコードなどを追加可能
- **ネームサーバー**: AWS Route53から自動割り当てされる4つの権威DNSサーバー。お名前.comでドメイン委任設定を行うために必要

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Route53コンソールでloanpedia.jpのホストゾーンが正常に表示され、ステータスがアクティブである
- **SC-002**: CloudFormation Outputsから4つのネームサーバー情報を取得でき、それぞれがawsdns形式のFQDNである
- **SC-003**: お名前.comでネームサーバーを変更後、24時間以内にDNS解決がAWS Route53経由で行われる
- **SC-004**: インフラのデプロイと削除が5分以内に完了し、エラーなく実行できる

## Assumptions

- AWS環境は既にセットアップされており、CDKのデプロイが可能である
- お名前.comでloanpedia.jpドメインは取得済みであり、ネームサーバー変更権限がある
- DNS浸透には最大48時間かかる可能性があるが、通常は数時間で完了する
- ホストゾーンの月額料金（$0.50/月）とクエリ料金は許容範囲内である
- 現時点ではDNSレコード（A、CNAME等）の追加は行わず、ホストゾーンの作成のみに焦点を当てる

## Dependencies

- AWS CDK環境が構築されていること（infra/ディレクトリに既存のCDKプロジェクトが存在）
- GitHub OIDC認証スタック（GitHubOidcStack）がデプロイ済みであること
- お名前.comのアカウントとドメイン管理権限

## Out of Scope

以下は本フィーチャーの範囲外です：

- DNSレコード（A、CNAME、Alias等）の作成
- SSL/TLS証明書（ACM）の作成
- CloudFrontディストリビューションやALBとの連携
- お名前.comでのネームサーバー変更作業（手動作業として別途実施）
- DNS浸透の監視とヘルスチェック
