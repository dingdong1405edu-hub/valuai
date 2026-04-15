"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listCompanies, getLatestValuation, formatVND } from "@/lib/api";
import type { Company, Valuation } from "@/lib/types";

interface CompanyWithValuation extends Company {
  latestValuation?: Valuation | null;
}

export default function DashboardPage() {
  const [companies, setCompanies] = useState<CompanyWithValuation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const list = await listCompanies();
        const enriched = await Promise.all(
          list.map(async (c) => {
            const val = await getLatestValuation(c.id).catch(() => null);
            return { ...c, latestValuation: val };
          })
        );
        setCompanies(enriched);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      {/* Hero */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-extrabold text-brand-900 mb-3">
          AI-Powered Business Valuation
        </h1>
        <p className="text-gray-500 text-lg max-w-2xl mx-auto">
          Upload documents, crawl your website, and get a professional valuation range
          using DCF, Comparable, and Scorecard methods — powered by Groq + Gemini.
        </p>
        <Link
          href="/upload"
          className="mt-6 inline-block bg-brand-600 hover:bg-brand-700 text-white px-8 py-3 rounded-lg font-semibold text-lg transition shadow-md"
        >
          Start New Valuation →
        </Link>
      </div>

      {/* Method pills */}
      <div className="grid grid-cols-3 gap-4 mb-12 text-center">
        {[
          { label: "DCF", desc: "Discounted Cash Flow", color: "bg-blue-50 border-blue-200 text-blue-800" },
          { label: "Comparable", desc: "Market Multiples (Fireant)", color: "bg-green-50 border-green-200 text-green-800" },
          { label: "Scorecard", desc: "Qualitative 10-factor", color: "bg-purple-50 border-purple-200 text-purple-800" },
        ].map((m) => (
          <div key={m.label} className={`border rounded-xl p-4 ${m.color}`}>
            <div className="font-bold text-lg">{m.label}</div>
            <div className="text-sm opacity-75">{m.desc}</div>
          </div>
        ))}
      </div>

      {/* Companies list */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-800">Recent Valuations</h2>
        <Link href="/upload" className="text-brand-600 hover:text-brand-700 text-sm font-medium">
          + New
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">Loading...</div>
      ) : companies.length === 0 ? (
        <div className="text-center py-16 border-2 border-dashed border-gray-200 rounded-xl">
          <p className="text-gray-400 text-lg mb-4">No valuations yet</p>
          <Link
            href="/upload"
            className="bg-brand-600 text-white px-6 py-2.5 rounded-lg hover:bg-brand-700 transition"
          >
            Create Your First Valuation
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {companies.map((c) => {
            const val = c.latestValuation;
            const statusColor = {
              completed: "bg-green-100 text-green-800",
              running: "bg-yellow-100 text-yellow-800",
              failed: "bg-red-100 text-red-800",
              pending: "bg-gray-100 text-gray-600",
            }[val?.status || "pending"] || "bg-gray-100 text-gray-600";

            return (
              <Link
                key={c.id}
                href={val ? `/results/${val.id}` : `/upload?company=${c.id}`}
                className="block bg-white border border-gray-200 rounded-xl p-5 hover:border-brand-400 hover:shadow-md transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-lg text-gray-900">{c.name}</h3>
                    <p className="text-gray-500 text-sm">
                      {c.industry || "Industry not specified"} •{" "}
                      {c.founded_year ? `Est. ${c.founded_year}` : ""}
                    </p>
                  </div>
                  <div className="text-right">
                    {val?.final_range_mid ? (
                      <div className="text-2xl font-bold text-brand-700">
                        {formatVND(val.final_range_mid)}
                      </div>
                    ) : null}
                    {val && (
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColor}`}>
                        {val.status}
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
