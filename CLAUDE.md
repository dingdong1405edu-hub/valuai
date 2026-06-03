# ValuAI — Tài liệu đầy đủ để xây lại từ đầu

> Phiên bản tài liệu: 2.0 | Ngày: 2026-06-03  
> Mục đích: Ghi lại toàn bộ thiết kế, luồng AI, cách render output — đủ để rebuild hoàn toàn.

---

## 1. Tổng quan dự án

**ValuAI** là nền tảng định giá doanh nghiệp vừa và nhỏ (SME) thị trường Việt Nam.

**Quy trình cốt lõi:**
1. User upload file Báo cáo tài chính (BCTC) — PDF hoặc ảnh
2. Hệ thống chạy pipeline 9 agent AI
3. Xuất báo cáo PDF chuyên nghiệp chuẩn sell-side equity research

**Business model: Freemium 2 phase**
- **Phase 1 (Miễn phí):** Xử lý BCTC, tạo "trailer" PDF xem trước ~4 trang
- **Phase 2 (Trả phí):** Sau thanh toán PayOS → báo cáo đầy đủ ~37 trang + explainer PDF + Excel

---

## 2. Stack kỹ thuật

| Layer | Công nghệ |
|---|---|
| Web framework | FastAPI + Python 3.12/3.13 |
| AI models | Claude API (Anthropic) — Opus 4.7, Haiku 4.5 |
| Database | PostgreSQL (asyncpg) via Railway |
| PDF render (chính) | Matplotlib — `PdfPages`, A4 = `(8.27, 11.69)` inches |
| PDF render (phụ) | HTML → Playwright/Chromium (trailer + explainer) |
| Excel export | openpyxl |
| Payment | PayOS (api-merchant.payos.vn) |
| HTML parse | BeautifulSoup4 |
| HTTP client | httpx (async + sync) |
| Auth | JWT (python-jose) + bcrypt |
| Deploy | Railway (Docker) |

---

## 3. Cấu trúc thư mục

```
phien-ban-2/
├── main.py                    # FastAPI app, orchestrator Phase 1+2
├── auth.py                    # JWT + bcrypt helpers
├── db.py                      # asyncpg pool, tất cả queries
├── config_schema.py           # DEFAULT_CONFIG, normalize_config, validate_config
├── config_store.py            # load/save/version active config
├── agent_common.py            # build_prompt, with_locked_schema, validate
├── html_pdf.py                # Playwright render_html_to_pdf
├── sample_data.py             # SAMPLE_PAYLOAD cho preview admin
├── explanations_default.py    # EXPLANATIONS_DEFAULT (explainer PDF)
├── agents/
│   ├── brand_scraper.py       # Agent 0: scrape website → brand colors + logo
│   ├── extractor.py           # Agent 1: BCTC → JSON financials
│   ├── industry.py            # Agent 2: phân tích ngành
│   ├── business_profile.py    # Agent 3: tổng quan DN
│   ├── analyzer.py            # Agent 4: tính ratio (Python thuần, không LLM)
│   ├── projector.py           # Agent 5: dự phóng 5 năm
│   ├── valuator.py            # Agent 6: DCF + Multiples + Sensitivity
│   ├── thesis_writer.py       # Agent 7: viết báo cáo đầu tư
│   ├── renderer.py            # Agent 8a: matplotlib ~37 trang PDF
│   ├── trailer_renderer.py    # matplotlib trailer (fallback)
│   ├── trailer_html.py        # HTML trailer (primary)
│   ├── explainer_renderer.py  # matplotlib explainer (fallback)
│   ├── explainer_html.py      # HTML explainer (primary)
│   ├── valuation_html.py      # HTML full report (preview only)
│   └── excel_exporter.py      # openpyxl Excel export
├── static/
│   ├── index.html             # Landing page
│   ├── app.html               # Upload UI
│   └── admin.html             # Admin panel (config + stats)
├── uploads/                   # File upload tạm thời (xóa sau xử lý)
│   └── config/                # Logo + ảnh admin upload
└── outputs/                   # File output của job
```

---

## 4. Luồng pipeline đầy đủ

```
User upload BCTC (PDF/ảnh)
       │
       ▼  POST /api/process
       │  Snapshot config → lưu vào job
       │
       ├──────────────────────────────────────────── PHASE 1 (FREE) ──
       │
       ├─── asyncio.gather ───────────────────────────────────────────┐
       │    Agent 0: brand_scraper(website_url)                       │
       │    → brand { primary, secondary, primary_light,              │
       │               accent, logo_b64, logo_mime }                  │
       │                                                              │
       │    Agent 1: extractor(file_path)                             │
       │    → financials { company, period, currency, unit,           │
       │                   balance_sheet, income_statement, cash_flow }│
       └──────────────────────────────────────────────────────────────┘
              │
              ├─── asyncio.gather ──────────────────────────────────────┐
              │    Agent 2: analyze_industry(financials)                │
              │    → industry { industry_name, market_size, swot,       │
              │                 porters_5_forces, competitors, ... }    │
              │                                                         │
              │    Agent 4: analyze(financials)  ← PYTHON ONLY, no LLM │
              │    → ratios { liquidity, leverage, profitability,       │
              │               efficiency, growth, dupont, wc_days,      │
              │               quality_of_earnings, common_size, ... }  │
              └─────────────────────────────────────────────────────────┘
                    │
                    ▼
              Agent 3: analyze_business(financials, industry)
              → business { business_model, shareholders, management,
                           value_chain, competitive_position, ... }
                    │
                    ▼
              Render Trailer PDF (HTML/Playwright primary,
                                  matplotlib fallback) ~4 trang
                    │
              Lưu partial.json = { a0_brand, a1, a2_industry,
                                   a3_business, a4_ratios, brand, config }
                    │
              Trả về trailer_url → User xem trước
       │
       │  ─── PAYMENT (PayOS) ─── User scan QR / chuyển khoản ───
       │
       ├──────────────────────────────────────────── PHASE 2 (PAID) ──
       │
       │  Webhook PayOS → verify HMAC-SHA256 → mark_order_paid()
       │  → asyncio.create_task(_run_phase2(job_id, package))
       │
       ▼  (background task)
       │
       ▼  Agent 5: project(financials, ratios, industry)
       │  → projection { base_year_label, assumptions,
       │                  projections[5], summary_5y }
       │
       ▼  Agent 6: value(financials, ratios, industry, projection)
       │  LLM: → assumptions { wacc_pct, terminal_growth_pct,
       │                        ev_ebitda_multiple, pe_multiple, pb_multiple,
       │                        comparable_companies, ... }
       │  Python: DCF + Multiples + Sensitivity + Scenarios
       │          + Football Field + Waterfall Bridge
       │
       ▼  Agent 7: write_thesis(financials, ratios, industry,
       │                         business, projection, valuation)
       │  → thesis { executive_summary, investment_thesis,
       │             risk_matrix, deal_recommendation,
       │             return_scenarios, exit_strategy, ... }
       │
       ▼  Agent 8: render_valuation_report(payload, out_path, brand, cfg)
          → {job_id}_valuation.pdf  (~37 trang, matplotlib)
          → {job_id}_explainer.pdf  (HTML/Playwright)
          → {job_id}_valuation.xlsx (pro only, openpyxl)
          → {job_id}_trace.json
          → {job_id}_debug.pdf
```

