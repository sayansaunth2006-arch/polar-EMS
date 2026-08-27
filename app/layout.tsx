import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "polar.EMS — Emergency operations, made clear",
  description: "A calm, connected operational platform for emergency medical teams.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" className="bg-[#071522]"><body>{children}</body></html>;
}
