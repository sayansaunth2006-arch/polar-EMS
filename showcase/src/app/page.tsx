import { Nav } from "@/components/Nav";
import { Hero } from "@/components/Hero";
import { LogoStrip } from "@/components/LogoStrip";
import { Features } from "@/components/Features";
import { HowItWorks } from "@/components/HowItWorks";
import { Testimonials } from "@/components/Testimonials";
import { Pricing } from "@/components/Pricing";
import { FAQ } from "@/components/FAQ";
import { CTASection } from "@/components/CTASection";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <div id="top">
      <Nav />
      <main>
        <Hero />
        <LogoStrip />
        <Features />
        <HowItWorks />
        <Testimonials />
        <Pricing />
        <FAQ />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
