export type SignupResponse = {
  userId: string;
};

export async function signup(
  email: string,
  password: string
): Promise<SignupResponse> {
  console.log("API signup:", { email, password });

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ userId: "dummy-user-id" });
    }, 500);
  });
}
