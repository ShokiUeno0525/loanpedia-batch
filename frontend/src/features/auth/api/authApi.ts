type SignupResponse = {
  userId: string;
};

export const signup = async (
  email: string,
  password: string,
): Promise<SignupResponse> => {
  console.log("API signup:", { email, password });

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ userId: "dummy-user-id" });
    }, 500);
  });
};
