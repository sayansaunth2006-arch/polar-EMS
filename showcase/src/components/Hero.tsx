"use client";

import { motion, useReducedMotion } from "motion/react";
import { ArrowRight, CheckCircle2, GitPullRequest, Zap } from "lucide-react";
import { Button } from "./Button";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, bounce: 0.15, visualDuration: 0.5 } },
};

export function Hero() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section className="relative overflow-hidden border-b border-border">
      <div className="pointer-events-none absolute inset-0 [background:radial-gradient(600px_circle_at_50%_-10%,rgba(59,130,246,0.15),transparent_70%)]" />

      <div className="mx-auto max-w-6xl px-6 pt-28 pb-20 text-center sm:pt-36 sm:pb-28">
        <motion.div
          variants={container}
          initial={shouldReduceMotion ? "show" : "hidden"}
          animate="show"
          className="mx-auto flex max-w-3xl flex-col items-center"
        >
          <motion.span
            variants={item}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-border-strong bg-surface px-3 py-1 text-xs text-muted"
          >
            <Zap className="h-3.5 w-3.5 text-brand" />
            Now routing on-call automatically during incidents
          </motion.span>

          <motion.h1 variants={item} className="text-4xl font-bold tracking-tight text-balance sm:text-6xl">
            The busywork between your <span className="text-brand">tasks, PRs, and on-call</span> — automated.
          </motion.h1>

          <motion.p variants={item} className="mt-6 max-w-xl text-lg text-muted text-balance">
            CobaltFlow watches your issue tracker, git provider, and pager, then handles the handoffs
            engineers usually do by hand — so nothing sits waiting for someone to notice it.
          </motion.p>

          <motion.div variants={item} className="mt-9 flex flex-col items-center gap-4 sm:flex-row">
            <Button href="#pricing" variant="primary" size="lg">
              Start free — 14 days <ArrowRight className="h-4 w-4" />
            </Button>
            <Button href="#how-it-works" variant="secondary" size="lg">
              See how it works
            </Button>
          </motion.div>

          <motion.div variants={item} className="mt-6 flex items-center gap-1.5 text-xs text-muted-2">
            <CheckCircle2 className="h-3.5 w-3.5 text-success" />
            No credit card required · Cancel anytime
          </motion.div>
        </motion.div>

        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring", bounce: 0.1, visualDuration: 0.6, delay: 0.35 }}
          className="relative mx-auto mt-16 max-w-4xl"
        >
          <ProductMockup />
        </motion.div>
      </div>
    </section>
  );
}

function ProductMockup() {
  return (
    <div className="overflow-hidden rounded-xl border border-border-strong bg-surface shadow-2xl shadow-black/40">
      <div className="flex items-center gap-1.5 border-b border-border bg-surface-raised px-4 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-[#ef4444]/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#f59e0b]/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#22c55e]/70" />
        <span className="font-mono-tech ml-3 text-xs text-muted-2">cobaltflow — platform-team</span>
      </div>
      <div className="grid grid-cols-1 gap-px bg-border sm:grid-cols-3">
        {[
          { icon: GitPullRequest, title: "PR #482 merged", desc: "Auto-assigned to on-call reviewer · 4s ago" },
          { icon: Zap, title: "Deploy queued", desc: "Routed to staging pipeline · 12s ago" },
          { icon: CheckCircle2, title: "Incident resolved", desc: "Runbook step 3 auto-completed · 1m ago" },
        ].map((row) => (
          <div key={row.title} className="flex flex-col gap-2 bg-surface p-5 text-left">
            <row.icon className="h-4 w-4 text-brand" />
            <p className="text-sm font-medium text-foreground">{row.title}</p>
            <p className="font-mono-tech text-xs text-muted-2">{row.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
