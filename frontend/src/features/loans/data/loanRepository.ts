import { LOANS, Loan, LoanType, Bank } from "../../loans/data/loans";

export type LoanQuery = {
  type?: LoanType;
  bank?: Bank;
  maxRate?: number;
};

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));
/**
 * ローン一覧を取得する
 * 条件があれば絞り込む
 */
export const getLoans = async (query?: LoanQuery): Promise<Loan[]> => {
  await delay(150); // 模擬的な遅延

  if (!query) return LOANS;

  return LOANS.filter((Loan) => {
    const matchType = query.type ? Loan.type === query.type : true;
    const matchBank = query.bank ? Loan.bank === query.bank : true;
    const matchRate =
      query.maxRate !== undefined ? Loan.rateFrom <= query.maxRate : true;

    return matchType && matchBank && matchRate;
  });
};
/**
 * IDからローンを1件取得する
 */
export const getLoanById = async (id: string): Promise<Loan | undefined> => {
  await delay(80);
  return LOANS.find((loan) => loan.id === id);
};
