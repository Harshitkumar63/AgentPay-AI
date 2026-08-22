"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard,
  ShoppingBag,
  Package,
  ClipboardList,
  BarChart3,
  Bot,
  Shield,
  Settings,
  Zap,
  Radio,
  Sliders,
  TrendingUp,
  AlertTriangle,
} from "lucide-react";

const NAV_SECTIONS = [
  {
    title: "Overview",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "AI Shop", href: "/shop", icon: ShoppingBag },
    ],
  },
  {
    title: "Merchant Growth",
    items: [
      { label: "Growth Center", href: "/growth", icon: TrendingUp },
      { label: "Products Catalog", href: "/products", icon: Package },
      { label: "Orders", href: "/orders", icon: ClipboardList },
      { label: "Revenue Analytics", href: "/analytics", icon: BarChart3 },
    ],
  },
  {
    title: "Governance & Safety",
    items: [
      { label: "Agent Trace", href: "/agent", icon: Bot },
      { label: "Audit Logs", href: "/audit", icon: Shield },
      { label: "Webhook Monitor", href: "/webhooks", icon: Radio },
      { label: "Policy & Simulator", href: "/settings", icon: Sliders },
      { label: "Security & Failure Lab", href: "/security", icon: AlertTriangle },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <Link href="/dashboard" className="sidebar-logo text-decoration-none">
          <div className="sidebar-logo-icon">
            <Zap size={18} color="white" />
          </div>
          <div>
            <h1 className="text-white text-base font-bold tracking-tight">AgentPay AI</h1>
            <p className="text-xs text-blue-400 font-medium">Agentic Commerce Engine</p>
          </div>
        </Link>
      </div>

      <nav className="sidebar-nav">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="nav-section">
            <div className="nav-section-title">{section.title}</div>
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`nav-link ${isActive ? "active" : ""}`}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="demo-badge">
          <Zap size={14} className="animate-pulse" />
          <span>RAZORPAY TEST MODE</span>
        </div>
      </div>
    </aside>
  );
}
