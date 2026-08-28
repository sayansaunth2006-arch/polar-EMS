import { Reveal } from "./Reveal";

const COMPANIES = ["Northwind Cloud", "Basalt Systems", "Vantage Labs", "Fernbridge", "Quillhouse", "Redwire"];

export function LogoStrip() {
  return (
    <section className="border-b border-border py-10">
      <Reveal className="mx-auto max-w-6xl px-6">
        <p className="text-center text-xs tracking-wide text-muted-2 uppercase">
          Trusted by platform teams at
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
          {COMPANIES.map((name) => (
            <span key={name} className="text-sm font-semibold text-muted-2">
              {name}
            </span>
          ))}
        </div>
      </Reveal>
    </section>
  );
}
