import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { LoanCard } from "../../landing/components/LoanCard";
import { LoanType, Bank, Loan } from "../../loans/data/loans";
import { getLoans, LoanQuery } from "../../loans/data/loanRepository";

type BankFilter = "すべて" | Bank;

// URL(searchParams) → LoanQuery を作る（undefined は「条件なし」）
const buildQueryFromParams = (searchParams: URLSearchParams): LoanQuery => {
  const type = (searchParams.get("type") as LoanType) ?? "住宅ローン";
  const bank = (searchParams.get("bank") as Bank) ?? undefined;

  const maxRateParam = searchParams.get("maxRate");
  const maxRate =
    maxRateParam !== null && maxRateParam !== ""
      ? Number(maxRateParam)
      : undefined;

  return { type, bank, maxRate };
};

export const LoanSearchPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // ---------------------------
  // ① フォーム入力中（draft）
  // ---------------------------
  const initialLoanType =
    (searchParams.get("type") as LoanType) ?? "住宅ローン";
  const initialBank = (searchParams.get("bank") as BankFilter) ?? "すべて";
  const initialMaxRate: number | "" =
    searchParams.get("maxRate") !== null
      ? Number(searchParams.get("maxRate"))
      : "";

  const [draftLoanType, setDraftLoanType] = useState<LoanType>(initialLoanType);
  const [draftBank, setDraftBank] = useState<BankFilter>(initialBank);
  const [draftMaxRate, setDraftMaxRate] = useState<number | "">(initialMaxRate);

  // ---------------------------
  // ② 検索確定（submittedQuery）
  //   - "検索ボタン押下"でだけ更新する
  // ---------------------------
  const [submittedQuery, setSubmittedQuery] = useState<LoanQuery | null>(null);

  // URLが変わったらフォームと検索条件を同期（直打ち/戻る進む対応）
  useEffect(() => {
    // draft は常にURLに追従
    const nextType = (searchParams.get("type") as LoanType) ?? "住宅ローン";
    const nextBank = (searchParams.get("bank") as BankFilter) ?? "すべて";
    const nextMaxRate: number | "" =
      searchParams.get("maxRate") !== null
        ? Number(searchParams.get("maxRate"))
        : "";

    setDraftLoanType(nextType);
    setDraftBank(nextBank);
    setDraftMaxRate(nextMaxRate);

    // URLに type があるなら「その条件で検索済み」とみなす（初回表示もOK）
    // これにより /search?type=教育ローン の直打ちでも結果が出る
    if (searchParams.get("type")) {
      setSubmittedQuery(buildQueryFromParams(searchParams));
    } else {
      // /search にクエリ無しで来た場合は未検索状態にする（好みで変更可）
      setSubmittedQuery(null);
    }
  }, [searchParams]);

  // ---------------------------
  // ③ React Query（検索ボタン押下＝submittedQuery更新で取得）
  // ---------------------------
  const {
    data: results = [],
    isLoading,
    isFetching,
    isError,
  } = useQuery<Loan[]>({
    queryKey: ["loans", submittedQuery],
    queryFn: () => getLoans(submittedQuery ?? undefined),
    enabled: submittedQuery !== null, // ✅ submittedQuery がある時だけ取得
  });

  // ---------------------------
  // ④ 検索ボタン：submittedQuery と URL を更新
  // ---------------------------
  const onSearch = () => {
    const query: LoanQuery = {
      type: draftLoanType,
      bank: draftBank === "すべて" ? undefined : (draftBank as Bank),
      maxRate: draftMaxRate === "" ? undefined : draftMaxRate,
    };

    setSubmittedQuery(query);

    const params: Record<string, string> = { type: draftLoanType };
    if (draftBank !== "すべて") params.bank = draftBank;
    if (draftMaxRate !== "") params.maxRate = String(draftMaxRate);
    setSearchParams(params);
  };

  const count = useMemo(() => results.length, [results.length]);

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
              onChange={(e) => setDraftBank(e.target.value as BankFilter)}
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

        {/* 検索ボタン（押したときだけ検索実行） */}
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
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold">検索結果</h2>

          <div className="flex items-center gap-2">
            {isFetching && !isLoading && (
              <span className="text-xs text-gray-500">更新中...</span>
            )}
            <p className="text-sm text-gray-600">{count} 件</p>
          </div>
        </div>

        {submittedQuery === null && (
          <div className="border rounded-lg p-6 text-center text-gray-600">
            条件を選んで「検索する」を押してください
          </div>
        )}

        {submittedQuery !== null && isLoading && (
          <p className="text-sm text-gray-500">読み込み中...</p>
        )}

        {submittedQuery !== null && isError && (
          <div className="border rounded-lg p-6 text-center text-red-600">
            取得に失敗しました
          </div>
        )}

        {submittedQuery !== null &&
          !isLoading &&
          !isError &&
          results.length === 0 && (
            <div className="border rounded-lg p-6 text-center text-gray-600">
              条件に合うローンが見つかりませんでした
            </div>
          )}

        {submittedQuery !== null &&
          !isLoading &&
          !isError &&
          results.length > 0 && (
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
