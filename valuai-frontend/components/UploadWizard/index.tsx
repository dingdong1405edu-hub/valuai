"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import {
  createCompany,
  uploadDocument,
  crawlUrl,
  runValuation,
  pollValuationStatus,
} from "@/lib/api";
import { WIZARD_STEPS, DOC_TYPE_MAP } from "@/lib/types";

// ─── Types ─────────────────────────────────────────────────────────

interface StepFile {
  file: File | null;
  url: string;
  uploaded: boolean;
  error: string;
}

const emptyStep = (): StepFile => ({ file: null, url: "", uploaded: false, error: "" });

// ─── Content hints per step ────────────────────────────────────────

interface Hint {
  title: string;
  items: string[];
}

const STEP_HINTS: Record<number, Hint> = {
  1: {
    title: "What improves valuation accuracy:",
    items: [
      "Employee count — used to estimate revenue when financial data is missing",
      "Founded year — business maturity affects the scoring multiplier",
      "Industry — determines the correct P/E and EV/EBITDA benchmark multiples",
    ],
  },
  2: {
    title: "Your financial report should contain:",
    items: [
      "Doanh thu (Revenue) — the single most important figure for all three methods",
      "Lợi nhuận sau thuế (Net profit) — used in P/E comparable calculation",
      "EBITDA — earnings before interest, tax, depreciation & amortisation",
      "Tổng tài sản (Total assets) & Nợ phải trả (Total liabilities / debt)",
      "Năm tài chính (Fiscal year) — e.g. 2023 or 2024",
      "Tỷ lệ tăng trưởng doanh thu (YoY revenue growth %)",
    ],
  },
  3: {
    title: "Ideal website / fanpage content for AI analysis:",
    items: [
      "About Us — company history, mission, leadership team",
      "Products / Services — descriptions, pricing, key features",
      "Client logos, case studies, or testimonials",
      "Recent news, press releases, or milestones",
    ],
  },
  4: {
    title: "Your catalogue should ideally contain:",
    items: [
      "Product / service names and full descriptions",
      "Pricing tiers or price ranges",
      "Target customer segments",
      "Unique selling propositions (USPs) and competitive advantages",
    ],
  },
  5: {
    title: "Your capability profile should ideally contain:",
    items: [
      "Company overview and years in operation",
      "Major client names and representative projects",
      "Certifications, awards, or industry accreditations",
      "Delivery capacity and team size breakdown",
    ],
  },
  6: {
    title: "Your business plan should ideally contain:",
    items: [
      "Revenue projections for 3–5 years with assumptions",
      "Market size (TAM / SAM) and annual growth rate",
      "Competitive landscape and positioning",
      "Funding requirements and planned use of funds",
    ],
  },
  7: {
    title: "Owner / founder CV should ideally contain:",
    items: [
      "Years of experience in this specific industry",
      "Previous companies founded, led, or exited",
      "Educational background and domain expertise",
      "Key achievements, recognitions, or media coverage",
    ],
  },
  8: {
    title: "CRM / Accounting data should ideally contain:",
    items: [
      "Monthly or quarterly revenue breakdown",
      "Customer count and churn / retention rates",
      "Recurring vs. one-time revenue split",
      "Top customers by revenue contribution",
    ],
  },
};

// ─── Sub-components ────────────────────────────────────────────────

