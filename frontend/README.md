# Loanpedia Frontend

Vite + React + TypeScript ベースのフロントエンド。

## ローカル開発
- 前提: Node.js `24.11.1`（`frontend/.node-version` の通り）
- セットアップ:
  1. `cd frontend`
  2. `npm ci`
  3. `npm run dev`

## コーディング規約
- Lint: `npm run lint`（ESLint）
- Format: `npm run format` / `npm run format:fix`（Prettier）
- Test: `npm run test`（Vitest + jsdom）

## ビルド

```
npm run build
```

`dist/` が S3 にデプロイ対象となります。

## CI/CD（GitHub Actions）
- ワークフロー: `.github/workflows/frontend_ci_cd.yml`
- トリガー:
  - PR: `frontend/**` の変更でCI（lint/test/build）を実行
  - main への push: CI 成功後にCD（S3デプロイ + CloudFront無効化）を実行

### 必要なGitHub Secrets
- `AWS_ROLE_ARN`: `infra/lib/github-oidc-stack.ts` で作成する `GitHubActionsDeployRole` のARN
- `AWS_REGION`: デプロイ先リージョン（例: `us-east-1`）

### 前提（CDK側）
インフラ側スタック（`infra/lib/frontend-stack.ts`）がデプロイ済みで、以下のCloudFormation Exportが存在すること:
- `LoanpediaFrontendBucketName`
- `LoanpediaCloudFrontDistributionId`

### デプロイの流れ（概要）
1. `frontend/` をビルドして `dist/` を生成
2. Export から S3 バケット名と CloudFront Distribution ID を解決
3. `index.html` は `no-cache`、それ以外のアセットは長期キャッシュで S3 にアップロード
4. CloudFront のキャッシュを `/*` で無効化

## トラブルシュート
- `list-exports` で値が空: インフラCDKが未デプロイ、またはExport名が一致していない可能性
- 403/404: CloudFront のOAC/OAI設定やデプロイ先のバケットが誤っている可能性
- Basic認証: 開発中は CloudFront Function によりBasic認証が有効化されています
