export type LoanType = "住宅ローン" | "マイカーローン" | "教育ローン";
export type Bank = "青森みちのく銀行" | "青い森信用金庫";

export type Loan = {
  id: string;
  bank: Bank;
  type: LoanType;
  rateFrom: number;
};

export const LOANS: Loan[] = [
  { id: "1", bank: "青森みちのく銀行", type: "住宅ローン", rateFrom: 0.45 },
  { id: "2", bank: "青森みちのく銀行", type: "マイカーローン", rateFrom: 1.2 },
  { id: "3", bank: "青い森信用金庫", type: "住宅ローン", rateFrom: 0.6 },
  { id: "4", bank: "青い森信用金庫", type: "教育ローン", rateFrom: 1.1 },
];
