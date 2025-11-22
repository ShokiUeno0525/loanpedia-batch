# Data Model: CloudFront フロントエンド配信基盤

**作成日**: 2025-11-18
**対象機能**: CloudFront + S3によるフロントエンド配信基盤

## 概要

本ドキュメントは、CloudFrontフロントエンド配信基盤を構成するAWSリソースの構造とその関係性を定義します。Infrastructure as Code（IaC）における「データモデル」は、作成されるAWSリソースとその属性、リソース間の依存関係を表します。

## リソースエンティティ

### 1. FrontendBucket（S3バケット）

**目的**: フロントエンド静的コンテンツの保存

**属性**:
| 属性名 | 型 | 必須 | 説明 | デフォルト値 |
|--------|-----|------|------|--------------|
| bucketName | string | Yes | バケット名 | `loanpedia-frontend-${accountId}` |
| blockPublicAccess | BlockPublicAccess | Yes | パブリックアクセスブロック設定 | BLOCK_ALL |
| encryption | BucketEncryption | Yes | 暗号化設定 | S3_MANAGED |
| versioned | boolean | No | バージョニング有効化 | true |
| removalPolicy | RemovalPolicy | Yes | スタック削除時の動作 | RETAIN |

**関係性**:
- **CloudFrontディストリビューション** に対して 1:1（オリジンとして使用）
- **OAC** からアクセス許可を受ける

**制約**:
- バケット名はグローバルに一意である必要がある
- パブリックアクセスは完全にブロック
- OAC経由のみアクセス可能

**状態遷移**:
```
[作成] → [OACポリシー適用] → [コンテンツアップロード] → [配信可能]
```

---

### 2. OriginAccessControl（OAC）

**目的**: CloudFrontがS3バケットにアクセスするための認証制御

**属性**:
| 属性名 | 型 | 必須 | 説明 | デフォルト値 |
|--------|-----|------|------|--------------|
| name | string | Yes | OAC名 | `loanpedia-frontend-oac` |
| description | string | No | 説明 | `OAC for Loanpedia frontend S3 bucket` |
| signing | Signing | Yes | 署名方式 | SIGV4_ALWAYS |
| originAccessControlOriginType | string | Yes | オリジンタイプ | `s3` |

**関係性**:
- **S3バケット** へのアクセス権限を持つ
- **CloudFrontディストリビューション** から使用される

**制約**:
- 1つのOACは複数のオリジンで再利用可能だが、本実装では1:1
- SIGV4署名を常に使用

---

### 3. CloudFrontDistribution

**目的**: コンテンツ配信ネットワーク（CDN）のエントリーポイント

**属性**:
| 属性名 | 型 | 必須 | 説明 | デフォルト値 |
|--------|-----|------|------|--------------|
| domainName | string | Yes | カスタムドメイン名 | `loanpedia.jp` |
| certificate | ICertificate | Yes | SSL/TLS証明書 | 既存のACM証明書ARN |
| defaultRootObject | string | Yes | デフォルトルートオブジェクト | `index.html` |
| priceClass | PriceClass | No | 価格クラス（エッジロケーション範囲） | PRICE_CLASS_200 |
| enableLogging | boolean | Yes | ログ有効化 | true |
| logBucket | IBucket | Yes | ログ出力先S3バケット | 別途作成 |
| webAclId | string | Yes | WAF WebACL ID | WAF WebACLのARN |

**ビヘイビア（Behaviors）**:

#### デフォルトビヘイビア
| 属性名 | 値 |
|--------|-----|
| pathPattern | `*`（すべてのパス） |
| origin | S3バケット（OAC経由） |
| viewerProtocolPolicy | REDIRECT_TO_HTTPS |
| allowedMethods | GET, HEAD |
| cachedMethods | GET, HEAD |
| compress | true |
| cachePolicy | CachingOptimized |

