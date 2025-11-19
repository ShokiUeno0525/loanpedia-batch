import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { FrontendStack } from '../lib/stacks/frontend-stack';

/**
 * FrontendStack のテスト
 * User Story 1: 基本的なフロントエンドコンテンツ配信
 */
describe('FrontendStack', () => {
  let app: cdk.App;
  let stack: FrontendStack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App({
      context: {
        'hosted-zone:account=test-account:domainName=loanpedia.jp:region=us-east-1': {
          Id: '/hostedzone/Z1234567890ABC',
          Name: 'loanpedia.jp.',
        },
      },
    });
    stack = new FrontendStack(app, 'TestFrontendStack', {
      env: {
        account: 'test-account',
        region: 'us-east-1',
      },
    });
    template = Template.fromStack(stack);
  });

  describe('S3バケット', () => {
    test('フロントエンドバケットが作成される', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        BucketName: 'loanpedia-frontend',
        PublicAccessBlockConfiguration: {
          BlockPublicAcls: true,
          BlockPublicPolicy: true,
          IgnorePublicAcls: true,
          RestrictPublicBuckets: true,
        },
        BucketEncryption: {
          ServerSideEncryptionConfiguration: [
            {
              ServerSideEncryptionByDefault: {
                SSEAlgorithm: 'AES256',
              },
            },
          ],
        },
        VersioningConfiguration: {
          Status: 'Enabled',
        },
      });
    });

    test('ログバケットが作成される', () => {
      template.hasResourceProperties('AWS::S3::Bucket', {
        BucketName: 'loanpedia-cloudfront-logs',
        PublicAccessBlockConfiguration: {
          BlockPublicAcls: true,
          BlockPublicPolicy: true,
          IgnorePublicAcls: true,
          RestrictPublicBuckets: true,
        },
        BucketEncryption: {
          ServerSideEncryptionConfiguration: [
            {
              ServerSideEncryptionByDefault: {
                SSEAlgorithm: 'AES256',
              },
            },
          ],
        },
        LifecycleConfiguration: {
          Rules: [
            {
              ExpirationInDays: 30,
              Id: 'DeleteOldLogs',
              Status: 'Enabled',
            },
          ],
        },
        OwnershipControls: {
          Rules: [
            {
              ObjectOwnership: 'ObjectWriter',
            },
          ],
        },
      });
    });
  });

  describe('CloudFrontディストリビューション', () => {
    test('CloudFrontディストリビューションが作成される', () => {
      template.hasResourceProperties('AWS::CloudFront::Distribution', {
        DistributionConfig: {
          Comment: 'Loanpedia フロントエンド配信用CloudFrontディストリビューション',
          DefaultRootObject: 'index.html',
          Enabled: true,
          HttpVersion: 'http2',
          IPV6Enabled: true,
          PriceClass: 'PriceClass_200',
        },
      });
    });

    test('カスタムドメインとACM証明書が設定される', () => {
      template.hasResourceProperties('AWS::CloudFront::Distribution', {
        DistributionConfig: {
          Aliases: ['loanpedia.jp'],
          ViewerCertificate: {
            AcmCertificateArn: Match.objectLike({
              'Fn::ImportValue': 'LoanpediaCertificateArn',
            }),
            MinimumProtocolVersion: 'TLSv1.2_2021',
            SslSupportMethod: 'sni-only',
          },
        },
      });
    });

    test('S3ログ設定が有効化される', () => {
      template.hasResourceProperties('AWS::CloudFront::Distribution', {
        DistributionConfig: {
          Logging: {
            Bucket: Match.anyValue(),
            IncludeCookies: false,
            Prefix: 'cloudfront/',
          },
        },
      });
    });

    test('デフォルトビヘイビアが正しく設定される', () => {
      template.hasResourceProperties('AWS::CloudFront::Distribution', {
        DistributionConfig: {
          DefaultCacheBehavior: {
            AllowedMethods: ['GET', 'HEAD'],
            CachedMethods: ['GET', 'HEAD'],
            Compress: true,
            ViewerProtocolPolicy: 'redirect-to-https',
            CachePolicyId: Match.anyValue(),
          },
        },
      });
    });
  });

  describe('OAC（Origin Access Control）', () => {
    test('CloudFront OACが作成される', () => {
      // S3BucketOrigin.withOriginAccessControl を使用すると、
      // 自動的に OriginAccessControl が作成される
      template.hasResourceProperties('AWS::CloudFront::Distribution', {
        DistributionConfig: {
          Origins: [
            {
              S3OriginConfig: {
                OriginAccessIdentity: '',
              },
              OriginAccessControlId: Match.anyValue(),
            },
          ],
        },
      });
    });

    test('S3バケットポリシーにOACアクセスが含まれる', () => {
      template.hasResourceProperties('AWS::S3::BucketPolicy', {
        Bucket: Match.anyValue(),
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: 's3:GetObject',
              Effect: 'Allow',
              Principal: {
                Service: 'cloudfront.amazonaws.com',
              },
              Resource: Match.anyValue(),
            }),
          ]),
        },
      });
    });
  });

  describe('WAF', () => {
    test('WAF WebACLが作成される', () => {
      template.hasResourceProperties('AWS::WAFv2::WebACL', {
        Name: 'loanpedia-cloudfront-waf',
        Scope: 'CLOUDFRONT',
        DefaultAction: {
          Allow: {},
        },
        VisibilityConfig: {
          CloudWatchMetricsEnabled: true,
          MetricName: 'WebAclMetric',
          SampledRequestsEnabled: true,
        },
      });
    });

    test('AWS Managed Rulesが含まれる', () => {
      template.hasResourceProperties('AWS::WAFv2::WebACL', {
        Rules: [
          {
            Name: 'AWSManagedRulesCommonRuleSet',
            Priority: 1,
            Statement: {
              ManagedRuleGroupStatement: {
                VendorName: 'AWS',
                Name: 'AWSManagedRulesCommonRuleSet',
              },
            },
            OverrideAction: {
              None: {},
            },
            VisibilityConfig: {
              CloudWatchMetricsEnabled: true,
              MetricName: 'AWSManagedRulesCommonRuleSetMetric',
              SampledRequestsEnabled: true,
            },
          },
        ],
      });
    });

    test('CloudFrontディストリビューションにWAFが関連付けられる', () => {
      template.hasResourceProperties('AWS::CloudFront::Distribution', {
        DistributionConfig: {
          WebACLId: Match.anyValue(),
        },
      });
    });
  });

  describe('Route53レコード', () => {
    test('Aレコードが作成される', () => {
      template.hasResourceProperties('AWS::Route53::RecordSet', {
        Name: 'loanpedia.jp.',
        Type: 'A',
        AliasTarget: {
          DNSName: Match.anyValue(),
          HostedZoneId: Match.anyValue(), // CloudFrontのホストゾーンID（FindInMapで解決）
        },
      });
    });
  });

  describe('CloudFormation Outputs', () => {
    test('DistributionId Outputが定義される', () => {
      template.hasOutput('DistributionId', {
        Description: 'CloudFrontディストリビューションID',
        Export: {
          Name: 'LoanpediaCloudFrontDistributionId',
        },
      });
    });

    test('DistributionDomainName Outputが定義される', () => {
      template.hasOutput('DistributionDomainName', {
        Description: 'CloudFrontのデフォルトドメイン名',
        Export: {
          Name: 'LoanpediaCloudFrontDomainName',
        },
      });
    });

    test('DistributionArn Outputが定義される', () => {
      template.hasOutput('DistributionArn', {
        Description: 'CloudFrontディストリビューションARN',
        Export: {
          Name: 'LoanpediaCloudFrontDistributionArn',
        },
      });
    });

    test('FrontendBucketName Outputが定義される', () => {
      template.hasOutput('FrontendBucketName', {
        Description: 'フロントエンド用S3バケット名',
        Export: {
          Name: 'LoanpediaFrontendBucketName',
        },
      });
    });

    test('FrontendBucketArn Outputが定義される', () => {
      template.hasOutput('FrontendBucketArn', {
        Description: 'フロントエンド用S3バケットARN',
        Export: {
          Name: 'LoanpediaFrontendBucketArn',
        },
      });
    });

    test('FrontendBucketDomainName Outputが定義される', () => {
      template.hasOutput('FrontendBucketDomainName', {
        Description: 'フロントエンド用S3バケットのドメイン名',
        Export: {
          Name: 'LoanpediaFrontendBucketDomainName',
        },
      });
    });

    test('LogBucketName Outputが定義される', () => {
      template.hasOutput('LogBucketName', {
        Description: 'CloudFrontログ用S3バケット名',
        Export: {
          Name: 'LoanpediaCloudFrontLogBucketName',
        },
      });
    });

    test('LogBucketArn Outputが定義される', () => {
      template.hasOutput('LogBucketArn', {
        Description: 'CloudFrontログ用S3バケットARN',
        Export: {
          Name: 'LoanpediaCloudFrontLogBucketArn',
        },
      });
    });

    test('WebAclId Outputが定義される', () => {
      template.hasOutput('WebAclId', {
        Description: 'WAF WebACL ID',
        Export: {
          Name: 'LoanpediaCloudFrontWebAclId',
        },
      });
    });

    test('WebAclArn Outputが定義される', () => {
      template.hasOutput('WebAclArn', {
        Description: 'WAF WebACL ARN',
        Export: {
          Name: 'LoanpediaCloudFrontWebAclArn',
        },
      });
    });

    test('CustomDomainName Outputが定義される', () => {
      template.hasOutput('CustomDomainName', {
        Value: 'loanpedia.jp',
        Description: 'CloudFrontに設定されたカスタムドメイン名',
        Export: {
          Name: 'LoanpediaCloudFrontCustomDomain',
        },
      });
    });

    test('Route53RecordName Outputが定義される', () => {
      template.hasOutput('Route53RecordName', {
        Value: 'loanpedia.jp',
        Description: '作成されたRoute53 Aレコード名',
        Export: {
          Name: 'LoanpediaCloudFrontRoute53RecordName',
        },
      });
    });
  });

  describe('スタック全体の検証', () => {
    test('スナップショットテスト', () => {
      expect(template.toJSON()).toMatchSnapshot();
    });

    test('最小限のリソースが作成される', () => {
      // S3バケット: 2個（frontend + logs）
      template.resourceCountIs('AWS::S3::Bucket', 2);

      // CloudFrontディストリビューション: 1個
      template.resourceCountIs('AWS::CloudFront::Distribution', 1);

      // WAF WebACL: 1個
      template.resourceCountIs('AWS::WAFv2::WebACL', 1);

      // Route53レコード: 1個
      template.resourceCountIs('AWS::Route53::RecordSet', 1);

      // S3バケットポリシー: 2個（フロントエンドバケット用 + ログバケット用）
      template.resourceCountIs('AWS::S3::BucketPolicy', 2);
    });
  });
});
