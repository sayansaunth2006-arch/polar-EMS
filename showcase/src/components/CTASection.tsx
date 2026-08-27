import { ArrowRight } from "lucide-react";
import { Button } from "./Button";
import { Reveal } from "./Reveal";

export function CTASection() {
  return (
    <section className="py-24">
      <Reveal className="mx-auto max-w-3xl rounded-2xl border border-border-strong bg-surface px-8 py-16 text-center">
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Stop being the glue between your tools</h2>
        <p className="mx-auto mt-4 max-w-xl text-muted">
          Fourteen days free, no credit card. Most teams see their first automated handoff on day one.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Button href="#pricing" variant="primary" size="lg">
            Start free <ArrowRight className="h-4 w-4" />
          </Button>
          <Button href="#" variant="secondary" size="lg">
            Talk to sales
          </Button>
        </div>
      </Reveal>
    </section>
  );
}
