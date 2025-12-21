import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";

const LOANS = [
  { id: "1", bank: "青森みちのく銀行", type: "住宅ローン", rateFrom: 0.45 },
  { id: "2", bank: "青森みちのく銀行", type: "マイカーローン", rateFrom: 1.2 },
  { id: "3", bank: "青い森信用金庫", type: "住宅ローン", rateFrom: 1.1 },
  { id: "4", bank: "青い森信用金庫", type: "教育ローン", rateFrom: 1.1 },
];

export const LoanDetailPage = () => {
  const { id } = useParams();

  const loan = useMemo(() => {
    return LOANS.find((x) => x.id === id);
  }, [id]);

  if (!loan) {
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
        {loan.bank}|{loan.type}
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
