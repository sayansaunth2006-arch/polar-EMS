"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { X, Snowflake } from "lucide-react";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "./nav";

export function MobileNav({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 md:hidden">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="absolute inset-y-0 left-0 flex w-64 flex-col border-r border-border bg-surface">
        <div className="flex items-center justify-between border-b border-border px-4 py-4">
          <div className="flex items-center gap-2">
            <Snowflake className="h-4 w-4 text-accent" />
            <span className="text-sm font-semibold text-foreground">POLAR-EMS</span>
          </div>
          <button onClick={onClose} className="text-muted hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
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
                    onClick={onClose}
                    className={cn(
                      "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm",
                      active ? "bg-accent/10 text-accent" : "text-muted hover:bg-surface-raised hover:text-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </div>
  );
}
