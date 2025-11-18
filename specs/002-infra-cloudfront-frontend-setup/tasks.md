# Tasks: CloudFront フロントエンド配信基盤

**Input**: Design documents from `/specs/001-cloudfront-frontend-setup/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: 本機能はTDD（テスト駆動開発）アプローチで進めます。各ユーザーストーリーの実装前にCDKテストを作成し、テストが失敗することを確認してから実装します。

**Organization**: タスクはユーザーストーリー（US1〜US4）ごとにグループ化し、各ストーリーが独立して実装・テスト可能になっています。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: このタスクが属するユーザーストーリー（US1, US2, US3, US4）
- 説明には正確なファイルパスを含める

## Path Conventions

本プロジェクトはAWS CDKによるインフラストラクチャ定義です：
- **infra/lib/**: CDKスタックとConstruct定義
- **infra/bin/**: CDKアプリケーションエントリーポイント
- **infra/test/**: CDK統合テスト

---

## Phase 1: Setup（共有インフラ）

**目的**: プロジェクト初期化と基本構造のセットアップ

- [X] T001 既存のinfra/ディレクトリ構造を確認し、新しいスタック用のファイル配置を計画
- [X] T002 infra/lib/constructs/ディレクトリを作成（Constructの配置場所）
- [X] T003 [P] package.jsonの依存関係を確認（aws-cdk-lib 2.215.0以上、TypeScript 5.6.3）

---

## Phase 2: Foundational（ブロッキング前提条件）

**目的**: すべてのユーザーストーリーの実装前に完了する必要があるコアインフラ

**⚠️ CRITICAL**: このフェーズが完了するまで、ユーザーストーリーの作業を開始できません

- [X] T004 既存のRoute53ホストゾーンとACM証明書を確認（loanpedia.jp）
- [X] T005 [P] infra/lib/constructs/frontend-s3-bucket.tsでFrontendBucket Constructを作成
- [X] T006 [P] infra/lib/constructs/waf-cloudfront.tsでWAF Construct（CfnWebACL）を作成
- [X] T007 infra/lib/001-cloudfront-frontend-setup-stack.tsでメインスタッククラスを作成

**Checkpoint**: 基盤準備完了 - ユーザーストーリー実装を並列開始可能

---

## Phase 3: User Story 1 - 基本的なフロントエンドコンテンツ配信 (Priority: P1) 🎯 MVP

**Goal**: エンドユーザーが https://loanpedia.jp にアクセスして、フロントエンドアプリケーションを閲覧できるようにする

**Independent Test**:
- S3バケットにテスト用のindex.htmlをアップロード
- ブラウザで https://loanpedia.jp にアクセス
- index.htmlの内容が正しく表示されることを確認

### Tests for User Story 1 (TDD) 🔴

> **重要**: これらのテストを最初に書き、テストが失敗することを確認してから実装を開始します

- [ ] T008 [P] [US1] CDKテストファイル（infra/test/001-cloudfront-frontend-setup.test.ts）を作成し、基本構造をセットアップ
  - Jestテストフレームワークの設定
  - スタックのインスタンス化テスト

- [ ] T009 [P] [US1] S3バケット作成のテストを追加（infra/test/001-cloudfront-frontend-setup.test.ts）
  - FrontendBucketが作成されることをテスト
  - LogBucketが作成されることをテスト
  - バケットプロパティ（暗号化、パブリックアクセスブロック等）をテスト
  - **期待される結果**: テスト失敗（赤🔴）- リソースがまだ実装されていない

- [ ] T010 [P] [US1] CloudFrontディストリビューション作成のテストを追加（infra/test/001-cloudfront-frontend-setup.test.ts）
  - CloudFrontディストリビューションが作成されることをテスト
  - domainName、certificate、defaultRootObject等のプロパティをテスト
  - デフォルトビヘイビアの設定をテスト
  - **期待される結果**: テスト失敗（赤🔴）

- [ ] T011 [P] [US1] OAC設定のテストを追加（infra/test/001-cloudfront-frontend-setup.test.ts）
  - OACが作成されることをテスト
  - S3バケットポリシーにOACアクセスが含まれることをテスト
  - **期待される結果**: テスト失敗（赤🔴）

- [ ] T012 [P] [US1] Route53レコード作成のテストを追加（infra/test/001-cloudfront-frontend-setup.test.ts）
  - Aレコードが作成されることをテスト
  - ターゲットがCloudFrontディストリビューションであることをテスト
  - **期待される結果**: テスト失敗（赤🔴）

- [ ] T013 [P] [US1] CloudFormation Outputsのテストを追加（infra/test/001-cloudfront-frontend-setup.test.ts）
  - 必要なOutputs（DistributionId、FrontendBucketName等）が定義されていることをテスト
  - Export名が正しいことをテスト
  - **期待される結果**: テスト失敗（赤🔴）

- [ ] T014 [US1] すべてのテストを実行して失敗を確認
  ```bash
  cd infra && npm test
  # 期待される結果: すべてのテストが失敗（赤🔴）
  ```

**Checkpoint**: すべてのテストが失敗（赤🔴）- これで実装を開始する準備が整いました

---

### Implementation for User Story 1 🟢

> **重要**: テストが失敗（赤🔴）することを確認してから、この実装セクションを開始します

#### S3バケット（基盤リソース）

- [ ] T015 [P] [US1] FrontendBucket Construct（infra/lib/constructs/frontend-s3-bucket.ts）にプライベートS3バケットを実装
  - bucketName: `loanpedia-frontend-${accountId}`
  - blockPublicAccess: BLOCK_ALL
  - encryption: S3_MANAGED
  - versioned: true
  - removalPolicy: RETAIN

- [ ] T016 [P] [US1] LogBucket用のS3バケット（infra/lib/constructs/frontend-s3-bucket.tsまたは別Construct）を実装
  - bucketName: `loanpedia-cloudfront-logs-${accountId}`
  - blockPublicAccess: BLOCK_ALL
  - encryption: S3_MANAGED
  - lifecycleRules: 30日後に削除
  - objectOwnership: OBJECT_WRITER

- [ ] T017 [US1] S3バケット関連のテストを実行して成功（緑🟢）を確認
  ```bash
  cd infra && npm test -- --testNamePattern="S3"
  # 期待される結果: S3バケットテストが成功（緑🟢）
  ```

#### OAC（アクセス制御）

- [ ] T018 [US1] infra/lib/constructs/frontend-distribution.tsでOAC（S3OriginAccessControl）を作成
  - signing: SIGV4_ALWAYS
  - originAccessControlOriginType: s3

- [ ] T019 [US1] OAC関連のテストを実行して成功（緑🟢）を確認
  ```bash
  cd infra && npm test -- --testNamePattern="OAC"
  # 期待される結果: OACテストが成功（緑🟢）
  ```

#### CloudFrontディストリビューション（コア配信）

- [ ] T020 [US1] FrontendDistribution Construct（infra/lib/constructs/frontend-distribution.ts）でCloudFrontディストリビューションを実装
  - domainName: loanpedia.jp（ACM証明書とカスタムドメイン設定）
  - certificate: 既存のACM証明書をImportまたはExportから参照
  - defaultRootObject: index.html
  - priceClass: PRICE_CLASS_200
  - enableLogging: true
  - logBucket: LogBucket参照
  - logFilePrefix: 'cloudfront/'

- [ ] T021 [US1] CloudFrontディストリビューションのデフォルトビヘイビアを設定
  - origin: S3BucketOrigin.withOriginAccessControl（FrontendBucket + OAC）
  - viewerProtocolPolicy: REDIRECT_TO_HTTPS
  - allowedMethods: ALLOW_GET_HEAD
  - cachedMethods: CACHE_GET_HEAD
  - compress: true
  - cachePolicy: CachingOptimized

- [ ] T022 [US1] /apiビヘイビアのプレースホルダーをTODOコメントとして追加

- [ ] T023 [US1] CloudFrontディストリビューション関連のテストを実行して成功（緑🟢）を確認
  ```bash
  cd infra && npm test -- --testNamePattern="CloudFront"
  # 期待される結果: CloudFrontディストリビューションテストが成功（緑🟢）
  ```

#### S3バケットポリシー（セキュリティ）

- [ ] T024 [US1] FrontendBucketにOAC経由のCloudFrontアクセスを許可するバケットポリシーを追加
  - principals: ServicePrincipal('cloudfront.amazonaws.com')
  - conditions: StringEquals 'AWS:SourceArn'
  - actions: s3:GetObject

#### Route53レコード（DNS設定）

- [ ] T025 [US1] メインスタック（infra/lib/001-cloudfront-frontend-setup-stack.ts）でRoute53 Aレコードを作成
  - zone: 既存のloanpedia.jpホストゾーンをfromLookup()で参照
  - recordName: loanpedia.jp
  - target: CloudFrontTarget(distribution)

- [ ] T026 [US1] Route53レコード関連のテストを実行して成功（緑🟢）を確認
  ```bash
  cd infra && npm test -- --testNamePattern="Route53"
  # 期待される結果: Route53レコードテストが成功（緑🟢）
  ```

#### スタック統合とOutputs

- [ ] T027 [US1] メインスタック（infra/lib/001-cloudfront-frontend-setup-stack.ts）ですべてのConstructをインスタンス化し統合
  - FrontendBucket Constructのインスタンス化
  - FrontendDistribution Constructのインスタンス化
  - Constructsの相互参照を設定

- [ ] T028 [US1] CloudFormation Outputsを実装（contracts/cloudformation-outputs.yamlに従う）
  - DistributionId（Export: LoanpediaCloudFrontDistributionId）
  - DistributionDomainName（Export: LoanpediaCloudFrontDomainName）
  - DistributionArn（Export: LoanpediaCloudFrontDistributionArn）
  - FrontendBucketName（Export: LoanpediaFrontendBucketName）
  - FrontendBucketArn（Export: LoanpediaFrontendBucketArn）
  - FrontendBucketDomainName（Export: LoanpediaFrontendBucketDomainName）
  - LogBucketName（Export: LoanpediaCloudFrontLogBucketName）
  - LogBucketArn（Export: LoanpediaCloudFrontLogBucketArn）
  - CustomDomainName（Export: LoanpediaCloudFrontCustomDomain）
  - Route53RecordName（Export: LoanpediaCloudFrontRoute53RecordName）

- [ ] T029 [US1] CloudFormation Outputs関連のテストを実行して成功（緑🟢）を確認
  ```bash
  cd infra && npm test -- --testNamePattern="Outputs"
  # 期待される結果: Outputsテストが成功（緑🟢）
  ```

#### CDKアプリケーション統合

- [ ] T030 [US1] infra/bin/loanpedia-app.tsに新しいスタック（CloudFrontFrontendStack）を追加
  - account: process.env.CDK_DEFAULT_ACCOUNT
  - region: process.env.CDK_DEFAULT_REGION（WAF以外のリソース用）

- [ ] T031 [US1] すべてのテストを実行して全体的な成功（緑🟢）を確認
  ```bash
  cd infra && npm test
  # 期待される結果: すべてのテストが成功（緑🟢）
  ```

**Checkpoint**: すべてのテストが成功（緑🟢）- 実装が完了しました

---

#### デプロイと手動検証

- [ ] T032 [US1] CDKスタックをシンセサイズして生成されたCloudFormationテンプレートを確認
  ```bash
  cd infra && cdk synth CloudFrontFrontendStack
  ```

- [ ] T033 [US1] CDKスタックをデプロイ（開発環境またはステージング環境）
  ```bash
  cd infra && cdk deploy CloudFrontFrontendStack
  ```

- [ ] T034 [US1] テスト用index.htmlを作成してS3バケットにアップロード
  - quickstart.mdのStep 9のHTMLコンテンツを使用
  - aws s3 cp /tmp/index.html s3://${BUCKET_NAME}/index.html

- [ ] T035 [US1] https://loanpedia.jp でブラウザアクセスして、index.htmlが表示されることを確認

- [ ] T036 [US1] デフォルトルートオブジェクト（/index.html）の動作を確認
  - https://loanpedia.jp/ にアクセスして自動的にindex.htmlが表示されることを確認

- [ ] T037 [US1] HTTPS接続と証明書の検証
  - ブラウザで証明書エラーが発生しないことを確認
  - SSL/TLS接続が正常に確立されることを確認

**Checkpoint**: この時点で、User Story 1は完全に機能し、独立してテスト可能です

---

## Phase 4: User Story 2 - セキュアなコンテンツ配信 (Priority: P2)

**Goal**: 管理者がS3バケットへの直接アクセスを防ぎ、CloudFront経由でのみフロントエンドコンテンツを配信できるようにする

**Independent Test**:
- S3バケットの直接URLにアクセスを試行し、アクセス拒否されることを確認
- CloudFront URLからは正常にアクセスできることを確認

### Implementation for User Story 2

**注**: User Story 2の実装はUser Story 1で既に完了しています（OAC、バケットポリシー、パブリックアクセスブロック）。このフェーズは検証とテストのみです。

#### セキュリティ検証

- [ ] T025 [US2] S3バケットの直接URLにアクセスしてアクセス拒否（403 Forbidden）を確認
  ```bash
  curl -I https://${BUCKET_DOMAIN}/index.html
  # 期待される結果: HTTP/1.1 403 Forbidden
  ```

- [ ] T026 [US2] CloudFront経由のアクセスが正常に機能することを確認
  ```bash
  curl -I https://loanpedia.jp/index.html
  # 期待される結果: HTTP/2 200
  ```

- [ ] T027 [US2] S3バケットのパブリックアクセスブロック設定を確認
  ```bash
  aws s3api get-public-access-block --bucket ${BUCKET_NAME}
  # すべてのパブリックアクセスがブロックされていることを確認
  ```

- [ ] T028 [US2] OACのバケットポリシーが正しく設定されていることを確認
  ```bash
  aws s3api get-bucket-policy --bucket ${BUCKET_NAME}
  # CloudFrontのOAC経由のみアクセス許可されていることを確認
  ```

- [ ] T029 [US2] CloudFrontディストリビューションのOAC設定を確認
  ```bash
  aws cloudfront get-distribution --id ${DISTRIBUTION_ID}
  # OACが正しく関連付けられていることを確認
  ```

**Checkpoint**: この時点で、User Stories 1とUser Story 2の両方が独立して機能します

---

## Phase 5: User Story 3 - WAFによる保護 (Priority: P3)

**Goal**: 管理者がWAFを使用して、悪意のあるトラフィックやDDoS攻撃からサービスを保護できるようにする

**Independent Test**:
- WAFがCloudFrontディストリビューションに関連付けられていることを確認
- WAFのメトリクスがCloudWatchで取得できることを確認

### Tests for User Story 3 (TDD) 🔴

> **重要**: これらのテストを最初に書き、テストが失敗することを確認してから実装を開始します

- [ ] T038 [P] [US3] WAF WebACL作成のテストを追加（infra/test/001-cloudfront-frontend-setup.test.ts）
  - WAF WebACLが作成されることをテスト
  - scope が CLOUDFRONT であることをテスト
  - AWS Managed Rulesが含まれることをテスト
  - CloudWatchメトリクスが有効であることをテスト
  - **期待される結果**: テスト失敗（赤🔴）- WAFがまだ実装されていない

- [ ] T039 [P] [US3] CloudFrontとWAF統合のテストを追加（infra/test/001-cloudfront-frontend-setup.test.ts）
  - CloudFrontディストリビューションにWAF WebACLが関連付けられていることをテスト
  - WebACL ARNが正しく設定されていることをテスト
  - **期待される結果**: テスト失敗（赤🔴）

- [ ] T040 [P] [US3] WAF Outputsのテストを追加（infra/test/001-cloudfront-frontend-setup.test.ts）
  - WebAclId、WebAclArn がOutputsに含まれることをテスト
  - **期待される結果**: テスト失敗（赤🔴）

- [ ] T041 [US3] WAF関連のすべてのテストを実行して失敗を確認
  ```bash
  cd infra && npm test -- --testNamePattern="WAF"
  # 期待される結果: すべてのWAFテストが失敗（赤🔴）
  ```

**Checkpoint**: すべてのWAFテストが失敗（赤🔴）- 実装を開始する準備が整いました

---

### Implementation for User Story 3 🟢

> **重要**: テストが失敗（赤🔴）することを確認してから、この実装セクションを開始します

#### WAF WebACL実装

- [ ] T042 [P] [US3] WAF Construct（infra/lib/constructs/waf-cloudfront.ts）でCfnWebACLを実装
  - name: loanpedia-cloudfront-waf
  - scope: CLOUDFRONT（必須：CloudFront用）
  - defaultAction: allow
  - region: us-east-1（必須：CloudFront用WAFはus-east-1リージョン）

- [ ] T043 [US3] AWS Managed RulesをWAF WebACLに追加
  - AWSManagedRulesCommonRuleSet
  - priority: 1
  - cloudWatchMetricsEnabled: true
  - metricName: AWSManagedRulesCommonRuleSetMetric

- [ ] T044 [US3] WAF WebACLのvisibilityConfigを設定
  - sampledRequestsEnabled: true
  - cloudWatchMetricsEnabled: true
  - metricName: WebAclMetric

- [ ] T045 [US3] WAF WebACL作成のテストを実行して成功（緑🟢）を確認
  ```bash
  cd infra && npm test -- --testNamePattern="WAF.*WebACL"
  # 期待される結果: WAF WebACLテストが成功（緑🟢）
  ```

#### CloudFrontとWAFの統合

- [ ] T046 [US3] メインスタック（infra/lib/001-cloudfront-frontend-setup-stack.ts）でWAF Constructをインスタンス化
  - us-east-1リージョンでWAFスタックまたはConstructを作成
  - WAF WebACL ARNを取得

- [ ] T047 [US3] CloudFrontディストリビューション（infra/lib/constructs/frontend-distribution.ts）にWAF WebACLを関連付け
  - webAclId: WAF WebACLのARN

- [ ] T048 [US3] CloudFrontとWAF統合のテストを実行して成功（緑🟢）を確認
  ```bash
  cd infra && npm test -- --testNamePattern="WAF.*CloudFront"
  # 期待される結果: WAF統合テストが成功（緑🟢）
  ```

#### CloudFormation Outputs追加

- [ ] T049 [US3] WAF関連のCloudFormation Outputsを追加
  - WebAclId（Export: LoanpediaCloudFrontWebAclId）
  - WebAclArn（Export: LoanpediaCloudFrontWebAclArn）

- [ ] T050 [US3] WAF Outputsのテストを実行して成功（緑🟢）を確認
  ```bash
  cd infra && npm test -- --testNamePattern="WAF.*Outputs"
  # 期待される結果: WAF Outputsテストが成功（緑🟢）
  ```

- [ ] T051 [US3] すべてのWAFテストを実行して全体的な成功（緑🟢）を確認
  ```bash
  cd infra && npm test -- --testNamePattern="WAF"
  # 期待される結果: すべてのWAFテストが成功（緑🟢）
  ```

**Checkpoint**: すべてのWAFテストが成功（緑🟢）- 実装が完了しました

---

#### デプロイと手動検証

- [ ] T052 [US3] CDKスタックを再デプロイしてWAFを有効化
  ```bash
  cd infra && cdk deploy CloudFrontFrontendStack
  ```

- [ ] T053 [US3] WAFがCloudFrontディストリビューションに正しく関連付けられていることを確認
  ```bash
  aws cloudfront get-distribution --id ${DISTRIBUTION_ID}
  # WebACLIdが設定されていることを確認
  ```

- [ ] T038 [US3] 通常のアクセスがWAFで許可されることを確認
  ```bash
  curl -I https://loanpedia.jp/
  # 期待される結果: HTTP/2 200（ブロックされない）
  ```

- [ ] T039 [US3] CloudWatch でWAFメトリクスを確認
  ```bash
  aws cloudwatch get-metric-statistics \
    --namespace AWS/WAFV2 \
    --metric-name AllowedRequests \
    --dimensions Name=WebACL,Value=${WEB_ACL_ID} Name=Region,Value=us-east-1 Name=Rule,Value=ALL \
    --start-time ... --end-time ... \
    --period 300 --statistics Sum
  ```

**Checkpoint**: すべてのUser Stories（US1、US2、US3）が独立して機能します

---

## Phase 6: User Story 4 - アクセスログの記録と監視 (Priority: P3)

**Goal**: 管理者がCloudFrontのアクセスログをCloudWatch Logsで確認し、トラフィックパターンや問題を分析できるようにする

**Independent Test**:
- CloudFrontディストリビューションにアクセス
- CloudWatch Logsでロググループを確認し、アクセスログが記録されていることを検証

**注**: 本フェーズでは、まずS3バケットへのログ出力を実装します。CloudWatch Logsへの転送は将来の拡張として残します。

### Implementation for User Story 4

#### ログ設定（既に実装済み）

**注**: User Story 1でLogBucketとCloudFrontのログ設定は既に実装済みです。このフェーズは検証のみです。

#### ログ検証

- [ ] T040 [US4] CloudFrontのログ設定を確認
  ```bash
  aws cloudfront get-distribution --id ${DISTRIBUTION_ID}
  # enableLogging: true, logBucket, logFilePrefix が設定されていることを確認
  ```

- [ ] T041 [US4] https://loanpedia.jp に複数回アクセスしてログを生成

- [ ] T042 [US4] S3ログバケットにログファイルが作成されることを確認（数分後）
  ```bash
  aws s3 ls s3://${LOG_BUCKET}/cloudfront/ --recursive
  ```

- [ ] T043 [US4] ログファイルをダウンロードして内容を確認
  ```bash
  aws s3 cp s3://${LOG_BUCKET}/cloudfront/[ログファイル名] /tmp/cloudfront-log.gz
  gunzip /tmp/cloudfront-log.gz
  cat /tmp/cloudfront-log
  # タイムスタンプ、IPアドレス、ステータスコード等が記録されていることを確認
  ```

#### 将来の拡張準備（オプション）

- [ ] T044 [P] [US4] CloudWatch Logsロググループを作成（将来の拡張用）
  - logGroupName: /aws/cloudfront/loanpedia
  - retention: ONE_MONTH
  - removalPolicy: DESTROY
  - **注**: S3からCloudWatch Logsへの転送は未実装（Lambda/Firehose必要）

**Checkpoint**: すべてのUser Stories（US1〜US4）が完了し、独立して機能します

---

## Phase 7: Polish & Cross-Cutting Concerns

**目的**: 複数のユーザーストーリーに影響する改善

- [ ] T045 [P] CDK統合テスト（infra/test/001-cloudfront-frontend-setup.test.ts）を作成
  - スタックが正しくシンセサイズされることをテスト
  - 主要なリソース（CloudFront、S3、WAF、Route53）が作成されることをテスト
  - CloudFormation Outputsが正しく定義されていることをテスト

- [ ] T046 [P] TypeScriptコードのリント・フォーマット確認
  ```bash
  cd infra && npm run lint && npm run format
  ```

- [ ] T047 [P] すべてのTypeScriptファイルに日本語コメントを追加
  - 憲章「I. 日本語優先」に準拠

- [ ] T048 スタックにタグを追加
  - Project: Loanpedia
  - Environment: Production
  - ManagedBy: CDK

- [ ] T049 quickstart.md（specs/001-cloudfront-frontend-setup/quickstart.md）のステップをすべて検証
  - セットアップ手順が正確であることを確認
  - トラブルシューティングセクションの有効性を確認

- [ ] T050 [P] セキュリティレビュー
  - すべての機密情報が環境変数またはCloudFormation Exportから参照されていることを確認
  - S3バケットポリシー、OAC設定、WAF設定のセキュリティベストプラクティス準拠を確認
  - IAM権限が最小権限の原則に従っていることを確認

- [ ] T051 [P] パフォーマンス最適化確認
  - CloudFrontのキャッシュポリシーが適切に設定されていることを確認
  - 自動圧縮が有効化されていることを確認
  - Price Classが適切（PRICE_CLASS_200）に設定されていることを確認

- [ ] T052 コードクリーンアップとリファクタリング
  - 重複コードの削除
  - Constructの再利用性向上
  - TypeScriptの型安全性向上

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存関係なし - すぐに開始可能
- **Foundational (Phase 2)**: Setupの完了に依存 - すべてのユーザーストーリーをブロック
- **User Stories (Phase 3-6)**: すべてFoundational phase完了に依存
  - ユーザーストーリーは並列実行可能（スタッフがいる場合）
  - または優先順位順に順次実行（P1 → P2 → P3 → P3）
- **Polish (Final Phase)**: すべての希望するユーザーストーリーの完了に依存

### User Story Dependencies

- **User Story 1 (P1)**: Foundational (Phase 2)の後に開始可能 - 他のストーリーへの依存なし
- **User Story 2 (P2)**: Foundational (Phase 2)の後に開始可能 - US1に統合される可能性があるが、独立してテスト可能
- **User Story 3 (P3)**: Foundational (Phase 2)の後に開始可能 - US1に統合される可能性があるが、独立してテスト可能
- **User Story 4 (P3)**: Foundational (Phase 2)の後に開始可能 - US1に統合される可能性があるが、独立してテスト可能

### 各ユーザーストーリー内

- Constructの実装 → スタックへの統合
- スタック統合 → CDKアプリケーション統合
- デプロイ → 検証
- コア実装 → 統合前
- ストーリー完了 → 次の優先度へ移動

### 並列実行の機会

- すべてのSetupタスク（[P]マーク）は並列実行可能
- すべてのFoundationalタスク（[P]マーク）は並列実行可能（Phase 2内）
- Foundational phase完了後、すべてのユーザーストーリーを並列開始可能（チーム容量が許せば）
- ストーリー内のモデル（Construct）で[P]マークされたものは並列実行可能
- 異なるユーザーストーリーは異なるチームメンバーが並列作業可能

---

## Parallel Example: User Story 1

```bash
# User Story 1のすべてのConstruct作成を並列実行:
Task: "FrontendBucket Constructにプライベート S3バケットを実装（infra/lib/constructs/frontend-s3-bucket.ts）"
Task: "LogBucket用のS3バケットを実装（infra/lib/constructs/frontend-s3-bucket.ts）"
# 注: これらは同じファイルの場合、順次実行が必要

