import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../api/authApi";

export const LoginPage = () => {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    try {
      setIsSubmitting(true);
      const result = await login(email, password);
      console.log("login success", result);

      // ✅ 次のStep（Auth状態管理）でここを「ログイン状態を保存」に置き換える
      // 今はログイン成功したら検索へ遷移でOK
      navigate("/search");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "ログインに失敗しました";
      setErrorMsg(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-md bg-white p-6 rounded-xl shadow space-y-4"
      >
        <h1 className="text-2xl font-bold text-center">ログイン</h1>

        {errorMsg && (
          <div className="border border-red-200 bg-red-50 text-red-700 rounded-md px-3 py-2 text-sm">
            {errorMsg}
          </div>
        )}

        {/* メール */}
        <div>
          <label className="block text-sm font-medium mb-1">
            メールアドレス
          </label>
          <input
            type="email"
            className="w-full border rounded-md px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </div>

        {/* パスワード */}
        <div>
          <label className="block text-sm font-medium mb-1">パスワード</label>
          <input
            type="password"
            className="w-full border rounded-md px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-2 bg-blue-600 text-white rounded-md disabled:opacity-60"
        >
          {isSubmitting ? "ログイン中..." : "ログイン"}
        </button>

        <div className="text-sm text-center text-gray-600">
          アカウントがない？{" "}
          <Link to="/signup" className="text-blue-600 underline">
            ユーザー登録
          </Link>
        </div>
      </form>
    </div>
  );
};