#### /apiビヘイビア（TODO）
| 属性名 | 値 |
|--------|-----|
| pathPattern | `/api/*` |
| origin | ALB（未実装） |
| viewerProtocolPolicy | REDIRECT_TO_HTTPS |
| allowedMethods | ALL |
| cachePolicy | None |

**関係性**:
- **S3バケット** をオリジンとして使用
- **OAC** を介してS3にアクセス
- **ACM証明書** を使用してHTTPS接続を提供
- **WAF WebACL** に関連付けられる
- **Route53 Aレコード** から参照される
- **LogBucket（S3）** にアクセスログを出力

**制約**:
- カスタムドメインを使用する場合、証明書はus-east-1リージョンに存在する必要がある
- デフォルトルートオブジェクトはS3バケットのルートに存在する必要がある

**状態遷移**:
```
[作成中] → [デプロイ中（15-20分）] → [有効] → [配信可能]
```

---

### 4. WAF WebACL

**目的**: Webアプリケーションファイアウォールによるセキュリティ保護

**属性**:
| 属性名 | 型 | 必須 | 説明 | デフォルト値 |
|--------|-----|------|------|--------------|
| name | string | Yes | WebACL名 | `loanpedia-cloudfront-waf` |
| scope | string | Yes | スコープ | `CLOUDFRONT` |
| defaultAction | Action | Yes | デフォルトアクション | allow |
| rules | Rule[] | Yes | ルールリスト | AWS Managed Rules |

**ルール構成**:

#### AWSManagedRulesCommonRuleSet
| 属性名 | 値 |
|--------|-----|
| priority | 1 |
| vendorName | `AWS` |
| name | `AWSManagedRulesCommonRuleSet` |
| overrideAction | none |
| cloudWatchMetricsEnabled | true |

**関係性**:
- **CloudFrontディストリビューション** に関連付けられる
- **CloudWatch** にメトリクスを送信

**制約**:
- CloudFront用のWebACLはus-east-1リージョンに作成する必要がある
- scopeは`CLOUDFRONT`固定

---

### 5. Route53 ARecord

**目的**: ドメイン名をCloudFrontディストリビューションにマッピング

**属性**:
| 属性名 | 型 | 必須 | 説明 | デフォルト値 |
|--------|-----|------|------|--------------|
| zone | IHostedZone | Yes | ホストゾーン | 既存のloanpedia.jpホストゾーン |
| recordName | string | Yes | レコード名 | `loanpedia.jp` |
| target | RecordTarget | Yes | ターゲット | CloudFrontディストリビューション |
| ttl | Duration | No | TTL | なし（Alias） |

**関係性**:
- **Route53ホストゾーン** に属する
- **CloudFrontディストリビューション** を指す

**制約**:
- Aliasレコードのため、TTLは設定不可
- CloudFrontディストリビューションが作成済みである必要がある

---

### 7. LogBucket（S3バケット）

**目的**: CloudFrontアクセスログの一時保存

**属性**:
| 属性名 | 型 | 必須 | 説明 | デフォルト値 |
|--------|-----|------|------|--------------|
| bucketName | string | Yes | バケット名 | `loanpedia-cloudfront-logs-${accountId}` |
| blockPublicAccess | BlockPublicAccess | Yes | パブリックアクセスブロック設定 | BLOCK_ALL |
| encryption | BucketEncryption | Yes | 暗号化設定 | S3_MANAGED |
| lifecycleRules | LifecycleRule[] | No | ライフサイクルルール | 30日後に削除 |
| objectOwnership | ObjectOwnership | Yes | オブジェクト所有権 | OBJECT_WRITER |

**関係性**:
- **CloudFrontディストリビューション** からログを受信

**制約**:
- CloudFrontがログを書き込むための権限が必要
- オブジェクト所有権は`OBJECT_WRITER`に設定

---

## リソース依存関係図

