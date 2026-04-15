import axios from "axios";
import type { APIResponse, Company, Document, Valuation } from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000, // 2 min for long uploads/valuations
});

// ── Companies ──────────────────────────────────────────────────────────────

export async function createCompany(data: {
  name: string;
  industry?: string;
  founded_year?: number;
  employee_count?: number;
  description?: string;
}): Promise<Company> {
  const res = await api.post<APIResponse<Company>>("/api/companies", data);
  if (!res.data.success || !res.data.data) throw new Error(res.data.error?.message || "Failed to create company");
  return res.data.data;
}

export async function getCompany(id: string): Promise<Company> {
  const res = await api.get<APIResponse<Company>>(`/api/companies/${id}`);
  if (!res.data.success || !res.data.data) throw new Error("Company not found");
  return res.data.data;
}

export async function listCompanies(): Promise<Company[]> {
  const res = await api.get<APIResponse<Company[]>>("/api/companies");
  return res.data.data || [];
}

// ── Documents ──────────────────────────────────────────────────────────────

export async function uploadDocument(
  file: File,
  companyId: string,
  docType: string,
  onProgress?: (pct: number) => void
): Promise<Document> {
  const form = new FormData();
  form.append("file", file);
  form.append("company_id", companyId);
  form.append("doc_type", docType);

  const res = await api.post<APIResponse<Document>>("/api/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
  if (!res.data.success || !res.data.data) throw new Error(res.data.error?.message || "Upload failed");
  return res.data.data;
}

export async function crawlUrl(
  url: string,
  companyId: string,
  sourceType: string = "website"
): Promise<Document> {
  const res = await api.post<APIResponse<Document>>("/api/documents/crawl", {
    company_id: companyId,
    url,
    source_type: sourceType,
  });
  if (!res.data.success || !res.data.data) throw new Error(res.data.error?.message || "Crawl failed");
  return res.data.data;
}

export async function listDocuments(companyId: string): Promise<Document[]> {
  const res = await api.get<APIResponse<Document[]>>(`/api/documents/company/${companyId}`);
  return res.data.data || [];
}

// ── Valuations ─────────────────────────────────────────────────────────────

export async function runValuation(
  companyId: string,
  wacc: number = 0.15,
  privateDiscount: number = 0.25
): Promise<Valuation> {
  const res = await api.post<APIResponse<Valuation>>("/api/valuations/run", {
    company_id: companyId,
    wacc,
    private_discount: privateDiscount,
  });
  if (!res.data.success || !res.data.data) throw new Error(res.data.error?.message || "Valuation failed");
  return res.data.data;
}

export async function getValuation(id: string): Promise<Valuation> {
  const res = await api.get<APIResponse<Valuation>>(`/api/valuations/${id}`);
  if (!res.data.success || !res.data.data) throw new Error("Valuation not found");
  return res.data.data;
}

export async function getValuationStatus(
  id: string
): Promise<{ id: string; status: string; error?: string; final_range_mid?: number }> {
  const res = await api.get(`/api/valuations/${id}/status`);
  return res.data.data;
}

export async function getLatestValuation(companyId: string): Promise<Valuation | null> {
  try {
    const res = await api.get<APIResponse<Valuation>>(`/api/valuations/company/${companyId}/latest`);
    return res.data.data || null;
  } catch {
    return null;
  }
}

export async function exportPdf(valuationId: string): Promise<{ pdf_path: string }> {
  const res = await api.post(`/api/valuations/${valuationId}/export`);
  return res.data.data;
}

// ── Helpers ────────────────────────────────────────────────────────────────

export function formatVND(value?: number | null): string {
  if (!value) return "N/A";
  const billions = value > 1_000_000 ? value / 1_000_000_000 : value;
  return `${billions.toLocaleString("vi-VN", { maximumFractionDigits: 1 })} tỷ ₫`;
}

/** Poll valuation status until completed or failed. */
export async function pollValuationStatus(
  valuationId: string,
  onUpdate: (status: string) => void,
  intervalMs: number = 3000
): Promise<Valuation> {
  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      try {
        const statusData = await getValuationStatus(valuationId);
        onUpdate(statusData.status);
        if (statusData.status === "completed") {
          clearInterval(interval);
          const full = await getValuation(valuationId);
          resolve(full);
        } else if (statusData.status === "failed") {
          clearInterval(interval);
          reject(new Error(statusData.error || "Valuation failed"));
        }
      } catch (err) {
        clearInterval(interval);
        reject(err);
      }
    }, intervalMs);
  });
}
