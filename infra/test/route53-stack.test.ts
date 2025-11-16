import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import { Route53Stack } from '../lib/route53-stack';

describe('Route53Stack', () => {
  test('loanpedia.jp のパブリックホストゾーンが作成される', () => {
    const app = new cdk.App();
    const stack = new Route53Stack(app, 'TestStack');
    const template = Template.fromStack(stack);

    // ホストゾーンが loanpedia.jp で作成されることを確認
    template.hasResourceProperties('AWS::Route53::HostedZone', {
      Name: 'loanpedia.jp.',
    });
  });

  test('4つのネームサーバーOutputsが存在する', () => {
    const app = new cdk.App();
    const stack = new Route53Stack(app, 'TestStack');
    const template = Template.fromStack(stack);

    // 4つのネームサーバーOutputが存在することを確認
    template.hasOutput('NameServer1', {});
    template.hasOutput('NameServer2', {});
    template.hasOutput('NameServer3', {});
    template.hasOutput('NameServer4', {});
  });

  test('HostedZoneId Output が存在し、エクスポートされる', () => {
    const app = new cdk.App();
    const stack = new Route53Stack(app, 'TestStack');
    const template = Template.fromStack(stack);

    // HostedZoneId Outputが存在し、正しくエクスポートされることを確認
    template.hasOutput('HostedZoneId', {
      Export: {
        Name: 'LoanpediaHostedZoneId',
      },
    });
  });

  test('ホストゾーンが1つだけ作成される', () => {
    const app = new cdk.App();
    const stack = new Route53Stack(app, 'TestStack');
    const template = Template.fromStack(stack);

    // 意図しない複数のホストゾーンが作られていないことを確認
    template.resourceCountIs('AWS::Route53::HostedZone', 1);
  });
});
