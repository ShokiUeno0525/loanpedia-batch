# Phase 0: 技術調査 - CloudFront フロントエンド配信基盤

**作成日**: 2025-11-18
**対象機能**: CloudFront + S3によるフロントエンド配信基盤

## 調査概要

本ドキュメントは、CloudFrontディストリビューション、S3バケット、WAFを使用したフロントエンド配信基盤の実装に必要な技術調査結果をまとめています。

## 既存インフラ構造の確認

### 既存のCDKスタック

プロジェクトには以下の既存スタックが存在します：

1. **GitHubOidcStack**: GitHub ActionsからのCI/CDデプロイ用OIDC認証
2. **Route53Stack**: loanpedia.jpドメインのパブリックホストゾーン
3. **AcmCertificateStack**: loanpedia.jpのACM証明書（us-east-1リージョン）

### 既存リソースの参照方法

- **Route53ホストゾーン**: `route53.HostedZone.fromLookup()` でドメイン名から検索
- **ACM証明書**: CloudFormation Export `LoanpediaCertificateArn` から参照可能

### ディレクトリ構造

```
infra/
├── bin/
│   └── loanpedia-app.ts          # CDKアプリケーションエントリーポイント
├── lib/
│   ├── github-oidc-stack.ts
│   ├── route53-stack.ts
│   └── acm-certificate-stack.ts
└── test/
```

## 技術決定事項

### 1. CloudFront OAC（Origin Access Control）の選択

**決定**: CloudFront OACを使用（OAIではなく）

**理由**:
- OAC（Origin Access Control）は、OAI（Origin Access Identity）の後継で、より新しく推奨される方法
- すべてのS3バケット設定（SSE-S3、SSE-KMS、DSSE-KMSなど）で動作
- より詳細なアクセス制御が可能
- AWS公式ドキュメントでOACが推奨されている

**実装方法**:
```typescript
const oac = new cloudfront.S3OriginAccessControl(this, 'OAC', {
  signing: cloudfront.Signing.SIGV4_ALWAYS,
});

// S3オリジンで使用
const origin = origins.S3BucketOrigin.withOriginAccessControl(bucket, {
  originAccessControl: oac,
});
```

**代替案**:
- OAI（Origin Access Identity）: 古い方式のため非推奨
- パブリックバケット: セキュリティ要件に反するため却下

### 2. WAFの構成

**決定**: AWS Managed RulesをベースにしたWAF WebACLを作成

**理由**:
- CloudFrontにはAWS WAFを直接関連付ける必要がある（WAFv2のみ対応）
- AWS Managed Rulesは一般的な脅威に対する基本的な保護を提供
- カスタムルールは後から追加可能で、段階的な実装が可能

**実装方法**:
```typescript
const webAcl = new wafv2.CfnWebACL(this, 'WebAcl', {
  scope: 'CLOUDFRONT', // CloudFront用はCLOUDFRONTスコープ必須
  defaultAction: { allow: {} },
  rules: [
    {
      name: 'AWSManagedRulesCommonRuleSet',
      priority: 1,
      statement: {
        managedRuleGroupStatement: {
          vendorName: 'AWS',
          name: 'AWSManagedRulesCommonRuleSet',
        },
      },
      overrideAction: { none: {} },
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: 'AWSManagedRulesCommonRuleSetMetric',
      },
    },
  ],
  visibilityConfig: {
    sampledRequestsEnabled: true,
    cloudWatchMetricsEnabled: true,
    metricName: 'WebAclMetric',
  },
});
```

**注意事項**:
- WAF WebACLはus-east-1リージョンで作成する必要がある（CloudFront用の場合）
- CloudFormation Cfnリソースを使用する必要がある（L2 Constructは未対応）

**代替案**:
- カスタムルールのみ: 基本的な保護が不足するため却下
- WAFなし: セキュリティ要件に反するため却下

### 3. CloudFrontアクセスログの出力

**決定**: CloudFront標準アクセスログをS3バケットに出力

**理由**:
- リアルタイムログは高コストで、本機能の要件には過剰
- 標準アクセスログで十分な監視が可能（数分の遅延は許容）
- S3に保存することで、Athenaなどで柔軟に分析可能
- コスト効率が高い（CloudWatch Logsへの転送コストが不要）

**実装方法**:
```typescript
// CloudFrontディストリビューションで設定
new cloudfront.Distribution(this, 'Distribution', {
  // ... other props
  enableLogging: true,
  logBucket: logBucket,
  logFilePrefix: 'cloudfront/',
  logIncludesCookies: false,
});
```

**注意事項**:
- CloudFrontの標準アクセスログはS3バケットに出力される
- S3からCloudWatch Logsへの転送が必要な場合はLambdaまたはKinesis Data Firehoseを使用可能（将来の拡張）
- ログファイルは自動的にGzip圧縮される

