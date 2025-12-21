import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Footer } from "./Footer";

export const AppLayout = () => {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900">
      {/* 全ページ共通ヘッダー */}
      <Header />

      {/* ページごとの中身が差し込まれる場所 */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* 全ページ共通フッター */}
      <Footer />
    </div>
  );
};
