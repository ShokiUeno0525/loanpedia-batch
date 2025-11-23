# Feature Specification: バックエンドインフラストラクチャ

**Feature Branch**: `001-backend-stack`
**Created**: 2025-11-23
**Status**: Draft
**Input**: User description: "インフラの最後の仕上げです。バックエンドスタックを追加します。仕様を整理してください。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - VPCマルチAZ対応の完了 (Priority: P1)

既存のVPCネットワークをシングルAZからマルチAZ構成に拡張し、高可用性を実現する。ALBの配置要件を満たすため、2つのアベイラビリティゾーン（ap-northeast-1a, 1c）にサブネットを展開する。

**Why this priority**: ALBは最低2AZ必須であり、これが完了しないと後続のすべてのコンポーネント（ALB、ECS、RDS）をデプロイできない。インフラの基盤となる最重要タスク。

**Independent Test**: VPCスタックをデプロイし、AWS Console/CLIで以下を確認できる:
- パブリックサブネットが2AZ（1a, 1c）に存在
- プライベートサブネットが2AZ（1a, 1c）に存在
- アイソレートサブネットが2AZ（1a, 1c）に存在
- NAT Gatewayが1a側のみに存在
- 各サブネットのCIDRブロックが仕様通り（10.16.x.x/20）

**Acceptance Scenarios**:

1. **Given** 既存VPCスタック（シングルAZ: 1a）が存在、**When** スタックを更新してマルチAZ対応を適用、**Then** パブリック/プライベート/アイソレートサブネットがAZ-a、AZ-cの両方に作成される
2. **Given** マルチAZ VPCが構築済み、**When** AZ-cのプライベートサブネットからインターネットアクセスを試行、**Then** AZ-aのNAT Gateway経由で通信が成功する
3. **Given** マルチAZ VPCが構築済み、**When** サブネットのCIDRブロックを確認、**Then** パブリック（0.0/20, 16.0/20）、プライベート（32.0/20, 48.0/20）、アイソレート（64.0/20, 80.0/20）が仕様通り割り当てられている

---

### User Story 2 - ACM証明書とRoute53レコードの構成 (Priority: P1)

ALB用のSSL/TLS証明書を`api.loanpedia.jp`ドメインでap-northeast-1リージョンに発行し、Route53でAレコード（Alias）を設定する。

**Why this priority**: ALBでHTTPS通信を実現するために必須。証明書の発行とDNS検証には時間がかかるため、早期に開始する必要がある。P1コンポーネントの前提条件。

**Independent Test**: ACMスタックをデプロイ後、以下を確認:
- ACM証明書が`api.loanpedia.jp`で発行済み（Status: Issued）
- DNS検証が完了している
- Route53に`api.loanpedia.jp`のAレコードが存在（ターゲットはALBのDNS名）

**Acceptance Scenarios**:

1. **Given** Route53ホストゾーン`loanpedia.jp`が存在、**When** ACMスタックをデプロイ、**Then** `api.loanpedia.jp`のACM証明書がap-northeast-1リージョンで発行リクエストされる
2. **Given** ACM証明書発行リクエスト済み、**When** DNS検証用CNAMEレコードがRoute53に自動追加、**Then** 証明書のステータスが"Issued"になる
3. **Given** ALBが作成済み、**When** Route53に`api.loanpedia.jp`のAliasレコードを追加、**Then** レコードのターゲットがALBのDNS名を指す

---

### User Story 3 - ECRリポジトリの作成 (Priority: P1)

Dockerイメージを保存するためのECRリポジトリ（`loanpedia-api`、`loanpedia-migration`）を作成し、イメージスキャンとAES-256暗号化を有効化する。

**Why this priority**: ECSタスク定義がECRイメージを参照するため、ECSデプロイの前提条件。イメージビルドとプッシュは別タスクだが、リポジトリ自体の存在が必要。

**Independent Test**: ECRリポジトリをデプロイ後、AWS Console/CLIで確認:
- `loanpedia-api`リポジトリが存在
- `loanpedia-migration`リポジトリが存在
- 両リポジトリでイメージスキャンが有効
- 両リポジトリでAES-256暗号化が有効

