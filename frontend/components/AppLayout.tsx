"use client";

import Sidebar from "@/components/Sidebar";
import Link from "next/link";
import { ShieldCheck, PlayCircle, Zap, ExternalLink } from "lucide-react";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Buildathon Demo Bar (Phase 30) */}
        <header className="demo-top-bar">
          <div className="demo-top-left">
            <span className="demo-pill">
              <Zap size={12} className="inline mr-1 text-yellow-400" />
              DEMO MODE
            </span>
            <span className="demo-notice">
              Razorpay Test Mode Active — No live financial transactions are processed.
            </span>
          </div>

          <div className="demo-quick-links">
            <Link href="/shop" className="demo-action-btn">
              <PlayCircle size={13} />
              AI Shop Demo
            </Link>
            <Link href="/security" className="demo-action-btn">
              <ShieldCheck size={13} />
              Security Lab
            </Link>
            <Link href="/webhooks" className="demo-action-btn">
              <Zap size={13} />
              Webhook Monitor
            </Link>
          </div>
        </header>

        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}
