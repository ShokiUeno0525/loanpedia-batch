import { Link } from "react-router-dom";
import { Button } from "@/shared/components/ui/button";

export const HeroSection = () => {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-[#E9F7FF] via-white to-[#ECFDF5] py-24">
      <div className="max-w-5xl mx-auto px-4 text-center space-y-8">
        {/* 小さめのリード文 */}
        <p className="text-primary font-semibold tracking-wide text-sm sm:text-base">
          青森のローン比較に特化したサービス
        </p>

        {/* メインのキャッチコピー */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight text-gray-900">
          青森県内のローン商品を
          <br className="hidden sm:block" />
          <span className="text-[#2563EB]">まとめて比較・検索できます</span>
        </h1>
        {/* サブ説明文 */}
        <p className="text-gray-600 text-base sm:text-lg leading-relaxed">
          地元金融機関の住宅ローン・マイカーローン・教育ローンなどを一括でチェック
          <br className="hidden sm:block" />
          面倒な情報収集を、もっと簡単に
        </p>

        {/* CTAボタン */}
        <div className="flex flex-col sm:flex-row justify-center gap-4 pt-4">
          <Button size="lg" className="px-10 py-6 text-lg rounded-xl shadow-md">
            無料で試してみる
          </Button>

          <Link to="/search">
            <Button
              variant="outline"
              size="lg"
              className="px-10 py-6 text-lg rounded-xl border-gray-300 text-gray-800"
            >
              ローンを探す
            </Button>
          </Link>
        </div>

        {/* 補足テキスト */}
        <p className="text-xs text-muted-foreground">
          ※現在はベータ版のため、対応金融機関・商品は順次追加予定です。
        </p>
      </div>
    </section>
  );
};
