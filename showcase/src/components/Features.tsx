import { GitPullRequest, Bell, Workflow, ShieldCheck, Clock, BarChart3 } from "lucide-react";
import { Reveal } from "./Reveal";

const FEATURES = [
  {
    icon: GitPullRequest,
    title: "PR routing that isn't a coin flip",
    desc: "Reviewers are assigned by codeowners, current load, and time zone — not whoever's avatar is on top.",
  },
  {
    icon: Bell,
    title: "On-call handoffs that actually happen",
    desc: "Pages route to the right rotation automatically, with context from the last three related incidents attached.",
  },
  {
    icon: Workflow,
    title: "Task handoffs, automated end to end",
    desc: "When a ticket's status changes, the next owner is notified with everything they need — no Slack archaeology.",
  },
  {
    icon: Clock,
    title: "Stale work gets surfaced, not lost",
    desc: "CobaltFlow flags tasks and PRs that have gone quiet for longer than your team's own SLA, before they're forgotten.",
  },
  {
    icon: ShieldCheck,
    title: "Runs where your data already is",
    desc: "Reads from your existing issue tracker, git provider, and pager via their APIs — nothing is duplicated or migrated.",
  },
  {
    icon: BarChart3,
    title: "See where handoffs actually slow down",
    desc: "A weekly digest shows exactly which stage of your workflow is the bottleneck, with real numbers, not vibes.",
  },
];

export function Features() {
  return (
    <section id="features" className="border-b border-border py-24">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Everything between &ldquo;done&rdquo; and &ldquo;someone noticed&rdquo;
          </h2>
          <p className="mt-4 text-muted">
            CobaltFlow doesn&apos;t replace your tools — it fills the gap where a human was supposed to
            remember to do something.
          </p>
        </Reveal>

        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <Reveal key={f.title} delay={Math.min(i * 0.05, 0.2)}>
              <div className="h-full rounded-xl border border-border bg-surface p-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-bg text-brand">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 font-semibold text-foreground">{f.title}</h3>
                <p className="mt-2 text-sm text-muted">{f.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
