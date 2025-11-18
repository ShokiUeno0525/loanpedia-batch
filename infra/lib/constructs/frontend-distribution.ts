import * as cdk from 'aws-cdk-lib';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import { Construct } from 'constructs';

/**
 * FrontendDistribution Constructプロパティ
 */
export interface FrontendDistributionProps {
  /**
   * フロントエンドコンテンツ用S3バケット
   */
  readonly frontendBucket: s3.IBucket;

  /**
   * CloudFrontログ用S3バケット
   */
  readonly logBucket: s3.IBucket;

  /**
   * ACM証明書
   */
  readonly certificate: acm.ICertificate;

  /**
   * カスタムドメイン名
   */
  readonly domainName: string;

  /**
   * WAF WebACL ARN（オプション）
   */
  readonly webAclArn?: string;

  /**
   * デフォルトルートオブジェクト
   * @default 'index.html'
   */
  readonly defaultRootObject?: string;

  /**
   * Price Class
   * @default PRICE_CLASS_200
   */
  readonly priceClass?: cloudfront.PriceClass;

  /**
   * Basic認証用のCloudFront Function（オプション）
   */
  readonly basicAuthFunction?: cloudfront.IFunction;
}

/**
 * CloudFrontディストリビューションのConstruct
 *
 * @remarks
 * このConstructは以下のリソースを作成します：
 * - CloudFrontディストリビューション
 * - Origin Access Control (OAC)
 * - S3バケットポリシー（OAC経由のアクセス許可）
 *
 * セキュリティ設定：
 * - HTTPS強制（REDIRECT_TO_HTTPS）
 * - OAC経由のみS3アクセス可能
 * - カスタムドメイン（loanpedia.jp）
 * - ACM証明書によるHTTPS接続
 *
 * 将来の拡張：
 * - /apiビヘイビア（ALBへのルーティング、現在はTODO）
 */
export class FrontendDistribution extends Construct {
  /**
   * CloudFrontディストリビューション
   */
  public readonly distribution: cloudfront.Distribution;

  constructor(scope: Construct, id: string, props: FrontendDistributionProps) {
    super(scope, id);

    const defaultRootObject = props.defaultRootObject || 'index.html';
    const priceClass = props.priceClass || cloudfront.PriceClass.PRICE_CLASS_200;

    // T020-T022: CloudFrontディストリビューションの作成
    this.distribution = new cloudfront.Distribution(this, 'Distribution', {
      // カスタムドメイン設定
      domainNames: [props.domainName],
      certificate: props.certificate,

      // デフォルトルートオブジェクト
      defaultRootObject: defaultRootObject,

      // Price Class（エッジロケーション範囲）
      priceClass: priceClass,

      // 標準アクセスログ設定（S3バケットに出力）
      enableLogging: true,
      logBucket: props.logBucket,
      logFilePrefix: 'cloudfront/',
      logIncludesCookies: false,

      // WAF WebACL（User Story 3）
      webAclId: props.webAclArn,

      // デフォルトビヘイビア（S3オリジン）
      defaultBehavior: {
        // T018: S3オリジン（OAC経由）
        // OACはS3BucketOrigin.withOriginAccessControlで自動作成される
        origin: origins.S3BucketOrigin.withOriginAccessControl(props.frontendBucket),
        // ビューワープロトコルポリシー: HTTPSにリダイレクト
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        // 許可されたHTTPメソッド: GET, HEAD
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD,
        // キャッシュされるメソッド: GET, HEAD
        cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD,
        // 圧縮を有効化
        compress: true,
        // キャッシュポリシー: CachingOptimized
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        // Basic認証Functionを追加（オプション）
        functionAssociations: props.basicAuthFunction
          ? [
              {
                function: props.basicAuthFunction,
                eventType: cloudfront.FunctionEventType.VIEWER_REQUEST,
              },
            ]
          : undefined,
      },

      // エラーレスポンス設定
      errorResponses: [
        {
          httpStatus: 403,
          responseHttpStatus: 404,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.minutes(5),
        },
        {
          httpStatus: 404,
          responseHttpStatus: 404,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.minutes(5),
        },
      ],

      comment: 'Loanpedia フロントエンド配信用CloudFrontディストリビューション',
    });

    // T024: S3バケットポリシーを追加（OAC経由のCloudFrontアクセスを許可）
    // Note: CloudFront DistributionのOACが自動的にバケットポリシーを設定するため、
    // 手動でのバケットポリシー追加は不要。OACが自動的に適切なポリシーを作成します。
    // 詳細: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html

    // T022: TODO: 将来の拡張 - /apiビヘイビア（ALBへのルーティング）
    // 現在はバックエンドALBが未実装のため、TODOとして残す
    // TODO: /apiビヘイビアを追加
    // - pathPattern: '/api/*'
    // - origin: ALB（未実装）
    // - viewerProtocolPolicy: REDIRECT_TO_HTTPS
    // - allowedMethods: ALL
    // - cachePolicy: None（APIはキャッシュしない）

    // タグ付け
    cdk.Tags.of(this).add('Component', 'Frontend');
    cdk.Tags.of(this).add('Purpose', 'ContentDelivery');
  }
}
