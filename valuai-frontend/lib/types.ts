export interface Company {
  id: string;
  name: string;
  industry?: string;
  founded_year?: number;
  employee_count?: number;
  description?: string;
  created_at: string;
}

export interface Document {
  id: string;
  company_id: string;
  type: string;
  file_url?: string;
  source_url?: string;
  status: "pending" | "parsing" | "parsed" | "extracted" | "failed";
  mime_type?: string;
  created_at: string;
}

export interface ScorecardCriterion {
  score: number;
  reason: string;
}

export interface Valuation {
  id: string;
  company_id: string;
  status: "pending" | "running" | "completed" | "failed";

  dcf_value?: number;
  dcf_assumptions?: Record<string, unknown>;
  dcf_confidence: number;

  comparable_value?: number;
  comparable_peers?: unknown[];
  comparable_confidence: number;

  scorecard_value?: number;
  scorecard_breakdown?: Record<string, ScorecardCriterion>;
  scorecard_total: number;
  scorecard_confidence: number;

  final_range_min?: number;
  final_range_mid?: number;
  final_range_max?: number;
  currency: string;

  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
  recommendations: string[];
  report_text?: string;
  model_used?: string;
  tokens_used: number;

  created_at: string;
}

export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string; details?: Record<string, unknown> };
  meta: { model_used: string; tokens: number };
}

export interface WizardStep {
  id: number;
  title: string;
  description: string;
  required: boolean;
}

export const WIZARD_STEPS: WizardStep[] = [
  { id: 1, title: "Company Info", description: "Basic company information", required: true },
  { id: 2, title: "Financial Report", description: "PDF or Excel financial statements", required: true },
  { id: 3, title: "Website / Fanpage", description: "Company website or social media URL", required: false },
  { id: 4, title: "Catalogue", description: "Product catalogue or brochure", required: false },
  { id: 5, title: "Capability Profile", description: "Company capability document", required: false },
  { id: 6, title: "Business Plan", description: "Business plan document", required: false },
  { id: 7, title: "Owner CV", description: "Founder / CEO curriculum vitae", required: false },
  { id: 8, title: "CRM / Accounting", description: "CRM export or accounting data", required: false },
  { id: 9, title: "Review & Submit", description: "Review all inputs and start valuation", required: true },
];

export const DOC_TYPE_MAP: Record<number, string> = {
  2: "financial_report",
  3: "web_content",
  4: "catalogue",
  5: "capability_profile",
  6: "business_plan",
  7: "cv",
  8: "accounting",
};
