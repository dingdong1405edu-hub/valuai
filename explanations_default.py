EXPLANATIONS_DEFAULT = [
    {
        "id": "dcf",
        "title": "DCF — Discounted Cash Flow",
        "formula": "Enterprise Value = Σ FCFF_t / (1+WACC)^t + Terminal Value / (1+WACC)^n",
        "body": (
            "Phương pháp DCF định giá doanh nghiệp dựa trên giá trị hiện tại của "
            "các dòng tiền tự do (FCFF) trong tương lai. FCFF được chiết khấu về "
            "hiện tại bằng WACC (chi phí vốn bình quân gia quyền). Terminal Value "
            "đại diện cho giá trị của doanh nghiệp sau năm thứ 5, được tính theo "
            "mô hình Gordon Growth."
        ),
        "variables": [
            {"name": "FCFF", "desc": "Free Cash Flow to Firm = EBIT×(1-tax) + D&A - CAPEX - ΔWC"},
            {"name": "WACC", "desc": "Weighted Average Cost of Capital"},
            {"name": "g", "desc": "Tốc độ tăng trưởng dài hạn (terminal growth rate)"},
            {"name": "n", "desc": "Số năm dự phóng (thường 5 năm)"},
        ],
    },
    {
        "id": "wacc",
        "title": "WACC — Chi phí vốn bình quân",
        "formula": "WACC = E/(D+E) × Ke + D/(D+E) × Kd × (1-t)",
        "body": (
            "WACC phản ánh chi phí vốn bình quân của doanh nghiệp, gồm chi phí "
            "vốn cổ phần (Ke) và chi phí nợ sau thuế (Kd×(1-t)). Chi phí vốn cổ "
            "phần được ước tính theo mô hình CAPM: Ke = Rf + β×(Rm-Rf) + size premium + "
            "country risk premium."
        ),
        "variables": [
            {"name": "Ke", "desc": "Chi phí vốn cổ phần (CAPM)"},
            {"name": "Kd", "desc": "Chi phí nợ trước thuế"},
            {"name": "t", "desc": "Thuế suất doanh nghiệp"},
            {"name": "E/(D+E)", "desc": "Tỷ trọng vốn cổ phần"},
            {"name": "β", "desc": "Beta — độ nhạy cảm với biến động thị trường"},
        ],
    },
    {
        "id": "ev_ebitda",
        "title": "EV/EBITDA Multiple",
        "formula": "Equity Value = EBITDA × EV/EBITDA Multiple − Net Debt",
        "body": (
            "Phương pháp bội số EV/EBITDA so sánh doanh nghiệp với các công ty "
            "cùng ngành. EV (Enterprise Value) bằng EBITDA nhân với bội số ngành. "
            "Equity Value được tính bằng cách trừ đi nợ ròng từ EV."
        ),
        "variables": [
            {"name": "EBITDA", "desc": "Lợi nhuận trước lãi vay, thuế, khấu hao"},
            {"name": "EV/EBITDA", "desc": "Bội số so sánh ngành"},
            {"name": "Net Debt", "desc": "Tổng nợ vay − Tiền mặt"},
        ],
    },
    {
        "id": "pe",
        "title": "P/E — Price to Earnings",
        "formula": "Market Cap = Net Income × P/E Multiple",
        "body": (
            "Bội số P/E định giá vốn hóa thị trường dựa trên lợi nhuận ròng. "
            "P/E phù hợp nhất với doanh nghiệp có lợi nhuận ổn định và không có "
            "lợi nhuận bất thường."
        ),
        "variables": [
            {"name": "Net Income", "desc": "Lợi nhuận ròng sau thuế"},
            {"name": "P/E", "desc": "Bội số giá / thu nhập ngành"},
        ],
    },
    {
        "id": "pb",
        "title": "P/B — Price to Book",
        "formula": "Market Cap = Book Value of Equity × P/B Multiple",
        "body": (
            "Bội số P/B phù hợp với doanh nghiệp thâm dụng tài sản (ngân hàng, "
            "bất động sản, sản xuất). Book Value là giá trị sổ sách của vốn chủ sở hữu."
        ),
        "variables": [
            {"name": "Book Value", "desc": "Tổng vốn chủ sở hữu theo sổ sách"},
            {"name": "P/B", "desc": "Bội số giá / giá trị sổ sách ngành"},
        ],
    },
    {
        "id": "football_field",
        "title": "Football Field Chart",
        "formula": "Tổng hợp min-max từ DCF, EV/EBITDA, P/E, P/B",
        "body": (
            "Football Field tổng hợp khoảng giá trị từ mọi phương pháp định giá "
            "vào một biểu đồ thanh ngang. Giá trị trung bình được tính có trọng số "
            "tùy theo phương pháp phù hợp nhất với đặc thù ngành."
        ),
        "variables": [],
    },
    {
        "id": "sensitivity",
        "title": "Sensitivity Analysis — Ma trận nhạy cảm",
        "formula": "EV = f(WACC, g) — thay đổi WACC ±2%, g ±2%",
        "body": (
            "Ma trận sensitivity cho thấy giá trị doanh nghiệp thay đổi thế nào "
            "khi WACC và tốc độ tăng trưởng dài hạn (g) biến động. Đây là công cụ "
            "quan trọng để đánh giá rủi ro định giá."
        ),
        "variables": [
            {"name": "WACC", "desc": "Thay đổi ±0.5% mỗi bước"},
            {"name": "g", "desc": "Thay đổi ±0.5% mỗi bước"},
        ],
    },
    {
        "id": "liquidity",
        "title": "Tỷ số thanh khoản",
        "formula": "Current Ratio = Tài sản ngắn hạn / Nợ ngắn hạn",
        "body": (
            "Tỷ số thanh khoản đo lường khả năng trả nợ ngắn hạn. Current Ratio > 1.5 "
            "là tốt. Quick Ratio loại trừ hàng tồn kho. Cash Ratio chỉ tính tiền mặt."
        ),
        "variables": [
            {"name": "Current Ratio", "desc": "> 1.5: tốt, 1-1.5: cảnh báo, < 1: rủi ro"},
            {"name": "Quick Ratio", "desc": "(Tài sản ngắn hạn - Hàng tồn kho) / Nợ ngắn hạn"},
            {"name": "Cash Ratio", "desc": "Tiền mặt / Nợ ngắn hạn"},
        ],
    },
    {
        "id": "dupont",
        "title": "Phân tích DuPont",
        "formula": "ROE = Net Margin × Asset Turnover × Equity Multiplier",
        "body": (
            "DuPont phân tách ROE thành 3 nhân tố: hiệu quả lợi nhuận (Net Margin), "
            "hiệu quả sử dụng tài sản (Asset Turnover), và đòn bẩy tài chính "
            "(Equity Multiplier = Total Assets / Equity)."
        ),
        "variables": [
            {"name": "Net Margin", "desc": "Lợi nhuận ròng / Doanh thu"},
            {"name": "Asset Turnover", "desc": "Doanh thu / Tổng tài sản"},
            {"name": "Equity Multiplier", "desc": "Tổng tài sản / Vốn chủ sở hữu"},
        ],
    },
    {
        "id": "ccc",
        "title": "Cash Conversion Cycle (CCC)",
        "formula": "CCC = DSO + DIO − DPO",
        "body": (
            "CCC đo lường số ngày từ khi chi tiền mua hàng đến khi thu được tiền "
            "từ khách hàng. CCC thấp hơn = quản lý vốn lưu động tốt hơn."
        ),
        "variables": [
            {"name": "DSO", "desc": "Days Sales Outstanding — ngày thu tiền"},
            {"name": "DIO", "desc": "Days Inventory Outstanding — ngày tồn kho"},
            {"name": "DPO", "desc": "Days Payable Outstanding — ngày trả tiền NCC"},
        ],
    },
]
