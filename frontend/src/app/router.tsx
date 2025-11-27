import { Routes, Route } from "react-router-dom";
import { AppLayout } from "@/shared/components/layout/AppLayout";
import { LandingPage } from "@/features/landing/pages/LandingPage";

export const AppRouter = () => {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<LandingPage />} />
      </Route>
    </Routes>
  );
};
