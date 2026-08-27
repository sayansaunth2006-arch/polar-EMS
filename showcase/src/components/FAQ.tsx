import { ChevronDown } from "lucide-react";
import { Reveal } from "./Reveal";

const FAQS = [
  {
    q: "Does CobaltFlow replace our issue tracker or git provider?",
    a: "No. It reads from the tools you already use via their APIs and automates the handoffs between them — nothing is migrated or duplicated.",
  },
  {
    q: "What data does it need access to?",
    a: "Only what your handoff rules reference: issue status/assignee, PR review state, and on-call rotation membership. You choose read-only or read-write per integration.",
  },
  {
    q: "Can we customize the routing logic?",
    a: "Yes — rules are defined per team using your existing codeowners and rotation data, with overrides for exceptions like vacation coverage.",
  },
  {
    q: "How long does setup take?",
    a: "Most teams are fully routing handoffs within an afternoon: connect integrations, confirm the auto-detected rules, and turn it on.",
  },
  {
    q: "Is there a self-hosted option?",
    a: "Enterprise plans support regional data residency. Fully self-hosted deployments are available on request — talk to sales for details.",
  },
];

export function FAQ() {
  return (
    <section id="faq" className="border-b border-border py-24">
      <div className="mx-auto max-w-3xl px-6">
        <Reveal className="text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Questions, answered</h2>
        </Reveal>

        <div className="mt-12 divide-y divide-border rounded-xl border border-border bg-surface">
          {FAQS.map((item) => (
            <details key={item.q} className="group px-6 py-5 open:pb-5">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-sm font-medium text-foreground marker:content-none">
                {item.q}
                <ChevronDown className="h-4 w-4 shrink-0 text-muted transition-transform duration-200 group-open:rotate-180" />
              </summary>
              <p className="mt-3 text-sm text-muted">{item.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
