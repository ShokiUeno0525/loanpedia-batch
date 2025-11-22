import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { S3Stack } from '../lib/stacks/s3-stack';

/**
 * S3Stack のテスト
 * フロントエンド用S3バケットとログバケットを管理
 */
describe('S3Stack', () => {
  let app: cdk.App;
  let stack: S3Stack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App();
    stack = new S3Stack(app, 'TestS3Stack', {
      env: {
        account: 'test-account',
        region: 'ap-northeast-1',
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

  describe('CloudFormation Outputs', () => {
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
  });

  describe('リージョン検証', () => {
    test('スタックがap-northeast-1リージョンで作成される', () => {
      expect(stack.region).toBe('ap-northeast-1');
    });
  });

  describe('スタック全体の検証', () => {
    test('スナップショットテスト', () => {
      expect(template.toJSON()).toMatchSnapshot();
    });

    test('S3バケットのみが作成される', () => {
      // S3バケット: 2個（frontend + logs）
      template.resourceCountIs('AWS::S3::Bucket', 2);

      // S3バケットポリシー: 1個（ログバケット用、フロントエンドバケットはCloudFrontスタックで設定）
      template.resourceCountIs('AWS::S3::BucketPolicy', 1);

      // CloudFront関連リソースは存在しない
      template.resourceCountIs('AWS::CloudFront::Distribution', 0);
      template.resourceCountIs('AWS::WAFv2::WebACL', 0);
      template.resourceCountIs('AWS::Route53::RecordSet', 0);
    });
  });
});