```
┌─────────────────────────────────────────────────────────────────┐
│                         既存リソース                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐        ┌──────────────────┐             │
│  │ Route53          │        │ ACM Certificate  │             │
│  │ HostedZone       │        │ (us-east-1)      │             │
│  │ loanpedia.jp     │        │ loanpedia.jp     │             │
│  └────────┬─────────┘        └────────┬─────────┘             │
│           │                           │                        │
└───────────┼───────────────────────────┼────────────────────────┘
            │                           │
            │                           │
┌───────────┼───────────────────────────┼────────────────────────┐
│           │  新規リソース (ap-northeast-1) 🇯🇵                   │
├───────────┼───────────────────────────┼────────────────────────┤
│           │                           │                        │
│  ┌──────────────────┐    ┌──────────────────────────┐         │
│  │ FrontendBucket   │    │ LogBucket (S3)           │         │
│  │      (S3)        │    │ CloudFrontログ保存       │         │
│  │ - Private        │    │                          │         │
│  │ - OAC Only       │    │                          │         │
│  └──────────────────┘    └──────────────────────────┘         │
│                                                               │
└───────────────────────────────────────────────────────────────┘
            │                           │
            │ (crossRegionReferences)   │
            │                           │
┌───────────┼───────────────────────────┼────────────────────────┐
│           │  新規リソース (us-east-1) 🇺🇸                        │
├───────────┼───────────────────────────┼────────────────────────┤
│           │                           │                        │
│           v                           v                        │
│  ┌──────────────────────────────────────────────┐             │
│  │         CloudFront Distribution              │             │
│  │  - domainName: loanpedia.jp                  │             │
│  │  - certificate: 既存ACM証明書                 │             │
│  │  - defaultRootObject: index.html             │             │
│  │  - origin: S3 (ap-northeast-1から参照)       │             │
│  └────┬──────────────┬──────────────┬───────────┘             │
│       │              │              │                         │
│       │              │              │                         │
│       v              v              v                         │
│  ┌─────────┐   ┌─────────┐   ┌──────────────┐               │
│  │   OAC   │   │   WAF   │   │ Route53      │               │
│  │         │   │ WebACL  │   │ ARecord      │               │
│  └─────────┘   └─────────┘   └──────────────┘               │
│                                                               │
└───────────────────────────────────────────────────────────────┘

**リージョン戦略**:
- **S3Stack (ap-northeast-1)**: データ保管場所の最適化
- **FrontendStack (us-east-1)**: CloudFront/WAF要件（証明書・WAFはus-east-1必須）
- **クロスリージョン参照**: CDKの`crossRegionReferences: true`を使用し、FrontendStackがS3Stackのバケットを直接参照
```

## リソース作成順序

### Phase 1: S3Stack (ap-northeast-1)

1. **LogBucket（S3）**: ログ出力先バケット
2. **FrontendBucket（S3）**: フロントエンドコンテンツバケット
3. **CloudFormation Outputs**: バケット情報を出力（参照用、exportNameなし）

### Phase 2: FrontendStack (us-east-1) - セキュリティリソース

4. **S3バケット参照**: S3StackからバケットをProps経由で取得（crossRegionReferencesで自動処理）
5. **WAF WebACL**: Webアプリケーションファイアウォール
6. **OAC**: CloudFrontからS3へのアクセス制御

### Phase 3: FrontendStack (us-east-1) - 配信リソース

7. **CloudFrontDistribution**: CDNディストリビューション（OAC、WAF、LogBucketを参照）
8. **S3バケットポリシー**: FrontendBucketへのOACアクセス許可（自動設定）

### Phase 4: FrontendStack (us-east-1) - DNS設定

9. **Route53 ARecord**: ドメイン名をCloudFrontにマッピング

**デプロイ順序**:
1. S3Stack → S3バケット作成
2. FrontendStack → CloudFront/WAF/Route53作成（S3Stackに依存）

## バリデーションルール

### FrontendBucket

- ✅ パブリックアクセスが完全にブロックされている
- ✅ 暗号化が有効化されている
- ✅ バケットポリシーにOACからのアクセスのみ許可されている

