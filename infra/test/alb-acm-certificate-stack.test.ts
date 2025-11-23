import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import { AlbAcmCertificateStack } from '../lib/stacks/alb-acm-certificate-stack';

describe('AlbAcmCertificateStack', () => {
  let app: cdk.App;
  let stack: AlbAcmCertificateStack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App();
    stack = new AlbAcmCertificateStack(app, 'TestAlbAcmCertificateStack', {
      env: {
        account: '123456789012',
        region: 'ap-northeast-1',
      },
    });
    template = Template.fromStack(stack);
  });

  describe('ACM証明書', () => {
    test('ACM証明書が1個作成される', () => {
      template.resourceCountIs('AWS::CertificateManager::Certificate', 1);
    });

    test('ドメイン名がapi.loanpedia.jpである', () => {
      template.hasResourceProperties('AWS::CertificateManager::Certificate', {
        DomainName: 'api.loanpedia.jp',
        ValidationMethod: 'DNS',
      });
    });
  });

  describe('CloudFormation Outputs', () => {
    test('CertificateArnが出力される', () => {
      template.hasOutput('CertificateArn', {
        Description: 'ALB用ACM証明書ARN (api.loanpedia.jp)',
        Export: {
          Name: 'LoanpediaAlbCertificateArn',
        },
      });
    });
  });

  describe('スナップショットテスト', () => {
    test('ALB ACM Certificate Stackのスナップショットが一致する', () => {
      expect(template.toJSON()).toMatchSnapshot();
    });
  });
});
