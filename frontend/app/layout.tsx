import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentPay AI — AI-Powered Agentic Commerce",
  description: "AI-Powered Agentic Commerce for Modern Merchants. Smart shopping, revenue growth, and Razorpay-integrated payments.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
