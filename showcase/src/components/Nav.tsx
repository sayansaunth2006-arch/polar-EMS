import Link from "next/link";
import { Waypoints } from "lucide-react";
import { Button } from "./Button";
import { MobileMenuButton } from "./MobileMenuButton";

const LINKS = [
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#pricing", label: "Pricing" },
  { href: "#faq", label: "FAQ" },
];

export function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/85 backdrop-blur">
      <div className="relative mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="#top" className="flex items-center gap-2 font-semibold tracking-tight">
          <Waypoints className="h-5 w-5 text-brand" />
          CobaltFlow
        </Link>

        <nav className="hidden items-center gap-8 sm:flex">
          {LINKS.map((link) => (
            <Link key={link.href} href={link.href} className="text-sm text-muted hover:text-foreground">
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-3 sm:flex">
          <Button href="#" variant="ghost" size="md">
            Sign in
          </Button>
          <Button href="#pricing" variant="primary" size="md">
            Start free
          </Button>
        </div>

        <MobileMenuButton />
      </div>
    </header>
  );
}