**Acceptance Scenarios**:

1. **Given** AWSアカウントにECRリポジトリが未作成、**When** BackendStackをデプロイ、**Then** `loanpedia-api`と`loanpedia-migration`の2つのリポジトリが作成される
2. **Given** ECRリポジトリが作成済み、**When** リポジトリ設定を確認、**Then** イメージスキャンオンプッシュが有効化されている
3. **Given** ECRリポジトリが作成済み、**When** 暗号化設定を確認、**Then** AES-256暗号化が有効化されている

---

### User Story 4 - RDS MySQL データベースの構築 (Priority: P2)

MySQL 8.0データベースインスタンス（db.t3.micro、シングルAZ）をアイソレートサブネットに配置し、Secrets Managerで認証情報を管理する。

**Why this priority**: アプリケーションの永続化層として必須だが、VPC/ECRが完了していれば独立してテスト可能。ECSサービス起動前に存在する必要があるが、並行作業可能。

**Independent Test**: RDSインスタンスをデプロイ後、以下を確認:
- RDSインスタンスが"Available"ステータス
- エンドポイントがアイソレートサブネット（AZ-a）に配置
- Secrets Managerにシークレット`loanpedia/rds/credentials`が存在
- パラメータグループで文字セットがutf8mb4、照合順序がutf8mb4_unicode_ci
- バックアップ保持期間が7日間

**Acceptance Scenarios**:

1. **Given** マルチAZ VPCが構築済み、**When** RDSインスタンスをデプロイ、**Then** インスタンスがアイソレートサブネット（ap-northeast-1a: 10.16.64.0/20）に作成される
2. **Given** RDSインスタンス作成中、**When** Secrets Managerを確認、**Then** `loanpedia/rds/credentials`シークレットが自動生成され、username/password/host/portが含まれる
3. **Given** RDSインスタンスが稼働中、**When** パラメータグループを確認、**Then** `character_set_server=utf8mb4`、`collation_server=utf8mb4_unicode_ci`が設定されている
4. **Given** RDSインスタンスが稼働中、**When** バックアップ設定を確認、**Then** 保持期間7日間、バックアップウィンドウが深夜2-3時（JST）に設定されている
5. **Given** RDSセキュリティグループが設定済み、**When** インバウンドルールを確認、**Then** ECS SGからのポート3306のみ許可されている

---

### User Story 5 - Cognito User Poolの構成 (Priority: P2)

ユーザー認証基盤としてCognito User Poolを作成し、emailベースのサインイン、EMAIL_OTP方式のMFA、アプリクライアントを設定する。

**Why this priority**: 認証は重要だが、インフラ検証段階では認証なしでAPIをテスト可能。アプリケーションコード実装時に必要になるため、P2。

**Independent Test**: Cognitoスタックをデプロイ後、以下を確認:
- User Poolが作成され、ユーザー名属性がemail
- MFAがREQUIRED、方式がEMAIL_OTP
- アプリクライアントが存在し、クライアントシークレットあり
- Secrets Managerに`loanpedia/cognito/client-secret`が保存されている

**Acceptance Scenarios**:

1. **Given** AWSアカウントにCognito User Poolが未作成、**When** BackendStackをデプロイ、**Then** User Poolが作成され、ユーザー名属性がemailに設定される
2. **Given** User Poolが作成済み、**When** MFA設定を確認、**Then** MFAモードがREQUIRED、方式がEMAIL_OTPに設定されている
3. **Given** User Poolが作成済み、**When** アプリクライアントを確認、**Then** クライアントシークレット付きのクライアントが存在し、認証フローがUSER_PASSWORD_AUTH、REFRESH_TOKEN_AUTH、USER_SRP_AUTHを含む
4. **Given** アプリクライアントが作成済み、**When** トークン有効期限を確認、**Then** アクセス/IDトークンが1時間、リフレッシュトークンが30日に設定されている
5. **Given** アプリクライアント作成済み、**When** Secrets Managerを確認、**Then** `loanpedia/cognito/client-secret`シークレットにクライアントシークレットが保存されている

---