---

## 5. Chi tiết từng Agent

### Agent 0 — `brand_scraper.py`

**Model:** `claude-haiku-4-5-20251001`  
**Chạy:** Song song với Agent 1 (`asyncio.gather`)  
**Input:** `website_url: str`

**Quy trình scrape:**
1. Fetch HTML với `httpx`, timeout 15s, `verify=False` (bỏ qua SSL lỗi)
2. Parse với BeautifulSoup4
3. Trích xuất color hints:
   - CSS variables (`--color-*`, `--primary`, v.v.)
   - `<meta name="theme-color">`
   - Inline styles từ `body`, `header`, `nav`
   - Đếm hex màu phổ biến nhất trong `<style>` tags (Counter)
4. Claude Haiku chọn bảng màu thương hiệu từ hints
5. Fetch logo: thử theo thứ tự → OG image → apple-touch-icon → favicon → `<img class="logo">`
6. Chuyển logo sang PNG base64 bằng PIL

**Output:**
```json
{
  "brand": {
    "primary": "#1e3a8a",
    "secondary": "#2563eb",
    "primary_light": "#eff6ff",
    "accent": "#10b981",
    "logo_b64": "<base64>",
    "logo_mime": "image/png",
    "source": "scraped"
  }
}
```

**Fallback:** Nếu URL rỗng hoặc fetch lỗi → trả `_FALLBACK_BRAND` (navy `#1e3a8a`)

**Prompt sentinel:** `"TRẢ VỀ JSON (không markdown, không giải thích):"`

---

### Agent 1 — `extractor.py`

**Model:** `claude-opus-4-7`  
**Thinking:** `adaptive`, effort = `medium`  
**Max tokens:** 16 000  
**Chạy:** Song song với Agent 0  
**Input:** File path (PDF hoặc ảnh PNG/JPG/WebP/GIF)

**Xử lý file:**
- PDF → đọc bytes → gửi qua Anthropic API dưới dạng `document` block
- Ảnh → base64 encode → gửi qua `image` block với mime type tương ứng

**Quy tắc số học Việt Nam (quan trọng):**
- `"."` = phân cách hàng nghìn: `"1.234.567"` → `1234567`
- `","` = phân cách thập phân: `"1.234,56"` → `1234.56`
- Ô trống / gạch ngang `-` → `null` (KHÔNG phải `0`)
- Ngoặc đơn `(1.234)` = số âm `-1234`
- Kiểm tra: `total_assets = total_liabilities + total_equity`, nếu sai → ghi vào `notes`

**Output JSON — key `financials`:**
```
company:         { name, tax_code, address, industry, report_type }
period:          { current: {label}, previous: {label} }
currency, unit
balance_sheet:
  current/previous:
    assets:      { cash_and_equivalents, short_term_investments,
                   short_term_receivables, inventory, other_current_assets,
                   current_assets_total, long_term_receivables, fixed_assets,
                   investment_properties, long_term_investments,
                   other_non_current_assets, non_current_assets_total, total_assets }
    liabilities: { short_term_debt, accounts_payable, other_current_liabilities,
                   current_liabilities_total, long_term_debt,
                   other_non_current_liabilities, non_current_liabilities_total,
                   total_liabilities }
    equity:      { share_capital, retained_earnings, other_equity, total_equity }
income_statement:
  current/previous:
    { revenue, revenue_deductions, net_revenue, cogs, gross_profit,
      financial_income, financial_expense, interest_expense,
      selling_expense, admin_expense, operating_profit,
      other_income, other_expense, profit_before_tax,
      current_tax, deferred_tax, net_profit_after_tax, eps }
cash_flow:
  current/previous:
    { cf_operating, cf_investing, cf_financing, net_cf, ending_cash }
raw_transcription: "<verbatim tables>"
notes: "<bất thường>"
```

**Prompt sentinel:** `"Return ONLY this JSON shape"`

---

### Agent 2 — `industry.py`

**Model:** `claude-opus-4-7`  
**Thinking:** `adaptive`, effort = `medium`  
**Max tokens:** 10 000  
**Chạy:** Song song với Agent 4  
**Input:** `financials` (từ Agent 1)

**Prompt style:** Template với `build_prompt` — placeholders bắt buộc:  
`{name}`, `{industry_hint}`, `{revenue}`, `{unit}`, `{cogs}`