**代替案**:
- リアルタイムログ: コストが高く、要件に過剰なため却下
- CloudWatch Logsへの直接出力: CloudFrontの標準アクセスログは直接CloudWatch Logsに出力できないため却下
- ログなし: 運用要件に反するため却下

### 4. S3バケットのセキュリティ設定

**決定**: プライベートバケット + OAC + バケットポリシー

**理由**:
- パブリックアクセスブロックを有効化してセキュリティを強化
- OACによる特定のCloudFrontディストリビューションからのみアクセス許可
- バケットポリシーで明示的にOACからのアクセスを許可

**実装方法**:
```typescript
const bucket = new s3.Bucket(this, 'FrontendBucket', {
  bucketName: 'loanpedia-frontend',
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
  encryption: s3.BucketEncryption.S3_MANAGED,
  removalPolicy: cdk.RemovalPolicy.RETAIN,
});

// OAC経由のアクセスを許可するバケットポリシー
bucket.addToResourcePolicy(new iam.PolicyStatement({
  actions: ['s3:GetObject'],
  resources: [bucket.arnForObjects('*')],
  principals: [new iam.ServicePrincipal('cloudfront.amazonaws.com')],
  conditions: {
    StringEquals: {
      'AWS:SourceArn': `arn:aws:cloudfront::${accountId}:distribution/${distribution.distributionId}`,
    },
  },
}));
```

**代替案**:
- パブリックバケット: セキュリティ要件に反するため却下
- OAI使用: OACが推奨されるため非推奨

### 5. CloudFrontのビヘイビア設定

**決定**: デフォルトビヘイビア（S3）+ /apiビヘイビア（TODO）

**理由**:
- デフォルトビヘイビアはフロントエンド用S3バケットへルーティング
- /apiパスのビヘイビアは将来のALB実装に備えて設定のみ（TODOコメント付き）
- ビヘイビアの優先順位で/apiが先に評価されるように設定

**実装方法**:
```typescript
new cloudfront.Distribution(this, 'Distribution', {
  defaultBehavior: {
    origin: s3Origin,
    viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
    allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD,
    cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD,
  },
  additionalBehaviors: {
    // TODO: バックエンドALB実装後に設定
    // '/api/*': {
    //   origin: albOrigin,
    //   viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
    //   allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
    // },
  },
  defaultRootObject: 'index.html',
});
```

**代替案**:
- /apiビヘイビアを実装しない: 将来の拡張性に欠けるため却下

### 6. ドメイン設定とRoute53レコード

**決定**: 既存のホストゾーンにAliasレコードを追加

**理由**:
- Route53スタックで既にloanpedia.jpのホストゾーンが作成済み
- CloudFrontディストリビューションへのAliasレコードが最適
- Aレコード（Alias）は無料で、CloudFrontへのルーティングに最適

**実装方法**:
```typescript
// 既存ホストゾーンの参照
const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
  domainName: 'loanpedia.jp',
});

// CloudFrontディストリビューションへのAliasレコード
new route53.ARecord(this, 'CloudFrontARecord', {
  zone: hostedZone,
  recordName: 'loanpedia.jp',
  target: route53.RecordTarget.fromAlias(
    new targets.CloudFrontTarget(distribution)
  ),
});
```

**代替案**:
- CNAMEレコード: Aliasレコードの方がCloudFrontに最適なため非推奨

## ベストプラクティス

### CloudFront設定

1. **キャッシュポリシー**: CachingOptimizedポリシーを使用
2. **圧縮**: 自動圧縮を有効化（gzip、brotli）
3. **HTTP/2, HTTP/3**: デフォルトで有効
4. **価格クラス**: PriceClass.PRICE_CLASS_ALL（全エッジロケーション）または PRICE_CLASS_200（日本含む）

### S3設定

1. **バージョニング**: 有効化（誤削除対策）
2. **暗号化**: S3マネージドキー（SSE-S3）
3. **ライフサイクルポリシー**: 古いバージョンの自動削除

### WAF設定

1. **レートリミット**: 必要に応じて追加
2. **GeoBlocking**: 日本のみ許可する場合に使用
3. **IP制限**: 管理用途で必要な場合に使用

### S3ログ設定

1. **保持期間**: 30日（ライフサイクルルールで自動削除）
2. **ログフォーマット**: 標準アクセスログ（Gzip圧縮）
3. **ログプレフィックス**: `cloudfront/`
4. **分析方法**: Amazon Athenaまたは直接S3からダウンロード

## セキュリティ考慮事項

### 1. 機密情報の管理

- ACM証明書ARN: CloudFormation Exportから参照
- ホストゾーンID: CDKの`fromLookup()`で動的取得
- AWSアカウントID: `cdk.Stack.of(this).account` で取得

