# Tasks: VPCネットワーク基盤の構築

**Input**: Design documents from `/specs/003-infra-vpc-network-setup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md

**Tests**: テストはAWS CDKの単体テストとして実装し、デプロイ後の動作確認を含む

**Organization**: インフラ構築のため、ユーザーストーリーごとに段階的にリソースを追加していく構成

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: このタスクが属するユーザーストーリー（US1, US2, US3, US4）
- 説明には正確なファイルパスを含める

## Path Conventions

このプロジェクトは既存の CDK インフラプロジェクト構造を使用:
- **infra/bin/**: CDK アプリエントリーポイント
- **infra/lib/stacks/**: スタック定義
- **infra/lib/constructs/**: 再利用可能なコンストラクト
- **infra/test/**: テスト

## Phase 1: Setup（セットアップ）

**目的**: CDK プロジェクトの初期化と基本構造の準備

- [x] T001 既存 infra/ ディレクトリに VPC スタック用のファイル構造を作成
- [x] T002 [P] infra/package.json に aws-ec2 依存関係が含まれていることを確認
- [x] T003 [P] infra/tsconfig.json が VPC スタック用の設定を含むことを確認
- [x] T004 [P] .gitignore に cdk.out/, node_modules/, .env が含まれることを確認

---

## Phase 2: Foundational（基盤構築）

**目的**: すべてのユーザーストーリーが依存する VPC とスタック基盤の構築

**⚠️ CRITICAL**: このフェーズが完了するまで、ユーザーストーリーの実装は開始できない

- [x] T005 VPC スタック定義を infra/lib/stacks/vpc-network-stack.ts に作成
- [x] T006 [P] VPC コンストラクトを infra/lib/constructs/vpc-construct.ts に作成
- [x] T007 infra/bin/app.ts に VpcNetworkStack をインポートして登録

**Checkpoint**: 基盤準備完了 - ユーザーストーリーの実装を並列で開始可能

---

## Phase 3: User Story 1 - 基本ネットワークインフラの構築 (Priority: P1) 🎯 MVP

**Goal**: VPC と3つのサブネット（パブリック、プライベート、アイソレート）を作成し、正しい CIDR ブロックを設定

**Independent Test**: AWS Console または CLI で VPC (10.16.0.0/16) と3つのサブネット（10.16.0.0/20, 10.16.32.0/20, 10.16.64.0/20）が存在することを確認

### 実装 for User Story 1

- [ ] T008 [US1] vpc-construct.ts で VPC (CIDR: 10.16.0.0/16) を作成
- [ ] T009 [US1] vpc-construct.ts にシングル AZ 設定（maxAzs: 1）を追加
- [ ] T010 [P] [US1] subnet-construct.ts でパブリックサブネット (CIDR: 10.16.0.0/20) を作成
- [ ] T011 [P] [US1] subnet-construct.ts でプライベートサブネット (CIDR: 10.16.32.0/20) を作成
- [ ] T012 [P] [US1] subnet-construct.ts でアイソレートサブネット (CIDR: 10.16.64.0/20) を作成
- [ ] T013 [US1] パブリックサブネットで mapPublicIpOnLaunch を有効化
- [ ] T014 [US1] vpc-network-stack.ts で VPC と3つのサブネットを統合
- [ ] T015 [US1] スタックレベルで統一タグ（Project, Environment, ManagedBy, Feature, CostCenter）を追加
- [ ] T016 [US1] 各リソースに識別可能な Name タグを追加

### テスト for User Story 1

- [ ] T017 [P] [US1] infra/test/vpc-network-stack.test.ts に VPC CIDR ブロックのテストを追加
- [ ] T018 [P] [US1] infra/test/vpc-network-stack.test.ts に3つのサブネット存在確認テストを追加
- [ ] T019 [P] [US1] infra/test/vpc-network-stack.test.ts にサブネット CIDR ブロックのテストを追加

### テンプレート生成確認 for User Story 1

- [ ] T020 [US1] cdk synth VpcNetworkStack を実行し CloudFormation テンプレートにエラーがないことを確認

**Checkpoint**: User Story 1 のコードとテストが完成、CDでデプロイ可能

---

## Phase 4: User Story 2 - インターネット接続の確立 (Priority: P2)

**Goal**: Internet Gateway を作成してパブリックサブネットに接続し、インターネットへの双方向通信を実現

**Independent Test**: パブリックサブネットに EC2 インスタンス（パブリック IP 付き）を起動し、インターネットからのアクセスが成功することを確認

### 実装 for User Story 2

- [ ] T024 [US2] gateway-construct.ts で Internet Gateway を作成
- [ ] T025 [US2] Internet Gateway を VPC にアタッチ
- [ ] T026 [US2] パブリックサブネット用のルートテーブルを作成 in infra/lib/constructs/route-table-construct.ts
- [ ] T027 [US2] パブリックルートテーブルに 0.0.0.0/0 → Internet Gateway のルートを追加
- [ ] T028 [US2] パブリックサブネットをパブリックルートテーブルに関連付け
- [ ] T029 [US2] vpc-network-stack.ts に Internet Gateway とルートテーブルを統合

### テスト for User Story 2

- [ ] T030 [P] [US2] infra/test/vpc-network-stack.test.ts に Internet Gateway 存在確認テストを追加
- [ ] T031 [P] [US2] infra/test/vpc-network-stack.test.ts にパブリックルートテーブルのルート設定テストを追加

### テンプレート生成確認 for User Story 2

- [ ] T032 [US2] cdk synth VpcNetworkStack を実行し CloudFormation テンプレートにエラーがないことを確認

**Checkpoint**: User Story 2 のコードとテストが完成、CDでデプロイ可能

---

## Phase 5: User Story 3 - プライベートリソースのインターネットアクセス確立 (Priority: P3)

**Goal**: NAT Gateway を作成してプライベートサブネットからインターネットへの外向き通信を実現

**Independent Test**: プライベートサブネットに EC2 インスタンス（パブリック IP なし）を起動し、NAT Gateway 経由で外部インターネットへの HTTP リクエストが成功することを確認

### 実装 for User Story 3

- [ ] T037 [US3] gateway-construct.ts で Elastic IP を作成
- [ ] T038 [US3] gateway-construct.ts でパブリックサブネットに NAT Gateway を作成
- [ ] T039 [US3] NAT Gateway に Elastic IP を関連付け
- [ ] T040 [US3] route-table-construct.ts でプライベートサブネット用のルートテーブルを作成
- [ ] T041 [US3] プライベートルートテーブルに 0.0.0.0/0 → NAT Gateway のルートを追加
- [ ] T042 [US3] プライベートサブネットをプライベートルートテーブルに関連付け
- [ ] T043 [US3] vpc-network-stack.ts に NAT Gateway とプライベートルートテーブルを統合

### テスト for User Story 3

- [ ] T044 [P] [US3] infra/test/vpc-network-stack.test.ts に NAT Gateway 存在確認テストを追加
- [ ] T045 [P] [US3] infra/test/vpc-network-stack.test.ts に Elastic IP 割り当て確認テストを追加
- [ ] T046 [P] [US3] infra/test/vpc-network-stack.test.ts にプライベートルートテーブルのルート設定テストを追加

### テンプレート生成確認 for User Story 3

- [ ] T047 [US3] cdk synth VpcNetworkStack を実行し CloudFormation テンプレートにエラーがないことを確認

**Checkpoint**: User Story 3 のコードとテストが完成、CDでデプロイ可能

---

## Phase 6: User Story 4 - データベースの完全隔離環境の構築 (Priority: P4)

**Goal**: アイソレートサブネット用のルートテーブルを作成し、外部通信を完全に遮断（VPC 内通信のみ許可）

**Independent Test**: アイソレートサブネットのルートテーブルに外部通信へのルートが存在せず、VPC ローカル通信（10.16.0.0/16）のみが許可されていることを確認

### 実装 for User Story 4

- [ ] T053 [US4] route-table-construct.ts でアイソレートサブネット用のルートテーブルを作成
- [ ] T054 [US4] アイソレートルートテーブルにはデフォルトルート（0.0.0.0/0）を追加しない（VPC ローカルのみ）
- [ ] T055 [US4] アイソレートサブネットをアイソレートルートテーブルに関連付け
- [ ] T056 [US4] vpc-network-stack.ts にアイソレートルートテーブルを統合

### テスト for User Story 4

- [ ] T057 [P] [US4] infra/test/vpc-network-stack.test.ts にアイソレートルートテーブル存在確認テストを追加
- [ ] T058 [P] [US4] infra/test/vpc-network-stack.test.ts にアイソレートルートテーブルにデフォルトルートが存在しないことのテストを追加

### テンプレート生成確認 for User Story 4

- [ ] T059 [US4] cdk synth VpcNetworkStack を実行し CloudFormation テンプレートにエラーがないことを確認

**Checkpoint**: User Story 4 のコードとテストが完成、CDでデプロイ可能

---

## Phase 7: Polish & Cross-Cutting Concerns（最終調整）

**目的**: 複数のユーザーストーリーに影響する改善と検証

- [ ] T060 [P] VPC スタック全体のスナップショットテストを infra/test/vpc-network-stack.test.ts に追加
- [ ] T061 [P] infra/README.md に VPC ネットワーク構成の説明を追加
- [ ] T062 コードに日本語コメントを追加（憲章 I. 日本語優先に準拠）
- [ ] T063 npm test を実行し全テストがパスすることを確認
- [ ] T064 cdk synth VpcNetworkStack でエラーがないことを確認
- [ ] T065 [P] 最終的な CloudFormation テンプレートを specs/003-infra-vpc-network-setup/cloudformation-template.json として保存（参照用）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし - すぐに開始可能
- **Foundational (Phase 2)**: Setup 完了に依存 - すべてのユーザーストーリーをブロック
- **User Stories (Phase 3-6)**: すべて Foundational フェーズ完了に依存
  - 各ユーザーストーリーは並列実行可能（リソースがあれば）
  - または優先順位順に順次実行（P1 → P2 → P3 → P4）
- **Polish (Phase 7)**: すべてのユーザーストーリー完了に依存

### User Story Dependencies

- **User Story 1 (P1)**: Foundational 完了後に開始可能 - 他ストーリーへの依存なし
- **User Story 2 (P2)**: Foundational 完了後に開始可能 - User Story 1 のサブネットを使用するが独立してテスト可能
- **User Story 3 (P3)**: Foundational 完了後に開始可能 - User Story 1, 2 のリソースを使用するが独立してテスト可能
- **User Story 4 (P4)**: Foundational 完了後に開始可能 - User Story 1 のサブネットを使用するが独立してテスト可能

### 各ユーザーストーリー内

- コンストラクト作成 → スタック統合 → テスト作成 → デプロイ → 動作確認
- 並列可能なタスク（[P] マーク）は同時実行可能
- デプロイ前にテストがパスすることを確認
- 各ストーリー完了後、次の優先度に移る前に独立して検証

### Parallel Opportunities

- Phase 1 の [P] マークタスク（T002, T003, T004）は並列実行可能
- Phase 2 の [P] マークタスク（T006）は T005 と並列実行可能
- 各ユーザーストーリー内の [P] マークタスク:
  - US1: T010, T011, T012（サブネット作成）と T017, T018, T019（テスト）
  - US2: T030, T031（テスト）
  - US3: T044, T045, T046（テスト）
  - US4: T057, T058（テスト）
- Foundational 完了後、複数の開発者がいれば User Story 1-4 を並列で作業可能

---

## Parallel Example: User Story 1

```bash
# User Story 1 のサブネット作成を並列で起動:
Task: "subnet-construct.ts でパブリックサブネット (CIDR: 10.16.0.0/20) を作成"
Task: "subnet-construct.ts でプライベートサブネット (CIDR: 10.16.32.0/20) を作成"
Task: "subnet-construct.ts でアイソレートサブネット (CIDR: 10.16.64.0/20) を作成"