### User Story 6 - ALB（Application Load Balancer）の構築 (Priority: P2)

internet-facingなALBを2AZ（パブリックサブネット）に配置し、HTTP→HTTPSリダイレクトとHTTPSリスナーを設定する。CloudFrontのIPレンジのみからのアクセスを許可する。

**Why this priority**: ECSサービスへのルーティングに必須だが、ECSタスク定義とターゲットグループの統合が必要なため、RDS/Cognitoと並行作業可能。

**Independent Test**: ALBをデプロイ後、以下を確認:
- ALBが2AZ（パブリックサブネット: 1a, 1c）に配置
- HTTP:80リスナーがHTTPS:443にリダイレクト
- HTTPS:443リスナーがACM証明書を使用
- ターゲットグループが作成され、タイプがIP、ポート80、ヘルスチェックパス`/health`
- セキュリティグループがCloudFront IPレンジのみ許可

**Acceptance Scenarios**:

1. **Given** マルチAZ VPCとACM証明書が準備済み、**When** ALBをデプロイ、**Then** internet-facing ALBが2AZ（パブリックサブネット: 10.16.0.0/20, 10.16.16.0/20）に作成される
2. **Given** ALBが作成済み、**When** HTTP:80でアクセス、**Then** HTTPS:443にリダイレクトされる
3. **Given** ALBが作成済み、**When** HTTPS:443リスナーを確認、**Then** `api.loanpedia.jp`のACM証明書が関連付けられている
4. **Given** ターゲットグループが作成済み、**When** 設定を確認、**Then** ターゲットタイプがIP、プロトコルHTTP、ポート80、ヘルスチェック（パス`/health`、間隔30秒、タイムアウト5秒、しきい値2回）が設定されている
5. **Given** ALBセキュリティグループが設定済み、**When** インバウンドルールを確認、**Then** CloudFrontマネージドプレフィックスリストからのポート443のみ許可されている

---

### User Story 7 - ECS Fargate クラスターとタスク定義の作成 (Priority: P2)

ECSクラスター`loanpedia-cluster`を作成し、Web API用タスク定義（CPU 512、メモリ1024 MB）とマイグレーション用タスク定義（CPU 256、メモリ512 MB）を定義する。

**Why this priority**: ECSサービス起動の前提条件だが、RDS/Cognito/ALBが揃っていれば独立してテスト可能。タスク定義はデプロイ可能だが、実行には後続のサービス設定が必要。

**Independent Test**: ECSクラスターとタスク定義をデプロイ後、以下を確認:
- クラスター`loanpedia-cluster`が存在（Container Insights無効）
- Web APIタスク定義が登録され、CPU 512、メモリ1024 MB、コンテナポート80
- マイグレーションタスク定義が登録され、CPU 256、メモリ512 MB
- 両タスク定義のログ設定がCloudWatch Logs（`/ecs/loanpedia-api`、`/ecs/loanpedia-migration`）
- タスク実行ロールがECR/CloudWatch/Secrets Manager権限を持つ

**Acceptance Scenarios**:

1. **Given** ECRリポジトリが作成済み、**When** ECSクラスターをデプロイ、**Then** `loanpedia-cluster`が作成され、Container Insightsが無効化されている
2. **Given** ECSクラスターが存在、**When** Web APIタスク定義を登録、**Then** CPU 512（0.5 vCPU）、メモリ1024 MB、コンテナポート80が設定される
3. **Given** ECSクラスターが存在、**When** マイグレーションタスク定義を登録、**Then** CPU 256（0.25 vCPU）、メモリ512 MBが設定される
4. **Given** タスク定義が登録済み、**When** ログ設定を確認、**Then** Web APIが`/ecs/loanpedia-api`、マイグレーションが`/ecs/loanpedia-migration`にログを送信する設定になっている
5. **Given** タスク定義が登録済み、**When** IAMタスク実行ロールを確認、**Then** ECRイメージプル、CloudWatch Logs書き込み、Secrets Manager参照の権限が付与されている

---

### User Story 8 - ECS Fargate Web APIサービスの起動 (Priority: P3)