### 2. IAMポリシー

- S3バケットポリシー: OACからのGetObject権限のみ
- ログバケットポリシー: CloudFrontからのログ書き込み権限（ObjectOwnership: OBJECT_WRITER）

### 3. ネットワークセキュリティ

- HTTPS強制: viewerProtocolPolicy.REDIRECT_TO_HTTPS
- TLS最低バージョン: TLSv1.2以上
- セキュリティヘッダー: ResponseHeadersPolicyで設定（将来的に追加）

## パフォーマンス最適化

### キャッシュ戦略

- **静的コンテンツ**: 長期キャッシュ（1年）
- **HTML**: 短期キャッシュ（5分）または no-cache
- **API**: キャッシュなし

### 圧縮

- 自動圧縮有効化（gzip、brotli）
- 対象: テキストファイル（HTML、CSS、JS、JSON）

### エッジロケーション

- PriceClass.PRICE_CLASS_200: 日本、アジア、北米、欧州をカバー
- コスト削減が必要な場合はPRICE_CLASS_100（北米、欧州のみ）

## コスト見積もり

### CloudFront

- データ転送: 最初の10TB/月 $0.114/GB（アジア）
- HTTPSリクエスト: $0.012/10,000リクエスト

### S3

- ストレージ: $0.025/GB/月（スタンダード）
- GETリクエスト: $0.00037/1,000リクエスト

### WAF

- WebACL: $5/月
- ルール: $1/月/ルール
- リクエスト: $0.60/100万リクエスト

### S3ストレージ（ログ用）

- ログストレージ: $0.025/GB/月（標準S3）
- 30日で自動削除（ライフサイクルルール）

**月間推定コスト** (低トラフィック想定):
- CloudFront: ~$10
- S3（コンテンツ + ログ）: ~$3
- WAF: ~$10
- **合計**: ~$23/月

## 実装順序

### Phase 1: コア実装

1. S3バケット作成
2. OAC作成
3. CloudFrontディストリビューション作成（基本設定）
4. バケットポリシー設定
5. Route53 Aレコード追加

### Phase 2: セキュリティ強化

1. WAF WebACL作成
2. CloudFrontにWAF関連付け
3. CloudFrontログ設定（S3バケット）

### Phase 3: 検証

1. テスト用index.htmlをS3にアップロード
2. https://loanpedia.jp でアクセス確認
3. S3直接アクセスの拒否確認
4. S3ログバケットでアクセスログの記録確認
5. WAFメトリクスの確認

## 依存関係

### 外部依存

- **Route53ホストゾーン**: 既存（Route53Stack）
- **ACM証明書**: 既存（AcmCertificateStack）

### 内部依存

- **CDKライブラリ**: aws-cdk-lib 2.215.0以上
- **Node.js**: 20.x以上（既存インフラと同じ）

## リスクと緩和策

### リスク1: ACM証明書の検証遅延

**影響**: CloudFrontディストリビューション作成が待機状態になる
**緩和策**: ACM証明書は既に発行・検証済みのため、リスクなし

### リスク2: CloudFrontディストリビューションのデプロイ時間

**影響**: デプロイに15〜20分かかる
**緩和策**: CI/CDパイプラインでタイムアウトを30分に設定

### リスク3: WAFのレートリミット誤検知

**影響**: 正当なユーザーがブロックされる可能性
**緩和策**: 初期はAWS Managed Rulesのみ使用し、カスタムルールは段階的に追加

### リスク4: S3ログストレージのコスト増加

**影響**: トラフィック増加時にログストレージコストが増加
**緩和策**: ライフサイクルルールで30日後に自動削除、必要に応じてS3 Intelligent-Tieringを使用

## 参考資料

### AWS公式ドキュメント

- [CloudFront OAC](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- [AWS WAF](https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html)
- [CloudFront ログ](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html)

### CDKドキュメント

- [aws-cdk-lib/aws-cloudfront](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudfront-readme.html)
- [aws-cdk-lib/aws-s3](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_s3-readme.html)
- [aws-cdk-lib/aws-wafv2](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_wafv2-readme.html)

## 結論

本調査により、CloudFront + S3によるフロントエンド配信基盤の実装に必要な技術要素が明確になりました。既存のRoute53ホストゾーンとACM証明書を活用し、OAC、WAF、S3ログバケットを組み合わせることで、セキュアで監視可能なCDN環境を構築できます。

CloudFrontの標準アクセスログはS3バケットに保存され、Athenaなどで分析可能です。将来的にCloudWatch Logsへの転送が必要な場合は、Lambda関数またはKinesis Data Firehoseを追加することで実現できます。

次のPhase 1では、データモデル（インフラリソース構造）とAPI契約（CloudFormation Outputs）を定義します。
