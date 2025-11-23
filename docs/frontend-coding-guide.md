# Loanpedia Frontend Coding Guide


本ドキュメントは、Loanpedia フロントエンド開発における
コーディング規約・ベストプラクティスをまとめたガイドです。

---

## 目次

1. [基本方針](#1-基本方針)
2. [TypeScript](#2-typescript)
3. [React コンポーネント](#3-react-コンポーネント)
4. [スタイリング（TailwindCSS）](#4-スタイリングtailwindcss)
5. [状態管理](#5-状態管理)
6. [フォーム](#6-フォーム)
7. [ルーティング](#7-ルーティング)
8. [テスト](#8-テスト)
9. [ファイル・ディレクトリ構成](#9-ファイルディレクトリ構成)
10. [インポート順序](#10-インポート順序)
11. [コメント・ドキュメント](#11-コメントドキュメント)
12. [パフォーマンス](#12-パフォーマンス)
13. [アクセシビリティ](#13-アクセシビリティ)
14. [禁止事項](#14-禁止事項)

---

## 1. 基本方針

### コード品質の優先順位

1. **可読性** - 他の開発者が理解しやすいコード
2. **保守性** - 変更・拡張が容易な構造
3. **型安全性** - TypeScript の型システムを最大活用
4. **パフォーマンス** - 必要な場合のみ最適化

### ツールチェーン

| ツール | 用途 | コマンド |
|--------|------|----------|
| ESLint | 静的解析 | `npm run lint` |
| Prettier | コードフォーマット | `npm run format` |
| TypeScript | 型チェック | `npm run build` |
| Vitest | テスト | `npm run test` |

### 自動化

- コミット前に `npm run lint` と `npm run format` を実行
- CI/CD で全チェックを自動実行

---

## 2. TypeScript

### 厳格モード

`tsconfig.json` で `strict: true` を有効化しています。

```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### 型定義

```typescript
// Good: 明示的な型定義
type User = {
  id: string;
  name: string;
  email: string;
};

// Good: オブジェクト型は type を使用
type LoanProduct = {
  id: string;
  name: string;
  interestRate: number;
};

// Good: Union型
type LoanCategory = 'housing' | 'car' | 'education' | 'business';

// Good: interfaceは拡張が必要な場合のみ
interface ApiResponse<T> {
  data: T;
  status: number;
}
```

### 型の使い分け

| 用途 | 推奨 |
|------|------|
| オブジェクト型 | `type` |
| Union / Intersection | `type` |
| 関数の引数・戻り値 | インライン or `type` |
| 拡張が必要なもの | `interface` |
| Enumの代替 | `as const` オブジェクト |

### 型アサーション

```typescript
// Bad: as による型アサーション（避ける）
const value = someValue as string;

// Good: 型ガードを使用
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

if (isString(value)) {
  console.log(value.toUpperCase());
}

// 許容: 非nullアサーション（DOM要素取得時など）
const element = document.getElementById('root')!;
```

### any の禁止

```typescript
// Bad: any を使用
function process(data: any) { ... }

// Good: unknown + 型ガード
function process(data: unknown) {
  if (isValidData(data)) {
    // 型安全に処理
  }
}

// Good: ジェネリクスを使用
function process<T>(data: T) { ... }
```

### 未使用変数

```typescript
// eslint: @typescript-eslint/no-unused-vars
// アンダースコアプレフィックスで未使用を明示

// Good: 未使用の引数は _ プレフィックス
const handleClick = (_event: MouseEvent) => {
  doSomething();
};

// Good: 分割代入で一部のみ使用
const { id, _name } = user;
```

---

## 3. React コンポーネント

### コンポーネント定義

```tsx
// 推奨: アロー関数 + named export
export const MyComponent = () => {
  return <div>Content</div>;
};

// Props がある場合
type Props = {
  title: string;
  onAction: () => void;
  children?: React.ReactNode;
};

export const MyComponent = ({ title, onAction, children }: Props) => {
  return (
    <div>
      <h1>{title}</h1>
      <button onClick={onAction}>Action</button>
      {children}
    </div>
  );
};
```

### Props の型定義

```tsx
// Good: 型エイリアスを使用
type Props = {
  /** ボタンのラベル */
  label: string;
  /** クリック時のコールバック */
  onClick: () => void;
  /** 無効状態 */
  disabled?: boolean;
  /** バリアント */
  variant?: 'primary' | 'secondary';
};

// Good: children を含む場合
type Props = {
  title: string;
  children: React.ReactNode;
};

// Good: HTMLの属性を継承
type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary';
};
```

### コンポーネントの分類

| 種類 | 場所 | 特徴 |
|------|------|------|
| Page | `features/*/pages/` | ルーティング対象、データ取得 |
| Feature Component | `features/*/components/` | 機能固有のUI |
| Layout | `shared/components/layout/` | ページ構造（Header, Footer） |
| UI | `shared/components/ui/` | 汎用的なUI部品 |

### Hooks

```tsx
// Good: カスタムフックは use プレフィックス
export const useLoanSearch = (params: SearchParams) => {
  const [results, setResults] = useState<Loan[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // ...

  return { results, isLoading };
};

// Good: フックの呼び出しはコンポーネントのトップレベル
export const SearchPage = () => {
  const { results, isLoading } = useLoanSearch(params);
  const [query, setQuery] = useState('');

  // ...
};
```

### イベントハンドラ

```tsx
// Good: handle プレフィックス
const handleClick = () => { ... };
const handleSubmit = (e: React.FormEvent) => { ... };
const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => { ... };

// Good: Props の場合は on プレフィックス
type Props = {
  onClick: () => void;
  onSubmit: (data: FormData) => void;
};
```

### 条件付きレンダリング

```tsx
// Good: 早期リターン
if (isLoading) {
  return <LoadingSpinner />;
}

if (error) {
  return <ErrorMessage error={error} />;
}

return <MainContent data={data} />;

// Good: 短い条件は && 演算子
return (
  <div>
    {isVisible && <Modal />}
    {items.length > 0 && <ItemList items={items} />}
  </div>
);

// Good: 三項演算子は単純な場合のみ
return (
  <button className={isActive ? 'bg-blue-500' : 'bg-gray-500'}>
    {isLoading ? 'Loading...' : 'Submit'}
  </button>
);
```

---

## 4. スタイリング（TailwindCSS）

### 基本方針

- TailwindCSS のユーティリティクラスを優先
- インラインスタイルは使用しない
- CSS ファイルは最小限に

### クラスの記述順序

```tsx
// 推奨順序:
// 1. レイアウト (display, position, flex, grid)
// 2. サイズ (width, height, padding, margin)
// 3. タイポグラフィ (font, text)
// 4. 背景・ボーダー
// 5. エフェクト (shadow, opacity)
// 6. インタラクティブ (hover, focus)

<div className="flex items-center justify-between p-4 text-lg font-bold bg-white border rounded-lg shadow-md hover:shadow-lg">
  Content
</div>
```

### レスポンシブデザイン

```tsx
// モバイルファースト
<div className="
  p-4
  md:p-6
  lg:p-8
">
  <h1 className="
    text-xl
    md:text-2xl
    lg:text-3xl
  ">
    Title
  </h1>
</div>
```

### ブレークポイント

| プレフィックス | 画面幅 | デバイス |
|---------------|--------|----------|
| (なし) | 0px~ | モバイル |
| `sm:` | 640px~ | 小型タブレット |
| `md:` | 768px~ | タブレット |
| `lg:` | 1024px~ | デスクトップ |
| `xl:` | 1280px~ | 大型デスクトップ |

### カラーパレット

```tsx
// プロジェクト共通カラー（tailwind.config.js で定義予定）
// プライマリ: blue-600
// セカンダリ: gray-600
// アクセント: green-500
// エラー: red-500
// 警告: yellow-500

<button className="bg-blue-600 hover:bg-blue-700 text-white">
  Primary Button
</button>
```

### 長いクラス名の整理

```tsx
// Bad: 1行に長すぎるクラス
<div className="flex items-center justify-between p-4 mb-4 text-lg font-bold bg-white border border-gray-200 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200">

// Good: 改行して整理
<div
  className="
    flex items-center justify-between
    p-4 mb-4
    text-lg font-bold
    bg-white border border-gray-200 rounded-lg
    shadow-md hover:shadow-lg
    transition-shadow duration-200
  "
>
```

---

## 5. 状態管理

### ローカル状態

```tsx
// useState: コンポーネント内の単純な状態
const [isOpen, setIsOpen] = useState(false);
const [query, setQuery] = useState('');

// useReducer: 複雑な状態ロジック
const [state, dispatch] = useReducer(reducer, initialState);
```

### 状態の配置

| 状態の種類 | 配置場所 |
|-----------|----------|
| UIの一時的な状態 | コンポーネント内 useState |
| フォーム状態 | React Hook Form |
| サーバーデータ | React Query（将来） |
| グローバル状態 | Zustand（将来） |

### 状態の持ち上げ

```tsx
// 子コンポーネント間で状態を共有する場合は親に持ち上げ
const ParentComponent = () => {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <>
      <ListComponent selectedId={selectedId} onSelect={setSelectedId} />
      <DetailComponent selectedId={selectedId} />
    </>
  );
};
```

---

## 6. フォーム

### React Hook Form

```tsx
import { useForm } from 'react-hook-form';

type FormValues = {
  email: string;
  password: string;
};

export const LoginForm = () => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>();

  const onSubmit = async (data: FormValues) => {
    // API呼び出し
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input
        type="email"
        {...register('email', {
          required: 'メールアドレスは必須です',
          pattern: {
            value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
            message: '有効なメールアドレスを入力してください',
          },
        })}
      />
      {errors.email && <span>{errors.email.message}</span>}

      <input
        type="password"
        {...register('password', {
          required: 'パスワードは必須です',
          minLength: {
            value: 8,
            message: 'パスワードは8文字以上で入力してください',
          },
        })}
      />
      {errors.password && <span>{errors.password.message}</span>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? '送信中...' : 'ログイン'}
      </button>
    </form>
  );
};
```

---

## 7. ルーティング

### React Router v6

```tsx
// app/router.tsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { LandingPage } from '@/features/landing/pages/LandingPage';
import { LoanSearchPage } from '@/features/loanSearch/pages/LoanSearchPage';
import { LoanDetailPage } from '@/features/loanDetail/pages/LoanDetailPage';

const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/search',
    element: <LoanSearchPage />,
  },
  {
    path: '/loans/:id',
    element: <LoanDetailPage />,
  },
]);

export const AppRouter = () => <RouterProvider router={router} />;
```

### ナビゲーション

```tsx
import { Link, useNavigate, useParams } from 'react-router-dom';

// リンク
<Link to="/search">検索ページへ</Link>
<Link to={`/loans/${loan.id}`}>詳細を見る</Link>

// プログラマティックナビゲーション
const navigate = useNavigate();
navigate('/search');
navigate(-1); // 戻る

// パラメータ取得
const { id } = useParams<{ id: string }>();
```

---

## 8. テスト

### テストファイルの配置

```
src/
├── components/
│   ├── Button.tsx
│   └── Button.test.tsx  # 同じディレクトリに配置
└── test/
    └── setup.ts         # グローバル設定
```

### コンポーネントテスト

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    await userEvent.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

### テストの命名規則

```tsx
describe('ComponentName', () => {
  describe('when condition', () => {
    it('should do something', () => { ... });
  });
});

// または
describe('ComponentName', () => {
  it('renders correctly', () => { ... });
  it('handles click event', () => { ... });
  it('shows error state when invalid', () => { ... });
});
```

### テストのベストプラクティス

- ユーザーの視点でテスト（実装詳細ではなく振る舞い）
- `getByRole`, `getByLabelText` を優先
- `getByTestId` は最終手段

---

## 9. ファイル・ディレクトリ構成

### 命名規則

| 種類 | 規則 | 例 |
|------|------|-----|
| ディレクトリ | camelCase | `loanSearch/` |
| コンポーネント | PascalCase | `LoanCard.tsx` |
| フック | camelCase + use | `useLoanSearch.ts` |
| ユーティリティ | camelCase | `formatCurrency.ts` |
| 型定義 | camelCase | `types.ts` |
| 定数 | camelCase | `constants.ts` |
| テスト | 元ファイル名 + .test | `LoanCard.test.tsx` |

### Feature モジュール構造

```
features/loanSearch/
├── components/           # UI コンポーネント
│   ├── SearchForm.tsx
│   ├── SearchResults.tsx
│   └── LoanCard.tsx
├── pages/                # ページコンポーネント
│   └── LoanSearchPage.tsx
├── hooks/                # カスタムフック
│   └── useLoanSearch.ts
├── api/                  # API通信
│   └── loanApi.ts
├── types/                # 型定義
│   └── index.ts
└── index.ts              # Public exports
```

### index.ts によるエクスポート

```typescript
// features/loanSearch/index.ts
export { LoanSearchPage } from './pages/LoanSearchPage';
export { useLoanSearch } from './hooks/useLoanSearch';
export type { SearchParams, SearchResult } from './types';
```

---

## 10. インポート順序

```tsx
// 1. React
import { useState, useEffect } from 'react';

// 2. 外部ライブラリ
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';

// 3. 内部モジュール（絶対パス）
import { Button } from '@/shared/components/ui/Button';
import { useLoanSearch } from '@/features/loanSearch';

// 4. 相対パス（同一feature内）
import { SearchForm } from '../components/SearchForm';

// 5. 型（type import）
import type { Loan } from '@/shared/types';

// 6. スタイル・アセット
import './styles.css';
```

---

## 11. コメント・ドキュメント

### JSDoc コメント

```tsx
/**
 * ローンカードコンポーネント
 *
 * @example
 * <LoanCard
 *   loan={loanData}
 *   onFavorite={handleFavorite}
 * />
 */
export const LoanCard = ({ loan, onFavorite }: Props) => { ... };
```

### インラインコメント

```tsx
// Good: 「なぜ」を説明
// 金利は小数点以下2桁で表示（金融庁ガイドライン準拠）
const formattedRate = rate.toFixed(2);

// Bad: 「何を」しているかの説明（コードで自明）
// 金利を2桁に丸める
const formattedRate = rate.toFixed(2);
```

### TODO コメント

```tsx
// TODO: APIエンドポイント実装後に実データに切り替え
const mockData = [...];

// FIXME: パフォーマンス改善が必要
// HACK: 一時的な回避策（Issue #123 で対応予定）
```

---

## 12. パフォーマンス

### React.memo

```tsx
// 再レンダリングを防ぎたい場合のみ使用
export const ExpensiveComponent = React.memo(({ data }: Props) => {
  // 重い計算処理
  return <div>{/* ... */}</div>;
});
```

### useMemo / useCallback

```tsx
// useMemo: 計算コストが高い値
const sortedItems = useMemo(() => {
  return items.sort((a, b) => a.name.localeCompare(b.name));
}, [items]);

// useCallback: 子コンポーネントに渡すコールバック
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);
```

### 遅延読み込み

```tsx
import { lazy, Suspense } from 'react';

// ルートレベルでのコード分割
const LoanDetailPage = lazy(() => import('./pages/LoanDetailPage'));

// 使用時
<Suspense fallback={<LoadingSpinner />}>
  <LoanDetailPage />
</Suspense>
```

---

## 13. アクセシビリティ

### 基本原則

```tsx
// セマンティックなHTML要素を使用
<button>ボタン</button>  // Good
<div onClick={...}>ボタン</div>  // Bad

// 適切なラベル
<label htmlFor="email">メールアドレス</label>
<input id="email" type="email" />

// alt属性
<img src="..." alt="青森銀行のロゴ" />

// aria属性（必要な場合）
<button aria-label="メニューを開く" aria-expanded={isOpen}>
  <MenuIcon />
</button>
```

### フォーカス管理

```tsx
// フォーカス可能な要素の順序を適切に
// tabIndex は 0 または -1 のみ使用
<button tabIndex={0}>フォーカス可能</button>
<div tabIndex={-1}>プログラムからのみフォーカス可能</div>
```

### カラーコントラスト

- テキストと背景のコントラスト比: 4.5:1 以上
- 大きなテキスト（18px以上）: 3:1 以上

---

## 14. 禁止事項

### 絶対禁止

```tsx
// any の使用
function process(data: any) { ... }  // Bad

// インラインスタイル
<div style={{ color: 'red' }}>  // Bad

// dangerouslySetInnerHTML（XSS脆弱性）
<div dangerouslySetInnerHTML={{ __html: userInput }} />  // Bad

// console.log の本番コード残留
console.log('debug');  // Bad（開発時のみ）
```

### 非推奨

```tsx
// クラスコンポーネント
class MyComponent extends React.Component { ... }  // 避ける

// defaultProps（型で代替）
MyComponent.defaultProps = { ... };  // 避ける

// PropTypes（TypeScriptで代替）
import PropTypes from 'prop-types';  // 避ける

// 過度なネスト
{condition1 && condition2 && condition3 && <Component />}  // 避ける
```

---

## 参考資料

- [React 公式ドキュメント](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [TailwindCSS ドキュメント](https://tailwindcss.com/docs)
- [Testing Library ドキュメント](https://testing-library.com/docs/)
- [React Hook Form ドキュメント](https://react-hook-form.com/)
