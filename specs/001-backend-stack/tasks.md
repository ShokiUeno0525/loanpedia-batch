# Tasks: バックエンドインフラストラクチャ

**Branch**: `001-backend-stack` | **Date**: 2025-11-23
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

## 実装タスク

本ドキュメントは、バックエンドインフラストラクチャのAWS CDK実装タスクを定義する。

**テスト方針**: スナップショットテスト + 重要な部分のみassertで検証

---

## Phase 1: VPC 2AZ対応（ALB用パブリックサブネット追加のみ）

### T1.1: VPC Stackに2個目のパブリックサブネット追加

**ファイル**: `infra/lib/stacks/vpc-network-stack.ts`

**タスク内容**:
- [X] 既存VPC Stackを読み込み、現在の構成を確認
- [X] AZ-c（ap-northeast-1c）用のパブリックサブネット追加（10.16.16.0/20）
  - **理由**: ALBは最低2AZ必須（AWS仕様）。ダミー用途のパブリックサブネットのみ追加。
- [X] CloudFormation Outputsに新規サブネットIDを追加（`PublicSubnetCId`）
- [X] 日本語コメントで「ALB 2AZ要件のためのダミーサブネット」と記載

**依存関係**: なし

**検証方法**: T1.2のテストで確認

---

### T1.2: VPC Stackのスナップショットテスト更新

**ファイル**: `infra/test/vpc-network-stack.test.ts`

**タスク内容**:
- [X] 既存テストファイルを確認
- [X] スナップショットテストを追加/更新（`expect(template).toMatchSnapshot()`）
- [X] 重要な検証のみassert追加:
  - [X] パブリックサブネットが2個存在（AZ-a、AZ-c）
  - [X] CloudFormation Output `PublicSubnetCId`が存在

**依存関係**: T1.1

**検証方法**: `npm test -- vpc-network-stack.test.ts`

---

## Phase 2: ALB用ACM証明書スタック

### T2.1: ALB ACM Certificate Stack実装

**ファイル**: `infra/lib/stacks/alb-acm-certificate-stack.ts`

**タスク内容**:
- [X] 新規スタッククラス作成（`AlbAcmCertificateStack`）
- [X] Route53 Stackからホストゾーンを参照
- [X] `Certificate`で`api.loanpedia.jp`証明書を作成（DNS検証）
- [X] リージョンを`ap-northeast-1`に設定
- [X] CloudFormation Outputsに証明書ARNを追加（`CertificateArn`）
- [X] 日本語コメントで証明書の用途を記載

**依存関係**: T1.1

**検証方法**: T2.2のテストで確認

---

### T2.2: ALB ACM Certificate Stackのスナップショットテスト作成

**ファイル**: `infra/test/alb-acm-certificate-stack.test.ts`

**タスク内容**:
- [X] 新規テストファイル作成
- [X] スナップショットテストを追加（`expect(template).toMatchSnapshot()`）
- [X] 重要な検証のみassert追加:
  - [X] ACM証明書が1個存在
  - [X] ドメイン名が`api.loanpedia.jp`

**依存関係**: T2.1

**検証方法**: `npm test -- alb-acm-certificate-stack.test.ts`

---

## Phase 3: Security Groups Construct

### T3.1: Security Groups Construct実装

**ファイル**: `infra/lib/constructs/security-groups-construct.ts`

**タスク内容**:
- [X] 新規Constructクラス作成（`SecurityGroupsConstruct`）
- [X] ALB Security Group作成
  - [X] インバウンド: CloudFrontマネージドプレフィックスリスト → 443
  - [X] アウトバウンド: ECS SG → 80
- [X] ECS Security Group作成
  - [X] インバウンド: ALB SG → 80
  - [X] アウトバウンド: RDS SG → 3306、0.0.0.0/0 → 443
- [X] RDS Security Group作成
  - [X] インバウンド: ECS SG → 3306
  - [X] アウトバウンド: なし
- [X] 各SGのpropertyを公開（`albSg`、`ecsSg`、`rdsSg`）
- [X] 日本語コメントで各SGの役割を記載

