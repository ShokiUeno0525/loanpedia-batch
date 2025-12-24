import { useMemo, useState } from "react";
import { LoanCard } from "../../landing/components/LoanCard";
import { LOANS, LoanType, Bank } from "../../loans/data/loans";

type BankFilter = "すべて" | Bank;

export const LoanSearchPage = () => {
  // ①検索条件(state)
  const [draftLoanType, setDraftLoanType] = useState<LoanType>("住宅ローン");
  const [draftBank, setDraftBank] = useState<BankFilter>("すべて");
  const [draftMaxRate, setDraftMaxRate] = useState<number | "">("");
  const [appliedMaxRate, setAppliedMaxRate] = useState<number | "">("");

  // 検索条件の確定(検索ボタンを押したときに更新)
  const [appliedLoanType, setAppliedLoanType] =
    useState<LoanType>("住宅ローン");
  const [appliedBank, setAppliedBank] = useState<BankFilter>("すべて");
  // ②条件に応じた結果(フィルタ)
  const results = useMemo(() => {
    return LOANS.filter((loan) => {
      const matchType = loan.type === appliedLoanType;
      const matchBank =
        appliedBank === "すべて" ? true : loan.bank === appliedBank;
      const matchRate =
        appliedMaxRate === "" ? true : loan.rateFrom <= appliedMaxRate;
      return matchType && matchBank && matchRate;
    });
  }, [appliedLoanType, appliedBank]);

  const onSearch = () => {
    //検索ボタンを押したときだけ「確定条件」を更新
    setAppliedLoanType(draftLoanType);
    setAppliedBank(draftBank);
    setAppliedMaxRate(draftMaxRate);
  };

  return (
    <div className="py-16 max-w-5xl mx-auto px-6 space-y-10">
      {/* タイトル */}
      <header className="text-center space-y-2">
        <h1 className="text-3xl font-bold">ローン検索</h1>
        <p className="text-gray-600">
          条件を指定して、青森県内のローン商品を探せます
        </p>
      </header>

      {/* 検索フォーム */}
      <section className="bg-white rounded-xl shadow-sm p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {/* ローン種別 */}
          <div>
            <label className="block text-sm font-medium mb-1">ローン種別</label>
            <select
              className="w-full border rounded-md px-3 py-2"
              value={draftLoanType}
              onChange={(e) => setDraftLoanType(e.target.value as LoanType)}
            >
              <option value="住宅ローン">住宅ローン</option>
              <option value="マイカーローン">マイカーローン</option>
              <option value="教育ローン">教育ローン</option>
            </select>
          </div>

          {/* 金融機関 */}
          <div>
            <label className="block text-sm font-medium mb-1">金融機関</label>
            <select
              className="w-full border rounded-md px-3 py-2"
              value={draftBank}
              onChange={(e) => setDraftBank(e.target.value as Bank)}
            >
              <option value="すべて">すべて</option>
              <option value="青森みちのく銀行">青森みちのく銀行</option>
              <option value="青い森信用金庫">青い森信用金庫</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">上限金利(%)</label>
          <input
            type="number"
            step="0.01"
            className="w-full border rounded-md px-3 py-2"
            placeholder="例:1.0"
            value={draftMaxRate}
            onChange={(e) =>
              setDraftMaxRate(
                e.target.value === "" ? "" : Number(e.target.value)
              )
            }
          />
        </div>

        {/* ボタン(今回は見た目だけ。押しても結果は既に反映される) */}
        <div className="text-right">
          <button
            type="button"
            onClick={onSearch}
            className="px-6 py-2 bg-blue-600 text-white rounded-md"
          >
            検索する
          </button>
        </div>
      </section>

      {/* 検索結果 */}
      <section className="space-y-4">
        <div className="flex item-baseline justify-between">
          <h2 className="text-xl font-semibold">検索結果</h2>
          <p className="text-sm text-gray-600">{results.length} 件</p>
        </div>

        {results.length === 0 ? (
          <div className="border rounded-lg p-6 text-center text-gray-600">
            条件に合うローンが見つかりませんでした
          </div>
        ) : (
          <div className="space-y-3">
            {results.map((loan) => (
              <LoanCard
                key={loan.id}
                id={loan.id}
                bank={loan.bank}
                type={loan.type}
                rateFrom={loan.rateFrom}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
