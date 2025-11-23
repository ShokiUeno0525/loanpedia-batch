# Research: バックエンドインフラストラクチャ

**Date**: 2025-11-23
**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Phase 0: 技術調査と意思決定

本ドキュメントは、バックエンドインフラストラクチャ実装における技術的な意思決定と調査結果をまとめる。

## 調査項目

### 1. VPCマルチAZ対応の設計パターン

**調査内容**: 既存シングルAZ VPCをマルチAZ構成に拡張する際のベストプラクティス

**Decision**: 既存サブネット（AZ-a）を維持し、AZ-cに新規サブネットを追加

**Rationale**:
- **破壊的変更の回避**: 既存サブネット（ap-northeast-1a）を削除せず、新規サブネット（ap-northeast-1c）を追加することで、既存リソース（将来的に追加される可能性があるリソース）への影響を最小化
- **段階的移行**: VPCスタック更新→Backend Stack作成の順序で、段階的にマルチAZ化を実現
- **コスト最適化**: NAT Gatewayは1AZのみ配置（AZ-a）。AZ-cのプライベートサブネットはAZ-aのNAT Gatewayを使用（ルートテーブル設定）

**Alternatives considered**:
- **完全再作成**: VPCを削除して新規マルチAZ VPCを作成 → ❌ 既存リソース（CloudFront、S3）への影響大、ダウンタイム発生
- **2つのNAT Gateway**: 各AZにNAT Gatewayを配置 → ❌ コスト倍増（月額約$32×2 = $64）、開発環境には過剰

**実装詳細**:
- パブリックサブネット: AZ-a（10.16.0.0/20）、AZ-c（10.16.16.0/20）
- プライベートサブネット: AZ-a（10.16.32.0/20）、AZ-c（10.16.48.0/20）
- アイソレートサブネット: AZ-a（10.16.64.0/20）、AZ-c（10.16.80.0/20）
- NAT Gateway: AZ-aのパブリックサブネットのみ
- ルートテーブル: AZ-cのプライベートサブネット → AZ-aのNAT Gateway