**依存関係**: T1.1

**検証方法**: T3.2のテストで確認

---

### T3.2: Security Groups Constructのスナップショットテスト作成

**ファイル**: `infra/test/constructs/security-groups-construct.test.ts`

**タスク内容**:
- [X] 新規テストファイル作成
- [X] スナップショットテストを追加（`expect(template).toMatchSnapshot()`）
- [X] 重要な検証のみassert追加:
  - [X] Security Groupが3個存在（ALB、ECS、RDS）

**依存関係**: T3.1

**検証方法**: `npm test -- security-groups-construct.test.ts`

---

## Phase 4: Backend Stack基盤リソース

### T4.1: ECR Repositoriesの実装（Backend Stack内）

**ファイル**: `infra/lib/stacks/backend-stack.ts`（一部）

**タスク内容**:
- [ ] Backend Stack骨組み作成
- [ ] ECRリポジトリ2個作成（`loanpedia-api`、`loanpedia-migration`）
- [ ] イメージスキャンオンプッシュ有効化
- [ ] AES-256暗号化有効化
- [ ] CloudFormation Outputsにリポジトリ URIを追加
- [ ] 日本語コメントで各リポジトリの用途を記載

**依存関係**: T3.1

**検証方法**: T4.5のテストで確認

---

### T4.2: RDS Construct実装

**ファイル**: `infra/lib/constructs/rds-construct.ts`

**タスク内容**:
- [ ] 新規Constructクラス作成（`RdsConstruct`）
- [ ] RDSパラメータグループ作成（utf8mb4設定）
- [ ] RDS MySQLインスタンス作成
  - [ ] エンジン: MySQL 8.0
  - [ ] インスタンスタイプ: db.t3.micro
  - [ ] ストレージ: gp3 20GB
  - [ ] シングルAZ（ap-northeast-1a）
  - [ ] アイソレートサブネット配置（既存の1個のみ使用）
  - [ ] バックアップ保持期間: 7日間
  - [ ] バックアップウィンドウ: 17:00-18:00 UTC（JST 02:00-03:00）
  - [ ] 削除保護: 無効
- [ ] Secrets Manager統合（自動生成認証情報）
- [ ] RDS SGをアタッチ
- [ ] プロパティ公開（`instance`、`secret`）
- [ ] 日本語コメントでRDS設定の理由を記載

**依存関係**: T3.1

**検証方法**: T4.5のテストで確認

---

### T4.3: Cognito Construct実装

**ファイル**: `infra/lib/constructs/cognito-construct.ts`

**タスク内容**:
- [ ] 新規Constructクラス作成（`CognitoConstruct`）
- [ ] Cognito User Pool作成
  - [ ] ユーザー名属性: email
  - [ ] 必須属性: email
  - [ ] 自動検証: email
  - [ ] MFA: REQUIRED、EMAIL_OTP
  - [ ] パスワードポリシー: デフォルト（8文字以上）
- [ ] アプリクライアント作成
  - [ ] クライアントシークレット: 必須
  - [ ] 認証フロー: USER_PASSWORD_AUTH、REFRESH_TOKEN_AUTH、USER_SRP_AUTH
  - [ ] トークン有効期限: アクセス/ID 1時間、リフレッシュ 30日
- [ ] Secrets Managerにクライアントシークレット保存
- [ ] プロパティ公開（`userPool`、`appClient`、`clientSecret`）
- [ ] 日本語コメントでCognito設定の理由を記載

**依存関係**: なし

**検証方法**: T4.5のテストで確認

---

### T4.4: CloudWatch Logs Groups作成（Backend Stack内）

**ファイル**: `infra/lib/stacks/backend-stack.ts`（一部）

**タスク内容**:
- [ ] CloudWatch Logsロググループ2個作成
  - [ ] `/ecs/loanpedia-api`（保持期間7日間）
  - [ ] `/ecs/loanpedia-migration`（保持期間7日間）
