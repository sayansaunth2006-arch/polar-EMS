import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Zap,
  TrendingUp,
  SlidersHorizontal,
  BatteryCharging,
  Fuel,
  ListTree,
  AlertTriangle,
  Bell,
  CloudSnow,
  PlayCircle,
  GitCompareArrows,
  BarChart3,
  FileText,
  Settings,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/energy", label: "Energy Monitoring", icon: Zap },
  { href: "/forecasting", label: "AI Forecasting", icon: TrendingUp },
  { href: "/optimization", label: "Energy Optimization", icon: SlidersHorizontal },
  { href: "/battery", label: "Battery Management", icon: BatteryCharging },
  { href: "/generator", label: "Generator Management", icon: Fuel },
  { href: "/loads", label: "Load Management", icon: ListTree },
  { href: "/anomalies", label: "Anomaly Detection", icon: AlertTriangle },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/weather", label: "Polar Weather", icon: CloudSnow },
  { href: "/simulation", label: "Simulation Mode", icon: PlayCircle },
  { href: "/whatif", label: "What-If Analysis", icon: GitCompareArrows },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];
