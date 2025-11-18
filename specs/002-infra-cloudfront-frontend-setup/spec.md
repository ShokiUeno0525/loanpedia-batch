# Feature Specification: CloudFront フロントエンド配信基盤

**Feature Branch**: `001-cloudfront-frontend-setup`
**Created**: 2025-11-18
**Status**: Draft
**Input**: User description: "以下リソースを構築し、テスト用の適当なindex.htmlが表示されることがゴール
- CloudFrontディストリビューション + OAC
    - デフォルトパスは/index.html
    - デフォルトビヘイビア = フロントエンド用S3バケット
    - APIビヘイビア = /apiでALBに。ただしbackendスタックはまだ構築しないからTODOでOK
    - WAFをディストリビューションで有効化
    - ドメイン設定
        - 代替ドメインをloanpedia.jpにする
        - ACMで発行したHTTPS証明書を付与
        - Route53にloanpedia.jp→ディストリビューションのレコードを追加
    - ログ出力設定
        - S3バケットを作成し、標準アクセスログの出力先にする
    - S3へのアクセス許可
- フロントエンド用S3バケット
    - パブリックアクセス不可のプライベートバケット
    - 特定のOACからのみアクセスを許可するバケットポリシー
- コンソールからindex.htmlを配置し、URLにアクセスする"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 基本的なフロントエンドコンテンツ配信 (Priority: P1)

エンドユーザーが https://loanpedia.jp にアクセスして、ローン情報集約サービスのフロントエンドアプリケーションを閲覧できるようにする。

**Why this priority**: サービスの最も基本的な機能であり、これがなければユーザーはサービスにアクセスできません。すべての後続機能の基盤となります。

**Independent Test**: 以下の方法で独立してテストできます：
- S3バケットにテスト用のindex.htmlをアップロード
- ブラウザで https://loanpedia.jp にアクセス
- index.htmlの内容が正しく表示されることを確認

**Acceptance Scenarios**:

1. **Given** S3バケットにindex.htmlが配置されている状態で、**When** ユーザーが https://loanpedia.jp にアクセスすると、**Then** index.htmlのコンテンツが表示される
2. **Given** S3バケットにindex.htmlが配置されている状態で、**When** ユーザーが https://loanpedia.jp/ にアクセスすると、**Then** 自動的に/index.htmlにリダイレクトされてコンテンツが表示される
3. **Given** HTTPS接続を使用している状態で、**When** ユーザーが https://loanpedia.jp にアクセスすると、**Then** 証明書エラーなく安全な接続が確立される

---

### User Story 2 - セキュアなコンテンツ配信 (Priority: P2)

管理者がS3バケットへの直接アクセスを防ぎ、CloudFront経由でのみフロントエンドコンテンツを配信できるようにする。

**Why this priority**: セキュリティの基本要件であり、P1の基本機能が動作した後に確認すべき重要な保護機能です。

**Independent Test**: 以下の方法で独立してテストできます：
- S3バケットの直接URLにアクセスを試行し、アクセス拒否されることを確認
- CloudFront URLからは正常にアクセスできることを確認

**Acceptance Scenarios**:

1. **Given** S3バケットにコンテンツが配置されている状態で、**When** S3の直接URLにアクセスを試みると、**Then** アクセスが拒否される
2. **Given** OACが設定されている状態で、**When** CloudFront経由でアクセスすると、**Then** コンテンツが正常に配信される
3. **Given** パブリックアクセスブロックが有効な状態で、**When** インターネットから直接S3へのアクセスを試みると、**Then** すべてのリクエストが拒否される

---

### User Story 3 - WAFによる保護 (Priority: P3)

管理者がWAFを使用して、悪意のあるトラフィックやDDoS攻撃からサービスを保護できるようにする。

**Why this priority**: サービスの可用性とセキュリティを向上させる重要な機能ですが、基本的なコンテンツ配信機能の後に追加できます。

**Independent Test**: 以下の方法で独立してテストできます：
- WAFがCloudFrontディストリビューションに関連付けられていることを確認
- WAFのメトリクスがCloudWatchで取得できることを確認

**Acceptance Scenarios**:

1. **Given** WAFが有効化されている状態で、**When** 通常のユーザーがアクセスすると、**Then** リクエストが許可される
2. **Given** WAFルールが設定されている状態で、**When** CloudWatchでWAFメトリクスを確認すると、**Then** リクエストの統計情報が記録されている

---

### User Story 4 - アクセスログの記録と監視 (Priority: P3)

管理者がCloudFrontのアクセスログをS3バケットで確認し、トラフィックパターンや問題を分析できるようにする。

**Why this priority**: 運用上重要な機能ですが、基本的なサービス提供には必須ではありません。サービス稼働後の監視と分析に役立ちます。

**Independent Test**: 以下の方法で独立してテストできます：
- CloudFrontディストリビューションにアクセス
- S3バケットでログファイルを確認し、アクセスログが記録されていることを検証

**Acceptance Scenarios**:

