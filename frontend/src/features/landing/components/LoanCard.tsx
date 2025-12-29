import { Link } from "react-router-dom";

type LoanCardProps = {
  id: string;
  bank: string;
  type: string;
  rateFrom: number;
};

export const LoanCard = ({ id, bank, type, rateFrom }: LoanCardProps) => {
  return (
    <Link to={`/loans/${id}`} className="block">
      <div className="border rounded-lg p-4">
        <h3 className="font-medium">
          {bank}|{type}
        </h3>
        <p className="text-sm text-gray-600">金利:{rateFrom.toFixed(2)}%~</p>
      </div>
    </Link>
  );
};