Web APIタスクをプライベートサブネット（AZ-a）にデプロイし、ALBターゲットグループに統合する。タスク数は初期1、ECS SGでALB→80、RDS→3306、外部API→443を許可する。

**Why this priority**: すべてのP1/P2コンポーネントが揃って初めてエンドツーエンドの動作確認が可能。MVP的な価値提供の最終ステップ。

**Independent Test**: ECSサービスをデプロイ後、以下を確認:
- Web APIタスクが1個実行中（プライベートサブネット: ap-northeast-1a）
- タスクがALBターゲットグループに登録され、ヘルスチェックが"Healthy"
- ECS SGのインバウンドでALB SG→80、アウトバウンドでRDS SG→3306、0.0.0.0/0→443が許可
- CloudWatch Logsに`/ecs/loanpedia-api`のログストリームが出力されている

**Acceptance Scenarios**:

1. **Given** ALB、RDS、Cognitoが準備済み、**When** ECS Web APIサービスをデプロイ、**Then** タスクが1個、プライベートサブネット（ap-northeast-1a: 10.16.32.0/20）で起動する
2. **Given** ECSタスクが起動中、**When** ALBターゲットグループを確認、**Then** タスクのIPアドレスが登録され、ヘルスチェックステータスが"Healthy"になる
3. **Given** ECSセキュリティグループが設定済み、**When** インバウンドルールを確認、**Then** ALB SGからのポート80のみ許可されている
4. **Given** ECSセキュリティグループが設定済み、**When** アウトバウンドルールを確認、**Then** RDS SGへのポート3306と0.0.0.0/0へのポート443（NAT Gateway経由、Cognito/外部API用）が許可されている
5. **Given** ECSタスクが稼働中、**When** CloudWatch Logsを確認、**Then** `/ecs/loanpedia-api`ロググループにタスクのログが出力されている

---

### User Story 9 - CloudFront `/api/*` ビヘイビアの統合 (Priority: P3)

既存のCloudFrontディストリビューション（us-east-1）に`/api/*`パスパターンのビヘイビアを追加し、`api.loanpedia.jp`（ALB）をオリジンとして設定する。キャッシュ無効、全ヘッダー/Cookie転送。

**Why this priority**: エンドユーザーからのAPIアクセスを実現する最終統合ステップ。ALBに直接アクセスすることで動作確認は可能なため、P3。

**Independent Test**: CloudFrontディストリビューションを更新後、以下を確認:
- `/api/*`ビヘイビアが存在
- オリジンが`api.loanpedia.jp`（ALB）
- キャッシュポリシーがCACHING_DISABLED
- オリジンリクエストポリシーがALL_VIEWER
- 許可メソッドがALLOW_ALL
- `https://loanpedia.jp/api/health`でヘルスチェックが成功

**Acceptance Scenarios**:

1. **Given** 既存CloudFrontディストリビューション（S3オリジン）が存在、**When** `/api/*`ビヘイビアを追加、**Then** オリジンが`api.loanpedia.jp`（ALB）、オリジンプロトコルがHTTPS_ONLYになる
2. **Given** `/api/*`ビヘイビアが追加済み、**When** キャッシュ設定を確認、**Then** キャッシュポリシーがCACHING_DISABLED、オリジンリクエストポリシーがALL_VIEWER（全ヘッダー、Cookie、クエリ転送）になっている
3. **Given** `/api/*`ビヘイビアが追加済み、**When** 許可メソッドを確認、**Then** ALLOW_ALL（GET、POST、PUT、DELETE、PATCH、OPTIONS、HEAD）が設定されている
4. **Given** CloudFrontディストリビューションが更新済み、**When** `https://loanpedia.jp/api/health`にアクセス、**Then** ALB経由でECS Web APIのヘルスチェックが成功する

---

### User Story 10 - マイグレーションタスクの実行準備 (Priority: P3)

マイグレーション用ECSタスク定義をGitHub Actionsから`aws ecs run-task`で実行できるように準備する。タスクはプライベートサブネット（AZ-a）で実行され、RDSに接続してマイグレーションを実行する。

**Why this priority**: アプリケーションデプロイメントフローの一部だが、インフラ検証には不要。実際のマイグレーション実行は別タスク（GitHub Actions実装）。

