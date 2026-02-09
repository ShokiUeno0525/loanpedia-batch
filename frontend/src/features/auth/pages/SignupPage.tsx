import { useState } from "react";
import { signup } from "../api/authApi";

export const SignupPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Handle signup logic here
    if (password !== confirmPassword) {
      alert("パスワードが一致しません");
      return;
    }
    try {
      const response = await signup(email, password);
      console.log("Signup successful:", response);
      // Redirect or show success message
    } catch (error) {
      console.error("Signup failed:", error);
      alert("登録に失敗しました");
    }
  };
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-md bg-white p-6 rounded-xl shadow space-y-4"
      >
        <h1 className="text-2xl font-bold text-center">ユーザー登録</h1>

        {/* メール */}
        <div>
          <label className="block text-sm font-medium mb-1">
            メールアドレス
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        {/* パスワード */}
        <div>
          <label className="block text-sm font-medium mb-1">パスワード</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {/* パスワード確認 */}
        <div>
          <label className="block text-sm font-medium mb-1">
            パスワード確認
          </label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>

        <button
          type="submit"
          className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600 transition"
        >
          登録
        </button>
      </form>
    </div>
  );
};
