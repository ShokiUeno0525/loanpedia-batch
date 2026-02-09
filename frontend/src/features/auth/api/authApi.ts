export type SignupResponse = {
  userId: string;
};

export async function signup(
  email: string,
  password: string,
): Promise<SignupResponse> {
  console.log("API signup:", { email, password });

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ userId: "dummy-user-id" });
    }, 500);
  });
}

type LoginResponse = {
  token: string;
  email: string;
};

export const login = async (
  email: string,
  password: string,
): Promise<LoginResponse> => {
  console.log("API login", { email, password });

  // 仮実装：本番ではここが fetch になる
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 例：パスワードが短すぎたら失敗扱いにする（動作確認用）
      if (password.length < 4) {
        reject(new Error("メールアドレスまたはパスワードが正しくありません"));
        return;
      }
      resolve({ token: "dummy-token", email });
    }, 500);
  });
};
