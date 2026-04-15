import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ValuAI — Business Valuation Platform",
  description: "AI-powered business valuation for Vietnamese SMEs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <nav className="bg-brand-900 text-white px-6 py-3 flex items-center gap-3 shadow-md">
          <a href="/" className="flex items-center gap-2 font-bold text-lg tracking-tight">
            <span className="bg-blue-500 text-white px-2 py-0.5 rounded text-sm font-black">V</span>
            ValuAI
          </a>
          <span className="text-blue-300 text-sm ml-4 hidden sm:inline">
            AI-Powered Business Valuation
          </span>
          <div className="ml-auto flex items-center gap-4 text-sm">
            <a href="/" className="text-blue-200 hover:text-white transition">Dashboard</a>
            <a href="/upload" className="bg-blue-600 hover:bg-blue-500 px-3 py-1.5 rounded-md transition font-medium">
              + New Valuation
            </a>
          </div>
        </nav>
        <main className="min-h-screen">{children}</main>
        <footer className="text-center text-xs text-gray-400 py-6 border-t mt-12">
          ValuAI © {new Date().getFullYear()} — Confidential AI Valuation Platform
        </footer>
      </body>
    </html>
  );
}
