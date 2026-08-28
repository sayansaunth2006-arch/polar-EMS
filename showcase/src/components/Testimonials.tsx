import { Reveal } from "./Reveal";

const QUOTES = [
  {
    quote:
      "We stopped losing PRs in review limbo the week we turned this on. The routing logic actually understands our codeowners file, which sounds small until you've lived without it.",
    name: "Priya Raman",
    role: "Staff Engineer, Platform · Basalt Systems",
  },
  {
    quote:
      "On-call handoffs used to mean someone re-explaining an incident from scratch at 2am. Now the context just follows the page. That alone paid for itself.",
    name: "Dev Okafor",
    role: "Engineering Manager · Vantage Labs",
  },
  {
    quote:
      "Setup took us one afternoon because it reads our existing tools instead of asking us to re-model our workflow around it.",
    name: "Marta Lindqvist",
    role: "Head of Infrastructure · Fernbridge",
  },
];

export function Testimonials() {
  return (
    <section className="border-b border-border py-24">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Teams that stopped babysitting handoffs</h2>
        </Reveal>

        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3">
          {QUOTES.map((t, i) => (
            <Reveal key={t.name} delay={i * 0.06}>
              <figure className="flex h-full flex-col justify-between rounded-xl border border-border bg-surface p-6">
                <blockquote className="text-sm text-foreground/90">&ldquo;{t.quote}&rdquo;</blockquote>
                <figcaption className="mt-6">
                  <p className="text-sm font-semibold text-foreground">{t.name}</p>
                  <p className="text-xs text-muted-2">{t.role}</p>
                </figcaption>
              </figure>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
