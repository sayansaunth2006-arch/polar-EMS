"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Snowflake } from "lucide-react";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "./nav";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-border bg-surface md:flex">
      <div className="flex items-center gap-2 border-b border-border px-4 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-md border border-border-strong text-accent">
          <Snowflake className="h-4 w-4" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold tracking-wide text-foreground">POLAR-EMS</p>
          <p className="text-[10px] text-muted">Energy Operations</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3">
        <ul className="space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors",
                    active ? "bg-accent/10 text-accent" : "text-muted hover:bg-surface-raised hover:text-foreground"
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="truncate">{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-border px-4 py-3 text-[10px] text-muted-2">
        Synthetic demo data · Prototype build
      </div>
    </aside>
  );
}