# 異なるConstructファイルは並列実行可能:
Task: "FrontendBucket Construct を実装（infra/lib/constructs/frontend-s3-bucket.ts）"
Task: "WAF Construct を実装（infra/lib/constructs/waf-cloudfront.ts）"
```

---

## Implementation Strategy

### MVP First (User Story 1のみ)

1. Phase 1完了: Setup
2. Phase 2完了: Foundational（CRITICAL - すべてのストーリーをブロック）
3. Phase 3完了: User Story 1
4. **STOP and VALIDATE**: User Story 1を独立してテスト
5. 準備ができていればデプロイ/デモ

### Incremental Delivery

1. Setup + Foundational完了 → 基盤準備完了
2. User Story 1追加 → 独立してテスト → デプロイ/デモ（MVP！）
3. User Story 2追加 → 独立してテスト → デプロイ/デモ
4. User Story 3追加 → 独立してテスト → デプロイ/デモ
5. User Story 4追加 → 独立してテスト → デプロイ/デモ
6. 各ストーリーが前のストーリーを壊すことなく価値を追加

### Parallel Team Strategy

複数の開発者がいる場合:

1. チーム全体でSetup + Foundationalを完了
2. Foundational完了後:
   - 開発者A: User Story 1
   - 開発者B: User Story 3（WAF）
   - 開発者C: User Story 4（ログ）
   - **注**: User Story 2はUser Story 1に統合されているため、別タスクなし
3. ストーリーが独立して完了・統合

---

## Notes

- [P]タスク = 異なるファイル、依存関係なし
- [Story]ラベル = 特定のユーザーストーリーへのタスクのマッピング（トレーサビリティ）
- 各ユーザーストーリーは独立して完了・テスト可能
- 各タスクまたは論理的なグループの後にコミット
- どのチェックポイントでも停止して、ストーリーを独立して検証
- 避けるべきこと: 曖昧なタスク、同じファイルの競合、独立性を損なうストーリー間の依存関係

---

## TDD Cycle（Red-Green-Refactor）

本タスクリストは**テスト駆動開発（TDD）**アプローチに従っています：

### 🔴 Red Phase（失敗）
1. **テストを最初に書く**: 実装前にCDKテストを作成
2. **テストを実行**: `npm test` でテストが失敗（赤🔴）することを確認
3. **失敗の確認**: まだ実装されていないため、テストが期待通りに失敗

### 🟢 Green Phase（成功）
4. **最小限の実装**: テストを成功させるための最小限のコードを書く
5. **テストを再実行**: `npm test` でテストが成功（緑🟢）することを確認
6. **段階的な実装**: 各コンポーネント実装後にテストを実行

### 🔵 Refactor Phase（リファクタリング）
7. **コードの改善**: テストが成功している状態でコードを改善
8. **テストの維持**: リファクタリング後もテストが成功し続けることを確認
9. **次のサイクル**: 次の機能の🔴 Red Phaseに移行

### TDDの利点

- **バグの早期発見**: 実装前にテストがあるため、バグを早期に発見
- **設計の改善**: テストを書くことで、APIとインターフェースが明確になる
- **リファクタリングの安全性**: テストがあるため、安心してコードを改善できる
- **ドキュメントの役割**: テストが仕様書と実装例の役割を果たす

---

## Task Summary

- **合計タスク数**: 73タスク（TDD対応版）
- **並列実行可能タスク**: 18タスク（[P]マーク）
- **TDDサイクルタスク**:
  - **User Story 1**: 30タスク（T008-T037）
    - テスト作成: 7タスク（T008-T014）🔴
    - 実装: 16タスク（T015-T030）🟢
    - テスト検証: 6タスク（T017, T019, T023, T026, T029, T031）
    - デプロイ: 6タスク（T032-T037）
  - **User Story 2**: 5タスク（検証のみ）
  - **User Story 3**: 16タスク（T038-T053）
    - テスト作成: 4タスク（T038-T041）🔴
    - 実装: 9タスク（T042-T051）🟢
    - デプロイ: 2タスク（T052-T053）
  - **User Story 4**: 5タスク（検証のみ）
  - **Polish & Cross-Cutting**: 7タスク

## MVP Scope（推奨）

**User Story 1のみ**を実装してMVPとすることを推奨します：
- 基本的なフロントエンドコンテンツ配信（CloudFront + S3 + OAC）
- HTTPS接続（ACM証明書）
- DNS設定（Route53）
- セキュリティ（プライベートS3バケット、OAC）

### MVPのTDDフロー

1. 🔴 **Red**: User Story 1のテストを作成（T008-T014）→ テスト失敗を確認
2. 🟢 **Green**: User Story 1を実装（T015-T031）→ テスト成功を確認
3. **Deploy**: デプロイと手動検証（T032-T037）
4. **Validate**: MVPが完全に動作することを確認

MVPデプロイ後、User Story 2〜4を段階的に追加できます。
