# Tasks: Route53 パブリックホストゾーン作成

**Input**: Design documents from `/specs/001-route53-hosted-zone/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: CDK Assertionsを使用した単体テストを含みます（quickstart.mdに記載）

**Organization**: このフィーチャーは単一のUser Story（DNS管理基盤の確立）で構成されています。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: このタスクが属するユーザーストーリー（例: US1）
- ファイルパスを明示

## Path Conventions

- **Infrastructure Code**: `infra/lib/`, `infra/bin/`, `infra/test/` at repository root
- パスはplan.mdの構造に基づく

---

## Phase 1: Setup (共有インフラストラクチャ)

**Purpose**: プロジェクト初期化と基本構造の確認

- [x] T001 既存のCDKプロジェクト構造を確認（infra/ディレクトリ）
- [x] T002 [P] TypeScript依存関係を確認（aws-cdk-lib 2.215.0がインストール済み）
- [x] T003 [P] CDK環境変数を確認（AWS認証情報、CDK_DEFAULT_ACCOUNTなど）

---

## Phase 2: Foundational (ブロッキング前提条件)

**Purpose**: このフィーチャーはインフラ定義のみのため、foundationalタスクは不要

**⚠️ 注**: このフィーチャーには他のストーリーをブロックするfoundationalタスクはありません。User Story 1の実装に直接進めます。

---

## Phase 3: User Story 1 - DNS管理基盤の確立 (Priority: P1) 🎯 MVP

**Goal**: loanpedia.jpドメインのDNS管理をAWS Route53で行えるようにし、お名前.comとの統合基盤を確立する

**Independent Test**:
1. Route53コンソールでloanpedia.jpのホストゾーンが作成されている
2. CloudFormation Outputsから4つのネームサーバーが取得できる
3. CDKテストがすべてパスする
4. `cdk synth Route53Stack` が成功する

### Tests for User Story 1

> **NOTE: テストを先に作成し、実装前にFAILすることを確認**

- [x] T004 [P] [US1] Route53Stackの単体テストを作成 in infra/test/route53-stack.test.ts
  - PublicHostedZone が loanpedia.jp で作成されることを確認
  - ネームサーバーOutputsが存在することを確認
  - HostedZoneId Outputが存在することを確認

### Implementation for User Story 1

- [x] T005 [US1] Route53Stackファイルを作成 in infra/lib/route53-stack.ts
  - PublicHostedZoneを定義（zoneName: 'loanpedia.jp'）
  - ネームサーバー情報を個別にCfnOutputで出力（NameServer1-4）
  - HostedZoneIdをCfnOutputで出力（exportName: 'LoanpediaHostedZoneId'）
  - コメントを日本語で記述

- [x] T006 [US1] エントリポイントを更新 in infra/bin/loanpedia-app.ts
  - Route53Stackをインポート
  - Route53Stackをインスタンス化（既存GitHubOidcStackの後）
  - 環境変数（account, region）を設定

- [x] T007 [US1] CDKテストを実行して確認
  - `cd infra && npm test` を実行
  - すべてのテストがパスすることを確認

- [x] T008 [US1] CloudFormationテンプレートを生成して確認
  - `cd infra && cdk synth Route53Stack` を実行
  - 生成されたテンプレートでRoute53::HostedZoneリソースを確認
  - Outputsセクションにネームサーバー情報があることを確認

**Checkpoint**: この時点で、User Story 1は完全に機能し、独立してテスト可能です

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: 複数のユーザーストーリーに影響する改善（このフィーチャーではUser Story 1のみだが、将来の拡張性のため）

- [x] T009 [P] コードの最終レビューとリファクタリング
  - TypeScriptの型定義が適切か確認
  - コメントが日本語で記述されているか確認
  - 不要なコードを削除

- [x] T010 [P] ドキュメントの最終確認
  - quickstart.mdの手順が正確か確認
  - research.mdの決定事項が実装に反映されているか確認

- [x] T011 quickstart.mdの検証手順を実行
  - ステップ4のテスト実行
  - ステップ5のCloudFormationテンプレート確認
  - デプロイは行わない（本番環境への影響を避けるため）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存関係なし - すぐに開始可能
- **Foundational (Phase 2)**: スキップ（該当なし）
- **User Story 1 (Phase 3)**: Setup完了後に開始可能
- **Polish (Phase 4)**: User Story 1完了後に開始可能

### User Story Dependencies

- **User Story 1 (P1)**: Setup (Phase 1)完了後に開始可能 - 他のストーリーへの依存なし

### Within User Story 1

1. **T004**: テストを先に作成（implementation前にFAILすることを確認）
2. **T005**: Route53Stack実装（テストと並列可能）
3. **T006**: エントリポイント更新（T005に依存）
4. **T007**: テスト実行（T005, T006に依存）
5. **T008**: CDK synth実行（T005, T006に依存）

### Parallel Opportunities

- **Phase 1**: T002とT003は並列実行可能
- **Phase 3**: T004（テスト作成）とT005（実装）は並列実行可能
- **Phase 4**: T009とT010は並列実行可能

---

## Parallel Example: User Story 1

```bash
# Phase 1: Setup tasks in parallel
Task: "TypeScript依存関係を確認（aws-cdk-lib 2.215.0がインストール済み）"
Task: "CDK環境変数を確認（AWS認証情報、CDK_DEFAULT_ACCOUNTなど）"