**Output JSON — key `industry`:**
```
industry_name, industry_classification_basis, industry_overview
market_size: { tam_vnd_billion, sam_vnd_billion, som_vnd_billion,
               assumptions, company_market_share_pct }
industry_cagr_5y_pct
industry_growth_drivers: [list]
industry_trends: [list]
key_competitors: [{ name, estimated_revenue_vnd_billion,
                    market_share_pct, note }]
competitor_comparison: [{ name, is_subject, revenue_vnd_billion,
                          gross_margin_pct, net_margin_pct, roe_pct,
                          ev_ebitda_est, pe_est, market_share_pct,
                          strengths, weaknesses }]
swot: { strengths, weaknesses, opportunities, threats }
porters_5_forces: { buyer_power, supplier_power, threat_of_substitutes,
                    threat_of_new_entrants, competitive_rivalry }
  each: { score: 1-5, description }
competitive_landscape, industry_risks, regulatory_environment
barriers_to_entry: [list]
industry_outlook_3y: "<bull | neutral | bear + lý do>"
```

---

### Agent 3 — `business_profile.py`

**Model:** `claude-opus-4-7`  
**Thinking:** `adaptive`, effort = `low`  
**Max tokens:** 8 000  
**Chạy:** Sau khi có output Agent 2  
**Input:** `financials` + `industry`

**Quy tắc:** KHÔNG bịa ban lãnh đạo/cổ đông — ghi `"Không xác định từ BCTC"`

**Output JSON — key `business`:**
```
history_inferred, ownership_summary
shareholders: [{ name, ownership_pct, type, note }]
management_team: [{ name, role, background }]
founding_milestones: [{ year, event }]
headcount, management
business_model: { summary, revenue_model, products_services, customer_segments }
revenue_breakdown: [{ product, pct_of_revenue, note }]
top_customers: [{ name, revenue_pct, note }]
top_suppliers: [{ name, cost_pct, note }]
unit_economics: { gross_margin_pct, operating_margin_pct, comments }
value_chain: { input, production, distribution, customer }
scale_indicators: { revenue_size_class, employee_estimate, asset_intensity }
competitive_position: "<leader | challenger | niche | follower>"
growth_stage: "<startup | early-growth | scale-up | mature | turnaround>"
```

**Prompt sentinel:** `"TRẢ VỀ JSON (không markdown):"`

---

### Agent 4 — `analyzer.py`

**Model:** KHÔNG dùng LLM — Python thuần, 100% deterministic  
**Chạy:** Song song với Agent 2  
**Input:** `financials`

**Nhóm tỷ số tính toán:**

| Nhóm | Tỷ số |
|---|---|
| Liquidity | current_ratio, quick_ratio, cash_ratio |
| Leverage | debt_ratio, debt_to_equity, equity_multiplier, interest_coverage, debt_to_ebitda |
| Profitability | gross_margin, operating_margin, ebitda_margin, net_margin, roa, roe |
| Efficiency | asset_turnover, inventory_turnover, receivables_turnover |

Mỗi tỷ số: `{ value: float, rating: "good" | "warning" | "poor" | "n/a" }`

**Phân tích bổ sung:**
- `growth` — YoY tăng trưởng: doanh thu, lợi nhuận, tài sản, vốn chủ
- `dupont` — 3 nhân tố: Net Margin × Asset Turnover × Equity Multiplier
- `working_capital_days` — DSO, DIO, DPO, Cash Conversion Cycle (CCC)
- `quality_of_earnings` — so sánh LNST (accrual) vs OCF (cash)
- `common_size` — mọi dòng P&L theo % doanh thu
- `normalized_ebitda` — điều chỉnh EBIT nếu chi phí QLDN biến động >30% YoY
- `breakeven` — doanh thu hòa vốn dựa trên variable/fixed cost

---

### Agent 5 — `projector.py`

**Model:** `claude-opus-4-7`  
**Thinking:** `adaptive`, effort = `high`  
**Max tokens:** 10 000  
**Chạy:** Đầu Phase 2 (sequential)  
**Input:** `financials` + `ratios` + `industry`

**Prompt style:** Template — 19 placeholders bắt buộc:  
`{period_label}`, `{cur_revenue}`, `{cogs}`, `{gross_profit}`, `{selling_expense}`,  
`{admin_expense}`, `{ebit}`, `{interest_expense}`, `{current_tax}`, `{net_profit}`,  
`{fixed_assets}`, `{total_assets}`, `{inventory}`, `{receivables}`, `{prev_revenue}`,  
`{prev_net_profit}`, `{revenue_yoy}`, `{industry_cagr}`, `{unit}`

**Công thức FCFF:**
```
FCFF = EBIT × (1 - tax%) + D&A - CAPEX - ΔWC
```

**Output JSON — key `projection`:**
```
base_year_label
assumptions:
  revenue_growth_pct: [Y1, Y2, Y3, Y4, Y5]  ← giảm dần theo S-curve
  growth_rationale
  gross_margin_pct: [Y1..Y5]
  operating_expense_pct_revenue: [Y1..Y5]
  tax_rate_pct, depreciation_pct_revenue
  capex_pct_revenue: [Y1..Y5]
  working_capital_days
  rationale_capex, rationale_wc
projections: [5 items]
  each: { year_index, year_label, revenue, growth_pct, cogs,
          gross_profit, operating_expense, ebit, depreciation,
          ebitda, interest_expense, profit_before_tax, tax,
          net_income, capex, change_in_wc, fcff,
          ebitda_margin_pct, net_margin_pct }
summary_5y: { revenue_cagr_pct, ebitda_cagr_pct, fcff_cumulative, comments }
```

---

### Agent 6 — `valuator.py`

**Model:** `claude-opus-4-7` (chỉ phần LLM assumptions)  
**Thinking:** `adaptive`, effort = `medium`  
**Max tokens:** 8 000  
**Input:** `financials` + `ratios` + `industry` + `projection`