### CloudFrontDistribution

- ✅ HTTPS強制リダイレクトが有効
- ✅ デフォルトルートオブジェクトが設定されている
- ✅ WAFが関連付けられている
- ✅ ログ出力が有効化されている
- ✅ カスタムドメインとACM証明書が設定されている

### WAF WebACL

- ✅ scopeが`CLOUDFRONT`に設定されている
- ✅ 最低1つのマネージドルールが有効
- ✅ CloudWatchメトリクスが有効化されている

### Route53 ARecord

- ✅ Aliasレコードとして設定されている
- ✅ CloudFrontディストリビューションを指している

## CloudFormation Outputs

### S3Stack Outputs (ap-northeast-1)

| Output名 | 説明 | Export名 |
|----------|------|----------|
| `FrontendBucketName` | フロントエンド用S3バケット名 | なし（crossRegionReferencesで自動管理） |
| `FrontendBucketArn` | フロントエンド用S3バケットARN | なし（crossRegionReferencesで自動管理） |
| `FrontendBucketDomainName` | フロントエンド用S3バケットドメイン名 | なし（crossRegionReferencesで自動管理） |
| `LogBucketName` | ログ用S3バケット名 | なし（crossRegionReferencesで自動管理） |
| `LogBucketArn` | ログ用S3バケットARN | なし（crossRegionReferencesで自動管理） |

### FrontendStack Outputs (us-east-1)

| Output名 | 説明 | Export名 |
|----------|------|----------|
| `DistributionId` | CloudFrontディストリビューションID | `LoanpediaCloudFrontDistributionId` |
| `DistributionDomainName` | CloudFrontのデフォルトドメイン名 | `LoanpediaCloudFrontDomainName` |
| `DistributionArn` | CloudFrontディストリビューションARN | `LoanpediaCloudFrontDistributionArn` |
| `WebAclId` | WAF WebACL ID | `LoanpediaCloudFrontWebAclId` |
| `WebAclArn` | WAF WebACL ARN | `LoanpediaCloudFrontWebAclArn` |
| `CustomDomainName` | カスタムドメイン名 | `LoanpediaCloudFrontCustomDomain` |
| `Route53RecordName` | Route53レコード名 | `LoanpediaCloudFrontRoute53RecordName` |

## セキュリティ考慮事項

### アクセス制御

- S3バケットはOAC経由でのみCloudFrontからアクセス可能
- パブリックアクセスは完全にブロック
- IAM権限は最小権限の原則に従う

### 暗号化

- S3: SSE-S3（S3マネージドキー）
- CloudFront-S3間: HTTPS（TLS 1.2以上）
- ユーザー-CloudFront間: HTTPS強制

### 監視とロギング

- CloudFrontアクセスログをS3に出力
- WAFメトリクスをCloudWatchに送信
- 異常なトラフィックパターンの検知（将来の拡張）

## 拡張性

### 将来の拡張ポイント

1. **バックエンドAPI統合**: /apiビヘイビアでALBにルーティング
2. **CloudWatch Logsへのログ転送**: S3からFirehose/Lambda経由で転送（オプション）
3. **カスタムエラーページ**: 404、403エラー用のカスタムページ
4. **Lambda@Edge**: リクエスト/レスポンスの変換
5. **複数環境対応**: dev、staging、productionの分離
6. **WAFカスタムルール**: レートリミット、GeoBlocking、IP制限

## まとめ

本データモデルは、CloudFrontフロントエンド配信基盤を構成する6つの主要リソース（S3バケット2つ、OAC、CloudFrontディストリビューション、WAF WebACL、Route53 ARecord）とその関係性を定義しています。各リソースは明確な責務を持ち、セキュリティ、パフォーマンス、監視の各側面を考慮した設計となっています。CloudFrontの標準アクセスログはS3バケットに保存され、必要に応じてAthenaなどで分析可能です。
