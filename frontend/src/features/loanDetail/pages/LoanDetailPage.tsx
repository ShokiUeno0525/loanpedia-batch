import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getLoanById } from "../../loans/data/loanRepository";
import type { Loan } from "../../loans/data/loans";

export const LoanDetailPage = () => {
  const { id } = useParams<{ id: string }>();

  const {
    data: loan,
    isLoading,
    isError,
  } = useQuery<Loan | undefined>({
    queryKey: ["loan", id],
    queryFn: () => getLoanById(id as string),
    enabled: !!id, // id がある時だけ実行
  });

  if (!id) {
    return (
      <div className="py-16 max-w-3xl mx-auto px-6 space-y-6">
        <h1 className="text-2xl font-bold">不正なURLです</h1>
        <Link to="/search" className="text-blue-600 underline">
          検索に戻る
        </Link>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="py-16 max-w-3xl mx-auto px-6 space-y-6">
        <p className="text-sm text-gray-500">読み込み中...</p>
      </div>
    );
  }

  if (isError || !loan) {
    return (
      <div className="py-16 max-w-3xl mx-auto px-6 space-y-6">
        <h1 className="text-2xl font-bold">ローンが見つかりません</h1>
        <Link to="/search" className="text-blue-600 underline">
          検索に戻る
        </Link>
      </div>
    );
  }

  return (
    <div className="py-16 max-w-3xl mx-auto px-6 space-y-6">
      <Link to="/search" className="text-blue-600 underline">
        検索に戻る
      </Link>

      <h1 className="text-3xl font-bold">
        {loan.bank} | {loan.type}
      </h1>

      <div className="border rounded-xl p-6 space-y-2">
        <p className="text-gray-600">最低金利</p>
        <p className="text-2xl font-semibold">{loan.rateFrom.toFixed(2)}%~</p>
      </div>

      <p className="text-gray-600">
        ここに「借入額」「期間」「条件」などの詳細を追加していきます
      </p>
    </div>
  );
};