**Kiến trúc:** Hybrid — LLM lấy assumptions, Python tính toán deterministic

**LLM trả về** (`_claude_assumptions`):
```
wacc_pct
wacc_breakdown: { risk_free_rate_pct, equity_risk_premium_pct, beta,
                  size_premium_pct, country_risk_pct, total_cost_of_equity_pct,
                  cost_of_debt_pct, tax_shield_pct, after_tax_cost_of_debt_pct,
                  debt_weight_pct, equity_weight_pct }
terminal_growth_pct, terminal_growth_rationale
ev_ebitda_multiple, ev_ebitda_rationale
pe_multiple, pe_rationale
pb_multiple, pb_rationale
multiples_trading_vs_transaction
comparable_companies: [{ name, ev_ebitda, pe, pb, revenue_vnd_b, ... }]
valuation_method_recommendation
weighting_rationale
minority_discount_pct, minority_discount_rationale
```

**Python deterministic (không LLM):**

| Hàm | Mô tả |
|---|---|
| `_dcf_valuation()` | Chiết khấu FCFF 5 năm + Terminal Value (Gordon Growth) |
| `_multiples_valuation()` | EV/EBITDA, P/E, P/B → equity value |
| `_sensitivity()` | Ma trận 5×5: WACC ±2% × terminal growth ±2% |
| `_scenario_analysis()` | Bull (+25% FCFF), Base, Bear (-30% FCFF) |
| `_football_field()` | Tổng hợp ranges mọi phương pháp |
| `_waterfall_bridge()` | EV → (-Debt) → (+Cash) → Equity |
| `_build_summary()` | Fair value Low / Mid / High + minority discount |

**DCF formula:**
```python
terminal_value = fcff_5 * (1 + g) / (wacc - g)
pv_fcff = sum(fcff[i] / (1+wacc)**(i+1) for i in range(5))
enterprise_value = pv_fcff + terminal_value / (1+wacc)**5
equity_value = enterprise_value - net_debt
```

---

### Agent 7 — `thesis_writer.py`

**Model:** `claude-opus-4-7`  
**Thinking:** `adaptive`, effort = `high`  
**Max tokens:** 16 000  
**Input:** tất cả từ Agent 1-6

**Output JSON — key `thesis`:**
```
report_version, report_date, disclaimer
executive_summary: { headline, company_brief, industry_brief,
                     scale_brief, valuation_result, recommendation,
                     key_drivers }
investment_case_summary
key_value_drivers_ranked: [{ rank, driver, rationale }]
investment_thesis:
  thesis_points: [{ title, thesis, evidence }]
  catalysts: [{ type, description, horizon }]
  risks: [{ type, description, severity, mitigation, quantified_impact }]
risk_matrix: [{ risk, probability, impact, score (1-9), mitigation }]
  # score = probability × impact (low=1, medium=2, high=3)
operations_analysis: { revenue_drivers, margin_analysis,
                       channel_breakdown, key_metrics_observations }
financial_analysis_commentary: { balance_sheet_health,
                                  income_statement_quality,
                                  cash_flow_quality, leverage_view }
valuation_commentary: { method_comparison, reconciliation,
                        fair_value_view, weighting_applied, key_sensitivities }
deal_recommendation: { primary_objective, fair_value_range_text,
                       entry_price_recommendation, deal_structure,
                       post_deal_governance, next_steps,
                       pre_money_valuation, investment_amount_suggested,
                       post_money_valuation }
use_of_proceeds: [{ category, pct, amount_vnd_billion, note }]  # tổng = 100%
dilution_table: [{ shareholder, pre_deal_pct, post_deal_pct, shares_note }]
exit_strategy: { primary_exit, target_timeline_years, target_ev_at_exit,
                 exit_multiple_assumption, description }
return_scenarios: [Bull/Base/Bear × { irr_pct, moic, horizon_years,
                                       entry_ev, exit_ev, description }]
# IRR chuẩn: Bull 25-40%, Base 15-25%, Bear 5-15%
```

---

### Agent 8 — Rendering layer

Không phải 1 file — gồm nhiều renderer:

| File | Engine | Output | Dùng khi |
|---|---|---|---|
| `renderer.py` | Matplotlib | Full report ~37 trang | Phase 2 (luôn luôn) |
| `trailer_html.py` + `html_pdf.py` | HTML → Playwright | Trailer 4 trang | Phase 1 (primary) |
| `trailer_renderer.py` | Matplotlib | Trailer | Phase 1 (fallback nếu Playwright lỗi) |
| `explainer_html.py` + `html_pdf.py` | HTML → Playwright | Explainer PDF | Phase 2 (primary) |
| `explainer_renderer.py` | Matplotlib | Explainer | Phase 2 (fallback) |
| `valuation_html.py` + `html_pdf.py` | HTML → Playwright | Full report HTML | Preview admin only |
| `excel_exporter.py` | openpyxl | Excel | Phase 2 Pro |

---

## 6. Chi tiết render PDF (Matplotlib)

### 6.1 Cấu hình figure

```python
A4 = (8.27, 11.69)  # inches
rcParams["font.family"] = "DejaVu Sans"
rcParams["mathtext.fontset"] = "cm"
rcParams["axes.unicode_minus"] = False
```

### 6.2 12 Sections của full report

