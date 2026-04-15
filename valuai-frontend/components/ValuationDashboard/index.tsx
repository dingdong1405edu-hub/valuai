"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { Valuation } from "@/lib/types";
import { formatVND, exportPdf } from "@/lib/api";
import { useState } from "react";

// ─── Sub-components ─────────────────────────────────────────────────

function RangeCard({
  min, mid, max,
}: {
  min?: number | null;
  mid?: number | null;
  max?: number | null;
}) {
  const safeMin = min ?? 0;
  const safeMid = mid ?? 0;
  const safeMax = max ?? 0;
  const range = safeMax - safeMin;

  return (
    <div className="bg-gradient-to-br from-brand-900 to-brand-700 text-white rounded-2xl p-8 shadow-xl mb-6">
      <div className="text-sm font-semibold uppercase tracking-widest opacity-70 mb-2">
        Estimated Business Value
      </div>
      <div className="text-5xl font-extrabold mb-1">{formatVND(safeMid)}</div>
      <div className="text-blue-200 text-sm mb-6">Mid-point valuation</div>

      {/* Range bar */}
      <div className="relative h-3 bg-blue-800 rounded-full mb-3">
        {range > 0 && (
          <div
            className="absolute h-3 bg-blue-400 rounded-full"
            style={{
              left: `${((safeMin - safeMin) / range) * 100}%`,
              right: `${100 - ((safeMax - safeMin) / range) * 100}%`,
              width: `${((safeMax - safeMin) / range) * 100}%`,
            }}
          />
        )}
        <div
          className="absolute w-4 h-4 bg-white rounded-full shadow -top-0.5 -translate-x-1/2"
          style={{ left: range > 0 ? `${((safeMid - safeMin) / range) * 100}%` : "50%" }}
        />
      </div>

      <div className="flex justify-between text-xs text-blue-200">
        <div>
          <div className="font-semibold text-white">{formatVND(safeMin)}</div>
          <div>Minimum</div>
        </div>
        <div className="text-center">
          <div className="font-semibold text-white">{formatVND(safeMid)}</div>
          <div>Mid-point</div>
        </div>
        <div className="text-right">
          <div className="font-semibold text-white">{formatVND(safeMax)}</div>
          <div>Maximum</div>
        </div>
      </div>
    </div>
  );
}

function MethodCard({
  title,
  value,
  confidence,
  color,
  icon,
}: {
  title: string;
  value?: number | null;
  confidence: number;
  color: string;
  icon: string;
}) {
  return (
    <div className={`border rounded-xl p-5 ${color}`}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">{icon}</span>
        <span className="font-semibold text-sm">{title}</span>
      </div>
      <div className="text-2xl font-bold mb-1">{formatVND(value)}</div>
      <div className="flex items-center gap-2 mt-2">
        <div className="flex-1 bg-white/50 rounded-full h-1.5">
          <div
            className="bg-current h-1.5 rounded-full"
            style={{ width: `${confidence * 100}%` }}
          />
        </div>
        <span className="text-xs opacity-75">{(confidence * 100).toFixed(0)}%</span>
      </div>
      <div className="text-xs opacity-60 mt-1">Confidence</div>
    </div>
  );
}

