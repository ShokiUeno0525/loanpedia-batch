import { HeroSection } from "../components/HeroSection";
import { ReasonSection } from "../components/ReasonSection";
import { PopularLoanTypesSection } from "../components/PopularLoanTypesSection";
import { FinalCtaSection } from "../components/FinalCtaSection";

export const LandingPage = () => {
  return (
    <div>
      <HeroSection />
      <ReasonSection />
      <PopularLoanTypesSection />
      <FinalCtaSection />
    </div>
  );
};
