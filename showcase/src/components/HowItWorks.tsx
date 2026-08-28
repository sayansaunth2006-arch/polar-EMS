import { Plug, SlidersHorizontal, Rocket } from "lucide-react";
import { Reveal } from "./Reveal";

const STEPS = [
  {
    icon: Plug,
    step: "01",
    title: "Connect your tools",
    desc: "OAuth into your issue tracker, git provider, and pager. Read-only to start — CobaltFlow only writes what you explicitly enable.",
  },
  {
    icon: SlidersHorizontal,
    step: "02",
    title: "Set your handoff rules",
    desc: "Define who owns what, using the same codeowners and rotation data you already maintain — no new config to keep in sync.",
  },
  {
    icon: Rocket,
    step: "03",
    title: "Handoffs run themselves",
    desc: "From the next status change onward, routing, notification, and context-gathering happen automatically.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="border-b border-border bg-surface/40 py-24">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Live in an afternoon, not a quarter</h2>
          <p className="mt-4 text-muted">No migration, no new source of truth to maintain alongside the old one.</p>
        </Reveal>

        <div className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <Reveal key={s.step} delay={i * 0.08}>
              <div className="relative">
                <span className="font-mono-tech text-sm text-brand">{s.step}</span>
                <div className="mt-3 flex h-11 w-11 items-center justify-center rounded-lg border border-border-strong bg-surface text-brand">
                  <s.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 font-semibold text-foreground">{s.title}</h3>
                <p className="mt-2 text-sm text-muted">{s.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