**Independent Test**: マイグレーションタスク定義を登録後、以下を確認:
- `aws ecs run-task`コマンドで手動実行可能
- タスクがプライベートサブネット（ap-northeast-1a）で起動
- タスクがRDS SGに接続可能（セキュリティグループルール）
- CloudWatch Logsに`/ecs/loanpedia-migration`のログストリームが出力される

**Acceptance Scenarios**:

1. **Given** マイグレーションタスク定義が登録済み、**When** `aws ecs run-task`を実行、**Then** タスクがプライベートサブネット（ap-northeast-1a: 10.16.32.0/20）で起動する
2. **Given** マイグレーションタスクが起動中、**When** セキュリティグループを確認、**Then** API Serviceと同じECS SGを使用し、RDS SGへのポート3306接続が許可されている
3. **Given** マイグレーションタスクが実行完了、**When** CloudWatch Logsを確認、**Then** `/ecs/loanpedia-migration`ロググループにマイグレーションログが出力されている

---

### Edge Cases

- **ALB起動時にターゲットグループにHealthyなターゲットが存在しない場合**: ECSサービスが起動していない、またはヘルスチェックが失敗している。CloudWatch Logsでタスクエラーを確認し、ヘルスチェックエンドポイント`/health`が正しく実装されているか検証する。
- **RDS接続が失敗する場合**: ECS SGからRDS SGへのポート3306インバウンドルールが正しく設定されているか確認。Secrets Managerの認証情報（username、password、host、port）が正しいか検証。
- **CloudFrontから`/api/*`にアクセスできない場合**: ALB SGのインバウンドルールがCloudFront IPレンジ（マネージドプレフィックスリスト）を許可しているか確認。Route53の`api.loanpedia.jp`レコードがALBを正しく指しているか検証。
- **Cognitoでユーザー登録時にメールが届かない場合**: Cognitoの標準メール送信は50通/日制限があり、開発環境ではテストユーザー数に注意。本番環境ではSES統合を検討する必要がある。
- **NAT Gateway経由の通信が失敗する場合**: AZ-cのプライベートサブネットのルートテーブルがAZ-aのNAT Gatewayを正しく参照しているか確認。NAT GatewayのElastic IPが割り当てられているか検証。
- **ACM証明書のDNS検証が完了しない場合**: Route53ホストゾーンに検証用CNAMEレコードが自動追加されているか確認。ドメインのネームサーバーがRoute53のNSレコードを正しく参照しているか検証。
- **ECSタスクがECRからイメージをプルできない場合**: タスク実行ロールにECR権限（`ecr:GetAuthorizationToken`、`ecr:BatchCheckLayerAvailability`、`ecr:GetDownloadUrlForLayer`、`ecr:BatchGetImage`）が付与されているか確認。
- **マルチAZ VPC更新時に既存リソースが影響を受ける場合**: VPCスタック更新はサブネット追加のみで既存サブネットには影響しないが、CloudFormation変更セットで事前に変更内容を確認する。
- **RDSサブネットグループが2AZ要件を満たさない場合**: サブネットグループに最低2つのAZ（ap-northeast-1a、1c）のアイソレートサブネットが含まれているか確認。RDSインスタンス自体はシングルAZ（1a）だが、サブネットグループは2AZ必須。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: VPCスタックは既存のシングルAZ構成（ap-northeast-1a）からマルチAZ構成（ap-northeast-1a、ap-northeast-1c）に拡張されなければならない
- **FR-002**: パブリックサブネットはAZ-a（10.16.0.0/20）とAZ-c（10.16.16.0/20）に作成されなければならない
- **FR-003**: プライベートサブネットはAZ-a（10.16.32.0/20）とAZ-c（10.16.48.0/20）に作成されなければならない
- **FR-004**: アイソレートサブネットはAZ-a（10.16.64.0/20）とAZ-c（10.16.80.0/20）に作成されなければならない
- **FR-005**: NAT GatewayはAZ-aのパブリックサブネットにのみ配置され、AZ-cのプライベートサブネットはAZ-aのNAT Gatewayを使用しなければならない
- **FR-006**: ACM証明書は`api.loanpedia.jp`ドメインでap-northeast-1リージョンに発行され、DNS検証方式を使用しなければならない
- **FR-007**: Route53に`api.loanpedia.jp`のAレコード（Alias）が作成され、ALBのDNS名をターゲットとしなければならない
- **FR-008**: ALBはinternet-facingスキームで2AZ（パブリックサブネット: ap-northeast-1a、1c）に配置されなければならない
- **FR-009**: ALBのHTTP:80リスナーはHTTPS:443にリダイレクトしなければならない
- **FR-010**: ALBのHTTPS:443リスナーは`api.loanpedia.jp`のACM証明書を使用し、ターゲットグループにルーティングしなければならない
- **FR-011**: ALBのターゲットグループはターゲットタイプIP、プロトコルHTTP、ポート80で作成され、ヘルスチェックパス`/health`、間隔30秒、タイムアウト5秒、しきい値2回が設定されなければならない
- **FR-012**: ALBのセキュリティグループはCloudFrontのIPレンジ（マネージドプレフィックスリスト）からのポート443インバウンドのみを許可し、ECS SGへのポート80アウトバウンドを許可しなければならない
- **FR-013**: ECRリポジトリ`loanpedia-api`と`loanpedia-migration`が作成され、イメージスキャンオンプッシュとAES-256暗号化が有効化されなければならない
- **FR-014**: ECSクラスター`loanpedia-cluster`が作成され、Container Insightsは無効化されなければならない
- **FR-015**: Web API用ECSタスク定義はCPU 512（0.5 vCPU）、メモリ1024 MB、コンテナポート80で作成され、CloudWatch Logs（`/ecs/loanpedia-api`）に送信されなければならない
- **FR-016**: マイグレーション用ECSタスク定義はCPU 256（0.25 vCPU）、メモリ512 MBで作成され、CloudWatch Logs（`/ecs/loanpedia-migration`）に送信されなければならない
- **FR-017**: ECS Web APIサービスはタスク数1でプライベートサブネット（ap-northeast-1a）に配置され、ALBターゲットグループに統合されなければならない
- **FR-018**: ECSセキュリティグループはALB SGからのポート80インバウンドを許可し、RDS SGへのポート3306と0.0.0.0/0へのポート443（NAT Gateway経由）のアウトバウンドを許可しなければならない
- **FR-019**: RDS MySQLインスタンスはエンジンMySQL 8.0、インスタンスタイプdb.t3.micro、ストレージgp3 20 GB、シングルAZ（ap-northeast-1a）でアイソレートサブネット（10.16.64.0/20）に配置されなければならない
- **FR-020**: RDSサブネットグループは2AZ（ap-northeast-1a、1c）のアイソレートサブネットで構成されなければならない
- **FR-021**: RDSパラメータグループは`character_set_server=utf8mb4`、`collation_server=utf8mb4_unicode_ci`が設定されなければならない
- **FR-022**: RDSバックアップは保持期間7日間、バックアップウィンドウ深夜2-3時（JST）で設定され、削除保護は無効化されなければならない
- **FR-023**: RDS認証情報はSecrets Manager（`loanpedia/rds/credentials`）で自動生成され、RDS統合が有効化されなければならない
- **FR-024**: RDSセキュリティグループはECS SGからのポート3306インバウンドのみを許可し、アウトバウンドは許可しないものとする
- **FR-025**: Cognito User Poolはユーザー名属性email、必須属性email、MFAモードREQUIRED、MFA方式EMAIL_OTPで作成されなければならない
- **FR-026**: Cognitoのパスワードポリシーはデフォルト（大小英数記号8文字以上）で、メール検証が必須化されなければならない
- **FR-027**: Cognitoアプリクライアントはクライアントシークレット必須、認証フローUSER_PASSWORD_AUTH/REFRESH_TOKEN_AUTH/USER_SRP_AUTH、トークン有効期限（アクセス/ID: 1時間、リフレッシュ: 30日）で作成されなければならない
- **FR-028**: CognitoアプリクライアントシークレットはSecrets Manager（`loanpedia/cognito/client-secret`）に保存されなければならない
- **FR-029**: ECSタスク実行ロールはECRイメージプル、CloudWatch Logs書き込み、Secrets Manager参照の権限を持たなければならない
- **FR-030**: ECSタスクロールはCognito権限（`cognito-idp:*`など）を持たなければならない（アプリケーションからCognito SDKを呼び出すため）
- **FR-031**: CloudWatch Logsロググループ`/ecs/loanpedia-api`と`/ecs/loanpedia-migration`は保持期間7日間で作成されなければならない
- **FR-032**: CloudFrontディストリビューション（既存、us-east-1）に`/api/*`パスパターンのビヘイビアが追加され、オリジンは`api.loanpedia.jp`（ALB）、オリジンプロトコルHTTPS_ONLY、キャッシュCACHING_DISABLED、オリジンリクエストポリシーALL_VIEWER、許可メソッドALLOW_ALL、ビューワープロトコルREDIRECT_TO_HTTPSで設定されなければならない

