// eslint.config.mjs
import js from '@eslint/js';
import tsParser from '@typescript-eslint/parser';
import tseslint from '@typescript-eslint/eslint-plugin';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import jsxA11y from 'eslint-plugin-jsx-a11y';
// フラットconfig用のエントリを使う
import eslintConfigPrettier from 'eslint-config-prettier';

export default [
  // 共通で無視するパス
  {
    ignores: ['dist', 'node_modules'],
  },

  // JS/TS 共通ルール（バグ系＋React系）
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        document: 'readonly',
        window: 'readonly',
      },
    },
    plugins: {
      '@typescript-eslint': tseslint,
      react,
      'react-hooks': reactHooks,
      'jsx-a11y': jsxA11y,
    },
    rules: {
      // ベースの JS 推奨ルール
      ...js.configs.recommended.rules,

      // TypeScript 推奨ルール
      ...tseslint.configs.recommended.rules,

      // React 関連
      'react/react-in-jsx-scope': 'off', // Vite/React では不要
      'react/jsx-uses-react': 'off',

      // Hooks ルール
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },

  // 🧹 Prettier とぶつかる書式ルールを全部OFFにする
  //   → フォーマットは Prettier に完全おまかせ
  eslintConfigPrettier,
];
