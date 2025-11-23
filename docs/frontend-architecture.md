# Loanpedia Frontend Architecture

Loanpedia は、青森県内の金融機関が提供するローン商品を横断検索・比較できる
Web フロントエンド SPA（Single Page Application）です。

本書は、Loanpedia フロントエンドのアーキテクチャ設計、技術選定、ディレクトリ構造、
開発指針などをまとめた技術文書です。

---

## 1. Overview（概要）

Loanpedia の目的は、ローン選びに時間がかかるユーザーの意思決定をサポートすることです。

- 金利・返済額・条件の横断比較
- 直感的でわかりやすい UI
- 地域の金融機関に特化した情報提供
- 将来的にスクレイピングデータと連動した自動更新

本プロジェクトは以下の3つの画面を中心に構成されます。

1. **Landing Page（LP）** - サービス紹介・検索への導線
2. **Loan Search（検索）** - ローン商品の検索・一覧表示
3. **Loan Detail（詳細）** - 個別ローン商品の詳細情報

---

## 2. 技術スタック

### Frontend Core
| 技術 | バージョン | 用途 |
|------|-----------|------|
| React | 18.3.x | UIフレームワーク |
| TypeScript | 5.6.x | 型安全な開発 |
| Vite | 6.x | ビルドツール・開発サーバー |
| TailwindCSS | 4.x | ユーティリティファーストCSS |

### Routing & Forms
| 技術 | バージョン | 用途 |
|------|-----------|------|
| React Router DOM | 6.28.x | クライアントサイドルーティング |
| React Hook Form | 7.53.x | フォーム状態管理・バリデーション |

### Testing
| 技術 | バージョン | 用途 |
|------|-----------|------|
| Vitest | 2.x | テストランナー |
| Testing Library | 16.x | コンポーネントテスト |
| jsdom | 25.x | DOM環境エミュレーション |

### 将来的導入予定
| 技術 | 用途 |
|------|------|
| React Query (TanStack Query) | サーバー状態管理・キャッシュ |
| Zustand | クライアント状態管理 |

### Build & Deploy
- **S3** - SPAの静的ホスティング
- **CloudFront** - CDN + キャッシュ最適化
- **GitHub Actions** - CI/CD パイプライン

### キャッシュポリシー
| リソース | キャッシュ設定 |
|----------|---------------|
| index.html | no-cache（常に最新） |
| アセット（JS/CSS） | 1年キャッシュ（ハッシュ付きファイル名） |
| CloudFront | 毎デプロイ時に invalidation 実行 |

---

## 3. アーキテクチャパターン

Loanpedia は **Feature-Sliced Design (FSD)** を簡略化した構造を採用しています。
機能単位で閉じた構造にすることで、拡張性・可読性・保守性を高めます。

### FSD の基本レイヤー

```
src/
├── app/        # アプリケーション全体の設定（ルーティング、プロバイダー）
├── features/   # 機能単位のモジュール（各画面・機能）
├── shared/     # 共有リソース（コンポーネント、ユーティリティ）
└── test/       # テスト設定・ヘルパー
```

### 設計原則

1. **単方向依存** - `features/` → `shared/` への依存のみ許可
2. **機能の独立性** - 各 feature は他の feature に依存しない
3. **共有リソースの抽出** - 2箇所以上で使用するものは `shared/` へ

---

## 4. ディレクトリ構成

```
frontend/
├── src/
│   ├── app/                          # アプリケーション設定
│   │   └── router.tsx                # ルーティング定義
│   │
│   ├── features/                     # 機能モジュール
│   │   ├── landing/                  # LP機能
│   │   │   ├── components/           # LP専用コンポーネント
│   │   │   │   ├── HeroSection.tsx
│   │   │   │   ├── ReasonSection.tsx
│   │   │   │   ├── PopularLoanTypesSection.tsx
│   │   │   │   └── FinalCtaSection.tsx
│   │   │   └── pages/
│   │   │       └── LandingPage.tsx   # LPページコンポーネント
│   │   │
│   │   ├── loanSearch/               # 検索機能
│   │   │   └── pages/
│   │   │       └── LoanSearchPage.tsx
│   │   │
│   │   └── loanDetail/               # 詳細機能
│   │       └── pages/
│   │           └── LoanDetailPage.tsx
│   │
│   ├── shared/                       # 共有リソース
│   │   ├── components/
│   │   │   ├── layout/               # レイアウトコンポーネント
│   │   │   │   ├── Header.tsx
│   │   │   │   └── Footer.tsx
│   │   │   └── ui/                   # 汎用UIコンポーネント
│   │   │       └── (Button, Card, etc.)
│   │   └── lib/                      # ユーティリティ関数
│   │       └── (utils, constants, etc.)
│   │
│   ├── test/                         # テスト設定
│   │   └── setup.ts                  # Vitest セットアップ
│   │
│   ├── App.tsx                       # ルートコンポーネント
│   ├── App.test.tsx                  # ルートコンポーネントテスト
│   ├── main.tsx                      # エントリーポイント
│   └── index.css                     # グローバルスタイル
│
├── index.html                        # HTMLテンプレート
├── package.json                      # 依存関係
├── tsconfig.json                     # TypeScript設定
├── vite.config.ts                    # Vite設定
├── tailwind.config.js                # TailwindCSS設定
├── postcss.config.js                 # PostCSS設定
└── eslint.config.js                  # ESLint設定
```