- [ ] 削除ポリシー: DESTROY（開発環境）
- [ ] 日本語コメントでログの用途を記載

**依存関係**: なし

**検証方法**: T4.5のテストで確認

---

### T4.5: Backend Stack（基盤リソース）のスナップショットテスト作成

**ファイル**: `infra/test/backend-stack.test.ts`

**タスク内容**:
- [ ] 新規テストファイル作成
- [ ] スナップショットテストを追加（`expect(template).toMatchSnapshot()`）
- [ ] 重要な検証のみassert追加:
  - [ ] ECRリポジトリが2個存在
  - [ ] RDSインスタンスが1個存在
  - [ ] Cognito User Poolが1個存在
  - [ ] CloudWatch Logsロググループが2個存在
  - [ ] Secrets Managerシークレットが2個存在（RDS、Cognito）

**依存関係**: T4.1、T4.2、T4.3、T4.4

**検証方法**: `npm test -- backend-stack.test.ts`

---

## Phase 5: ALB Construct

### T5.1: ALB Construct実装

**ファイル**: `infra/lib/constructs/alb-construct.ts`

**タスク内容**:
- [ ] 新規Constructクラス作成（`AlbConstruct`）
- [ ] Application Load Balancer作成
  - [ ] internet-facing
  - [ ] 2AZ配置（パブリックサブネット: 1a、1c）
  - [ ] ALB SGアタッチ
- [ ] ターゲットグループ作成
  - [ ] ターゲットタイプ: IP（Fargate）
  - [ ] プロトコル: HTTP、ポート: 80
  - [ ] ヘルスチェック: パス `/health`、間隔 30秒、タイムアウト 5秒、しきい値 2回
- [ ] HTTPリスナー作成（80 → 443リダイレクト）
- [ ] HTTPSリスナー作成（443 → ターゲットグループ、ACM証明書使用）
- [ ] Route53 Aレコード作成（`api.loanpedia.jp` → ALB DNS名、Alias）
- [ ] プロパティ公開（`alb`、`targetGroup`）
- [ ] 日本語コメントでALB設定の理由を記載

**依存関係**: T2.1、T3.1

**検証方法**: T5.2のテストで確認

---

### T5.2: ALB Constructのスナップショットテスト作成

**ファイル**: `infra/test/constructs/alb-construct.test.ts`

**タスク内容**:
- [ ] 新規テストファイル作成
- [ ] スナップショットテストを追加（`expect(template).toMatchSnapshot()`）
- [ ] 重要な検証のみassert追加:
  - [ ] ALBが1個存在
  - [ ] ターゲットグループが1個存在
  - [ ] HTTPSリスナーがACM証明書を参照

**依存関係**: T5.1

**検証方法**: `npm test -- alb-construct.test.ts`

---

## Phase 6: ECS Construct

### T6.1: ECS Construct実装

**ファイル**: `infra/lib/constructs/ecs-construct.ts`

**タスク内容**:
- [ ] 新規Constructクラス作成（`EcsConstruct`）
- [ ] ECSクラスター作成（`loanpedia-cluster`、Container Insights無効）
- [ ] IAMタスク実行ロール作成
  - [ ] ECRイメージプル権限
  - [ ] CloudWatch Logs書き込み権限
  - [ ] Secrets Manager参照権限
- [ ] IAMタスクロール作成
  - [ ] Cognito権限（`cognito-idp:*`）
- [ ] Web APIタスク定義作成
  - [ ] Fargate、CPU 512、メモリ 1024MB
  - [ ] コンテナポート 80
  - [ ] ログ: CloudWatch Logs（`/ecs/loanpedia-api`）
  - [ ] 環境変数: Secrets Manager参照（RDS認証情報、Cognitoシークレット）
- [ ] マイグレーションタスク定義作成
  - [ ] Fargate、CPU 256、メモリ 512MB
  - [ ] ログ: CloudWatch Logs（`/ecs/loanpedia-migration`）
  - [ ] 環境変数: Secrets Manager参照（RDS認証情報）