| Section slug | Tiêu đề | Nội dung |
|---|---|---|
| `00_cover_disclaimer` | Bìa + Disclaimer | Trang bìa thương hiệu + bảng metadata + disclaimer text |
| `01_executive_summary` | Executive Summary | Headline, KPI nổi bật, key value drivers |
| `02_investment_thesis` | Luận điểm đầu tư | Thesis points, catalysts, risk matrix |
| `03_company_overview` | Tổng quan DN | Ban lãnh đạo, cổ đông, chuỗi giá trị, milestones |
| `04_industry` | Phân tích ngành | TAM/SAM/SOM, Porter's 5 Forces, SWOT, đối thủ |
| `05_operations` | Hoạt động KD | Common-size P&L, revenue drivers, margin analysis |
| `06_financial_statements` | Bảng BCTC | Bảng cân đối, KQKD, Lưu chuyển tiền + ratio table |
| `07_ratios` | Tỷ số tài chính | Radar chart, DuPont, Working Capital, Quality of Earnings |
| `08_projections` | Dự phóng 5 năm | Bảng 5Y, revenue chart, EBITDA chart |
| `09_valuation` | Định giá | DCF chi tiết, Multiples, Football Field, Waterfall |
| `10_sensitivity` | Sensitivity | Ma trận WACC × g, Scenario Bull/Base/Bear |
| `11_conclusion_appendix` | Kết luận | Deal recommendation, Return scenarios, Exit strategy |

### 6.3 Hệ thống màu sắc trong renderer

**Brand colors (từ config + scraped brand):**
```python
_DEFAULT_COLORS = {
    "primary": "#1e3a8a",      # Navy xanh đậm — header, titles
    "secondary": "#2563eb",    # Blue — accent bars
    "primary_light": "#eff6ff" # Light blue — stripe, highlight
}
```

**Neutral colors (text + border):**
```python
_NEUTRAL_DEFAULTS = {
    "text_primary": "#1f2937",  # Main text
    "text_body":    "#374151",  # Body text
    "text_muted":   "#6b7280",  # Label
    "text_faint":   "#9ca3af",  # Footnote
    "border":       "#d1d5db",  # Table borders
    "grid":         "#e5e7eb",  # Chart grid
    "stripe":       "#f8fafc",  # Alternate row
}
```

**Chart palettes:**
```python
_DEFAULT_GRADE   = {"A": "#10b981", "B": "#22c55e", "C": "#f59e0b",
                    "D": "#f97316", "F": "#ef4444"}
_DEFAULT_RATING  = {"good": "#10b981", "warning": "#f59e0b",
                    "poor": "#ef4444", "n/a": "#9ca3af"}
_DEFAULT_VCHAIN  = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]
_DEFAULT_SEVERITY = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"}
```

### 6.4 Cách render 1 trang (pattern chuẩn)

```python
with PdfPages(str(out_path)) as pdf:
    fig = plt.figure(figsize=A4)
    # Layout axes theo config:
    content_axes = _layout("content_axes")  # [0.07, 0.055, 0.86, 0.905]
    ax = fig.add_axes(content_axes)
    ax.axis("off")
    
    # Vẽ header bar (navy strip)
    fig.add_axes([0, 1-header_h, 1, header_h])
    # Vẽ accent bar (thin colored bar)
    fig.add_axes([0, 1-header_h-accent_h, 1, accent_h])
    # Vẽ footer bar
    fig.add_axes([0, 0, 1, footer_h])
    
    # Vẽ nội dung vào ax...
    
    _figure_postprocess(fig)  # scale fonts + remap màu theo config
    pdf.savefig(fig, bbox_inches="tight", dpi=150)
    plt.close(fig)
```

### 6.5 `_figure_postprocess` — Áp dụng config sau khi vẽ

Hàm này traverse tất cả objects trong figure và:
1. Scale font size theo `typography.scale` (config, range 0.6–1.8)
2. Scale border/line width theo `components.border_width_scale` (config, range 0.3–3.0)
3. Remap neutral hex colors theo admin config (so sánh hex literal → thay thế)

### 6.6 Thread-local state

```python
_local = threading.local()

def _apply_style(config, brand):
    _local.cfg = config or {}
    _local.theme = brand or {}    # scraped brand colors
    _local._logo_arr = _UNSET    # reset logo cache
    rcParams["font.family"] = ...
```

Mỗi render gọi `_apply_style()` ở đầu — đảm bảo thread-safe khi chạy nhiều jobs đồng thời.

---

## 7. Chi tiết render HTML (Playwright)

### 7.1 `html_pdf.py` — Wrapper Playwright

```python
def render_html_to_pdf(html: str, output_path: str, wait_fonts: bool = True) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")  # chờ Google Fonts load
        page.pdf(path=output_path, format="A4", print_background=True,
                 margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
```

Nếu Playwright không cài → raise `RuntimeError` → caller fallback sang matplotlib.

### 7.2 CSS Design System (dùng chung cho trailer + explainer)

CSS variables trong `explainer_html.py`:
```css
:root {
  --ink:        /* text_primary */
  --ink-soft:   /* text_body */
  --accent:     /* primary */
  --line:       /* border */
  --line-soft:  /* grid */
  --grey-fill:  /* stripe */
  --head:       /* font family */
}
.sheet { width: 210mm; min-height: 297mm; page-break-after: always; }
.sec { padding: 20mm; }
```

### 7.3 Trailer HTML (`trailer_html.py`)

4 trang (pages):
1. **Cover** — logo + tên công ty + định giá ước tính (bị lock/mờ)
2. **Snapshot** — KPI tài chính hiện tại + so sánh kỳ trước
3. **Industry + Ratios** — ngành + tỷ số nổi bật
4. **CTA** — bảng "được gì khi mua" + QR / nút thanh toán

**Giá trị định giá trong trailer** = `_estimate_valuation()` trong `trailer_renderer.py`  
→ deterministic estimate đơn giản từ EBITDA × multiple ngành (không dùng DCF đầy đủ)

---

## 8. Config System

### 8.1 Triết lý thiết kế

Config chỉ chạm **PRESENTATION**. KHÔNG BAO GIỜ ảnh hưởng số tính toán:
- `analyzer.analyze()` — tuyệt đối deterministic, không đọc config
- Math trong `valuator.value()` (DCF, sensitivity, v.v.) — không đọc config
- Config snapshot tại thời điểm start job → job cũ không bị ảnh hưởng bởi admin edit

