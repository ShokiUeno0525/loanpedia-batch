import { Routes, Route } from "react-router-dom";
import { SignupPage } from "@/features/auth/pages/SignupPage";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { AppLayout } from "@/shared/components/layout/AppLayout";
import { LandingPage } from "@/features/landing/pages/LandingPage";
import { LoanSearchPage } from "@/features/loanSearch/pages/LoanSearchPage";
import { LoanDetailPage } from "@/features/loanDetail/pages/LoanDetailPage";

export const AppRouter = () => {
  return (
    <Routes>
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<AppLayout />}>
        <Route index element={<LandingPage />} />
        <Route path="search" element={<LoanSearchPage />} />
        <Route path="/loans/:id" element={<LoanDetailPage />} />
      </Route>
    </Routes>
  );
};