- [ ] Web APIサービス作成
  - [ ] タスク数: 1
  - [ ] プライベートサブネット（ap-northeast-1a、既存の1個のみ）配置
  - [ ] ALBターゲットグループ統合
  - [ ] ECS SGアタッチ
- [ ] プロパティ公開（`cluster`、`apiService`、`apiTaskDefinition`、`migrationTaskDefinition`）
- [ ] 日本語コメントでECS設定の理由を記載

**依存関係**: T3.1、T4.2、T4.3、T4.4、T5.1

**検証方法**: T6.2のテストで確認

---

### T6.2: ECS Constructのスナップショットテスト作成

**ファイル**: `infra/test/constructs/ecs-construct.test.ts`

**タスク内容**:
- [ ] 新規テストファイル作成
- [ ] スナップショットテストを追加（`expect(template).toMatchSnapshot()`）
- [ ] 重要な検証のみassert追加:
  - [ ] ECSクラスターが1個存在
  - [ ] タスク定義が2個存在（API、マイグレーション）
  - [ ] ECSサービスが1個存在

**依存関係**: T6.1

**検証方法**: `npm test -- ecs-construct.test.ts`

---

## Phase 7: Backend Stack統合

### T7.1: Backend Stack完成

**ファイル**: `infra/lib/stacks/backend-stack.ts`

**タスク内容**:
- [ ] 既存の部分実装（T4.1、T4.4）を統合
- [ ] Security Groups Constructを追加
- [ ] RDS Constructを追加
- [ ] Cognito Constructを追加
- [ ] ALB Constructを追加
- [ ] ECS Constructを追加
- [ ] CloudFormation Outputs追加
  - [ ] `AlbDnsName`、`AlbArn`
  - [ ] `EcsClusterName`、`EcsClusterArn`
  - [ ] `ApiServiceName`、`ApiTaskDefinitionArn`、`MigrationTaskDefinitionArn`
  - [ ] `RdsEndpoint`、`RdsPort`、`RdsSecretArn`
  - [ ] `CognitoUserPoolId`、`CognitoAppClientId`、`CognitoSecretArn`
  - [ ] `EcrApiRepositoryUri`、`EcrMigrationRepositoryUri`
- [ ] 日本語コメントでスタック全体の構成を記載

**依存関係**: T4.1、T4.2、T4.3、T4.4、T5.1、T6.1

**検証方法**: T7.2のテストで確認

---

### T7.2: Backend Stack統合テスト更新

**ファイル**: `infra/test/backend-stack.test.ts`

**タスク内容**:
- [ ] 既存テスト（T4.5）を更新
- [ ] スナップショット再生成
- [ ] 追加検証:
  - [ ] ALBが存在
  - [ ] ECSクラスター、サービスが存在
  - [ ] CloudFormation Outputsがすべて存在

**依存関係**: T7.1

**検証方法**: `npm test -- backend-stack.test.ts`

---

## Phase 8: Frontend Stack更新

### T8.1: Frontend StackにCloudFront `/api/*` ビヘイビア追加

**ファイル**: `infra/lib/stacks/frontend-stack.ts`

**タスク内容**:
- [ ] 既存Frontend Stackを確認
- [ ] Backend StackからALB DNS名を参照
- [ ] CloudFront `/api/*` ビヘイビア追加
  - [ ] オリジン: `api.loanpedia.jp`（ALB）
  - [ ] オリジンプロトコル: HTTPS_ONLY
  - [ ] キャッシュポリシー: CACHING_DISABLED
  - [ ] オリジンリクエストポリシー: ALL_VIEWER
  - [ ] 許可メソッド: ALLOW_ALL
  - [ ] ビューワープロトコル: REDIRECT_TO_HTTPS
- [ ] 日本語コメントでビヘイビアの用途を記載

**依存関係**: T7.1

**検証方法**: T8.2のテストで確認

---

### T8.2: Frontend Stack更新テスト

**ファイル**: `infra/test/frontend-stack.test.ts`