### 8.2 Cấu trúc config (YAML-like)

```yaml
schema_version: 1

style:
  colors:
    primary: "#1e3a8a"
    secondary: "#2563eb"
    primary_light: "#eff6ff"
    text_primary: "#1f2937"
    text_body: "#374151"
    text_muted: "#6b7280"
    text_faint: "#9ca3af"
    border: "#d1d5db"
    grid: "#e5e7eb"
    stripe: "#f8fafc"
    positive: "#10b981"
    warning: "#f59e0b"
    negative: "#ef4444"
    info: "#3b82f6"
  chart_palette:
    grade:       { A, B, C, D, F }
    rating:      { good, warning, poor, n/a }
    value_chain: [4 colors]
    severity:    { HIGH, MEDIUM, LOW }
  font:
    family: "DejaVu Sans"       # matplotlib
    excel_family: "Calibri"     # openpyxl
  typography:
    scale: 1.0                  # font multiplier [0.6, 1.8]
  components:
    border_width_scale: 1.0     # line thickness [0.3, 3.0]
  report_css:                   # HTML renderer
    ink, ink_soft, accent, line, line_soft, grey_fill, head
    explainer_layout: "A"       # "A" | "B" | "C"
    valuation_engine: "matplotlib"   # ← LUÔN LÀ matplotlib
    trailer_engine: "html"      # "html" | "matplotlib"
  layout:
    content_axes: [0.07, 0.055, 0.86, 0.905]
    header_height: 0.046
    accent_height: 0.007
    footer_height: 0.022
    title_fontsize: 11.5

content:
  report_title: "BÁO CÁO ĐỊNH GIÁ DOANH NGHIỆP"
  report_subtitle: "SME Valuation Report"
  cover_generated_by: "Generated by 9-agent pipeline"
  footer_prefix: "Báo cáo tạo ngày"
  disclaimer_default: "..."
  disclaimer_meta: { model_label, tool_label, currency_label,
                     scope_label, limitation_label }
  method_notes: [list]
  trailer_brand_name, trailer_tagline, trailer_preview_badge, trailer_footer
  explainer_title, explainer_subtitle, explainer_intro
  explanations: [...]   # từ explanations_default.py

images:
  logo: { file, mime, placements: ["cover"] }
  items: [{ id, file, mime, placement, caption }]

sections: [   # enable/disable + reorder 12 sections
  { slug, title, enabled, order }
]

prompts:       # per-agent preamble overrides (empty = dùng default)
  extractor:        { preamble: "" }
  brand_scraper:    { preamble: "" }
  industry:         { preamble: "" }   # phải giữ {name},{industry_hint},{revenue},{unit},{cogs}
  business_profile: { preamble: "" }
  projector:        { preamble: "" }   # phải giữ 19 placeholders
  valuator:         { preamble: "" }
  thesis_writer:    { preamble: "" }
```

### 8.3 Quy trình `normalize_config`

```python
# config_schema.py
def normalize_config(raw: dict | None) -> dict:
    # Deep merge: defaults ← raw (raw thắng)
    # raw = None → trả về DEFAULT_CONFIG hoàn toàn
    result = copy.deepcopy(DEFAULT_CONFIG)
    _deep_merge(result, raw or {})
    return result
```

**Lưu ý:** Vì `normalize` deep-merge raw thắng → nếu DB có `valuation_engine: "html"`,  
nó sẽ override default "matplotlib". Giải pháp: force override sau normalize:

```python
# config_store.py
cfg = schema.normalize_config(raw)
cfg["style"]["report_css"]["valuation_engine"] = "matplotlib"  # force luôn
```

### 8.4 Prompt system (`agent_common.py`)

**Pattern 1: Template**
```python
build_prompt(default_preamble, schema_block, ctx, override)
```
- Admin có thể reword preamble nhưng phải giữ `{placeholders}`
- Schema block (JSON contract) được append cứng, không thể xóa

**Pattern 2: Free-text**
```python
with_locked_schema(default_full_prompt, schema_sentinel, override)
```
- Split tại `schema_sentinel` (vd: `"TRẢ VỀ JSON (không markdown):"`)
- Phần sau sentinel → locked, không thể sửa
- Admin chỉ edit phần trước sentinel

---

## 9. Database Schema

**Kết nối:** `asyncpg.Pool` via env var `DATABASE_URL`

```sql
-- Job tracking
CREATE TABLE usage_logs (
    id                SERIAL PRIMARY KEY,
    job_id            VARCHAR(32) UNIQUE NOT NULL,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    website_url       TEXT,
    filename          TEXT,
    file_size_bytes   INTEGER,
    company_name      TEXT,
    industry_name     TEXT,
    status            VARCHAR(20) DEFAULT 'processing',
    error_message     TEXT,
    total_elapsed_sec FLOAT,
    ip_address        TEXT,
    session_id        VARCHAR(128),
    result_json       TEXT,
    user_id           INTEGER
);

-- Admin auth
CREATE TABLE admin_users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(64) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,    -- bcrypt
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- End user auth
CREATE TABLE end_users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,    -- bcrypt
    display_name  VARCHAR(128),
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Payment
CREATE TABLE payment_orders (
    id           BIGSERIAL PRIMARY KEY,
    job_id       VARCHAR(32) NOT NULL,
    amount       INTEGER NOT NULL,
    package_type VARCHAR(20) DEFAULT 'basic',  -- 'basic' | 'pro'
    status       VARCHAR(20) DEFAULT 'pending',
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    paid_at      TIMESTAMPTZ,
    order_code   BIGINT
);

-- Config versioning
CREATE TABLE report_configs (
    id          SERIAL PRIMARY KEY,
    config_json TEXT NOT NULL,
    is_active   BOOLEAN DEFAULT FALSE,
    updated_by  TEXT,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Config snapshot per job
CREATE TABLE job_config_snapshots (
    job_id      VARCHAR(32) PRIMARY KEY,
    config_json TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

**Job lifecycle states:**
```
processing → trailer_ready → paid_processing → success
                                             ↘ error