function ProgressBar({ current, total }: { current: number; total: number }) {
  const pct = Math.round((current / total) * 100);
  return (
    <div className="w-full bg-gray-200 rounded-full h-2 mb-6">
      <div
        className="bg-brand-600 h-2 rounded-full transition-all duration-500"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function StepIndicator({ steps, current }: { steps: typeof WIZARD_STEPS; current: number }) {
  return (
    <div className="flex items-center gap-1 mb-8 overflow-x-auto pb-2">
      {steps.map((s, i) => {
        const done = i < current - 1;
        const active = i === current - 1;
        return (
          <div key={s.id} className="flex items-center gap-1 shrink-0">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all ${
                done
                  ? "bg-green-500 border-green-500 text-white"
                  : active
                  ? "bg-brand-600 border-brand-600 text-white"
                  : "bg-white border-gray-300 text-gray-400"
              }`}
            >
              {done ? "✓" : s.id}
            </div>
            {i < steps.length - 1 && (
              <div className={`h-0.5 w-4 ${done ? "bg-green-400" : "bg-gray-200"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function ContentHint({ hint }: { hint: Hint }) {
  return (
    <div className="mt-5 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
      <div className="flex items-center gap-1.5 mb-2">
        <span className="text-amber-500 text-sm">💡</span>
        <span className="text-xs font-semibold text-amber-800">{hint.title}</span>
      </div>
      <ul className="space-y-1">
        {hint.items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-xs text-amber-800">
            <span className="w-1 h-1 rounded-full bg-amber-400 mt-1.5 shrink-0" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function FileDropzone({
  onFile,
  accept,
  label,
  file,
}: {
  onFile: (f: File) => void;
  accept?: Record<string, string[]>;
  label: string;
  file: File | null;
}) {
  const onDrop = useCallback((accepted: File[]) => { if (accepted[0]) onFile(accepted[0]); }, [onFile]);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept || {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
    },
    maxFiles: 1,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
        isDragActive
          ? "border-brand-400 bg-brand-50"
          : file
          ? "border-green-400 bg-green-50"
          : "border-gray-300 hover:border-brand-300 hover:bg-gray-50"
      }`}
    >
      <input {...getInputProps()} />
      {file ? (
        <div className="text-green-700">
          <div className="text-3xl mb-2">✓</div>
          <div className="font-semibold">{file.name}</div>
          <div className="text-sm text-green-600">{(file.size / 1024).toFixed(0)} KB — Click to change</div>
        </div>
      ) : (
        <div className="text-gray-500">
          <div className="text-4xl mb-3">📄</div>
          <div className="font-medium">{label}</div>
          <div className="text-sm mt-1">Drag & drop or click to browse</div>
        </div>
      )}
    </div>
  );
}

// ─── Main Wizard ───────────────────────────────────────────────────

export default function UploadWizard() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [error, setError] = useState("");

  // Step 1: Company info
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [foundedYear, setFoundedYear] = useState("");
  const [employees, setEmployees] = useState("");

  // Steps 2-8: files and URLs
  const [stepData, setStepData] = useState<Record<number, StepFile>>({
    2: emptyStep(), 3: emptyStep(), 4: emptyStep(),
    5: emptyStep(), 6: emptyStep(), 7: emptyStep(), 8: emptyStep(),
  });

  const [companyId, setCompanyId] = useState<string | null>(null);

  const updateStep = (n: number, patch: Partial<StepFile>) =>
    setStepData((prev) => ({ ...prev, [n]: { ...prev[n], ...patch } }));

  const canAdvance = (): boolean => {
    if (step === 1) return companyName.trim().length > 0 && industry.trim().length > 0;
    if (step === 2) return !!stepData[2].file; // financial report required
    return true; // steps 3-8 are optional
  };

  // ── Step 1: Create company ─────────────────────────────────────────
  const handleCreateCompany = async () => {
    setLoading(true);
    setError("");
    try {
      const c = await createCompany({
        name: companyName,
        industry,
        founded_year: foundedYear ? parseInt(foundedYear) : undefined,
        employee_count: employees ? parseInt(employees) : undefined,
      });
      setCompanyId(c.id);
      setStep(2);
    } catch (e: unknown) {
      setError((e as Error).message || "Failed to create company");
    } finally {
      setLoading(false);
    }
  };

  // ── Steps 2-7: Upload file ─────────────────────────────────────────
  const handleUploadStep = async (stepNum: number) => {
    if (!companyId) return;
    const data = stepData[stepNum];
    if (!data.file) { setStep(stepNum + 1); return; } // skip if no file

    const docType = DOC_TYPE_MAP[stepNum];
    if (!docType) { setStep(stepNum + 1); return; }

    setLoading(true);
    setError("");
    setStatusMsg(`Uploading and parsing ${data.file.name}...`);
    try {
      await uploadDocument(data.file, companyId, docType, (pct) => {
        setStatusMsg(`Uploading ${data.file!.name}... ${pct}%`);
      });
      setStatusMsg(`Parsing complete ✓`);
      updateStep(stepNum, { uploaded: true });
      setStep(stepNum + 1);
    } catch (e: unknown) {
      const msg = (e as Error).message || "Upload failed";
      updateStep(stepNum, { error: msg });
      setError(msg);
    } finally {
      setLoading(false);
      setStatusMsg("");
    }
  };

  // ── Step 3: Crawl URL ──────────────────────────────────────────────
  const handleCrawlStep = async () => {
    if (!companyId) return;
    const data = stepData[3];
    if (!data.url.trim()) { setStep(4); return; }

    setLoading(true);
    setError("");
    setStatusMsg(`Crawling ${data.url}...`);
    try {
      await crawlUrl(data.url, companyId, "website");
      updateStep(3, { uploaded: true });
      setStatusMsg("Crawl complete ✓");
      setStep(4);
    } catch (e: unknown) {
      setError((e as Error).message || "Crawl failed");
    } finally {
      setLoading(false);
      setStatusMsg("");
    }
  };

  // ── Step 9: Run valuation ──────────────────────────────────────────
  const handleRunValuation = async () => {
    if (!companyId) return;
    setLoading(true);
    setError("");
    setStatusMsg("Starting AI valuation pipeline...");
    try {
      const val = await runValuation(companyId);
      setStatusMsg("Valuation running (DCF + Comparable + Scorecard in parallel)...");
      const completed = await pollValuationStatus(
        val.id,
        (status) => setStatusMsg(`Pipeline status: ${status}...`),
        3000
      );
      router.push(`/results/${completed.id}`);
    } catch (e: unknown) {
      setError((e as Error).message || "Valuation failed");
      setLoading(false);
      setStatusMsg("");
    }
  };

  const handleNext = async () => {
    setError("");
    if (step === 1) return handleCreateCompany();
    if (step === 3) return handleCrawlStep();
    if (step === 9) return handleRunValuation();
    if ([2, 4, 5, 6, 7, 8].includes(step)) return handleUploadStep(step);
    setStep((s) => Math.min(s + 1, 9));
  };

  const currentStepInfo = WIZARD_STEPS[step - 1];
  const hint = STEP_HINTS[step];

  return (
    <div className="max-w-2xl mx-auto">
      <StepIndicator steps={WIZARD_STEPS} current={step} />
      <ProgressBar current={step} total={9} />

      <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
        {/* Step header */}
        <div className="mb-6">
          <div className="text-xs font-semibold text-brand-600 uppercase tracking-wider mb-1">
            Step {step} of 9
          </div>
          <h2 className="text-2xl font-bold text-gray-900">{currentStepInfo.title}</h2>
          <p className="text-gray-500 text-sm mt-1">{currentStepInfo.description}</p>
          {!currentStepInfo.required && (
            <span className="inline-block mt-2 text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
              Optional — click Next to skip
            </span>
          )}
        </div>

        {/* Step content */}
        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company Name *</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
                placeholder="e.g. Công ty TNHH ABC"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Industry *</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
              >
                <option value="">Select industry...</option>
                {["Technology", "Retail", "Manufacturing", "Food & Beverage", "Healthcare",
                  "Real Estate", "Education", "Logistics", "Finance", "Agriculture",
                  "Construction", "Services", "Other"].map((ind) => (
                  <option key={ind} value={ind.toLowerCase()}>{ind}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Founded Year</label>
                <input
                  type="number" min="1900" max={new Date().getFullYear()}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
                  placeholder="2015"
                  value={foundedYear}
                  onChange={(e) => setFoundedYear(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Employees</label>
                <input
                  type="number" min="1"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
                  placeholder="50"
                  value={employees}
                  onChange={(e) => setEmployees(e.target.value)}
                />
              </div>
            </div>
            {hint && <ContentHint hint={hint} />}
          </div>
        )}

        {step === 2 && (
          <>
            <FileDropzone
              onFile={(f) => updateStep(2, { file: f })}
              file={stepData[2].file}
              label="Upload Financial Report (PDF or Excel) *"
            />
            {hint && <ContentHint hint={hint} />}
          </>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Website URL</label>
              <input
                type="url"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
                placeholder="https://company.vn"
                value={stepData[3].url}
                onChange={(e) => updateStep(3, { url: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Facebook Fanpage URL</label>
              <input
                type="url"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
                placeholder="https://facebook.com/company"
                value={stepData[3].url.includes("facebook") ? stepData[3].url : ""}
                onChange={(e) => updateStep(3, { url: e.target.value })}
              />
            </div>
            {hint && <ContentHint hint={hint} />}
          </div>
        )}

        {[4, 5, 6, 7, 8].includes(step) && (
          <>
            <FileDropzone
              onFile={(f) => updateStep(step, { file: f })}
              file={stepData[step].file}
              label={`Upload ${currentStepInfo.title} (PDF)`}
            />
            {hint && <ContentHint hint={hint} />}
          </>
        )}

        {step === 9 && (
          <div className="space-y-4">
            <div className="bg-blue-50 rounded-xl p-5">
              <h3 className="font-semibold text-brand-800 mb-3">Valuation Summary</h3>
              <div className="text-sm text-gray-700 space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-gray-500">Company</span>
                  <span className="font-medium">{companyName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Industry</span>
                  <span className="font-medium capitalize">{industry}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Financial Report</span>
                  <span className={stepData[2].file ? "text-green-600 font-medium" : "text-red-500"}>
                    {stepData[2].file ? `✓ ${stepData[2].file.name}` : "Not uploaded"}
                  </span>
                </div>
                {Object.entries(stepData)
                  .filter(([k]) => parseInt(k) >= 3)
                  .map(([k, v]) => {
                    const s = WIZARD_STEPS[parseInt(k) - 1];
                    if (!v.file && !v.url) return null;
                    return (
                      <div key={k} className="flex justify-between">
                        <span className="text-gray-500">{s?.title}</span>
                        <span className="text-green-600 text-xs font-medium">
                          ✓ {v.file?.name || v.url.slice(0, 40)}
                        </span>
                      </div>
                    );
                  })}
              </div>
            </div>

            {/* What the AI will do */}
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-base">🤖</span>
                <span className="text-sm font-semibold text-gray-800">What the AI will do</span>
              </div>
              <ol className="space-y-2">
                {[
                  { icon: "📄", label: "Parse & extract", desc: "Gemini Vision reads your documents and Groq extracts structured financial + qualitative data" },
                  { icon: "📈", label: "DCF Valuation", desc: "Gemini estimates growth parameters; Python calculates 3 scenarios (conservative / base / optimistic)" },
                  { icon: "🏢", label: "Comparable Valuation", desc: "Applies Vietnamese listed-company multiples (P/E, EV/EBITDA, EV/Revenue) with a 25% private discount" },
                  { icon: "⭐", label: "Scorecard Valuation", desc: "Groq scores 10 qualitative criteria (0–10 each) and maps the total to a revenue multiplier" },
                  { icon: "⚖️", label: "Confidence-weighted synthesis", desc: "Three methods are blended by confidence × base weight (DCF 45% / Comparable 35% / Scorecard 20%)" },
                  { icon: "📝", label: "SWOT & Recommendations", desc: "Gemini generates a full SWOT analysis, strategic recommendations, and executive summary using your documents as context" },
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                      {i + 1}
                    </div>
                    <div>
                      <span className="text-xs font-semibold text-gray-800">{item.icon} {item.label} — </span>
                      <span className="text-xs text-gray-600">{item.desc}</span>
                    </div>
                  </li>
                ))}
              </ol>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
              <strong>Note:</strong> The valuation will run for ~2–3 minutes. You&apos;ll be
              redirected to the results page automatically.
            </div>
          </div>
        )}

        {/* Status / Error */}
        {statusMsg && (
          <div className="mt-4 flex items-center gap-2 text-sm text-brand-700 bg-brand-50 rounded-lg px-4 py-3">
            <svg className="animate-spin w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            {statusMsg}
          </div>
        )}
        {error && (
          <div className="mt-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            {error}
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-6 border-t border-gray-100">
          <button
            onClick={() => setStep((s) => Math.max(s - 1, 1))}
            disabled={step === 1 || loading}
            className="px-5 py-2.5 text-sm border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition"
          >
            ← Back
          </button>
          <button
            onClick={handleNext}
            disabled={!canAdvance() || loading}
            className="px-6 py-2.5 text-sm bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-sm"
          >
            {loading
              ? "Processing..."
              : step === 9
              ? "Start AI Valuation →"
              : step === 8 || !WIZARD_STEPS[step - 1]?.required
              ? "Next →"
              : "Save & Continue →"}
          </button>
        </div>
      </div>
    </div>
  );
}