**タスク内容**:
- [ ] 既存テストを確認
- [ ] スナップショットテストを追加/更新
- [ ] 重要な検証のみassert追加:
  - [ ] CloudFrontディストリビューションが存在
  - [ ] `/api/*` ビヘイビアが存在

**依存関係**: T8.1

**検証方法**: `npm test -- frontend-stack.test.ts`

---

## Phase 9: CDKアプリエントリーポイント更新

### T9.1: CDKアプリに新規スタックを追加

**ファイル**: `infra/bin/infra.ts`

**タスク内容**:
- [ ] 既存CDKアプリエントリーポイントを確認
- [ ] `AlbAcmCertificateStack`をインスタンス化（ap-northeast-1）
- [ ] `BackendStack`をインスタンス化（ap-northeast-1）
- [ ] スタック間の依存関係を設定
  - [ ] Backend Stack → VPC Stack
  - [ ] Backend Stack → Route53 Stack
  - [ ] Backend Stack → ALB ACM Certificate Stack
  - [ ] Frontend Stack → Backend Stack
- [ ] 日本語コメントでデプロイ順序を記載

**依存関係**: T2.1、T7.1、T8.1

**検証方法**: `npm run build`でビルド成功確認

---

## Phase 10: ドキュメント更新

### T10.1: インフラREADME更新

**ファイル**: `infra/README.md`

**タスク内容**:
- [ ] 既存READMEを確認
- [ ] Backend Stack追加を記載
- [ ] デプロイ手順を更新
  1. VPC Stack更新（2個目のパブリックサブネット追加）
  2. ALB ACM Certificate Stack作成
  3. Backend Stack作成
  4. Frontend Stack更新
- [ ] 主要なCloudFormation Outputs一覧を追加
- [ ] 日本語で記載

**依存関係**: T9.1

**検証方法**: 目視確認

---

### T10.2: .gitignore確認・更新

**ファイル**: `.gitignore`（リポジトリルート）

**タスク内容**:
- [ ] 既存`.gitignore`を確認
- [ ] CDK関連パターン確認・追加
  - [ ] `cdk.out/`
  - [ ] `.cdk.staging/`
  - [ ] `*.js`、`*.d.ts`（TypeScriptビルド成果物）
- [ ] 機密情報パターン確認
  - [ ] `.env`、`.env.*`

**依存関係**: なし

**検証方法**: 目視確認

---

## タスク実行順序

### デプロイ依存関係に基づく順序

1. **Phase 1**: VPC 2AZ対応（T1.1 → T1.2）
2. **Phase 2**: ALB ACM証明書（T2.1 → T2.2）
3. **Phase 3**: Security Groups（T3.1 → T3.2）
4. **Phase 4**: 基盤リソース（T4.1〜T4.5、T4.1/T4.2/T4.3/T4.4は並行可能）
5. **Phase 5**: ALB（T5.1 → T5.2）
6. **Phase 6**: ECS（T6.1 → T6.2）
7. **Phase 7**: Backend Stack統合（T7.1 → T7.2）
8. **Phase 8**: Frontend Stack更新（T8.1 → T8.2）
9. **Phase 9**: CDKアプリ更新（T9.1）
10. **Phase 10**: ドキュメント更新（T10.1、T10.2、並行可能）

---

## 実装完了基準

- [ ] すべてのタスクが完了
- [ ] `npm run build`が成功
- [ ] `npm test`がすべてのテストでPASS
- [ ] スナップショットが生成されている
- [ ] 日本語コメントがすべてのファイルに記載されている
- [ ] CloudFormation Outputsが仕様通り出力されている

---

## 注意事項

- **デプロイは別作業**: 本タスクリストはCDKコード実装のみ。実際のAWSへのデプロイは別途実施。
- **ECRイメージは別作業**: ECRリポジトリの作成のみ。Dockerイメージのビルド・プッシュは別タスク。
- **アプリケーションコードは対象外**: ECSタスク定義の作成のみ。Laravel APIやマイグレーションコードは別タスク。
- **テスト方針**: スナップショットテスト中心、重要な検証のみassert。