```

---

## 10. Payment Integration (PayOS)

**Provider:** PayOS (api-merchant.payos.vn)

**Packages:**
- `basic` — `PRICE_BASIC` env (default 3,000 VND) → báo cáo PDF
- `pro` — `PRICE_PRO` env (default 5,000 VND) → PDF + Excel

**Create payment flow:**
```
POST /api/payment/create
  Body: { job_id, package }
  → Tạo order trong PayOS API
  → Trả về { payment_link_id, checkout_url, qr_code_data }
```

**Webhook flow:**
```
POST /api/payment/callback  ← PayOS gọi sau khi thanh toán
  1. Verify HMAC-SHA256:
     raw = "&".join(f"{k}={v}" for k,v in sorted(data.items()))
     signature = hmac.new(PAYOS_CHECKSUM_KEY, raw, sha256).hexdigest()
  2. mark_order_paid(order_code, paid_at)
  3. asyncio.create_task(_run_phase2(job_id, package))
```

---

## 11. API Endpoints

### Public

| Method | Path | Mô tả |
|---|---|---|
| `GET` | `/` | Landing page |
| `GET` | `/app` | App upload UI |
| `GET` | `/health` | Health check |
| `POST` | `/api/process` | Upload BCTC → Phase 1 |
| `GET` | `/api/job/status/{job_id}` | Poll job status |
| `GET` | `/api/download/{job_id}/trailer` | Download trailer PDF |
| `GET` | `/api/download/{job_id}/{kind}` | Download paid (valuation/explainer/excel/debug/trace) |
| `GET` | `/api/stats` | Usage stats |
| `GET` | `/api/history/{session_id}` | Session history |
| `POST` | `/api/payment/create` | Tạo payment link |
| `POST` | `/api/payment/callback` | PayOS webhook |
| `GET` | `/api/payment/status/{job_id}` | Check payment status |

### User Auth

| Method | Path |
|---|---|
| `POST` | `/api/user/register` |
| `POST` | `/api/user/login` |
| `GET` | `/api/user/history` |

### Admin (JWT required)

| Method | Path | Mô tả |
|---|---|---|
| `POST` | `/api/auth/login` | Admin login |
| `POST` | `/api/auth/register` | Tạo admin (cần ADMIN_SECRET) |
| `GET` | `/api/admin/stats` | Thống kê |
| `GET` | `/api/admin/job/{job_id}` | Chi tiết job |
| `GET` | `/api/admin/export.csv` | Export usage log |
| `GET` | `/api/admin/download/{job_id}/{kind}` | Download bypass payment |
| `POST` | `/api/admin/run_phase2/{job_id}` | Trigger Phase 2 không cần payment |
| `GET/PUT` | `/api/admin/config` | Đọc/lưu config |
| `GET` | `/api/admin/config/version/{v}` | Config version cũ |
| `POST` | `/api/admin/config/validate` | Validate draft config |
| `POST` | `/api/admin/config/image` | Upload logo/image |
| `POST` | `/api/admin/config/preview` | Render preview PDF |
| `GET` | `/api/admin/render-health` | Check Playwright availability |

### Security notes

- `job_id` validate: alphanumeric only, 1-32 chars (`_safe_job_id()`)
- Config images: whitelist `.png/.jpg/.jpeg/.svg`, max 2MB
- Uploads: whitelist `.pdf/.png/.jpg/.jpeg/.webp/.gif`, max 25MB
- Paid content: check `db.get_paid_package()` trước khi serve
- `/admin` endpoint: `Cache-Control: no-store` header (tránh browser cache)

---

## 12. Authentication

**Admin JWT:**
```python
# auth.py
import jwt  # python-jose
algorithm = "HS256"
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))

def create_token(username: str) -> str:
    payload = {"sub": username, "exp": datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, JWT_SECRET, algorithm=algorithm)

async def require_auth(request: Request):
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    try:
        jwt.decode(token, JWT_SECRET, algorithms=[algorithm])
    except Exception:
        raise HTTPException(401, "Unauthorized")
```

**End user JWT:**
```python
def create_user_token(uid: int, email: str) -> str:
    payload = {"sub": str(uid), "email": email,
               "exp": datetime.utcnow() + timedelta(days=30)}
    return jwt.encode(payload, JWT_SECRET, algorithm=algorithm)