### Key Entities *(include if feature involves data)*

- **VPCネットワーク**: 既存のシングルAZ構成をマルチAZ（ap-northeast-1a、1c）に拡張。パブリック/プライベート/アイソレートサブネットを各AZに配置。NAT GatewayはAZ-aのみ。
- **ACM証明書（ALB用）**: `api.loanpedia.jp`ドメイン、ap-northeast-1リージョン、DNS検証方式。ALBのHTTPSリスナーで使用。
- **Route53レコード**: `api.loanpedia.jp`のAレコード（Alias）、ターゲットはALBのDNS名。
- **ALB（Application Load Balancer）**: internet-facing、2AZ（パブリックサブネット）配置、HTTP→HTTPSリダイレクト、HTTPS→ターゲットグループ、CloudFront IPレンジのみ許可。
- **ターゲットグループ**: タイプIP、プロトコルHTTP、ポート80、ヘルスチェックパス`/health`。ECS Fargateタスク（API Service）が登録される。
- **ECRリポジトリ**: `loanpedia-api`（Web API用）、`loanpedia-migration`（DBマイグレーション用）。イメージスキャンとAES-256暗号化有効。
- **ECSクラスター**: `loanpedia-cluster`、Container Insights無効。
- **ECSタスク定義（Web API）**: CPU 512、メモリ1024 MB、コンテナポート80、プライベートサブネット配置、CloudWatch Logs送信、Secrets Manager参照。
- **ECSタスク定義（マイグレーション）**: CPU 256、メモリ512 MB、プライベートサブネット配置、CloudWatch Logs送信、GitHub Actionsから実行。
- **ECS Web APIサービス**: タスク数1、プライベートサブネット（ap-northeast-1a）配置、ALBターゲットグループ統合、ECS SG適用。
- **RDS MySQL**: エンジンMySQL 8.0、インスタンスタイプdb.t3.micro、ストレージgp3 20 GB、シングルAZ（ap-northeast-1a）、アイソレートサブネット配置、パラメータグループ（utf8mb4）、バックアップ7日間、Secrets Manager統合。
- **RDSサブネットグループ**: 2AZ（ap-northeast-1a、1c）のアイソレートサブネット構成。
- **Cognito User Pool**: ユーザー名属性email、MFA必須（EMAIL_OTP）、メール検証必須、パスワードポリシーデフォルト。
- **Cognitoアプリクライアント**: クライアントシークレット必須、認証フローUSER_PASSWORD_AUTH/REFRESH_TOKEN_AUTH/USER_SRP_AUTH、トークン有効期限（アクセス/ID: 1時間、リフレッシュ: 30日）、シークレットはSecrets Manager保存。
- **Secrets Manager（RDS）**: `loanpedia/rds/credentials`、RDS認証情報自動生成、ECSタスクから参照。
- **Secrets Manager（Cognito）**: `loanpedia/cognito/client-secret`、Cognitoアプリクライアントシークレット保存、ECSタスクから参照。
- **CloudWatch Logs**: `/ecs/loanpedia-api`（保持期間7日間）、`/ecs/loanpedia-migration`（保持期間7日間）。
- **セキュリティグループ（ALB）**: インバウンド: CloudFront IPレンジ→443、アウトバウンド: ECS SG→80。
- **セキュリティグループ（ECS）**: インバウンド: ALB SG→80、アウトバウンド: RDS SG→3306、0.0.0.0/0→443。
- **セキュリティグループ（RDS）**: インバウンド: ECS SG→3306、アウトバウンド: なし。
- **IAMタスク実行ロール**: ECRイメージプル、CloudWatch Logs書き込み、Secrets Manager参照権限。
- **IAMタスクロール**: Cognito権限（`cognito-idp:*`など）、その他AWSサービスアクセス権限。
- **CloudFrontビヘイビア（`/api/*`）**: オリジン`api.loanpedia.jp`（ALB）、オリジンプロトコルHTTPS_ONLY、キャッシュCACHING_DISABLED、オリジンリクエストポリシーALL_VIEWER、許可メソッドALLOW_ALL。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: VPCスタック更新後、2AZ（ap-northeast-1a、1c）のパブリック/プライベート/アイソレートサブネットがAWS Consoleで確認でき、各サブネットのCIDRブロックが仕様通り（10.16.x.x/20）である
- **SC-002**: ACM証明書が発行完了（Status: Issued）し、Route53で`api.loanpedia.jp`のDNS検証CNAMEレコードが自動追加され、証明書発行までの時間が30分以内である
- **SC-003**: ALBが2AZ（パブリックサブネット）に配置され、HTTP:80アクセスがHTTPS:443にリダイレクトされ、HTTPS:443でACM証明書を使用してターゲットグループにルーティングする
- **SC-004**: ECRリポジトリ`loanpedia-api`と`loanpedia-migration`が作成され、イメージスキャンとAES-256暗号化が有効化されている
- **SC-005**: RDS MySQLインスタンスが"Available"ステータスになり、アイソレートサブネット（ap-northeast-1a）に配置され、Secrets Managerに認証情報が自動生成されている
- **SC-006**: Cognito User Poolが作成され、ユーザー名属性がemail、MFAがREQUIRED（EMAIL_OTP）、アプリクライアントがクライアントシークレット付きで存在し、Secrets Managerにシークレットが保存されている
- **SC-007**: ECSクラスター`loanpedia-cluster`が作成され、Web API用タスク定義（CPU 512、メモリ1024 MB）とマイグレーション用タスク定義（CPU 256、メモリ512 MB）が登録されている
- **SC-008**: ECS Web APIサービスがタスク数1でプライベートサブネット（ap-northeast-1a）で起動し、ALBターゲットグループにHealthyステータスで登録され、ヘルスチェック`/health`が成功する
- **SC-009**: CloudFrontディストリビューションに`/api/*`ビヘイビアが追加され、`https://loanpedia.jp/api/health`にアクセスするとALB経由でECS Web APIのヘルスチェックが成功する
- **SC-010**: セキュリティグループ構成が正しく設定され、ALB SGがCloudFront IPレンジのみ許可、ECS SGがALB SG→80、RDS SG→3306、0.0.0.0/0→443を許可、RDS SGがECS SG→3306のみ許可している
- **SC-011**: CloudWatch Logsに`/ecs/loanpedia-api`と`/ecs/loanpedia-migration`のロググループが作成され、保持期間7日間が設定されている
- **SC-012**: マイグレーションタスクを`aws ecs run-task`で手動実行でき、プライベートサブネット（ap-northeast-1a）で起動し、CloudWatch Logsに`/ecs/loanpedia-migration`のログが出力される
- **SC-013**: 全スタック（VPC、ACM、Backend、Frontend更新）のデプロイが完了し、エラーなくCloudFormationでスタックステータスが"CREATE_COMPLETE"または"UPDATE_COMPLETE"になる
- **SC-014**: インフラ全体のデプロイ時間が初回60分以内、更新が30分以内に完了する（ACM DNS検証時間を除く）
- **SC-015**: RDSバックアップが7日間保持され、バックアップウィンドウが深夜2-3時（JST）に設定されており、バックアップから復元テストが成功する
