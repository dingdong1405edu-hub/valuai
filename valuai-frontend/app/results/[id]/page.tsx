"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getValuation, getCompany } from "@/lib/api";
import type { Valuation, Company } from "@/lib/types";
import ValuationDashboard from "@/components/ValuationDashboard";

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [valuation, setValuation] = useState<Valuation | null>(null);
  const [company, setCompany] = useState<Company | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const val = await getValuation(id);
        setValuation(val);
        const comp = await getCompany(val.company_id);
        setCompany(comp);
      } catch (e: unknown) {
        setError((e as Error).message || "Failed to load valuation");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">Loading valuation results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="text-5xl mb-4">⚠️</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
        <p className="text-gray-500 mb-6">{error}</p>
        <a href="/" className="text-brand-600 hover:text-brand-700 font-medium">← Back to Dashboard</a>
      </div>
    );
  }

  if (!valuation) return null;

  if (valuation.status === "running" || valuation.status === "pending") {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="w-16 h-16 border-4 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-6" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Valuation In Progress</h2>
        <p className="text-gray-500 mb-2">
          Running DCF + Comparable + Scorecard analysis...
        </p>
        <p className="text-sm text-gray-400">This usually takes 2-3 minutes. Page will refresh automatically.</p>
        <script
          dangerouslySetInnerHTML={{
            __html: `setTimeout(() => location.reload(), 5000)`,
          }}
        />
      </div>
    );
  }

  if (valuation.status === "failed") {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="text-5xl mb-4">❌</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Valuation Failed</h2>
        <p className="text-gray-500 mb-6">An error occurred during the valuation pipeline.</p>
        <a href="/upload" className="bg-brand-600 text-white px-6 py-2.5 rounded-lg hover:bg-brand-700 transition">
          Try Again
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      {/* Header */}
      <div className="mb-8">
        <a href="/" className="text-sm text-gray-400 hover:text-gray-600 mb-2 inline-block">
          ← Back to Dashboard
        </a>
        <h1 className="text-3xl font-extrabold text-gray-900">
          {company?.name || "Valuation Results"}
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          {company?.industry && <span className="capitalize">{company.industry}</span>}
          {company?.founded_year && <span> • Founded {company.founded_year}</span>}
          {company?.employee_count && <span> • {company.employee_count} employees</span>}
        </p>
        <p className="text-xs text-gray-400 mt-2">
          Report generated: {new Date(valuation.created_at).toLocaleString("vi-VN")}
          {valuation.model_used && ` • AI: ${valuation.model_used}`}
          {valuation.tokens_used > 0 && ` • ${valuation.tokens_used.toLocaleString()} tokens`}
        </p>
      </div>

      <ValuationDashboard valuation={valuation} />
    </div>
  );
}