# User Story 1 のテストを並列で起動:
Task: "infrastructure/test/vpc-network-stack.test.ts に VPC CIDR ブロックのテストを追加"
Task: "infrastructure/test/vpc-network-stack.test.ts に3つのサブネット存在確認テストを追加"
Task: "infrastructure/test/vpc-network-stack.test.ts にサブネット CIDR ブロックのテストを追加"
```

---

## Implementation Strategy

### MVP First (User Story 1 のみ)

1. Phase 1: Setup を完了
2. Phase 2: Foundational を完了（CRITICAL - すべてのストーリーをブロック）
3. Phase 3: User Story 1 を完了
4. **STOP and VALIDATE**: User Story 1 を独立してテスト
5. デプロイ/デモ準備完了

### Incremental Delivery

1. Setup + Foundational 完了 → 基盤準備完了
2. User Story 1 追加 → 独立テスト → CD でデプロイ（MVP!）
3. User Story 2 追加 → 独立テスト → CD でデプロイ（インターネット接続追加）
4. User Story 3 追加 → 独立テスト → CD でデプロイ（NAT Gateway 追加）
5. User Story 4 追加 → 独立テスト → CD でデプロイ（完全隔離環境追加）
6. 各ストーリーが前のストーリーを壊さずに価値を追加

### Parallel Team Strategy

複数の開発者がいる場合:

1. チーム全体で Setup + Foundational を完了
2. Foundational 完了後:
   - 開発者 A: User Story 1（VPC とサブネット）
   - 開発者 B: User Story 2（Internet Gateway）
   - 開発者 C: User Story 3（NAT Gateway）
   - 開発者 D: User Story 4（アイソレートサブネット）
3. 各ストーリーが独立して完了し、統合

---

## Notes

- **[P] タスク** = 異なるファイル、依存なし
- **[Story] ラベル** = 特定のユーザーストーリーへのタスクマッピング（トレーサビリティ）
- 各ユーザーストーリーは独立して完了・テスト可能
- テストは実装前に失敗することを確認
- 各タスクまたは論理的なグループ後にコミット
- 任意のチェックポイントで停止し、ストーリーを独立して検証可能
- 避けるべき: 曖昧なタスク、同一ファイルの競合、ストーリーの独立性を壊す相互依存

---

## Task Summary

- **Total Tasks**: 65
- **Setup Phase**: 4 tasks
- **Foundational Phase**: 3 tasks
- **User Story 1 (MVP)**: 13 tasks (実装・テスト・テンプレート生成)
- **User Story 2**: 7 tasks (実装・テスト・テンプレート生成)
- **User Story 3**: 11 tasks (実装・テスト・テンプレート生成)
- **User Story 4**: 7 tasks (実装・テスト・テンプレート生成)
- **Polish Phase**: 6 tasks
- **Parallel Opportunities**: 18 tasks marked with [P]

**注**: デプロイはCDで自動実行されるため、実装とテストに集中

---

## Suggested MVP Scope

**推奨 MVP**: Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (User Story 1)

これにより以下が実現されます:
- VPC (10.16.0.0/16) の作成
- 3つのサブネット（パブリック、プライベート、アイソレート）の作成
- 正しい CIDR ブロック設定
- 基本的なタグ付け
- 単体テスト
- CloudFormation テンプレート生成確認

**合計: 20タスク** でMVPが完成（デプロイはCDで自動実行）

後続のフェーズで段階的に機能を追加:
- Phase 4: インターネット接続
- Phase 5: NAT Gateway
- Phase 6: 完全隔離環境
