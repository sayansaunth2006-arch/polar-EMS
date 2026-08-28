"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, Menu, User as UserIcon, Wifi, WifiOff } from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { NAV_ITEMS } from "./nav";
import { api } from "@/lib/api";
import { MobileNav } from "./MobileNav";

const ROLE_LABEL: Record<string, string> = {
  operator: "Station Energy Operator",
  administrator: "Station Administrator",
  scientist: "Research Scientist",
};

export function Topbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { fullName, role, clearSession } = useAuthStore();
  const [now, setNow] = useState<Date | null>(null);
  const [online, setOnline] = useState<boolean | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  const current = NAV_ITEMS.find((i) => pathname === i.href || pathname.startsWith(i.href + "/"));

  useEffect(() => {
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .stations()
      .then(() => !cancelled && setOnline(true))
      .catch(() => !cancelled && setOnline(false));
    const id = setInterval(() => {
      api
        .stations()
        .then(() => !cancelled && setOnline(true))
        .catch(() => !cancelled && setOnline(false));
    }, 30000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  function handleLogout() {
    clearSession();
    router.push("/login");
  }

  return (
    <>
      <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-border bg-surface/95 px-4 backdrop-blur">
        <div className="flex items-center gap-3">
          <button className="text-muted hover:text-foreground md:hidden" onClick={() => setMobileOpen(true)} aria-label="Open navigation">
            <Menu className="h-5 w-5" />
          </button>
          <h2 className="text-sm font-semibold text-foreground">{current?.label ?? "POLAR-EMS"}</h2>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden items-center gap-1.5 text-xs text-muted sm:flex">
            {online === null ? null : online ? (
              <Wifi className="h-3.5 w-3.5 text-status-normal" />
            ) : (
              <WifiOff className="h-3.5 w-3.5 text-status-critical" />
            )}
            <span>{online ? "Backend connected" : online === false ? "Backend unreachable" : ""}</span>
          </div>

          <span className="font-data hidden text-xs text-muted sm:inline">
            {now ? now.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : ""}
          </span>

          <div className="flex items-center gap-2 border-l border-border pl-4">
            <div className="flex h-7 w-7 items-center justify-center rounded-full border border-border-strong text-muted">
              <UserIcon className="h-3.5 w-3.5" />
            </div>
            <div className="hidden leading-tight sm:block">
              <p className="text-xs font-medium text-foreground">{fullName ?? "—"}</p>
              <p className="text-[10px] text-muted">{role ? ROLE_LABEL[role] : ""}</p>
            </div>
            <button onClick={handleLogout} className="ml-1 text-muted hover:text-status-critical" aria-label="Log out">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>
      <MobileNav open={mobileOpen} onClose={() => setMobileOpen(false)} />
    </>
  );
}