```

**Password:** `bcrypt` via `passlib` — `hash_password()` / `verify_password()`

---

## 13. Files Output

| Filename | Nội dung |
|---|---|
| `{job_id}_trailer.pdf` | Free preview 4 trang (Phase 1) |
| `{job_id}_partial.json` | Data Phase 1 → dùng cho Phase 2 (xóa sau Phase 2) |
| `{job_id}_valuation.pdf` | Full report ~37 trang (Phase 2) |
| `{job_id}_explainer.pdf` | Explainer PDF giải thích công thức (Phase 2) |
| `{job_id}_valuation.xlsx` | Excel model (Phase 2 Pro only) |
| `{job_id}_trace.json` | Debug trace đầy đủ (Phase 2) |
| `{job_id}_debug.pdf` | Debug report PDF |

**Cấu trúc `partial.json`:**
```json
{
  "a0_brand":    { "brand": { ... } },
  "a1":          { "financials": { ... } },
  "a2_industry": { "industry": { ... } },
  "a3_business": { "business": { ... } },
  "a4_ratios":   { "ratios": { ... }, "growth": {...}, "dupont": {...} },
  "brand":       { "primary": "#...", "logo_b64": "..." },
  "config":      { ... }   // config snapshot tại thời điểm job start
}
```

---

## 14. Environment Variables

| Var | Bắt buộc | Mô tả |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Có** | Claude API key |
| `DATABASE_URL` | Nên có | PostgreSQL connection string |
| `PAYOS_CLIENT_ID` | Payment | PayOS client ID |
| `PAYOS_API_KEY` | Payment | PayOS API key |
| `PAYOS_CHECKSUM_KEY` | Payment | Webhook HMAC key |
| `PRICE_BASIC` | Optional | Giá basic (VND), default 3000 |
| `PRICE_PRO` | Optional | Giá pro (VND), default 5000 |
| `BASE_URL` | Optional | Public URL (auto-detect Railway) |
| `RAILWAY_PUBLIC_DOMAIN` | Optional | Railway domain |
| `ADMIN_SECRET` | Optional | Secret để tạo admin user thứ 2+ |
| `SEED_ADMIN_USER` | Optional | Seed admin username (DB trống) |
| `SEED_ADMIN_PASS` | Optional | Seed admin password |
| `RESET_ADMIN_USER` | Optional | Reset password tại startup |
| `RESET_ADMIN_PASS` | Optional | New password khi reset |
| `JWT_SECRET` | Optional | JWT signing key (random nếu không set) |

---

## 15. Deployment (Railway)

**`Dockerfile`:**
```dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps chromium
COPY . .
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
```

**`Procfile`:**
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**`railway.json`:**
```json
{ "build": { "builder": "DOCKERFILE" } }
```

**`runtime.txt`:**
```
python-3.12.7
```

**`requirements.txt` (main packages):**
```
fastapi
uvicorn[standard]
anthropic
asyncpg
httpx
pillow
matplotlib
playwright
openpyxl
python-jose[cryptography]
passlib[bcrypt]
beautifulsoup4
python-multipart
```

---

## 16. Quy tắc phát triển bắt buộc

### KHÔNG được vi phạm

1. **Config không ảnh hưởng số:** `analyzer.analyze()` và math trong `valuator.value()` phải luôn deterministic.

2. **JSON contract bất biến:** Phần sau sentinel trong prompt KHÔNG được sửa qua admin. Phần JSON schema là "contract" giữa các agent.

3. **Job snapshot cô lập:** Renderers đọc config từ snapshot của job, không từ config active. Old jobs luôn render giống như ban đầu.

4. **`valuation_engine` luôn là `matplotlib`:** Force override trong `load_active_config()` và trong `_render_valuation_pdf()`. HTML renderer chưa đủ parity.

5. **Thinking mode cho Opus:** Tất cả Opus agents dùng `thinking={"type": "adaptive"}` + `betas=["interleaved-thinking-2025-05-14"]`. Parse response: iterate qua `message.content`, tách `type=="thinking"` vs `type=="text"`.

### JSON parsing pattern (mọi agent)

```python
cleaned = re.sub(r"^```(?:json)?\s*", "", raw_response)
cleaned = re.sub(r"\s*```$", "", cleaned)
try:
    parsed = json.loads(cleaned)
except json.JSONDecodeError:
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    parsed = json.loads(match.group(0))
```

### Model hierarchy

| Model | Agents |
|---|---|
| `claude-opus-4-7` | extractor, industry, business_profile, projector, valuator, thesis_writer |
| `claude-haiku-4-5-20251001` | brand_scraper |
| Python thuần (no LLM) | analyzer |

### Parallel execution

```python
# Phase 1
a0_brand, a1 = await asyncio.gather(
    asyncio.to_thread(scrape_brand, ...),
    asyncio.to_thread(extract, ...)
)

a2_industry, a4_ratios = await asyncio.gather(
    asyncio.to_thread(analyze_industry, ...),
    asyncio.to_thread(analyze, ...)   # Agent 4: no config
)

a3_business = await asyncio.to_thread(analyze_business, ...)

# Phase 2: Sequential
a5 → a6 → a7 → a8
```

---

## 17. Các điểm dễ gây bug khi rebuild

1. **`normalize_config` deep-merge:** Nếu DB có giá trị cũ (vd `valuation_engine: "html"`), nó sẽ override default mới. Phải force sau normalize.

2. **Thread-local trong renderer:** `_local.cfg` và `_local.theme` phải set trước mỗi render bằng `_apply_style()`. Không set → dùng fallback default (không lỗi nhưng không đọc config).

3. **Playwright trên Railway:** Cần `playwright install chromium` VÀ `playwright install-deps chromium` trong Dockerfile. Thiếu deps → crash im lặng.

4. **Số Việt Nam:** Dấu `.` = nghìn, dấu `,` = thập phân. Rất khác chuẩn quốc tế. Agent 1 phải xử lý đúng.

5. **Unit đồng nhất:** Đơn vị (nghìn đồng / triệu đồng / tỷ đồng) lấy từ BCTC và truyền xuyên suốt. KHÔNG tự convert — để nguyên đơn vị từ Agent 1.

6. **Config snapshot:** Tại thời điểm `POST /api/process`, snapshot config và lưu vào `partial.json["config"]` + `job_config_snapshots`. Phase 2 đọc từ snapshot này, không phải active config.

7. **Browser cache admin.html:** Endpoint `/admin` phải trả `Cache-Control: no-store`. Nếu không, browser cache JS cũ → admin UI lỗi dù server đã deploy mới.

8. **`asyncio.to_thread` cho blocking code:** Tất cả LLM calls và matplotlib render là synchronous blocking → phải wrap `asyncio.to_thread`. Không được `await` trực tiếp.

9. **PayOS HMAC signature:**  
   ```python
   raw = "&".join(f"{k}={v}" for k, v in sorted(data.items()))
   expected = hmac.new(PAYOS_CHECKSUM_KEY.encode(), raw.encode(), sha256).hexdigest()
   ```
   Sort keys alphabetically, dùng `=` separator không phải `&value` only.

10. **Section order:** 12 sections trong config `sections[]` có `order` field — renderer sắp xếp theo `order`, không theo index trong array.
