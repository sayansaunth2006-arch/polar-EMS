import { AuthGuard } from "@/components/layout/AuthGuard";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { Toaster } from "@/components/ui/Toaster";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Sidebar />
        <div className="md:pl-60">
          <Topbar />
          <main className="mx-auto max-w-[1600px] px-4 py-5">{children}</main>
        </div>
      </div>
      <Toaster />
    </AuthGuard>
  );
}