1. **Given** CloudFrontログ用S3バケットが作成されている状態で、**When** ユーザーがCloudFrontにアクセスすると、**Then** アクセスログがS3バケットに記録される
2. **Given** ログが記録されている状態で、**When** 管理者がS3コンソールまたはAthenaで確認すると、**Then** リクエストの詳細情報（タイムスタンプ、IPアドレス、ステータスコード等）が表示される

---

### Edge Cases

- CloudFrontのデフォルトルートオブジェクト（/index.html）が存在しない場合、どのようなエラーが表示されるか？
- S3バケットが空の状態でCloudFrontにアクセスした場合、適切なエラーメッセージが表示されるか？
- ACM証明書の検証が完了していない状態でCloudFrontを設定しようとした場合、どのように処理されるか？
- Route53のレコードが既に存在する場合、どのように対処するか？
- OACの権限が正しく設定されていない場合、どのようなエラーが発生するか？

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは、loanpedia.jpドメインでHTTPS接続を提供しなければならない
- **FR-002**: システムは、CloudFrontディストリビューションのデフォルトルートオブジェクトとして/index.htmlを設定しなければならない
- **FR-003**: システムは、S3バケットへの直接アクセスを拒否し、CloudFrontのOAC経由でのみアクセスを許可しなければならない
- **FR-004**: システムは、フロントエンドコンテンツを保存するためのプライベートS3バケットを提供しなければならない
- **FR-005**: システムは、CloudFrontディストリビューションにWAFを関連付けなければならない
- **FR-006**: システムは、既存のACM証明書をCloudFrontディストリビューションに適用しなければならない
- **FR-007**: システムは、Route53でloanpedia.jpドメインをCloudFrontディストリビューションに向けるAレコードを作成しなければならない
- **FR-008**: システムは、CloudFrontの標準アクセスログをS3バケットに出力しなければならない
- **FR-009**: システムは、将来的に/apiパスでALBにルーティングするための準備（ビヘイビア設定）を含めなければならない（現時点ではTODOとして残す）
- **FR-010**: システムは、S3バケットへの書き込み権限を持つIAMロールまたはポリシーを提供しなければならない

### Key Entities

- **CloudFrontディストリビューション**: コンテンツ配信ネットワークのエントリーポイント。ドメイン名、SSL証明書、WAF、ログ設定、複数のビヘイビアを持つ
- **S3バケット（フロントエンド用）**: 静的コンテンツ（HTML、CSS、JavaScript等）を保存するストレージ。プライベート設定とOACによるアクセス制御を持つ
- **S3バケット（ログ用）**: CloudFrontの標準アクセスログを保存するストレージ。ログファイルはcloudfront/プレフィックス配下に保存される
- **OAC（Origin Access Control）**: CloudFrontがS3バケットにアクセスするための認証メカニズム
- **WAF**: Webアプリケーションファイアウォール。CloudFrontディストリビューションに関連付けられ、トラフィックをフィルタリング
- **ACM証明書**: SSL/TLS証明書。loanpedia.jpドメインのHTTPS接続を提供
- **Route53 Aレコード**: ドメイン名（loanpedia.jp）をCloudFrontディストリビューションにマッピングするDNSレコード

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ユーザーが https://loanpedia.jp にアクセスすると、3秒以内にindex.htmlのコンテンツが表示される
- **SC-002**: S3バケットへの直接アクセスを試みた場合、100%のリクエストがアクセス拒否される
- **SC-003**: CloudFront経由のアクセスリクエストの100%がS3ログバケットに記録される
- **SC-004**: WAFが有効化され、CloudFrontディストリビューションに関連付けられていることがAWSコンソールで確認できる
- **SC-005**: HTTPS接続に使用される証明書がブラウザで検証され、証明書エラーが発生しない
- **SC-006**: Route53のDNS設定により、loanpedia.jpがCloudFrontディストリビューションに正しく解決される

## Assumptions

- ACM証明書は既に発行済みで、検証が完了している
- Route53のホストゾーンは既に作成されている
- テスト用のindex.htmlは手動でS3バケットにアップロードする（自動デプロイは本機能の対象外）
- バックエンドのALBはまだ構築されていないため、/apiビヘイビアの設定は将来の実装として残す
- CloudFrontの標準アクセスログを使用する（リアルタイムログは対象外）
- WAFのルール設定は基本的なセキュリティルールのみを含む（詳細なカスタムルールは対象外）
- S3バケットへのコンテンツアップロードは、AWSコンソールまたはAWS CLI経由で手動で行う

## Dependencies

- ACM証明書が事前に発行されている必要がある
- Route53のホストゾーンが事前に作成されている必要がある
- loanpedia.jpドメインの所有権が確認されている必要がある

## Out of Scope

- バックエンドALBの構築と/apiパスへの実際のルーティング設定
- フロントエンドアプリケーションの開発
- CI/CDパイプラインを使用した自動デプロイメント
- CloudFrontのリアルタイムログ設定
- カスタムエラーページの作成
- 複数環境（dev、staging、production）の構築
- CloudFront関数やLambda@Edgeの使用
- 詳細なWAFルールのカスタマイズ
