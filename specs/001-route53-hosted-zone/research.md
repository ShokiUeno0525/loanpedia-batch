# Research: Route53 パブリックホストゾーン作成

**Feature**: Route53 パブリックホストゾーン作成
**Date**: 2025-11-16
**Phase**: 0 - Outline & Research

## 調査項目

### 1. AWS CDK Route53 ホストゾーンのベストプラクティス

#### Decision: PublicHostedZone Constructを使用

AWS CDK v2では、`aws-cdk-lib/aws-route53`モジュールの`PublicHostedZone` constructを使用してパブリックホストゾーンを作成します。

#### Rationale

- **型安全性**: TypeScriptの型システムにより、設定ミスを防止
- **シンプルAPI**: 最小限のコードでホストゾーン作成が可能
- **CloudFormation統合**: CDKが自動的にCloudFormationテンプレートを生成
- **ベストプラクティス適用**: CDK constructは自動的にAWSのベストプラクティスを適用

#### Alternatives Considered

| 選択肢 | 長所 | 短所 | 却下理由 |
|--------|------|------|----------|
| **CfnHostedZone**（L1 Construct） | CloudFormationに近い細かい制御 | 冗長なコード、型安全性が低い | PublicHostedZoneで十分な機能を提供 |
| **AWS CLI** | シンプル、スクリプト化可能 | IaCではない、再現性に欠ける | CDKプロジェクトと統合できない |
| **Terraform** | 別IaCツール | 新しいツールチェーン導入が必要 | 既存CDKプロジェクトと統合困難 |

#### Implementation Pattern

```typescript
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as cdk from 'aws-cdk-lib';

export class Route53Stack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const hostedZone = new route53.PublicHostedZone(this, 'LoanpediaHostedZone', {
      zoneName: 'loanpedia.jp',
    });

    // CloudFormation Outputsでネームサーバーを出力
    new cdk.CfnOutput(this, 'NameServers', {
      value: cdk.Fn.join(',', hostedZone.hostedZoneNameServers!),
      description: 'お名前.comで設定するネームサーバー',
    });
  }
}
```

---

### 2. CloudFormation Outputsのベストプラクティス

#### Decision: CfnOutputで個別にネームサーバーを出力

各ネームサーバーを個別のOutputとして出力し、お名前.comでの設定作業を簡便化します。

#### Rationale

- **視認性**: コンソールで各ネームサーバーが明確に表示される
- **コピー容易性**: 個別Outputなので1つずつコピー&ペーストしやすい
- **ドキュメント性**: 各Outputに説明を付けられる

#### Implementation Pattern

```typescript
// 方法1: カンマ区切りの単一Output
new cdk.CfnOutput(this, 'NameServers', {
  value: cdk.Fn.join(',', hostedZone.hostedZoneNameServers!),
  description: 'お名前.comで設定するネームサーバー（カンマ区切り）',
  exportName: 'LoanpediaNameServers',
});

// 方法2（推奨）: 個別Output
hostedZone.hostedZoneNameServers!.forEach((ns, index) => {
  new cdk.CfnOutput(this, `NameServer${index + 1}`, {
    value: ns,
    description: `ネームサーバー ${index + 1}`,
  });
});
```

---

### 3. お名前.comとの統合パターン

#### Decision: 手動でネームサーバーを変更（自動化は範囲外）

お名前.comのAPI経由での自動化は行わず、CloudFormation Outputs をコピーして手動で設定します。

#### Rationale

- **シンプル性**: API認証・実装が不要
- **リスク軽減**: DNS設定は慎重に行うべき操作であり、手動確認が望ましい
- **頻度**: ホストゾーン作成は1回のみの操作
- **検証可能性**: 各ステップを目視確認できる

#### 手順（quickstart.mdに記載予定）

1. `cdk deploy Route53Stack` 実行
2. CloudFormation Outputsから4つのネームサーバーをコピー
3. お名前.comの管理画面にログイン
4. 「ドメイン設定」→「ネームサーバーの変更」
5. 「他のネームサーバーを利用」を選択
6. 4つのネームサーバーを入力
7. 変更を保存
8. `nslookup loanpedia.jp` でDNS浸透を確認

#### Alternatives Considered

| 選択肢 | 長所 | 短所 | 却下理由 |
|--------|------|------|----------|
| **お名前.com API** | 完全自動化 | API認証実装が必要、エラーハンドリング複雑 | 1回のみの操作に対してオーバーエンジニアリング |
| **Terraform Onamae Provider** | IaCで管理 | 新しいツール導入、CDKと混在 | 既存CDKプロジェクトとの統合困難 |

---

### 4. テスト戦略

#### Decision: CDK Assertionsを使用した単体テスト

CDK v2の`@aws-cdk/assertions`を使用して、スタックの構成をテストします。

#### Test Cases

1. **ホストゾーンが作成されること**
   - `PublicHostedZone` リソースが存在する
   - ゾーン名が `loanpedia.jp` である

2. **CloudFormation Outputsが存在すること**
   - `NameServers` または個別ネームサーバーOutputが存在する

3. **スタックがエラーなく合成できること**
   - `cdk synth` が成功する

#### Implementation Pattern

```typescript
import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import { Route53Stack } from '../lib/route53-stack';

describe('Route53Stack', () => {
  test('PublicHostedZone Created', () => {
    const app = new cdk.App();
    const stack = new Route53Stack(app, 'TestStack');
    const template = Template.fromStack(stack);

    template.hasResourceProperties('AWS::Route53::HostedZone', {
      Name: 'loanpedia.jp.',
    });
  });

  test('CloudFormation Outputs Exist', () => {
    const app = new cdk.App();
    const stack = new Route53Stack(app, 'TestStack');
    const template = Template.fromStack(stack);

    template.hasOutput('NameServers', {});
  });
});
```

---

### 5. セキュリティ考慮事項

#### Decision: パブリックホストゾーンのみ（追加セキュリティ設定不要）

Route53パブリックホストゾーンは公開DNSサービスであり、特別なセキュリティ設定は不要です。

#### 考慮事項

- **アクセス制御**: Route53へのIAM権限は既存のGitHub OIDC認証で管理
- **機密情報**: ドメイン名は公開情報であり、機密性なし
- **料金**: ホストゾーン作成後は$0.50/月 + クエリ料金が発生（予算内）
- **削除保護**: スタック削除時にホストゾーンも削除される（意図的な設計）

---

## 技術的決定事項まとめ

| 項目 | 決定内容 | 根拠 |
|------|----------|------|
| **CDK Construct** | `PublicHostedZone` (L2) | 型安全性、シンプルAPI、ベストプラクティス適用 |
| **Output形式** | 個別ネームサーバーOutput | お名前.com設定の容易性 |
| **お名前.com統合** | 手動設定 | シンプル性、1回のみの操作 |
| **テスト** | CDK Assertions | CloudFormation構成の検証 |
| **セキュリティ** | IAM権限のみ | パブリックDNSサービスの性質上、追加設定不要 |

---

## 次のステップ

Phase 0完了 - Phase 1（quickstart.md作成、エージェントコンテキスト更新）に進行可能
