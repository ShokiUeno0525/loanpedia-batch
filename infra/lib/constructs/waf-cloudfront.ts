import * as cdk from 'aws-cdk-lib';
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';
import { Construct } from 'constructs';

/**
 * WAF Constructプロパティ
 */
export interface WafCloudFrontProps {
  /**
   * WAF WebACL名
   * @default 'loanpedia-cloudfront-waf'
   */
  readonly webAclName?: string;

  /**
   * CloudWatch メトリクスを有効化するか
   * @default true
   */
  readonly enableMetrics?: boolean;
}

/**
 * CloudFront用WAF WebACLのConstruct
 *
 * @remarks
 * このConstructは以下のリソースを作成します：
 * - WAF WebACL（CloudFront用、us-east-1リージョン）
 * - AWS Managed Rules（AWSManagedRulesCommonRuleSet）
 * - CloudWatchメトリクス設定
 *
 * 重要な制約：
 * - CloudFront用のWAFは必ずus-east-1リージョンで作成する必要がある
 * - scope は CLOUDFRONT に設定する必要がある
 */
export class WafCloudFront extends Construct {
  /**
   * WAF WebACL
   */
  public readonly webAcl: wafv2.CfnWebACL;

  constructor(scope: Construct, id: string, props?: WafCloudFrontProps) {
    super(scope, id);

    const webAclName = props?.webAclName || 'loanpedia-cloudfront-waf';
    const enableMetrics = props?.enableMetrics ?? true;

    // T042-T044: WAF WebACLの作成
    // CloudFront用のWAFは必ずus-east-1リージョンで作成
    this.webAcl = new wafv2.CfnWebACL(this, 'WebACL', {
      name: webAclName,
      // CloudFront用はCLOUDFRONTスコープ（リージョナルではない）
      scope: 'CLOUDFRONT',
      // デフォルトアクションはALLOW（ルールにマッチしないリクエストを許可）
      defaultAction: {
        allow: {},
      },
      // AWS Managed Rulesを追加
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
          overrideAction: {
            none: {},
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: enableMetrics,
            metricName: 'AWSManagedRulesCommonRuleSetMetric',
          },
        },
      ],
      // WebACL全体のメトリクス設定
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: enableMetrics,
        metricName: 'WebAclMetric',
      },
    });

    // タグ付け
    cdk.Tags.of(this).add('Component', 'Security');
    cdk.Tags.of(this).add('Purpose', 'WAF');
  }
}
