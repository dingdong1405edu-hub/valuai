"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { Valuation, ProcessLog } from "@/lib/types";
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

// ─── Pipeline Diagram helpers ─────────────────────────────────────────

function DataRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between gap-2 text-xs">
      <span className="opacity-60 shrink-0">{label}</span>
      <span className="font-semibold text-right">
        {typeof value === "number" ? value.toLocaleString() : value}
      </span>
    </div>
  );
}

function ConfBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const bar = pct >= 60 ? "bg-green-500" : pct >= 40 ? "bg-yellow-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2 mt-1.5">
      <div className="flex-1 bg-white/60 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${bar}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] shrink-0 opacity-70">{pct}% conf.</span>
    </div>
  );
}

function DiagramArrowDown({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center my-3">
      <div className="w-px h-5 bg-gray-300" />
      {label && (
        <div className="text-[10px] text-gray-500 bg-white border border-gray-200 rounded-full px-3 py-0.5 my-1.5 whitespace-nowrap">
          {label}
        </div>
      )}
      <div className="w-px h-5 bg-gray-300" />
      <div
        style={{
          width: 0, height: 0,
          borderLeft: "5px solid transparent",
          borderRight: "5px solid transparent",
          borderTop: "6px solid #d1d5db",
        }}
      />
    </div>
  );
}

// ─── Pipeline Diagram ─────────────────────────────────────────────────

