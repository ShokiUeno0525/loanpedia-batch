import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { AcmCertificateStack } from '../lib/acm-certificate-stack';

describe('AcmCertificateStack', () => {
  let app: cdk.App;
  let stack: AcmCertificateStack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App();
    stack = new AcmCertificateStack(app, 'TestAcmCertificateStack', {
      env: {
        account: '123456789012',
        region: 'us-east-1',
      },
    });
    template = Template.fromStack(stack);
  });

  // T015: スナップショットテスト
  // スタック全体の構造を検証
  test('スナップショットテスト: スタック全体の構造が期待通りであること', () => {
    expect(template.toJSON()).toMatchSnapshot();
  });

  // T016: Fine-grained assertions
  // 重要な設定のみを厳選して検証
  test('ACM証明書のドメイン名がloanpedia.jpであること', () => {
    template.hasResourceProperties('AWS::CertificateManager::Certificate', {
      DomainName: 'loanpedia.jp',
    });
  });

  test('ACM証明書の検証方式がDNSであること', () => {
    template.hasResourceProperties('AWS::CertificateManager::Certificate', {
      ValidationMethod: 'DNS',
    });
  });
});