function SWOTSection({ strengths, weaknesses, opportunities, threats }: {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}) {
  const sections = [
    { label: "Strengths", items: strengths, bg: "bg-green-50 border-green-200", badge: "bg-green-100 text-green-800", dot: "bg-green-500" },
    { label: "Weaknesses", items: weaknesses, bg: "bg-red-50 border-red-200", badge: "bg-red-100 text-red-800", dot: "bg-red-500" },
    { label: "Opportunities", items: opportunities, bg: "bg-blue-50 border-blue-200", badge: "bg-blue-100 text-blue-800", dot: "bg-blue-500" },
    { label: "Threats", items: threats, bg: "bg-orange-50 border-orange-200", badge: "bg-orange-100 text-orange-800", dot: "bg-orange-500" },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
      {sections.map((s) => (
        <div key={s.label} className={`border rounded-xl p-5 ${s.bg}`}>
          <div className={`inline-block text-xs font-bold px-2 py-0.5 rounded-full mb-3 ${s.badge}`}>
            {s.label}
          </div>
          <ul className="space-y-2">
            {(s.items || []).slice(0, 4).map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${s.dot}`} />
                {item}
              </li>
            ))}
            {(s.items || []).length === 0 && (
              <li className="text-xs text-gray-400 italic">No data</li>
            )}
          </ul>
        </div>
      ))}
    </div>
  );
}

function ScorecardRadar({ breakdown }: { breakdown: Record<string, { score: number; reason: string }> }) {
  const LABEL_MAP: Record<string, string> = {
    team_experience: "Team",
    market_size: "Market",
    product_uniqueness: "Product",
    customer_traction: "Customers",
    competitive_moat: "Moat",
    financial_health: "Financials",
    business_model: "Biz Model",
    legal_compliance: "Legal",
    esg_sustainability: "ESG",
    growth_potential: "Growth",
  };

  const data = Object.entries(breakdown).map(([key, val]) => ({
    subject: LABEL_MAP[key] || key,
    score: typeof val === "object" ? val.score : 5,
    fullMark: 10,
  }));

  if (data.length === 0) return null;

  return (
    <div className="mb-8">
      <h3 className="text-lg font-bold text-gray-800 mb-4">Scorecard Breakdown</h3>
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart data={data}>
            <PolarGrid strokeOpacity={0.3} />
            <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: "#6b7280" }} />
            <Radar
              name="Score"
              dataKey="score"
              stroke="#2563eb"
              fill="#2563eb"
              fillOpacity={0.25}
              strokeWidth={2}
            />
            <Tooltip formatter={(v: number) => [`${v}/10`, "Score"]} />
          </RadarChart>
        </ResponsiveContainer>

        {/* Score table */}
        <div className="mt-4 grid grid-cols-2 gap-2">
          {Object.entries(breakdown).map(([key, val]) => {
            const score = typeof val === "object" ? val.score : 0;
            const reason = typeof val === "object" ? val.reason : "";
            return (
              <div key={key} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xs font-bold shrink-0">
                  {score}
                </div>
                <div>
                  <div className="text-xs font-semibold text-gray-700">
                    {(LABEL_MAP[key] || key).replace(/_/g, " ")}
                  </div>
                  <div className="text-xs text-gray-400 truncate max-w-[150px]">{reason}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── Main Dashboard ─────────────────────────────────────────────────

export default function ValuationDashboard({ valuation }: { valuation: Valuation }) {
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState("");

  const handleExport = async () => {
    setExporting(true);
    setExportMsg("Generating PDF...");
    try {
      const result = await exportPdf(valuation.id);
      setExportMsg(`PDF ready: ${result.pdf_path}`);
    } catch (e: unknown) {
      setExportMsg(`Export failed: ${(e as Error).message}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div>
      {/* Valuation Range */}
      <RangeCard
        min={valuation.final_range_min}
        mid={valuation.final_range_mid}
        max={valuation.final_range_max}
      />

      {/* Method Breakdown */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <MethodCard
          title="DCF"
          value={valuation.dcf_value}
          confidence={valuation.dcf_confidence}
          color="bg-blue-50 border-blue-200 text-blue-800"
          icon="📈"
        />
        <MethodCard
          title="Comparable"
          value={valuation.comparable_value}
          confidence={valuation.comparable_confidence}
          color="bg-green-50 border-green-200 text-green-800"
          icon="🏢"
        />
        <MethodCard
          title="Scorecard"
          value={valuation.scorecard_value}
          confidence={valuation.scorecard_confidence}
          color="bg-purple-50 border-purple-200 text-purple-800"
          icon="⭐"
        />
      </div>

      {/* Scorecard Radar */}
      {valuation.scorecard_breakdown && Object.keys(valuation.scorecard_breakdown).length > 0 && (
        <ScorecardRadar breakdown={valuation.scorecard_breakdown as Record<string, { score: number; reason: string }>} />
      )}

      {/* SWOT */}
      <h3 className="text-lg font-bold text-gray-800 mb-4">SWOT Analysis</h3>
      <SWOTSection
        strengths={valuation.strengths}
        weaknesses={valuation.weaknesses}
        opportunities={valuation.opportunities}
        threats={valuation.threats}
      />

      {/* Recommendations */}
      {(valuation.recommendations || []).length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Strategic Recommendations</h3>
          <div className="space-y-3">
            {valuation.recommendations.map((rec, i) => (
              <div key={i} className="flex gap-3 bg-white border border-gray-200 rounded-xl p-4">
                <div className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center text-sm font-bold shrink-0">
                  {i + 1}
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{rec}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Executive Summary */}
      {valuation.report_text && (
        <div className="mb-8">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Executive Summary</h3>
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
            {valuation.report_text}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={handleExport}
          disabled={exporting}
          className="px-5 py-2.5 bg-brand-600 text-white rounded-lg text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 transition shadow-sm"
        >
          {exporting ? "Generating..." : "📄 Export PDF Report"}
        </button>
        <a
          href="/upload"
          className="px-5 py-2.5 border border-gray-300 text-gray-700 rounded-lg text-sm font-semibold hover:bg-gray-50 transition"
        >
          + New Valuation
        </a>
      </div>
      {exportMsg && (
        <div className="mt-3 text-xs text-gray-500 bg-gray-100 rounded-lg px-3 py-2">{exportMsg}</div>
      )}
    </div>
  );
}