function PipelineDiagram({ valuation }: { valuation: Valuation }) {
  const log = valuation.process_log;

  const step1 = log?.steps?.[0];
  const step2 = log?.steps?.[1];
  const step3 = log?.steps?.[2];
  const step4 = log?.steps?.[3];
  const step5 = log?.steps?.[4];
  const step6 = log?.steps?.[5];

  const finExtracted = (step1?.details?.financial_extracted as Record<string, unknown>) || {};
  const qualFields   = (step1?.details?.qualitative_fields_found as string[]) || [];
  const dcfAssump    = (step2?.details?.assumptions as Record<string, unknown>) || {};
  const compSource   = (step3?.details?.source as string) || "fallback";
  const compMult     = (step3?.details?.multiples_used as Record<string, unknown>) || {};
  const totalScore   = (step4?.details?.total_score as number) ?? valuation.scorecard_total;
  const top3         = (step4?.details?.top_3_criteria as Array<{ criterion: string; score: number }>) || [];
  const weights      = (step5?.details?.weights_applied as Record<string, string>) || {};
  const ragChunks    = (step6?.details?.rag_chunks_used as number) || 0;
  const synthTokens  = (step6?.details?.tokens_used as number) || 0;
  const totalTokens  = log?.total_tokens || valuation.tokens_used;

  return (
    <div className="mb-8">
      <h3 className="text-lg font-bold text-gray-800 mb-1">AI Pipeline Diagram</h3>
      <p className="text-xs text-gray-500 mb-5">
        Visual overview of every step AI performed to produce this valuation
        {totalTokens > 0 && (
          <> · <span className="font-semibold text-gray-700">{totalTokens.toLocaleString()} tokens</span> total</>
        )}
      </p>

      {/* ── Stage 1: Documents → Parse & Extract (horizontal) ── */}
      <div className="flex items-stretch gap-0">
        <div className="flex-1 min-w-0 border border-slate-200 rounded-xl overflow-hidden bg-slate-50">
          <div className="px-4 py-3 bg-slate-100 border-b border-slate-200 flex items-center gap-2">
            <span>📁</span>
            <div>
              <div className="text-sm font-bold text-slate-800">Documents</div>
              <div className="text-[10px] text-slate-500">Data ingested by pipeline</div>
            </div>
          </div>
          <div className="px-4 py-3 space-y-1.5">
            {finExtracted.revenue   != null && <DataRow label="Revenue"    value={`${finExtracted.revenue} tỷ`} />}
            {finExtracted.profit    != null && <DataRow label="Net profit" value={`${finExtracted.profit} tỷ`} />}
            {finExtracted.ebitda    != null && <DataRow label="EBITDA"     value={`${finExtracted.ebitda} tỷ`} />}
            {finExtracted.employees != null && <DataRow label="Employees"  value={String(finExtracted.employees)} />}
            {finExtracted.industry  && <DataRow label="Industry" value={String(finExtracted.industry)} />}
            {qualFields.length > 0  && <DataRow label="Qualitative fields" value={`${qualFields.length} found`} />}
            {Object.keys(finExtracted).length === 0 && qualFields.length === 0 && (
              <div className="text-xs text-slate-400 italic">Data shown after valuation runs</div>
            )}
          </div>
        </div>

        {/* → */}
        <div className="flex items-center px-2 shrink-0">
          <div className="w-5 h-px bg-gray-300" />
          <div style={{ width:0, height:0, borderTop:"5px solid transparent", borderBottom:"5px solid transparent", borderLeft:"6px solid #d1d5db" }} />
        </div>

        <div className="flex-1 min-w-0 border border-slate-200 rounded-xl overflow-hidden bg-slate-50">
          <div className="px-4 py-3 bg-slate-100 border-b border-slate-200 flex items-center gap-2">
            <span>🔍</span>
            <div>
              <div className="text-sm font-bold text-slate-800">Parse & Extract</div>
              <div className="text-[10px] text-slate-500">AI reads all documents</div>
            </div>
          </div>
          <div className="px-4 py-3 space-y-1.5">
            <DataRow label="PDF / image" value="Gemini Vision" />
            <DataRow label="JSON extract" value="Groq llama-3.3-70b" />
            <DataRow label="VN number fallback" value="Regex scanner" />
            <DataRow label="Embeddings" value="gemini-embedding-001" />
          </div>
        </div>
      </div>

      <DiagramArrowDown label="3 valuation methods in parallel" />

      {/* ── Stage 2: 3 parallel methods ── */}
      <div className="border border-brand-200 rounded-xl overflow-hidden">
        <div className="bg-brand-50 border-b border-brand-200 px-4 py-2 flex items-center gap-2">
          <span className="text-sm">⚡</span>
          <span className="text-xs font-bold text-brand-700">asyncio.gather — DCF · Comparable · Scorecard run simultaneously</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-gray-200">

          {/* DCF */}
          <div className="p-4 bg-blue-50">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">📈</span>
              <div>
                <div className="text-sm font-bold text-blue-800">DCF Valuation</div>
                <div className="text-[10px] text-blue-500">Gemini 2.0 Flash</div>
              </div>
            </div>
            <div className="space-y-1.5 text-blue-800 mb-3">
              {dcfAssump.base_revenue_billions != null
                ? <DataRow label="Base revenue" value={`${dcfAssump.base_revenue_billions} tỷ`} />
                : <div className="text-xs text-blue-400 italic">5-yr FCF + Gordon Growth terminal value</div>}
              {dcfAssump.growth_rate   != null && <DataRow label="Growth rate"   value={`${(Number(dcfAssump.growth_rate)   * 100).toFixed(0)}%/yr`} />}
              {dcfAssump.ebitda_margin != null && <DataRow label="EBITDA margin" value={`${(Number(dcfAssump.ebitda_margin) * 100).toFixed(0)}%`} />}
              {dcfAssump.wacc          != null && <DataRow label="WACC"          value={`${(Number(dcfAssump.wacc)          * 100).toFixed(0)}%`} />}
            </div>
            <div className="border-t border-blue-200 pt-3">
              <div className="text-xl font-extrabold text-blue-900 mb-0.5">{formatVND(valuation.dcf_value)}</div>
              <ConfBar confidence={valuation.dcf_confidence} />
              {weights.dcf && <div className="text-[10px] text-blue-600 mt-1">Synthesis weight: <span className="font-bold">{weights.dcf}</span></div>}
            </div>
          </div>

          {/* Comparable */}
          <div className="p-4 bg-green-50">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">🏢</span>
              <div>
                <div className="text-sm font-bold text-green-800">Comparable</div>
                <div className="text-[10px] text-green-500">
                  {compSource === "fireant" ? "HOSE/HNX live data" : "Industry benchmark table"}
                </div>
              </div>
            </div>
            <div className="space-y-1.5 text-green-800 mb-3">
              {compMult.pe         != null ? <DataRow label="P/E"         value={`${compMult.pe}×`}         /> : null}
              {compMult.ev_ebitda  != null ? <DataRow label="EV/EBITDA"   value={`${compMult.ev_ebitda}×`}  /> : null}
              {compMult.ev_revenue != null ? <DataRow label="EV/Revenue"  value={`${compMult.ev_revenue}×`} /> : null}
              {Object.keys(compMult).length === 0 && <div className="text-xs text-green-400 italic">Market multiple approach</div>}
              <DataRow label="Private discount" value="−25%" />
            </div>
            <div className="border-t border-green-200 pt-3">
              <div className="text-xl font-extrabold text-green-900 mb-0.5">{formatVND(valuation.comparable_value)}</div>
              <ConfBar confidence={valuation.comparable_confidence} />
              {weights.comparable && <div className="text-[10px] text-green-600 mt-1">Synthesis weight: <span className="font-bold">{weights.comparable}</span></div>}
            </div>
          </div>

          {/* Scorecard */}
          <div className="p-4 bg-purple-50">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">⭐</span>
              <div>
                <div className="text-sm font-bold text-purple-800">Scorecard</div>
                <div className="text-[10px] text-purple-500">Groq llama-3.3-70b</div>
              </div>
            </div>
            <div className="space-y-1.5 text-purple-800 mb-3">
              <DataRow label="Total score" value={`${(totalScore || 0).toFixed(1)} / 10`} />
              {top3.length > 0
                ? top3.map((c, i) => (
                    <div key={i} className="flex items-baseline gap-1.5 text-xs">
                      <span className="font-bold shrink-0">{c.score}/10</span>
                      <span className="text-purple-600 truncate">{c.criterion}</span>
                    </div>
                  ))
                : <div className="text-xs text-purple-400 italic">10-criterion qualitative scoring</div>
              }
            </div>
            <div className="border-t border-purple-200 pt-3">
              <div className="text-xl font-extrabold text-purple-900 mb-0.5">{formatVND(valuation.scorecard_value)}</div>
              <ConfBar confidence={valuation.scorecard_confidence} />
              {weights.scorecard && <div className="text-[10px] text-purple-600 mt-1">Synthesis weight: <span className="font-bold">{weights.scorecard}</span></div>}
            </div>
          </div>
        </div>
      </div>

      <DiagramArrowDown label="confidence-weighted blend" />

      {/* ── Stage 3: Synthesis ── */}
      <div className="border border-indigo-200 rounded-xl overflow-hidden bg-indigo-50">
        <div className="px-4 py-3 bg-indigo-100 border-b border-indigo-200 flex items-center gap-2">
          <span>⚖️</span>
          <div>
            <div className="text-sm font-bold text-indigo-800">Confidence-Weighted Synthesis</div>
            <div className="text-[10px] text-indigo-500">
              weight = max(conf, 0.10) × base_weight (DCF 45% / Comparable 35% / Scorecard 20%)
            </div>
          </div>
        </div>
        <div className="px-4 py-4">
          {Object.keys(weights).length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {Object.entries(weights).map(([m, w]) => (
                <div key={m} className="flex items-center gap-1.5 bg-white border border-indigo-200 rounded-full px-3 py-1">
                  <span className="text-xs text-indigo-600 capitalize">{m}</span>
                  <span className="text-xs font-bold text-indigo-900">{w}</span>
                </div>
              ))}
            </div>
          )}
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center bg-white border border-indigo-200 rounded-xl p-3">
              <div className="text-[10px] text-indigo-400 mb-1">Minimum</div>
              <div className="text-base font-bold text-indigo-700">{formatVND(valuation.final_range_min)}</div>
            </div>
            <div className="text-center bg-indigo-600 rounded-xl p-3">
              <div className="text-[10px] text-indigo-200 mb-1">Mid-point</div>
              <div className="text-base font-bold text-white">{formatVND(valuation.final_range_mid)}</div>
            </div>
            <div className="text-center bg-white border border-indigo-200 rounded-xl p-3">
              <div className="text-[10px] text-indigo-400 mb-1">Maximum</div>
              <div className="text-base font-bold text-indigo-700">{formatVND(valuation.final_range_max)}</div>
            </div>
          </div>
        </div>
      </div>

      <DiagramArrowDown />

      {/* ── Stage 4: SWOT + Report ── */}
      <div className="border border-amber-200 rounded-xl overflow-hidden bg-amber-50">
        <div className="px-4 py-3 bg-amber-100 border-b border-amber-200 flex items-center gap-2">
          <span>📝</span>
          <div>
            <div className="text-sm font-bold text-amber-800">SWOT Analysis & Recommendations</div>
            <div className="text-[10px] text-amber-500">Gemini 2.0 Flash · pgvector RAG context</div>
          </div>
        </div>
        <div className="px-4 py-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
            {[
              { label: "Strengths",     count: valuation.strengths?.length     || 0, bg: "bg-green-50  border-green-200  text-green-700" },
              { label: "Weaknesses",    count: valuation.weaknesses?.length    || 0, bg: "bg-red-50    border-red-200    text-red-700" },
              { label: "Opportunities", count: valuation.opportunities?.length || 0, bg: "bg-blue-50   border-blue-200   text-blue-700" },
              { label: "Threats",       count: valuation.threats?.length       || 0, bg: "bg-orange-50 border-orange-200 text-orange-700" },
            ].map((s) => (
              <div key={s.label} className={`text-center border rounded-lg p-2 ${s.bg}`}>
                <div className="text-xl font-bold">{s.count}</div>
                <div className="text-[10px]">{s.label}</div>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-4 text-xs text-amber-800">
            <span>📋 <span className="font-semibold">{valuation.recommendations?.length || 0}</span> recommendations</span>
            {ragChunks    > 0 && <span>🔍 <span className="font-semibold">{ragChunks}</span> RAG chunks used</span>}
            {synthTokens  > 0 && <span>🎯 <span className="font-semibold">{synthTokens.toLocaleString()}</span> tokens for SWOT</span>}
          </div>
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

      {/* Pipeline Diagram */}
      <PipelineDiagram valuation={valuation} />

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