---

## 5. Feature モジュール構造

各 feature は以下の構造を持ちます：

```
features/{featureName}/
├── components/     # feature専用のUIコンポーネント
├── pages/          # ページコンポーネント（ルーティング対象）
├── hooks/          # feature専用のカスタムフック（必要時）
├── api/            # API通信ロジック（必要時）
├── types/          # feature専用の型定義（必要時）
└── index.ts        # Public API（エクスポート）
```

### 命名規則

| 種類 | 命名規則 | 例 |
|------|---------|-----|
| ページコンポーネント | PascalCase + Page | `LoanSearchPage.tsx` |
| 通常コンポーネント | PascalCase | `HeroSection.tsx` |
| フック | camelCase + use | `useLoanSearch.ts` |
| ユーティリティ | camelCase | `formatCurrency.ts` |

---

## 6. 開発ガイドライン

### コンポーネント設計

```tsx
// 推奨：関数コンポーネント + TypeScript
type Props = {
  title: string;
  onAction: () => void;
};

export function MyComponent({ title, onAction }: Props) {
  return (
    <div>
      <h1>{title}</h1>
      <button onClick={onAction}>Action</button>
    </div>
  );
}
```

### スタイリング

- TailwindCSS のユーティリティクラスを優先
- 複雑なスタイルは `@apply` でカスタムクラス化
- レスポンシブ対応は Tailwind のブレークポイントを使用

```tsx
// レスポンシブ例
<div className="p-4 md:p-6 lg:p-8">
  <h1 className="text-xl md:text-2xl lg:text-3xl">Title</h1>
</div>
```

### テスト方針

```tsx
// コンポーネントテスト例
import { render, screen } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders title correctly', () => {
    render(<MyComponent title="Test" onAction={() => {}} />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

---

## 7. 開発コマンド

```bash
# 開発サーバー起動
npm run dev

# ビルド（型チェック + プロダクションビルド）
npm run build

# プレビュー（ビルド結果の確認）
npm run preview

# テスト実行
npm run test

# テスト（ウォッチモード）
npm run test:watch

# リント
npm run lint
npm run lint:fix

# フォーマット
npm run format
npm run format:check
```

---

## 8. ルーティング設計

| パス | ページ | 説明 |
|------|--------|------|
| `/` | LandingPage | トップページ（LP） |
| `/search` | LoanSearchPage | ローン検索・一覧 |
| `/loans/:id` | LoanDetailPage | ローン詳細 |

### 将来的な拡張

| パス | ページ | 説明 |
|------|--------|------|
| `/login` | LoginPage | ログイン |
| `/register` | RegisterPage | 新規登録 |
| `/favorites` | FavoritesPage | お気に入り一覧 |
| `/account` | AccountPage | アカウント設定 |

---

## 9. API連携（将来実装）

### ディレクトリ構造

```
shared/
└── api/
    ├── client.ts       # APIクライアント設定
    ├── endpoints.ts    # エンドポイント定義
    └── types.ts        # 共通レスポンス型
```

### React Query 導入後

```tsx
// features/loanSearch/api/useLoanSearch.ts
export function useLoanSearch(params: SearchParams) {
  return useQuery({
    queryKey: ['loans', 'search', params],
    queryFn: () => fetchLoans(params),
  });
}
```

---

## 10. パフォーマンス指針

### バンドル最適化
- コード分割（React.lazy + Suspense）
- Tree shaking による未使用コード削除
- 画像最適化（WebP、遅延読み込み）

### ランタイム最適化
- React.memo による不要な再レンダリング防止
- useMemo / useCallback の適切な使用
- 仮想スクロール（大量データ表示時）

### 目標メトリクス
| 指標 | 目標値 |
|------|--------|
| LCP (Largest Contentful Paint) | < 2.5s |
| FID (First Input Delay) | < 100ms |
| CLS (Cumulative Layout Shift) | < 0.1 |

---

## 11. 関連ドキュメント

- [機能概要](./features-overview.md) - 機能要件の詳細
- [画面仕様書](./screen-specification.md) - UI/UX設計
- [API仕様書](./api-specification.md) - バックエンドAPI定義
- [データベース設計](./database/database-design.md) - データモデル