**参考資料**:
- [AWS VPC Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-best-practices.html)
- [AWS Multi-AZ Architecture Patterns](https://aws.amazon.com/architecture/well-architected/)

---

### 2. ALBとCloudFrontの統合パターン

**調査内容**: CloudFront（us-east-1）とALB（ap-northeast-1）の統合におけるセキュリティベストプラクティス

**Decision**: CloudFront Managed Prefix Listを使用してALB SGのインバウンドルールを制限

**Rationale**:
- **セキュリティ強化**: CloudFrontのIPレンジのみを許可することで、直接ALBへのアクセスを防止
- **自動更新**: Managed Prefix Listは AWS が管理するため、CloudFrontのIPレンジ変更時も自動的に反映
- **運用負荷削減**: 手動でIPレンジを更新する必要がなく、メンテナンスフリー

**Alternatives considered**:
- **カスタムヘッダー検証**: CloudFront→ALB間でカスタムヘッダー（X-Custom-Header）を送信し、ALBで検証 → ✅ 追加の保護層として実装可能だが、今回は Managed Prefix List のみで十分
- **AWS WAF**: ALBにWAFを適用してCloudFront以外をブロック → ❌ コスト増（月額$5 + リクエスト課金）、開発環境には過剰
- **VPC Endpoint**: CloudFront→ALB間でVPC Endpointを使用 → ❌ CloudFrontはVPC Endpointをサポートしていない

**実装詳細**:
- ALB SG インバウンド: `com.amazonaws.global.cloudfront.origin-facing`（Managed Prefix List）→ ポート443
- ALB SG アウトバウンド: ECS SG → ポート80
- HTTPS通信: CloudFront→ALB、HTTP通信: ALB→ECS（VPC内部）

**参考資料**:
- [CloudFront with ALB Best Practices](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/restrict-access-to-load-balancer.html)
- [AWS Managed Prefix Lists](https://docs.aws.amazon.com/vpc/latest/userguide/managed-prefix-lists.html)

---

### 3. ECS Fargateタスク定義のベストプラクティス

**調査内容**: Web APIタスクとマイグレーションタスクの設計パターン

**Decision**: 2つの独立したタスク定義を作成（Web API用、マイグレーション用）

**Rationale**:
- **責務の分離**: Web APIとマイグレーションは異なる目的を持ち、実行タイミングも異なる
- **リソース最適化**: Web APIはCPU 512/メモリ1024 MB、マイグレーションはCPU 256/メモリ512 MBと、必要なリソースを最適化
- **実行制御**: Web APIはECSサービスで常時実行、マイグレーションは`aws ecs run-task`で手動/GitHub Actionsから実行

**Alternatives considered**:
- **単一タスク定義**: Web APIとマイグレーションを1つのタスク定義にまとめる → ❌ 責務が混在、リソース割り当てが非効率
- **サイドカーコンテナ**: マイグレーションをWeb APIのサイドカーとして実行 → ❌ マイグレーションは1回限りの実行、常時起動は不要

**実装詳細**:

**Web APIタスク定義**:
- CPU: 512（0.5 vCPU）
- メモリ: 1024 MB
- コンテナポート: 80
- ログ: CloudWatch Logs（`/ecs/loanpedia-api`）
- 環境変数: Secrets Manager参照（RDS認証情報、Cognitoクライアントシークレット）
- タスクロール: Cognito権限（`cognito-idp:*`）
- 実行ロール: ECRイメージプル、CloudWatch Logs書き込み、Secrets Manager参照

**マイグレーションタスク定義**:
- CPU: 256（0.25 vCPU）
- メモリ: 512 MB
- ログ: CloudWatch Logs（`/ecs/loanpedia-migration`）
- 環境変数: Secrets Manager参照（RDS認証情報）
- セキュリティグループ: Web APIと共用（ECS SG）
- 実行: GitHub Actionsから`aws ecs run-task`

**参考資料**:
- [ECS Fargate Task Definition Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/task-definition.html)
- [ECS Fargate Sizing Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html)

---

### 4. RDS MySQLのパラメータグループ設定

**調査内容**: 日本語対応とLaravelアプリケーション向けのMySQL設定

**Decision**: カスタムパラメータグループで`utf8mb4`文字セット、`utf8mb4_unicode_ci`照合順序を設定

**Rationale**:
- **日本語対応**: `utf8mb4`は4バイトUnicode文字をサポート（絵文字、一部の漢字に必要）
- **Laravel互換性**: Laravel 10のデフォルト文字セットは`utf8mb4`、照合順序は`utf8mb4_unicode_ci`
- **データ品質**: 憲章III「データ品質の保証」に準拠。文字化けを防止し、データの正確性を保証

**Alternatives considered**:
- **utf8 (utf8mb3)**: MySQL 5.x のデフォルト文字セット → ❌ 3バイトUnicodeのみ、絵文字・一部漢字が使用不可
- **utf8mb4_general_ci**: より高速な照合順序 → ❌ 大文字小文字の区別が不正確、日本語ソートに問題

**実装詳細**:
```typescript
const parameterGroup = new rds.ParameterGroup(this, 'LoanpediaParamGroup', {
  engine: rds.DatabaseInstanceEngine.mysql({ version: rds.MysqlEngineVersion.VER_8_0 }),
  parameters: {
    character_set_server: 'utf8mb4',
    collation_server: 'utf8mb4_unicode_ci',
    character_set_client: 'utf8mb4',
    character_set_connection: 'utf8mb4',
    character_set_database: 'utf8mb4',
    character_set_results: 'utf8mb4',
  },
});
```

**参考資料**:
- [MySQL UTF8MB4 Best Practices](https://dev.mysql.com/doc/refman/8.0/en/charset-unicode-utf8mb4.html)
- [Laravel Database Configuration](https://laravel.com/docs/10.x/database#configuration)

---

### 5. Cognito User PoolのMFA設定

**調査内容**: ユーザー認証のセキュリティ強化（MFA）の実装パターン

**Decision**: EMAIL_OTP方式のMFA必須、メール検証必須

**Rationale**:
- **セキュリティ強化**: MFA必須によりパスワード漏洩時のリスクを軽減
- **コスト最適化**: SMS_MFAは送信ごとに課金（1通$0.00645）、EMAIL_OTPは無料
- **初期フェーズ適合**: 開発/MVP段階ではEMAIL_OTPで十分。本番環境でSMS_MFAやTOTP（Authenticator App）に移行可能
- **ユーザー体験**: メールアドレスをユーザー名として使用し、メール検証とMFAを統合

**Alternatives considered**:
- **SMS_MFA**: SMS経由でOTPを送信 → ❌ コスト高（1通$0.00645）、初期フェーズには過剰
- **TOTP (Authenticator App)**: Google Authenticatorなどのアプリを使用 → ⚠️ ユーザー体験が複雑、MVP後に検討
- **MFAオプショナル**: MFAを任意にする → ❌ セキュリティリスク高、憲章V（セキュリティ基本原則）に反する

**実装詳細**:
```typescript
const userPool = new cognito.UserPool(this, 'LoanpediaUserPool', {
  userPoolName: 'loanpedia-user-pool',
  signInAliases: { email: true },
  autoVerify: { email: true },
  mfa: cognito.Mfa.REQUIRED,
  mfaSecondFactor: {
    sms: false,
    otp: true, // EMAIL_OTP
  },
  passwordPolicy: {
    minLength: 8,
    requireLowercase: true,
    requireUppercase: true,
    requireDigits: true,
    requireSymbols: true,
  },
  accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
});
```

**Cognitoメール送信制限**:
- 標準: 50通/日（無料）
- SES統合: 50,000通/日（SES料金適用、1通$0.0001）
- **開発環境**: 標準メール送信で十分
- **本番環境**: SES統合を検討

**参考資料**:
- [Cognito MFA Best Practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html)
- [Cognito Pricing](https://aws.amazon.com/cognito/pricing/)

---

### 6. Secrets Managerの使用パターン

**調査内容**: RDS認証情報とCognitoクライアントシークレットの管理方法

**Decision**: Secrets Managerで機密情報を管理し、ECSタスクから参照

**Rationale**:
- **セキュリティベストプラクティス**: 憲章V（セキュリティ基本原則）に準拠。機密情報をリポジトリにコミットしない
- **自動ローテーション**: RDS認証情報の自動ローテーションをサポート（将来的に有効化可能）
- **ECS統合**: ECSタスク定義で`secrets`フィールドを使用してSecrets Managerから直接読み込み
- **監査**: CloudTrailによるSecrets Managerアクセスの監査ログ

**Alternatives considered**:
- **環境変数**: ECSタスク定義に直接環境変数として記述 → ❌ 平文で保存、セキュリティリスク高
- **Parameter Store**: Systems Manager Parameter Storeを使用 → ✅ 無料だが、RDS自動ローテーション非対応
- **.envファイル**: S3に.envファイルを保存してECSタスク起動時にダウンロード → ❌ 複雑、Secrets Managerの方がシンプル

**実装詳細**:

**シークレット1: RDS認証情報**
- シークレット名: `loanpedia/rds/credentials`
- 自動生成: RDS Constructで`DatabaseInstance.secret`を使用
- 内容: `{ username, password, host, port, dbname }`
- ECSタスク定義で参照:
  ```typescript
  environment: {
    DB_HOST: ecs.Secret.fromSecretsManager(rdsSecret, 'host'),
    DB_PORT: ecs.Secret.fromSecretsManager(rdsSecret, 'port'),
    DB_USERNAME: ecs.Secret.fromSecretsManager(rdsSecret, 'username'),
    DB_PASSWORD: ecs.Secret.fromSecretsManager(rdsSecret, 'password'),
  }
  ```

**シークレット2: Cognitoクライアントシークレット**
- シークレット名: `loanpedia/cognito/client-secret`
- 手動作成: Cognitoアプリクライアント作成後、シークレットを保存
- ECSタスク定義で参照:
  ```typescript
  environment: {
    COGNITO_CLIENT_SECRET: ecs.Secret.fromSecretsManager(cognitoSecret),
  }
  ```

**コスト**:
- Secrets Manager: $0.40/月/シークレット × 2 = $0.80/月
- API呼び出し: 最初の10,000回無料、以降$0.05/10,000回

**参考資料**:
- [Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [ECS Secrets Integration](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/specifying-sensitive-data-secrets.html)

---

### 7. CloudWatch Logsの保持期間設定

**調査内容**: ECSタスクログの保持期間と成本最適化

**Decision**: 7日間保持、手動でエクスポート可能

**Rationale**:
- **コスト最適化**: 保持期間7日間により、ログストレージコストを削減（$0.03/GB/月）
- **トラブルシューティング**: 7日間あれば、ほとんどの問題を調査可能
- **長期保存**: 必要に応じてS3にエクスポート（手動、将来的に自動化可能）
- **憲章IV（AI処理の透明性）**: ログ出力による処理のトレーサビリティ確保

**Alternatives considered**:
- **30日間保持**: より長期のログ保存 → ❌ コスト約4倍、開発環境には過剰
- **無期限保持**: ログを永続的に保存 → ❌ コスト増、ログ肥大化
- **1日間保持**: 最小限の保持期間 → ❌ トラブルシューティングに不十分

**実装詳細**:
```typescript
const apiLogGroup = new logs.LogGroup(this, 'ApiLogGroup', {
  logGroupName: '/ecs/loanpedia-api',
  retention: logs.RetentionDays.ONE_WEEK,
  removalPolicy: cdk.RemovalPolicy.DESTROY, // 開発環境のみ
});

const migrationLogGroup = new logs.LogGroup(this, 'MigrationLogGroup', {
  logGroupName: '/ecs/loanpedia-migration',
  retention: logs.RetentionDays.ONE_WEEK,
  removalPolicy: cdk.RemovalPolicy.DESTROY,
});
```

**コスト試算**:
- ログ取り込み: $0.50/GB
- ログストレージ: $0.03/GB/月（7日間）
- 想定ログ量: 1GB/月（初期）
- 月額コスト: 約$0.50 + $0.03 = $0.53/月

**参考資料**:
- [CloudWatch Logs Pricing](https://aws.amazon.com/cloudwatch/pricing/)
- [CloudWatch Logs Retention Best Practices](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html)

---

### 8. ACM証明書のDNS検証パターン

**調査内容**: ALB用ACM証明書（ap-northeast-1）の発行と検証

**Decision**: DNS検証、Route53自動検証レコード追加

**Rationale**:
- **自動化**: CDKで`DnsValidatedCertificate`を使用することで、Route53に検証用CNAMEレコードを自動追加
- **検証時間**: DNS検証は通常5-30分で完了（メール検証より高速）
- **本番運用**: 証明書の自動更新に対応（DNS検証レコードが存在する限り自動更新）

**Alternatives considered**:
- **メール検証**: ドメイン所有者のメールアドレスに検証メールを送信 → ❌ 手動操作が必要、自動化不可
- **HTTP検証**: `.well-known/acme-challenge/`にファイルを配置 → ❌ ALB起動前に証明書が必要、循環依存

**実装詳細**:
```typescript
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';

const albCertificate = new acm.DnsValidatedCertificate(this, 'AlbCertificate', {
  domainName: 'api.loanpedia.jp',
  hostedZone: hostedZone, // Route53 Stack から参照
  region: 'ap-northeast-1',
  validation: acm.CertificateValidation.fromDns(hostedZone),
});
```

**検証プロセス**:
1. ACM証明書リクエスト作成
2. Route53に検証用CNAMEレコード自動追加（`_xxxxx.api.loanpedia.jp`）
3. ACMが検証レコードを確認（5-30分）
4. 証明書ステータスが"Issued"に変更

**参考資料**:
- [ACM DNS Validation](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html)
- [CDK DnsValidatedCertificate](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_certificatemanager.DnsValidatedCertificate.html)

---

### 9. ALBターゲットグループのヘルスチェック設定

**調査内容**: ECS Fargateタスクのヘルスチェック最適化

**Decision**: `/health`エンドポイント、間隔30秒、タイムアウト5秒、しきい値2回

**Rationale**:
- **バランス**: 頻繁すぎるヘルスチェックはタスクに負荷をかけ、間隔が長すぎると障害検知が遅れる
- **AWS推奨**: 30秒間隔は一般的なWebアプリケーションの標準設定
- **しきい値2回**: 1回の失敗では除外せず、2回連続失敗で除外（一時的なネットワークエラーに対応）

**Alternatives considered**:
- **間隔10秒**: より頻繁なヘルスチェック → ❌ タスクへの負荷増、コスト増（ヘルスチェックリクエスト課金）
- **しきい値3回**: より保守的な設定 → ❌ 障害検知が遅れる（最大90秒）

**実装詳細**:
```typescript
const targetGroup = new elbv2.ApplicationTargetGroup(this, 'ApiTargetGroup', {
  vpc,
  port: 80,
  protocol: elbv2.ApplicationProtocol.HTTP,
  targetType: elbv2.TargetType.IP,
  healthCheck: {
    path: '/health',
    interval: cdk.Duration.seconds(30),
    timeout: cdk.Duration.seconds(5),
    healthyThresholdCount: 2,
    unhealthyThresholdCount: 2,
  },
});
```

**ヘルスチェックエンドポイント要件**（アプリケーション側で実装）:
- パス: `/health`
- レスポンス: HTTP 200
- レスポンスボディ: `{"status": "ok"}`（推奨、必須ではない）
- 処理時間: <5秒（タイムアウト内）

**参考資料**:
- [ALB Health Checks Best Practices](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html)

---

### 10. ECS Fargateネットワークモード

**調査内容**: ECS Fargateのネットワークモード選択

**Decision**: `awsvpc`ネットワークモード（Fargate必須）

**Rationale**:
- **Fargate要件**: Fargateは`awsvpc`ネットワークモードのみサポート
- **ENI割り当て**: 各タスクに独立したElastic Network Interface（ENI）を割り当て
- **セキュリティグループ**: タスクレベルでセキュリティグループを適用可能

**実装詳細**:
- タスク定義: `networkMode: ecs.NetworkMode.AWS_VPC`（デフォルト、Fargate必須）
- サービス: プライベートサブネット（ap-northeast-1a）に配置
- セキュリティグループ: ECS SG（ALB SG→80、RDS SG→3306、0.0.0.0/0→443）

**参考資料**:
- [ECS Network Modes](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-networking.html)

---

## 調査結果サマリー

### 技術スタック確定

| コンポーネント | 技術選定 | 理由 |
|-------------|---------|------|
| Infrastructure as Code | AWS CDK (TypeScript 5.6.3) | 型安全、既存インフラとの統合、チーム習熟 |
| VPCアーキテクチャ | マルチAZ（2AZ）、NAT Gateway 1個 | ALB要件（2AZ必須）、コスト最適化 |
| ALBセキュリティ | CloudFront Managed Prefix List | CloudFront IPレンジのみ許可、自動更新 |
| ECS実行環境 | Fargate、awsvpcネットワークモード | サーバーレス、ENI割り当て、タスクレベルSG |
| RDS文字セット | utf8mb4 + utf8mb4_unicode_ci | 日本語対応、Laravel互換性、データ品質保証 |
| Cognito MFA | EMAIL_OTP、MFA必須 | セキュリティ強化、コスト最適化、初期フェーズ適合 |
| 機密情報管理 | Secrets Manager | セキュリティベストプラクティス、ECS統合、自動ローテーション対応 |
| ログ保持 | CloudWatch Logs（7日間） | コスト最適化、トラブルシューティング可能期間 |
| ACM証明書検証 | DNS検証、Route53自動レコード追加 | 自動化、証明書自動更新対応 |
| ヘルスチェック | `/health`、30秒間隔、しきい値2回 | AWS推奨、負荷とレスポンスのバランス |

### 未解決事項

なし。全ての技術的意思決定が完了し、Phase 1設計フェーズに進む準備が整った。

### 次のステップ

**Phase 1: Design & Contracts**に進む。以下の成果物を作成:

1. **data-model.md**: RDSデータモデル定義（Laravel マイグレーション仕様）
2. **contracts/**: CloudFormation出力定義、スタック間の依存関係
3. **quickstart.md**: 開発者向けクイックスタートガイド

**Phase 1設計後の憲章再チェック**:
- セキュリティグループ構成の妥当性検証
- Secrets Managerによる機密情報管理の実装確認
- CloudWatch Logsの設定確認
