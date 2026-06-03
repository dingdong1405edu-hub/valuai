"""Agent 1 — Extractor: BCTC file → structured JSON financials."""
import base64
import io
from pathlib import Path

from agent_common import (call_opus, call_opus_multimodal,
                          parse_json_response, with_locked_schema)

_SENTINEL = "Return ONLY this JSON shape"

_SCHEMA_BLOCK = """{
  "financials": {
    "company": {
      "name": "...", "tax_code": "...", "address": "...",
      "industry": "...", "report_type": "..."
    },
    "period": {
      "current": {"label": "Năm 20XX"},
      "previous": {"label": "Năm 20XX"}
    },
    "currency": "VND",
    "unit": "triệu đồng | nghìn đồng | tỷ đồng",
    "balance_sheet": {
      "current": {
        "assets": {
          "cash_and_equivalents": null,
          "short_term_investments": null,
          "short_term_receivables": null,
          "inventory": null,
          "other_current_assets": null,
          "current_assets_total": null,
          "long_term_receivables": null,
          "fixed_assets": null,
          "investment_properties": null,
          "long_term_investments": null,
          "other_non_current_assets": null,
          "non_current_assets_total": null,
          "total_assets": null
        },
        "liabilities": {
          "short_term_debt": null,
          "accounts_payable": null,
          "other_current_liabilities": null,
          "current_liabilities_total": null,
          "long_term_debt": null,
          "other_non_current_liabilities": null,
          "non_current_liabilities_total": null,
          "total_liabilities": null
        },
        "equity": {
          "share_capital": null,
          "retained_earnings": null,
          "other_equity": null,
          "total_equity": null
        }
      },
      "previous": {}
    },
    "income_statement": {
      "current": {
        "revenue": null, "revenue_deductions": null,
        "net_revenue": null, "cogs": null, "gross_profit": null,
        "financial_income": null, "financial_expense": null,
        "interest_expense": null, "selling_expense": null,
        "admin_expense": null, "operating_profit": null,
        "other_income": null, "other_expense": null,
        "profit_before_tax": null, "current_tax": null,
        "deferred_tax": null, "net_profit_after_tax": null, "eps": null
      },
      "previous": {}
    },
    "cash_flow": {
      "current": {
        "cf_operating": null, "cf_investing": null,
        "cf_financing": null, "net_cf": null, "ending_cash": null
      },
      "previous": {}
    },
    "raw_transcription": "...",
    "notes": "..."
  }
}"""

_DEFAULT_PROMPT = """Bạn là chuyên gia phân tích tài chính Việt Nam. Hãy trích xuất toàn bộ dữ liệu từ Báo cáo Tài chính (BCTC) được cung cấp.

QUY TẮC SỐ HỌC VIỆT NAM (BẮT BUỘC):
- Dấu "." = phân cách hàng nghìn: "1.234.567" → 1234567
- Dấu "," = thập phân: "1.234,56" → 1234.56
- Ô trống / dấu "-" → null (KHÔNG phải 0)
- Ngoặc đơn (1.234) = số âm → -1234
- Giữ nguyên đơn vị từ BCTC (nghìn đồng / triệu đồng / tỷ đồng)
- Kiểm tra: total_assets = total_liabilities + total_equity

Ghi nhận raw_transcription: chép nguyên văn các bảng số chính.
Ghi nhận notes: mọi điểm bất thường (số không cân bằng, thiếu dữ liệu...).

"""

_MIME_MAP = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

_SYSTEM = "You are a Vietnamese financial analysis expert. Extract financial data from balance sheets (BCTC) accurately."


def _extract_pdf_text(data: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


def extract(file_path: str, prompt_override: str = "",
            api_key: str = None) -> dict:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    data = path.read_bytes()

    preamble = prompt_override.strip() if prompt_override and prompt_override.strip() else _DEFAULT_PROMPT
    full_prompt = f"{preamble}\n\n{_SENTINEL}:\n{_SCHEMA_BLOCK}"

    if suffix == ".pdf":
        pdf_text = _extract_pdf_text(data)
        prompt = f"{full_prompt}\n\nNỘI DUNG BÁO CÁO TÀI CHÍNH:\n{pdf_text}"
        raw = call_opus(prompt, system=_SYSTEM, max_tokens=16000, effort="medium")
    else:
        mime = _MIME_MAP.get(suffix, "image/jpeg")
        b64 = base64.standard_b64encode(data).decode("utf-8")
        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": mime, "data": b64},
            },
            {"type": "text", "text": full_prompt},
        ]
        raw = call_opus_multimodal(content, system=_SYSTEM, max_tokens=16000, effort="medium")

    result = parse_json_response(raw)

    if "financials" in result:
        return result
    return {"financials": result}
