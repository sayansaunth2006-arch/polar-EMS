"use client";

import { useState } from "react";
import { Check } from "lucide-react";
import { motion } from "motion/react";
import { Button } from "./Button";
import { Reveal } from "./Reveal";
import { cn } from "@/lib/utils";

const PLANS = [
  {
    name: "Starter",
    monthly: 0,
    annual: 0,
    desc: "For a single team trying it out.",
    features: ["Up to 8 engineers", "1 issue tracker + 1 git provider", "Basic handoff rules", "Community support"],
    cta: "Start free",
    highlighted: false,
  },
  {
    name: "Team",
    monthly: 24,
    annual: 19,
    desc: "For platform teams running real on-call.",
    features: [
      "Unlimited engineers",
      "All integrations, incl. on-call paging",
      "Custom handoff & SLA rules",
      "Weekly bottleneck digest",
      "Priority support",
    ],
    cta: "Start 14-day trial",
    highlighted: true,
  },
  {
    name: "Enterprise",
    monthly: null,
    annual: null,
    desc: "For orgs with audit, SSO, and data-residency needs.",
    features: ["SSO / SCIM", "Audit log export", "Regional data residency", "Dedicated support engineer"],
    cta: "Talk to sales",
    highlighted: false,
  },
];

export function Pricing() {
  const [annual, setAnnual] = useState(true);

  return (
    <section id="pricing" className="border-b border-border bg-surface/40 py-24">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Simple pricing, no seat-count games</h2>
          <p className="mt-4 text-muted">Every plan includes unlimited handoffs. You only pay for who&apos;s on the team.</p>

          <div className="mt-8 inline-flex items-center gap-3 rounded-full border border-border-strong bg-surface p-1">
            <button
              onClick={() => setAnnual(false)}
              className={cn("cursor-pointer rounded-full px-4 py-1.5 text-sm transition-colors", !annual ? "bg-brand text-white" : "text-muted")}
            >
              Monthly
            </button>
            <button
              onClick={() => setAnnual(true)}
              className={cn("cursor-pointer rounded-full px-4 py-1.5 text-sm transition-colors", annual ? "bg-brand text-white" : "text-muted")}
            >
              Annual — 2 months free
            </button>
          </div>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {PLANS.map((plan, i) => (
            <Reveal key={plan.name} delay={i * 0.06}>
              <div
                className={cn(
                  "flex h-full flex-col rounded-2xl border p-7",
                  plan.highlighted ? "border-brand bg-brand-bg/40 shadow-lg shadow-brand/10" : "border-border bg-surface"
                )}
              >
                {plan.highlighted && (
                  <span className="mb-4 inline-block w-fit rounded-full bg-brand px-3 py-1 text-xs font-semibold text-white">
                    Most popular
                  </span>
                )}
                <h3 className="text-lg font-semibold text-foreground">{plan.name}</h3>
                <p className="mt-1 text-sm text-muted">{plan.desc}</p>

                <div className="mt-6 flex items-baseline gap-1">
                  {plan.monthly === null ? (
                    <span className="text-3xl font-bold text-foreground">Custom</span>
                  ) : (
                    <>
                      <span className="font-mono-tech text-3xl font-bold text-foreground">
                        <motion.span key={annual ? "annual" : "monthly"} initial={{ opacity: 0.4 }} animate={{ opacity: 1 }}>
                          ${annual ? plan.annual : plan.monthly}
                        </motion.span>
                      </span>
                      <span className="text-sm text-muted">/ engineer / mo</span>
                    </>
                  )}
                </div>

                <ul className="mt-6 flex-1 space-y-3">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm text-muted">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                      {f}
                    </li>
                  ))}
                </ul>

                <Button href="#" variant={plan.highlighted ? "primary" : "secondary"} className="mt-8 w-full justify-center">
                  {plan.cta}
                </Button>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