# Phase 3: Tests and implementation in parallel
Task: "Route53Stackの単体テストを作成 in infra/test/route53-stack.test.ts"
Task: "Route53Stackファイルを作成 in infra/lib/route53-stack.ts"

# Phase 4: Polish tasks in parallel
Task: "コードの最終レビューとリファクタリング"
Task: "ドキュメントの最終確認"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → 環境確認完了
2. Complete Phase 3: User Story 1 → DNS管理基盤確立
   - テスト作成 → 実装 → 検証
3. **STOP and VALIDATE**: User Story 1を独立してテスト
   - CDKテストがパスすることを確認
   - CloudFormationテンプレートが正しく生成されることを確認
4. Complete Phase 4: Polish → 最終確認
5. デプロイ準備完了（本番デプロイは別タスク）

### デプロイ戦略（実装後）

User Story 1完了後、以下の手順でデプロイ：

1. `cdk deploy Route53Stack` を実行
2. CloudFormation Outputsから4つのネームサーバー情報を取得
3. お名前.comでネームサーバーを手動で変更（quickstart.md参照）
4. DNS浸透を確認（`nslookup loanpedia.jp`）

---

## Task Summary

### Total Tasks: 11

**Phase 1 (Setup)**: 3 tasks
- Parallel: 2 tasks (T002, T003)

**Phase 2 (Foundational)**: 0 tasks（スキップ）

**Phase 3 (User Story 1)**: 5 tasks
- Parallel: 2 tasks (T004, T005)

**Phase 4 (Polish)**: 3 tasks
- Parallel: 2 tasks (T009, T010)

### Tasks per User Story

- **User Story 1 (DNS管理基盤の確立)**: 5 tasks
  - 1 test task
  - 4 implementation tasks

### Parallel Opportunities

- Phase 1: 2 tasks can run in parallel
- Phase 3: 2 tasks can run in parallel (test creation + implementation)
- Phase 4: 2 tasks can run in parallel

### Independent Test Criteria

**User Story 1**:
1. ✅ CDKテストがすべてパスする
2. ✅ CloudFormationテンプレートが正しく生成される
3. ✅ Route53::HostedZoneリソースがloanpedia.jpで定義される
4. ✅ 4つのネームサーバーOutputsが存在する

### Suggested MVP Scope

**MVP = User Story 1のみ**

Phase 1 (Setup) + Phase 3 (User Story 1) + Phase 4 (Polish) を完了すれば、Route53パブリックホストゾーンが作成され、お名前.comとの統合準備が整います。これで最小限の価値を提供できます。

---

## Format Validation

✅ すべてのタスクがチェックリスト形式に従っています：
- Checkbox: `- [ ]`
- Task ID: T001-T011（実行順）
- [P] marker: 並列実行可能なタスクに付与
- [Story] label: User Story 1のタスクに[US1]を付与
- Description: ファイルパスを含む明確なアクション

---

## Notes

- [P] タスク = 異なるファイル、依存関係なし
- [US1] ラベル = User Story 1へのトレーサビリティ
- User Story 1は独立して完成・テスト可能
- 実装前にテストがFAILすることを確認
- 各タスクまたは論理グループごとにコミット
- チェックポイントで独立してストーリーを検証
- 回避事項: 曖昧なタスク、同一ファイルの競合、ストーリー間の不要な依存関係
