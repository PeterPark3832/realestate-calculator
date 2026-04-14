"""
🏠 부동산 갈아타기 계산기 (공개버전)
대출 시뮬레이터 · 갈아타기 손익 · 이사 일정 역산

외부 API / DB 의존 없음 — 순수 계산 엔진
규제 기준: 2025.10.15 주택시장 안정화 대책 + 스트레스 DSR 3단계
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta

# ═══════════════════════════════════════════════════════════
# 페이지 설정 (가장 먼저)
# ═══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="갈아타기 계산기",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════
# CSS — 한국 핀테크 스타일 (Toss 레퍼런스)
# ═══════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

/* ── 기본 ── */
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', -apple-system, sans-serif !important;
}

/* Streamlit 기본 상단 헤더 툴바 숨김 — 콘텐츠가 잘리는 문제 해결 */
header[data-testid="stHeader"]         { display: none !important; }
#MainMenu                               { display: none !important; }
footer                                  { display: none !important; }
[data-testid="stToolbar"]              { display: none !important; }
[data-testid="stDecoration"]           { display: none !important; }
[data-testid="collapsedControl"]       { top: 0.5rem !important; }

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1300px;
}

/* ── 탭 스타일 ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #E9ECF0;
    border-radius: 14px;
    padding: 5px;
    margin-bottom: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    color: #6B7684;
    font-weight: 500;
    font-size: 0.92rem;
    padding: 0.5rem 1.4rem;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #1B64DA !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.10);
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1rem; }

/* ── 입력 카드 ── */
.input-section {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 1.1rem 1.3rem 0.8rem;
    margin-bottom: 0.9rem;
    border: 1px solid #E5E8EB;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: #9CA3AF;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.5rem;
}

/* ── 결과 카드 ── */
.kpi-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 0.8rem;
    border: 1px solid #E5E8EB;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.kpi-card.primary { border-left: 4px solid #1B64DA; }
.kpi-card.success { border-left: 4px solid #00C73C; }
.kpi-card.warning { border-left: 4px solid #FF6B00; }
.kpi-card.danger  { border-left: 4px solid #F03C2E; }
.kpi-card.neutral { border-left: 4px solid #9CA3AF; }

.kpi-label { font-size: 0.76rem; font-weight: 500; color: #6B7684; margin-bottom: 0.3rem; }

/* KPI 큰 숫자 — flex:1 컨테이너 안에서 절대 줄바꿈 안 함 */
.kpi-num {
    font-size: 1.35rem;
    font-weight: 800;
    color: #191F28;
    line-height: 1.25;
    white-space: nowrap;      /* 강제 한 줄 */
    overflow: hidden;
    text-overflow: ellipsis;  /* 넘치면 … 처리 (사실상 발생 안 함) */
}

/* 손익·타임라인 등 보조 큰 숫자 */
.kpi-value {
    font-size: 1.35rem;
    font-weight: 800; color: #191F28; line-height: 1.25;
    word-break: keep-all;
}
.kpi-value-md { font-size: 1.1rem; font-weight: 700; color: #191F28; word-break: keep-all; }
.kpi-sub   { font-size: 0.73rem; color: #9CA3AF; margin-top: 0.25rem; }
.badge {
    display: inline-block;
    font-size: 0.70rem;
    font-weight: 600;
    padding: 0.15rem 0.55rem;
    border-radius: 99px;
    margin-top: 0.3rem;
    letter-spacing: 0.02em;
}
.badge-blue   { background: #EFF6FF; color: #1B64DA; }
.badge-green  { background: #F0FDF4; color: #15803D; }
.badge-red    { background: #FEF2F2; color: #B91C1C; }
.badge-orange { background: #FFF7ED; color: #C2410C; }
.badge-gray   { background: #F3F4F6; color: #6B7684; }

/* ── 알림 박스 ── */
.alert {
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin: 0.35rem 0;
    font-size: 0.87rem;
    line-height: 1.5;
}
.alert-warn   { background: #FFF7ED; border: 1px solid #FED7AA; color: #92400E; }
.alert-danger { background: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; }
.alert-ok     { background: #F0FDF4; border: 1px solid #BBF7D0; color: #166534; }
.alert-info   { background: #EFF6FF; border: 1px solid #BFDBFE; color: #1E40AF; }

/* ── 자금 흐름 박스 ── */
.flow-item {
    background: #F9FAFB;
    border-radius: 10px;
    border: 1px solid #E5E8EB;
    padding: 0.65rem 0.8rem;
    text-align: center;
}
.flow-label { font-size: 0.73rem; color: #6B7684; margin-bottom: 0.2rem; white-space: nowrap; }
.flow-value { font-size: 0.85rem; font-weight: 700; color: #191F28; overflow-wrap: anywhere; line-height: 1.35; }

/* ── DSR 게이지 ── */
.dsr-bar-wrap {
    background: #F3F4F6;
    border-radius: 99px;
    height: 10px;
    margin: 0.5rem 0;
    overflow: hidden;
}
.dsr-bar-fill {
    height: 100%;
    border-radius: 99px;
    transition: width 0.4s ease;
}

/* ── 퀵버튼 ── */
/* Streamlit 1.32+ 실제 DOM: data-testid="stBaseButton-secondary" */
button[data-testid="stBaseButton-secondary"] {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    white-space: nowrap !important;   /* 핵심: 줄바꿈 금지 */
    height: 28px !important;
    min-height: 0 !important;
    padding: 0 10px !important;
    line-height: 28px !important;
    border-radius: 7px !important;
    border: 1px solid #E2E5EA !important;
    background: #F5F6F8 !important;
    color: #6B7684 !important;
    box-shadow: none !important;
    letter-spacing: -0.01em !important;
}
button[data-testid="stBaseButton-secondary"]:hover {
    background: #EBF2FF !important;
    border-color: #BFDBFE !important;
    color: #1B64DA !important;
}

/* ── 숫자 입력 ── */
.stNumberInput > div > div > input {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    height: 44px !important;
    border-radius: 10px !important;
}

/* 퀵버튼 위 여백 최소화 — 입력칸과 바짝 붙도록 */
[data-testid="stHorizontalBlock"]:has(button[data-testid="stBaseButton-secondary"]) {
    margin-top: -0.5rem !important;
    margin-bottom: 0.2rem !important;
}

/* ── 타임라인 스텝 카드 ── */
.step-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.5rem;
    border: 1px solid #E5E8EB;
    display: flex;
    gap: 0.9rem;
    align-items: flex-start;
}
.step-card.done   { opacity: 0.55; }
.step-card.active { border-color: #1B64DA; background: #EFF6FF; }
.step-card.urgent { border-color: #F03C2E; background: #FEF2F2; }
.step-dot {
    width: 36px; height: 36px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    font-size: 1rem;
    font-weight: 700;
}
.dot-done   { background: #F3F4F6; color: #6B7684; }
.dot-active { background: #DBEAFE; color: #1B64DA; }
.dot-future { background: #F3F4F6; color: #374151; }
.dot-urgent { background: #FEE2E2; color: #B91C1C; }
.step-content-label { font-size: 0.77rem; color: #6B7684; }
.step-content-ym { font-size: 1.05rem; font-weight: 700; color: #191F28; }
.step-content-desc { font-size: 0.78rem; color: #9CA3AF; }

/* ── 섹션 구분선 타이틀 ── */
.divider-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: #6B7684;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    padding: 0.5rem 0 0.3rem;
    border-top: 1px solid #F3F4F6;
    margin-top: 0.7rem;
}

/* ── 손익분기 큰 숫자 ── */
.be-box {
    background: linear-gradient(135deg, #1B64DA 0%, #2563EB 100%);
    border-radius: 18px;
    padding: 1.8rem;
    color: #FFFFFF;
    margin-bottom: 0.8rem;
    text-align: center;
}
.be-label { font-size: 0.78rem; opacity: 0.8; margin-bottom: 0.4rem; }
.be-value { font-size: 2.4rem; font-weight: 900; line-height: 1.1; }
.be-sub   { font-size: 0.82rem; opacity: 0.75; margin-top: 0.4rem; }

.be-box-fail {
    background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%);
    border-radius: 18px;
    padding: 1.8rem;
    color: #FFFFFF;
    margin-bottom: 0.8rem;
    text-align: center;
}

/* ── 모드 토글 (라디오 → 세그먼트 컨트롤) ── */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex !important;
    gap: 0 !important;
    background: #E9ECF0;
    border-radius: 14px;
    padding: 5px;
    width: fit-content;
}
div[data-testid="stRadio"] label {
    cursor: pointer;
    border-radius: 10px;
    padding: 0.45rem 1.4rem !important;
    font-weight: 500;
    font-size: 0.95rem !important;
    color: #6B7684 !important;
    transition: all 0.15s;
    margin: 0 !important;
    user-select: none;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background: #FFFFFF !important;
    color: #1B64DA !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.10);
}
div[data-testid="stRadio"] span[data-testid="stMarkdownContainer"] p {
    font-size: 0.95rem !important;
}
/* 라디오 도트 숨기기 */
div[data-testid="stRadio"] [data-testid="stWidgetLabel"] { display: none; }
div[data-testid="stRadio"] svg { display: none !important; }
div[data-testid="stRadio"] input[type="radio"] { display: none !important; }

/* ── 모바일 반응형 ── */
@media (max-width: 768px) {
    /* st.columns → 세로 스택 */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0.5rem !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        width: 100% !important;
        flex: none !important;
        min-width: 100% !important;
    }

    /* KPI 카드 폰트 축소 */
    .kpi-value { font-size: 1.3rem !important; }
    .kpi-label { font-size: 0.7rem !important; }

    /* 자금 흐름 — 좁은 화면에서 세로 배치 */
    .flow-row {
        flex-direction: column !important;
        gap: 0.4rem !important;
    }
    .flow-op { display: none !important; }
    .flow-item { width: 100% !important; text-align: left !important; padding: 0.5rem 0.75rem !important; }
    .flow-value { font-size: 0.9rem !important; }

    /* 사이드바 여백 축소 */
    section[data-testid="stSidebar"] { min-width: 0 !important; }
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# 규제 상수
# ═══════════════════════════════════════════════════════════

REGION_REGULATED = "규제지역"
REGION_METRO     = "수도권비규제"
REGION_LOCAL     = "지방"
OWN_NONE         = "무주택"
OWN_ONE_COND     = "1주택(처분조건부)"
OWN_ONE          = "1주택"
OWN_TWO_PLUS     = "2주택이상"
LOAN_VARIABLE    = "변동형"
LOAN_MIXED       = "혼합형"
LOAN_FIXED       = "고정형"

STRESS_RATE = {
    REGION_REGULATED: 0.030,
    REGION_METRO:     0.015,
    REGION_LOCAL:     0.0075,
}
LTV_LIMITS = {
    REGION_REGULATED: {OWN_NONE: 0.40, OWN_ONE_COND: 0.40, OWN_ONE: 0.00, OWN_TWO_PLUS: 0.00},
    REGION_METRO:     {OWN_NONE: 0.70, OWN_ONE_COND: 0.70, OWN_ONE: 0.60, OWN_TWO_PLUS: 0.00},
    REGION_LOCAL:     {OWN_NONE: 0.80, OWN_ONE_COND: 0.80, OWN_ONE: 0.70, OWN_TWO_PLUS: 0.60},
}
LOAN_CEILING = [(150_000, 60_000), (250_000, 40_000), (None, 20_000)]
LTV_FIRST_HOME  = 0.70
DSR_BANK        = 0.40
MAX_YEARS_METRO = 30


# ═══════════════════════════════════════════════════════════
# 계산 엔진
# ═══════════════════════════════════════════════════════════

def _get_ltv(region, ownership, is_first):
    if is_first and region in (REGION_REGULATED, REGION_METRO):
        return LTV_FIRST_HOME
    return LTV_LIMITS.get(region, LTV_LIMITS[REGION_LOCAL]).get(ownership, 0.0)

def _get_ceiling(target, region):
    if region == REGION_LOCAL:
        return None
    for thr, ceil in LOAN_CEILING:
        if thr is None or target <= thr:
            return ceil
    return LOAN_CEILING[-1][1]

def _stress_addon(region, loan_type):
    base = STRESS_RATE.get(region, 0.0)
    if loan_type == LOAN_MIXED:  return base * 0.6
    if loan_type == LOAN_FIXED:  return 0.0
    return base

def _monthly_pmt(principal, rate, years):
    if rate <= 0 or years <= 0 or principal <= 0:
        return 0
    r = rate / 12;  n = years * 12
    return round(principal * r * (1 + r) ** n / ((1 + r) ** n - 1))

def _credit_dsr(bal, rate, yrs, is_inst):
    if bal <= 0 or yrs <= 0:
        return 0
    p = bal * 10_000
    if is_inst:
        return _monthly_pmt(p, rate, yrs) * 12
    return round(p / min(yrs, 10) + p * rate)

def calc_acquisition_tax(price, is_large):
    pa = price / 10_000
    if price <= 60_000:    rate = 0.01
    elif price <= 90_000:  rate = max(0.01, min(0.03, (pa * 2/3 - 3) / 100))
    else:                  rate = 0.03
    base = price * 10_000 * rate
    edu  = base * 0.1
    agr  = base * 0.2 if is_large else 0
    return {"base": round(base), "edu": round(edu), "agr": round(agr),
            "total": round(base + edu + agr), "rate_pct": round(rate * 100, 2)}

def calc_brokerage(price):
    p = price
    if p < 5_000:    rate, cap = 0.006, 250_000
    elif p < 20_000: rate, cap = 0.005, 800_000
    elif p < 90_000: rate, cap = 0.004, None
    elif p < 120_000:rate, cap = 0.005, None
    elif p < 150_000:rate, cap = 0.006, None
    else:            rate, cap = 0.007, None
    fee = price * 10_000 * rate
    return round(min(fee, cap) if cap else fee)

def run_sim(p):
    region, ownership, loan_type = p["region"], p["ownership"], p["loan_type"]
    is_first, loan_rate, loan_years = p["is_first"], p["loan_rate"], int(p["loan_years"])
    cur, cur_loan, tgt, cash = int(p["cur"]), int(p["cur_loan"]), int(p["tgt"]), int(p["cash"])
    income, moving, is_large = int(p["income"]), int(p["moving"]), p["is_large"]
    ex_loans = p.get("ex_loans", [])
    warnings = []

    ltv = _get_ltv(region, ownership, is_first)
    if ltv == 0.0:
        warnings.append(("danger", "⛔ 해당 조건에서는 주택 구입 목적 주담대가 불가합니다"))

    if region in (REGION_REGULATED, REGION_METRO) and loan_years > MAX_YEARS_METRO:
        loan_years = MAX_YEARS_METRO
        warnings.append(("warn", f"⚠️ 수도권·규제지역 최대 대출기간 {MAX_YEARS_METRO}년으로 조정되었습니다"))

    net_sell    = cur - cur_loan
    total_avail = net_sell + cash
    need_loan   = max(0, tgt - total_avail)

    max_by_ltv = int(tgt * ltv)
    ceiling    = _get_ceiling(tgt, region)
    max_loan   = min(max_by_ltv, ceiling) if ceiling else max_by_ltv
    act_loan   = min(need_loan, max_loan)
    shortfall  = max(0, need_loan - act_loan)

    if shortfall > 0:
        warnings.append(("warn",
            f"⚠️ 규제 한도 부족 — 필요 {need_loan:,}만원, 가능 {act_loan:,}만원 (부족 {shortfall:,}만원)"))

    act_원       = act_loan * 10_000
    monthly      = _monthly_pmt(act_원, loan_rate, loan_years)
    stress_add   = _stress_addon(region, loan_type)
    stress_rate  = loan_rate + stress_add
    monthly_str  = _monthly_pmt(act_원, stress_rate, loan_years)

    ex_annual = sum(_credit_dsr(l["bal"], l["rate"], l["yrs"], l["is_inst"]) for l in ex_loans)
    dsr = stress_dsr = dsr_ok = None
    if income > 0:
        inc_원      = income * 10_000
        dsr         = round((monthly * 12 + ex_annual) / inc_원 * 100, 1)
        stress_dsr  = round((monthly_str * 12 + ex_annual) / inc_원 * 100, 1)
        dsr_ok      = stress_dsr <= DSR_BANK * 100
        if not dsr_ok:
            warnings.append(("warn",
                f"⚠️ 스트레스 DSR {stress_dsr}% > 은행 한도 40% 초과 (가산 금리 +{round(stress_add*100,2)}%p 반영)"))

    tax   = calc_acquisition_tax(tgt, is_large)
    sf    = calc_brokerage(cur)
    bf    = calc_brokerage(tgt)
    total_cost = tax["total"] + sf + bf + moving * 10_000

    rate_scen = {}
    for d in (0.005, 0.010, 0.015, 0.020):
        sp = _monthly_pmt(act_원, loan_rate + d, loan_years)
        rate_scen[f"+{d*100:.1f}%p"] = {
            "rate": round((loan_rate + d) * 100, 2),
            "pmt": sp, "diff": sp - monthly,
        }

    # 상환 스케줄 (연간 요약)
    amort = []
    balance = act_원
    r = loan_rate / 12
    for yr in range(1, min(loan_years + 1, 31)):
        yr_int = yr_prin = 0
        for _ in range(12):
            interest = balance * r
            principal = monthly - interest
            if principal < 0: principal = 0
            balance = max(0, balance - principal)
            yr_int  += interest
            yr_prin += principal
        amort.append({"year": yr, "interest": round(yr_int/10_000), "principal": round(yr_prin/10_000), "balance": round(balance/10_000)})

    return {
        "net_sell": net_sell, "total_avail": total_avail,
        "need_loan": need_loan, "act_loan": act_loan, "shortfall": shortfall,
        "monthly": monthly, "monthly_str": monthly_str,
        "loan_rate_pct": round(loan_rate*100,2), "stress_rate_pct": round(stress_rate*100,2),
        "stress_add_pct": round(stress_add*100,2), "loan_years": loan_years,
        "ltv_pct": round(act_loan/tgt*100,1) if tgt else 0,
        "ltv_limit_pct": round(ltv*100),
        "ceiling": ceiling,
        "dsr": dsr, "stress_dsr": stress_dsr, "dsr_ok": dsr_ok,
        "tax": tax, "sell_fee": sf, "buy_fee": bf,
        "total_brokerage": sf+bf, "moving_원": moving*10_000,
        "total_cost": total_cost,
        "warnings": warnings, "rate_scen": rate_scen, "amort": amort,
    }

def calc_breakeven(total_cost, monthly_gain, new_loan, loan_rate, opp_rate):
    if monthly_gain <= 0:
        return {"months": None, "note": "기대 상승액을 입력하면 손익분기를 계산합니다"}
    interest = new_loan * loan_rate / 12
    opp      = (total_cost / 10_000) * opp_rate / 12
    net      = monthly_gain - interest - opp
    if net <= 0:
        return {"months": None, "net": round(net), "interest": round(interest), "opp": round(opp),
                "note": "대출이자 + 기회비용이 기대 상승액보다 큽니다"}
    return {"months": round(total_cost / (net * 10_000), 1),
            "net": round(net), "interest": round(interest), "opp": round(opp),
            "note": f"실질 월 이득 {round(net):,}만원"}

def calc_schedule(yr, mo, cur_price, eg):
    today = date.today()
    td    = date(yr, mo, 1)
    left  = (td.year - today.year) * 12 + (td.month - today.month)
    bc    = td    - relativedelta(months=2)
    bk    = bc    - relativedelta(months=2)
    sc    = bk    - relativedelta(weeks=2)
    sk    = sc    - relativedelta(months=2)
    late  = sk < today
    if late:       status = ("⚠️ 이미 매도 시작해야 할 시점", "urgent")
    elif left >= 8: status = ("🟢 여유 있음", "ok")
    elif left >= 5: status = ("🟡 슬슬 준비해야 함", "warn")
    else:           status = ("🔴 서둘러야 함", "danger")
    opp = cur_price * 0.025 / 12
    return {
        "left": left, "status": status, "late": late,
        "steps": [
            ("📋", "매도 계약", sk.strftime("%Y-%m"), "지금부터 매물 내놓기 시작"),
            ("🔑", "매도 잔금", sc.strftime("%Y-%m"), "잔금 수령 및 이사 준비"),
            ("🖊️", "매수 계약", bk.strftime("%Y-%m"), "신규 주택 매수 계약 체결"),
            ("💳", "매수 잔금", bc.strftime("%Y-%m"), "잔금 납부 · 소유권 이전 등기"),
            ("🏠", "목표 입주", td.strftime("%Y-%m"), "입주"),
        ],
        "opp": round(opp), "net": round(eg - opp),
    }

def calc_max_price(cash, income, region, ownership, is_first,
                   loan_rate, loan_years, loan_type):
    """보유 현금 + 소득 → 최대 구매 가능 금액 역산 (LTV / DSR 두 제약 중 낮은 값)"""
    ltv        = _get_ltv(region, ownership, is_first)
    stress_add = _stress_addon(region, loan_type)
    stress_rate = loan_rate + stress_add

    # ① LTV 제약: price × (1 - ltv) ≤ cash  →  price ≤ cash / (1 - ltv)
    if ltv <= 0:
        max_price_ltv = cash
        max_loan_ltv  = 0
    elif ltv >= 1:
        max_price_ltv = 999_999
        max_loan_ltv  = 999_999 - cash
    else:
        max_price_ltv = int(cash / (1 - ltv))
        max_loan_ltv  = max_price_ltv - cash
        # 대출 한도(ceiling) 적용
        ceiling = _get_ceiling(max_price_ltv, region)
        if ceiling and max_loan_ltv > ceiling:
            max_loan_ltv  = ceiling
            max_price_ltv = cash + ceiling

    # ② DSR 제약: 스트레스 DSR ≤ 40%  →  역산 최대 대출
    max_price_dsr = max_price_ltv  # 소득 0이면 DSR 제약 없음
    max_loan_dsr  = max_loan_ltv
    if income > 0 and stress_rate > 0 and loan_years > 0:
        max_monthly    = income * 10_000 * DSR_BANK / 12  # 원
        r = stress_rate / 12;  n = loan_years * 12
        factor         = r * (1 + r) ** n / ((1 + r) ** n - 1)
        max_loan_dsr   = int(max_monthly / factor) // 10_000  # 만원
        max_price_dsr  = cash + max_loan_dsr
        # DSR로 도출된 대출도 ceiling 체크
        ceiling2 = _get_ceiling(max_price_dsr, region)
        if ceiling2 and max_loan_dsr > ceiling2:
            max_loan_dsr  = ceiling2
            max_price_dsr = cash + ceiling2

    # ③ 두 제약 중 더 타이트한 쪽
    if max_price_ltv <= max_price_dsr:
        binding     = "LTV"
        max_price   = max_price_ltv
        actual_loan = max_loan_ltv
    else:
        binding     = "DSR"
        max_price   = max_price_dsr
        actual_loan = max_loan_dsr

    actual_loan = max(0, actual_loan)
    max_price   = max(0, max_price)
    down_pmt    = max(0, max_price - actual_loan)

    monthly     = _monthly_pmt(actual_loan * 10_000, loan_rate, loan_years)
    monthly_str = _monthly_pmt(actual_loan * 10_000, stress_rate, loan_years)

    dsr = stress_dsr_val = None
    if income > 0 and monthly > 0:
        inc_원          = income * 10_000
        dsr             = round(monthly     * 12 / inc_원 * 100, 1)
        stress_dsr_val  = round(monthly_str * 12 / inc_원 * 100, 1)

    tax       = calc_acquisition_tax(max_price, False)
    brokerage = calc_brokerage(max_price)

    return {
        "max_price"      : max_price,
        "actual_loan"    : actual_loan,
        "down_payment"   : down_pmt,
        "ltv_pct"        : round(actual_loan / max_price * 100, 1) if max_price else 0,
        "ltv_limit_pct"  : round(ltv * 100),
        "binding"        : binding,
        "monthly"        : monthly,
        "monthly_str"    : monthly_str,
        "dsr"            : dsr,
        "stress_dsr"     : stress_dsr_val,
        "stress_add"     : round(stress_add * 100, 2),
        "stress_rate"    : round(stress_rate * 100, 2),
        "tax"            : tax,
        "brokerage"      : brokerage,
        "total_acq_cost" : tax["total"] + brokerage,  # 원
    }

def calc_stamp_tax(price_만):
    """인지세 (매매계약서, 원 단위 반환)"""
    if price_만 < 1_000:     return 0
    elif price_만 < 3_000:   return 20_000
    elif price_만 < 5_000:   return 40_000
    elif price_만 < 10_000:  return 70_000
    elif price_만 < 100_000: return 150_000
    else:                    return 350_000


# ═══════════════════════════════════════════════════════════
# 포맷 & UI 헬퍼
# ═══════════════════════════════════════════════════════════

def 억만(v):
    v = int(v)
    억 = v // 10_000;  rem = v % 10_000
    if 억 > 0:
        # \u00A0 = non-breaking space — 이 위치에서 줄바꿈 방지
        return f"{억}억\u00A0{rem:,}만" if rem else f"{억}억"
    return f"{v:,}만"

def 억만원(v):
    return 억만(v) + "원"

def 억만_원(v):
    """원 단위 입력"""
    v = int(v)
    억 = v // 100_000_000;  만 = (v % 100_000_000) // 10_000
    if 억 > 0:
        return f"{억}억 {만:,}만원" if 만 else f"{억}억원"
    return f"{만:,}만원"

def kpi(label, value, sub="", cls="primary"):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""<div class="kpi-card {cls}">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{value}</div>
  {sub_html}
</div>"""

def kpi_md(label, value, sub="", cls="primary"):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""<div class="kpi-card {cls}">
  <div class="kpi-label">{label}</div>
  <div class="kpi-value-md">{value}</div>
  {sub_html}
</div>"""

def alert(msg, kind="warn"):
    return f'<div class="alert alert-{kind}">{msg}</div>'

def section(title):
    st.markdown(f'<div class="divider-title">{title}</div>', unsafe_allow_html=True)

def _init(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

def _make_delta_fn(key: str, delta: int, min_val: int = 0):
    """on_click 콜백 팩토리 — 버튼 클릭 후 다음 run 시작 전에 호출되므로 위젯 미등록 상태에서 안전하게 session_state 수정 가능"""
    def _fn():
        current = int(st.session_state.get(key, 0))
        st.session_state[key] = max(min_val, current + delta)
    return _fn

def price_buttons(key,
                  presets=(10_000, 5_000, -5_000, -10_000),
                  labels=("+1억", "+5천", "–5천", "–1억")):
    """빠른 금액 조정 버튼 — on_click 콜백으로 session_state 충돌 회피"""
    cols = st.columns(len(presets), gap="small")
    for i, (amt, lbl) in enumerate(zip(presets, labels)):
        cols[i].button(
            lbl,
            key=f"_pb_{key}_{i}",
            on_click=_make_delta_fn(key, amt),
            use_container_width=True,
        )


# ═══════════════════════════════════════════════════════════
# 헤더 + 모드 토글
# ═══════════════════════════════════════════════════════════

st.markdown(
    '<div style="margin-bottom:0.7rem;">'
    '<span style="font-size:1.7rem;font-weight:900;color:#191F28;">🏠 부동산 계산기</span>'
    '</div>',
    unsafe_allow_html=True,
)

mode = st.radio(
    "계산기 모드",
    ["🔄 갈아타기 계산기", "🏠 첫 집 마련 계산기"],
    horizontal=True,
    label_visibility="collapsed",
    key="calc_mode",
)

# ════════════════════════════════════════════════════════════
# 첫 집 마련 계산기
# ════════════════════════════════════════════════════════════
if mode == "🏠 첫 집 마련 계산기":

    ftab1, ftab2, ftab3, ftab4 = st.tabs([
        "  💰 구매 가능 예산  ",
        "  🏦 정책대출 비교  ",
        "  ⚖️ 전세 vs 매매  ",
        "  📋 취득 비용 상세  ",
    ])

    # ── Tab 1: 구매 가능 예산 역산 ──────────────────────────
    with ftab1:
        f1L, f1R = st.columns([1, 1.15], gap="large")

        with f1L:
            st.markdown('<div class="input-section"><div class="section-label">내 자산 현황</div>', unsafe_allow_html=True)
            _init("f1_cash", 10_000)
            f1_cash = st.number_input("보유 현금 (만원)", key="f1_cash", min_value=0, step=500)
            price_buttons("f1_cash")
            _init("f1_income", 6_000)
            f1_income = st.number_input("연소득 세전 (만원)", key="f1_income", min_value=0, step=500,
                                        help="세전 연소득 기준 / 0 입력 시 DSR 계산 생략")
            price_buttons("f1_income",
                          presets=(5_000, 1_000, -1_000, -5_000),
                          labels=("+5천", "+1천", "–1천", "–5천"))
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="input-section"><div class="section-label">대출 조건</div>', unsafe_allow_html=True)
            f1c1, f1c2 = st.columns(2)
            f1_region    = f1c1.selectbox("지역",
                [REGION_REGULATED, REGION_METRO, REGION_LOCAL], index=1, key="f1_region",
                help="규제지역: 서울 전역 + 경기 12곳")
            f1_ownership = f1c2.selectbox("주택 보유",
                [OWN_NONE, OWN_ONE_COND, OWN_ONE, OWN_TWO_PLUS], index=0, key="f1_ownership")

            f1c3, f1c4 = st.columns(2)
            f1_loan_type = f1c3.selectbox("금리 유형",
                [LOAN_VARIABLE, LOAN_MIXED, LOAN_FIXED], key="f1_loan_type",
                help="변동형: 스트레스 100% | 혼합형: 60% | 고정형: 0%")
            f1_is_first  = f1c4.checkbox("생애최초", key="f1_is_first", value=True,
                                          help="LTV 70% 특례 + 취득세 감면 적용")

            f1c5, f1c6 = st.columns([2, 1])
            f1_loan_rate_pct = f1c5.slider("대출 금리 (%)", 1.0, 10.0, 3.7, 0.05,
                                            format="%.2f%%", key="f1_loan_rate")
            f1_loan_years    = int(f1c6.number_input("기간 (년)", value=30, min_value=1,
                                                      max_value=50, step=5, key="f1_loan_years"))
            st.markdown('</div>', unsafe_allow_html=True)

        with f1R:
            FA = calc_max_price(
                cash=f1_cash, income=f1_income,
                region=f1_region, ownership=f1_ownership, is_first=f1_is_first,
                loan_rate=f1_loan_rate_pct / 100, loan_years=f1_loan_years,
                loan_type=f1_loan_type,
            )

            # ── KPI 3개 ──────────────────────────────────────
            bind_bc, bind_lbl = (
                ("badge-orange", "DSR 제약") if FA["binding"] == "DSR"
                else ("badge-blue", "LTV 제약")
            )
            st.markdown(f"""
<div style="display:flex;gap:0.75rem;margin-bottom:0.9rem;">
  <div class="kpi-card primary" style="flex:1;min-width:0;">
    <div class="kpi-label">최대 구매 가능</div>
    <div class="kpi-num">{억만원(FA["max_price"])}</div>
    <div class="kpi-sub"><span class="badge {bind_bc}">{bind_lbl}</span></div>
  </div>
  <div class="kpi-card neutral" style="flex:1;min-width:0;">
    <div class="kpi-label">필요 대출</div>
    <div class="kpi-num">{억만원(FA["actual_loan"])}</div>
    <div class="kpi-sub">LTV {FA["ltv_pct"]}% (한도 {FA["ltv_limit_pct"]}%)</div>
  </div>
  <div class="kpi-card neutral" style="flex:1;min-width:0;">
    <div class="kpi-label">월 상환액</div>
    <div class="kpi-num">{억만_원(FA["monthly"])}</div>
    <div class="kpi-sub">스트레스 {억만_원(FA["monthly_str"])}</div>
  </div>
</div>
""", unsafe_allow_html=True)

            # ── DSR 게이지 ────────────────────────────────────
            if FA["stress_dsr"] is not None:
                dsr_ok    = FA["stress_dsr"] <= 40
                dsr_color = "#00C73C" if dsr_ok else "#F03C2E"
                bar_pct   = min(100, FA["stress_dsr"])
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;'
                    f'font-size:0.82rem;color:#6B7684;margin-bottom:4px;">'
                    f'<span>스트레스 DSR: <b style="color:#191F28;">{FA["stress_dsr"]}%</b>'
                    f' (+{FA["stress_add"]}%p 가산)</span>'
                    f'<span>은행 한도 40%</span></div>'
                    f'<div class="dsr-bar-wrap">'
                    f'<div class="dsr-bar-fill" style="width:{bar_pct}%;background:{dsr_color};"></div>'
                    f'</div>'
                    f'<div style="font-size:0.78rem;color:{dsr_color};font-weight:600;margin-top:4px;">'
                    f'{"✅ 한도 통과" if dsr_ok else "❌ 한도 초과"}'
                    f' &nbsp;|&nbsp; 실제 DSR {FA["dsr"]}%</div>',
                    unsafe_allow_html=True,
                )

            # ── 총 필요 자금 흐름 ─────────────────────────────
            section("총 필요 자금")
            acq_만         = FA["total_acq_cost"] // 10_000
            total_needed_만 = FA["down_payment"] + acq_만
            cash_ok   = f1_cash >= total_needed_만
            ok_color  = "#15803D" if cash_ok else "#B91C1C"
            ok_bg     = "#F0FDF4" if cash_ok else "#FFF1F0"
            ok_border = "#86EFAC" if cash_ok else "#FECACA"

            st.markdown(f"""
<div style="display:flex;gap:0.5rem;align-items:stretch;flex-wrap:wrap;">
  <div class="flow-item" style="flex:1;min-width:0;">
    <div class="flow-label">자기자본</div>
    <div class="flow-value">{억만원(FA["down_payment"])}</div>
  </div>
  <div style="display:flex;align-items:center;color:#9CA3AF;font-size:1.1rem;font-weight:700;flex-shrink:0;padding:0 0.2rem;" class="flow-op">＋</div>
  <div class="flow-item" style="flex:1;min-width:0;">
    <div class="flow-label">취득비용</div>
    <div class="flow-value">{억만원(acq_만)}</div>
  </div>
  <div style="display:flex;align-items:center;color:#9CA3AF;font-size:1.1rem;font-weight:700;flex-shrink:0;padding:0 0.2rem;" class="flow-op">＝</div>
  <div class="flow-item" style="flex:1;min-width:0;background:{ok_bg};border-color:{ok_border};">
    <div class="flow-label">총 필요 현금</div>
    <div class="flow-value" style="color:{ok_color};">{억만원(total_needed_만)}</div>
  </div>
</div>
""", unsafe_allow_html=True)

            if cash_ok:
                leftover = f1_cash - total_needed_만
                st.markdown(
                    alert(f"✅ 구매 후 여유 자금 {억만원(leftover)}", "ok"),
                    unsafe_allow_html=True,
                )
            else:
                shortfall = total_needed_만 - f1_cash
                st.markdown(
                    alert(f"⚠️ 현금 {억만원(shortfall)} 부족 — 구매 가능 금액을 낮추거나 추가 저축이 필요합니다", "warn"),
                    unsafe_allow_html=True,
                )

            # ── 현금별 최대 구매 가능 금액 차트 ──────────────
            section("현금별 최대 구매 가능 금액")
            base_c   = max(f1_cash, 1_000)
            cash_pts = [max(1_000, int(base_c * r / 10)) for r in range(3, 21)]
            price_pts = []
            for c in cash_pts:
                fa_tmp = calc_max_price(
                    c, f1_income, f1_region, f1_ownership, f1_is_first,
                    f1_loan_rate_pct / 100, f1_loan_years, f1_loan_type,
                )
                price_pts.append(fa_tmp["max_price"] / 10_000)  # 억원

            fig_fa = go.Figure()
            fig_fa.add_trace(go.Scatter(
                x=[c / 10_000 for c in cash_pts],
                y=price_pts,
                mode="lines+markers",
                line=dict(color="#1B64DA", width=2.5),
                marker=dict(size=7, color="#1B64DA"),
                fill="tozeroy",
                fillcolor="rgba(27,100,218,0.07)",
                hovertemplate="현금 %{x:.1f}억 → 최대 %{y:.1f}억<extra></extra>",
            ))
            fig_fa.add_shape(
                type="line",
                x0=f1_cash / 10_000, x1=f1_cash / 10_000,
                y0=0, y1=1, xref="x", yref="paper",
                line=dict(dash="dash", color="#FF6B00", width=1.5),
            )
            fig_fa.add_annotation(
                x=f1_cash / 10_000, y=1, xref="x", yref="paper",
                text=f"현재 {f1_cash/10_000:.1f}억",
                showarrow=False,
                font=dict(color="#FF6B00", size=10),
                yanchor="bottom",
            )
            fig_fa.update_layout(
                xaxis_title="보유 현금 (억원)",
                yaxis_title="구매 가능 금액 (억원)",
                height=220,
                margin=dict(l=0, r=20, t=10, b=0),
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(size=11),
                showlegend=False,
            )
            st.plotly_chart(fig_fa, use_container_width=True)

    # ── Tab 2~4 ──────────────────────────────────────────────
    with ftab2:
        f2L, f2R = st.columns([1, 1.5], gap="large")

        # ── 입력 ─────────────────────────────────────────────
        with f2L:
            st.markdown('<div class="input-section"><div class="section-label">내 조건</div>', unsafe_allow_html=True)
            _init("f2_income", 6_000)
            f2_income = st.number_input("연소득 세전 (만원, 부부합산)", key="f2_income",
                                         min_value=0, step=500)
            price_buttons("f2_income",
                          presets=(5_000, 1_000, -1_000, -5_000),
                          labels=("+5천", "+1천", "–1천", "–5천"))
            _init("f2_price", 45_000)
            f2_price = st.number_input("희망 주택가 (만원)", key="f2_price",
                                        min_value=1_000, step=1_000)
            price_buttons("f2_price")
            f2c1, f2c2 = st.columns(2)
            f2_years    = int(f2c1.selectbox("대출 만기", [10, 15, 20, 25, 30, 40],
                                              index=4, key="f2_years",
                                              format_func=lambda x: f"{x}년"))
            f2_is_first = f2c2.checkbox("생애최초", key="f2_is_first2", value=True)
            f2c3, f2c4 = st.columns(2)
            f2_newlywed = f2c3.checkbox("신혼가구 (7년 이내)", key="f2_newlywed",
                                         help="디딤돌·보금자리론 소득 한도 확대")
            f2_newborn  = f2c4.checkbox("신생아 특례 대상", key="f2_newborn",
                                         help="2023.1.1 이후 출생아 또는 입양 가구")
            st.markdown('</div>', unsafe_allow_html=True)

            with st.expander("⚙️ 금리 기준 직접 수정 (2025.04 기준)"):
                st.caption("고시 금리 변경 시 직접 수정하세요")

                st.markdown("**디딤돌 대출 (소득 구간별)**")
                da, db_col = st.columns(2)
                _init("f2_dd_r1", 2.15);  _init("f2_dd_r2", 2.35)
                dd_r1 = da.number_input("~2천만원 (%)",    key="f2_dd_r1", min_value=0.1, max_value=10.0, format="%.2f", step=0.05)
                dd_r2 = db_col.number_input("2천~4천만 (%)", key="f2_dd_r2", min_value=0.1, max_value=10.0, format="%.2f", step=0.05)
                dc_col, de_col = st.columns(2)
                _init("f2_dd_r3", 2.65);  _init("f2_dd_r4", 2.85)
                dd_r3 = dc_col.number_input("4천~6천만 (%)",    key="f2_dd_r3", min_value=0.1, max_value=10.0, format="%.2f", step=0.05)
                dd_r4 = de_col.number_input("6천~8.5천만 (%)", key="f2_dd_r4", min_value=0.1, max_value=10.0, format="%.2f", step=0.05)

                st.markdown("**보금자리론 (만기별 고정금리)**")
                ba, bb_col = st.columns(2)
                _init("f2_bg_r10", 3.95);  _init("f2_bg_r20", 4.00)
                bg_r10 = ba.number_input("10~15년 (%)", key="f2_bg_r10", min_value=0.1, max_value=10.0, format="%.2f", step=0.05)
                bg_r20 = bb_col.number_input("20~25년 (%)", key="f2_bg_r20", min_value=0.1, max_value=10.0, format="%.2f", step=0.05)
                bc_col, bd_col = st.columns(2)
                _init("f2_bg_r30", 4.15);  _init("f2_bg_r40", 4.25)
                bg_r30 = bc_col.number_input("30년 (%)", key="f2_bg_r30", min_value=0.1, max_value=10.0, format="%.2f", step=0.05)
                bg_r40 = bd_col.number_input("40년 (%)", key="f2_bg_r40", min_value=0.1, max_value=10.0, format="%.2f", step=0.05)

                st.markdown("**신생아특례대출 (소득 구간별)**")
                na_col, nb_col2 = st.columns(2)
                _init("f2_nb_r1", 2.00);  _init("f2_nb_r2", 3.00)
                nb_r1 = na_col.number_input("~8.5천만원 (%)",    key="f2_nb_r1", min_value=0.1, max_value=10.0, format="%.2f", step=0.05)
                nb_r2 = nb_col2.number_input("8.5천~1.3억 (%)", key="f2_nb_r2", min_value=0.1, max_value=10.0, format="%.2f", step=0.05)

        # ── 계산 + 결과 ───────────────────────────────────────
        with f2R:
            ltv2 = 0.80 if f2_is_first else 0.70

            # 디딤돌 ────────────────────────────────────────────
            dd_inc_lim = 8_500 if f2_newlywed else 6_000
            dd_prc_lim = 60_000 if f2_newlywed else 50_000
            dd_ok_inc  = f2_income <= dd_inc_lim
            dd_ok_prc  = f2_price  <= dd_prc_lim
            dd_ok      = dd_ok_inc and dd_ok_prc
            if   f2_income <= 2_000: dd_rate = dd_r1 / 100
            elif f2_income <= 4_000: dd_rate = dd_r2 / 100
            elif f2_income <= 6_000: dd_rate = dd_r3 / 100
            else:                    dd_rate = dd_r4 / 100
            dd_max_loan = min(int(f2_price * ltv2), 30_000)
            dd_monthly  = _monthly_pmt(dd_max_loan * 10_000, dd_rate, f2_years) if dd_ok else 0

            # 보금자리론 ────────────────────────────────────────
            bg_inc_lim = 8_500 if f2_newlywed else 7_000
            bg_ok_inc  = f2_income <= bg_inc_lim
            bg_ok_prc  = f2_price  <= 60_000
            bg_ok      = bg_ok_inc and bg_ok_prc
            if   f2_years <= 15: bg_rate = bg_r10 / 100
            elif f2_years <= 25: bg_rate = bg_r20 / 100
            elif f2_years <= 30: bg_rate = bg_r30 / 100
            else:                bg_rate = bg_r40 / 100
            bg_max_loan = min(int(f2_price * ltv2), 36_000)
            bg_monthly  = _monthly_pmt(bg_max_loan * 10_000, bg_rate, f2_years) if bg_ok else 0

            # 신생아특례 ────────────────────────────────────────
            nb_ok_inc  = f2_income <= 13_000
            nb_ok_prc  = f2_price  <= 90_000
            nb_ok      = f2_newborn and nb_ok_inc and nb_ok_prc
            nb_rate    = (nb_r1 if f2_income <= 8_500 else nb_r2) / 100
            nb_max_loan = min(int(f2_price * ltv2), 50_000)
            nb_monthly  = _monthly_pmt(nb_max_loan * 10_000, nb_rate, f2_years) if nb_ok else 0

            # ── 카드 헬퍼 ────────────────────────────────────
            def _reject(ok_inc, ok_prc, inc_lim, prc_lim, birth_ok=True):
                if not birth_ok: return "신생아 특례 비해당"
                r = []
                if not ok_inc: r.append(f"소득 {inc_lim:,}만 초과")
                if not ok_prc: r.append(f"주택가 {prc_lim//10_000}억 초과")
                return " · ".join(r) if r else "조건 불충족"

            def _loan_card(name, ok, rate_pct, max_loan, monthly,
                           inc_lim, prc_lim, color, note, reject_msg):
                num_c = "#191F28" if ok else "#9CA3AF"
                badge = (
                    '<span class="badge badge-green">✅ 적격</span>'
                    if ok else
                    f'<span class="badge badge-gray">❌ {reject_msg}</span>'
                )
                m_str = f"{monthly/10_000:,.0f}만원" if monthly else "—"
                return f"""<div class="kpi-card" style="border-left:4px solid {color};opacity:{'1.0' if ok else '0.55'};flex:1;min-width:0;display:flex;flex-direction:column;">
  <div style="font-size:0.9rem;font-weight:800;color:{color};margin-bottom:0.35rem;">{name}</div>
  <div style="margin-bottom:0.6rem;">{badge}</div>
  <div style="display:flex;gap:1rem;margin-bottom:0.55rem;">
    <div>
      <div class="kpi-label">금리</div>
      <div style="font-size:1.35rem;font-weight:800;color:{num_c};">{rate_pct:.2f}%</div>
    </div>
    <div>
      <div class="kpi-label">최대 대출</div>
      <div style="font-size:1.0rem;font-weight:700;color:{num_c};">{억만원(max_loan)}</div>
    </div>
  </div>
  <div class="kpi-label">월 상환액 (원리금균등)</div>
  <div style="font-size:1.1rem;font-weight:700;color:{num_c};margin-bottom:0.4rem;">{m_str}</div>
  <div style="font-size:0.72rem;color:#9CA3AF;line-height:1.6;margin-top:auto;">
    소득 {inc_lim:,}만 이하 &nbsp;|&nbsp; 주택 {prc_lim//10_000}억 이하<br>{note}
  </div>
</div>"""

            _card_dd = _loan_card(
                "디딤돌 대출", dd_ok, dd_rate * 100,
                dd_max_loan, dd_monthly, dd_inc_lim, dd_prc_lim,
                "#10B981", "변동/혼합/고정 선택 가능",
                _reject(dd_ok_inc, dd_ok_prc, dd_inc_lim, dd_prc_lim),
            )
            _card_bg = _loan_card(
                "보금자리론", bg_ok, bg_rate * 100,
                bg_max_loan, bg_monthly, bg_inc_lim, 60_000,
                "#3B82F6", f"고정금리 · 만기 {f2_years}년 기준",
                _reject(bg_ok_inc, bg_ok_prc, bg_inc_lim, 60_000),
            )
            _card_nb = _loan_card(
                "신생아특례대출", nb_ok, nb_rate * 100,
                nb_max_loan, nb_monthly, 13_000, 90_000,
                "#F59E0B", "특례 5년 후 일반금리 전환",
                _reject(nb_ok_inc, nb_ok_prc, 13_000, 90_000, birth_ok=f2_newborn),
            )
            st.markdown(
                f'<div style="display:flex;gap:0.75rem;align-items:stretch;">'
                f'{_card_dd}{_card_bg}{_card_nb}'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── 월 상환액 비교 차트 ──────────────────────────
            section("월 상환액 비교")
            bar_vals   = [dd_monthly / 10_000, bg_monthly / 10_000, nb_monthly / 10_000]
            bar_labels = ["디딤돌", "보금자리론", "신생아특례"]
            bar_colors = [
                "#10B981" if dd_ok else "#E5E7EB",
                "#3B82F6" if bg_ok else "#E5E7EB",
                "#F59E0B" if nb_ok else "#E5E7EB",
            ]
            bar_text = [
                f"{v:,.0f}만원" if v > 0 else "부적격"
                for v in bar_vals
            ]
            fig_bar = go.Figure(go.Bar(
                x=bar_labels, y=bar_vals,
                marker_color=bar_colors,
                text=bar_text, textposition="outside",
                width=0.45,
            ))
            fig_bar.update_layout(
                yaxis_title="월 상환액 (만원)", yaxis_rangemode="tozero",
                height=230,
                margin=dict(l=0, r=0, t=30, b=0),
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(size=12), showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # ── 조건 요약표 ──────────────────────────────────
            with st.expander("📋 정책대출 조건 전체 비교"):
                cond_rows = {
                    "소득 기준 (기본)":   ["6천만 이하",  "7천만 이하",  "1.3억 이하"],
                    "소득 기준 (신혼)":   ["8.5천만 이하","8.5천만 이하","(동일)"],
                    "주택가 기준":        ["5억 (신혼 6억)","6억 이하",   "9억 이하"],
                    "최대 대출":          ["3억",          "3.6억",       "5억"],
                    "LTV (기본)":         ["70%",          "70%",         "70%"],
                    "LTV (생애최초)":     ["80%",          "80%",         "80%"],
                    "금리 종류":          ["변동/혼합/고정","고정금리",   "고정(특례 5년)"],
                    "만기":              ["10~30년",       "10~40년",     "10~30년"],
                    "특이사항":          ["실수요 정책금리","장기 고정",   "2023년 이후 출산"],
                }
                cond_df = pd.DataFrame(cond_rows, index=["디딤돌","보금자리론","신생아특례"]).T
                cond_df.index.name = "항목"
                st.dataframe(cond_df, use_container_width=True)

    with ftab3:
        f3L, f3R = st.columns([1, 1.15], gap="large")

        # ── 입력 ─────────────────────────────────────────────
        with f3L:
            st.markdown('<div class="input-section"><div class="section-label">전세 조건</div>', unsafe_allow_html=True)
            _init("f3_jeonse", 30_000)
            f3_jeonse = st.number_input("전세 보증금 (만원)", key="f3_jeonse", min_value=0, step=1_000)
            price_buttons("f3_jeonse")
            f3_opp_rate = st.slider("기회비용 금리 (%)", 1.0, 8.0, 3.5, 0.25, format="%.2f%%",
                                    key="f3_opp",
                                    help="전세금을 예금·ETF 등에 투자했을 때 기대 수익률")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="input-section"><div class="section-label">매매 조건</div>', unsafe_allow_html=True)
            _init("f3_price", 50_000)
            f3_price = st.number_input("매매가 (만원)", key="f3_price", min_value=1_000, step=1_000)
            price_buttons("f3_price")
            _init("f3_loan3", 20_000)
            f3_loan = st.number_input("대출금 (만원)", key="f3_loan3", min_value=0, step=1_000)
            price_buttons("f3_loan3",
                          presets=(5_000, 1_000, -1_000, -5_000),
                          labels=("+5천", "+1천", "–1천", "–5천"))
            f3_loan_rate = st.slider("대출 금리 (%)", 1.0, 10.0, 3.7, 0.05,
                                     format="%.2f%%", key="f3_loan_rate")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="input-section"><div class="section-label">비교 설정</div>', unsafe_allow_html=True)
            f3_appr  = st.slider("기대 주택 상승률 (%/년)", -5.0, 15.0, 3.0, 0.5,
                                  format="%.1f%%", key="f3_appr",
                                  help="연간 집값 기대 상승률 (음수=하락)")
            f3_maint = st.number_input("연간 유지비 (만원)", value=200, step=50, min_value=0,
                                        key="f3_maint",
                                        help="재산세 + 관리비 + 수선비 등 연간 합계")
            f3_hold  = int(st.slider("비교 기간 (년)", 3, 30, 10, 1, key="f3_hold"))
            st.markdown('</div>', unsafe_allow_html=True)

        # ── 계산 + 결과 ───────────────────────────────────────
        with f3R:
            # 월별 비용 항목
            jeonse_m  = f3_jeonse * (f3_opp_rate / 100) / 12          # 만원/월
            interest_m = f3_loan  * (f3_loan_rate / 100) / 12         # 만원/월 (이자만)
            maint_m   = f3_maint / 12                                   # 만원/월
            appr_m    = f3_price  * (f3_appr / 100) / 12              # 만원/월 가격 상승 편익

            acq_cost  = (calc_acquisition_tax(f3_price, False)["total"]
                         + calc_brokerage(f3_price)) / 10_000           # 만원
            buy_net_m = interest_m + maint_m - appr_m                   # 만원/월 (음수=이득)

            # 손익분기
            net_diff = jeonse_m - buy_net_m  # 양수=매매 월 유리
            if net_diff > 0:
                be_months = acq_cost / net_diff
                be_yr, be_mo = int(be_months // 12), int(be_months % 12)
            else:
                be_months = None
                be_yr = be_mo = 0

            # ── KPI 3개 ──────────────────────────────────────
            adv_m   = net_diff  # 양수 = 매매 유리
            adv_cls = "success" if adv_m > 0 else "danger"
            st.markdown(f"""
<div style="display:flex;gap:0.75rem;margin-bottom:0.9rem;">
  <div class="kpi-card neutral" style="flex:1;min-width:0;">
    <div class="kpi-label">전세 월 기회비용</div>
    <div class="kpi-num">{jeonse_m:,.0f}만원</div>
    <div class="kpi-sub">보증금 × {f3_opp_rate:.2f}% ÷ 12</div>
  </div>
  <div class="kpi-card neutral" style="flex:1;min-width:0;">
    <div class="kpi-label">매매 월 순비용</div>
    <div class="kpi-num">{buy_net_m:+,.0f}만원</div>
    <div class="kpi-sub">이자 + 유지비 − 상승분</div>
  </div>
  <div class="kpi-card {adv_cls}" style="flex:1;min-width:0;">
    <div class="kpi-label">월 매매 유불리</div>
    <div class="kpi-num">{adv_m:+,.0f}만원</div>
    <div class="kpi-sub">{'매매가 유리' if adv_m > 0 else '전세가 유리'}</div>
  </div>
</div>
""", unsafe_allow_html=True)

            # ── 손익분기 박스 ─────────────────────────────────
            if be_months is not None and 0 < be_months <= f3_hold * 12:
                st.markdown(
                    f'<div class="be-box">'
                    f'<div class="be-label">취득비용 회수 완료 (손익분기)</div>'
                    f'<div class="be-value">{be_yr}년 {be_mo}개월</div>'
                    f'<div class="be-sub">이후 보유할수록 매매가 전세보다 유리</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            elif be_months is not None and be_months > f3_hold * 12:
                st.markdown(
                    f'<div class="be-box-fail">'
                    f'<div class="be-label">손익분기</div>'
                    f'<div class="be-value" style="font-size:1.25rem;">비교 기간 초과</div>'
                    f'<div class="be-sub">약 {be_yr}년 {be_mo}개월 후 — 더 오래 보유해야 매매 유리</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                if buy_net_m < 0:
                    st.markdown(
                        f'<div class="be-box">'
                        f'<div class="be-label">손익분기</div>'
                        f'<div class="be-value">즉시</div>'
                        f'<div class="be-sub">상승 편익 {appr_m:,.0f}만원/월 이 이자·유지비 초과 — 취득비용 {acq_cost:,.0f}만원만 회수하면 완전 유리</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="be-box-fail">'
                        f'<div class="be-label">손익분기</div>'
                        f'<div class="be-value" style="font-size:1.25rem;">없음</div>'
                        f'<div class="be-sub">현 조건에서는 매매 월 순비용이 전세 기회비용보다 큼</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # ── 누적 비용 추이 차트 ──────────────────────────
            section("누적 비용 추이")
            months_list = list(range(0, f3_hold * 12 + 1))
            yr_list     = [m / 12 for m in months_list]
            jeonse_cum  = [jeonse_m * m for m in months_list]
            buy_cum     = [acq_cost + buy_net_m * m for m in months_list]

            fig_be = go.Figure()
            fig_be.add_trace(go.Scatter(
                x=yr_list, y=jeonse_cum,
                name="전세 누적 기회비용",
                line=dict(color="#1B64DA", width=2.5),
                fill="tozeroy", fillcolor="rgba(27,100,218,0.07)",
            ))
            fig_be.add_trace(go.Scatter(
                x=yr_list, y=buy_cum,
                name="매매 누적 순비용",
                line=dict(color="#F03C2E", width=2, dash="dot"),
                fill="tozeroy", fillcolor="rgba(240,60,46,0.04)",
            ))
            if be_months is not None and 0 < be_months <= f3_hold * 12 * 1.05:
                fig_be.add_shape(
                    type="line",
                    x0=be_months / 12, x1=be_months / 12,
                    y0=0, y1=1, xref="x", yref="paper",
                    line=dict(dash="dash", color="#FF6B00", width=1.5),
                )
                fig_be.add_annotation(
                    x=be_months / 12, y=1, xref="x", yref="paper",
                    text=f"손익분기 {be_months/12:.1f}년",
                    showarrow=False, font=dict(color="#FF6B00", size=10),
                    yanchor="bottom",
                )
            fig_be.update_layout(
                xaxis_title="보유 기간 (년)",
                yaxis_title="누적 비용 (만원)",
                height=270,
                margin=dict(l=0, r=10, t=10, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                plot_bgcolor="white", paper_bgcolor="white",
                hovermode="x unified", font=dict(size=11),
            )
            st.plotly_chart(fig_be, use_container_width=True)

            # ── 연도별 비교표 ────────────────────────────────
            with st.expander("📋 연도별 상세 비교"):
                checkpoints = [y for y in [3, 5, 7, 10, 15, 20, 25, 30] if y <= f3_hold]
                rows = []
                for yr in checkpoints:
                    t  = yr * 12
                    jc = jeonse_m * t
                    bc = acq_cost + buy_net_m * t
                    diff = jc - bc
                    rows.append({
                        "보유 기간":       f"{yr}년",
                        "전세 누적비용":   f"{jc:,.0f}만원",
                        "매매 누적순비용": f"{bc:,.0f}만원",
                        "유불리":          f"{'매매' if diff >= 0 else '전세'} 유리 {abs(diff):,.0f}만원",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                st.caption(
                    "매매 누적순비용 = 취득비용 + 누적 이자 + 유지비 − 주택 가격 상승분  |  "
                    "전세 누적비용 = 보증금 × 기회비용금리 × 기간"
                )

    with ftab4:
        f4L, f4R = st.columns([1, 1.35], gap="large")

        # ── 입력 ─────────────────────────────────────────────
        with f4L:
            st.markdown('<div class="input-section"><div class="section-label">주택 정보</div>', unsafe_allow_html=True)
            _init("f4_price", 50_000)
            f4_price = st.number_input("매매가 (만원)", key="f4_price", min_value=1_000, step=1_000)
            price_buttons("f4_price")
            f4a, f4b = st.columns(2)
            f4_is_large4  = f4a.checkbox("전용 85㎡ 초과", key="f4_is_large4",
                                          help="농어촌특별세(취득세 × 20%) 추가 부과")
            f4_is_first4  = f4b.checkbox("생애최초", key="f4_is_first4", value=True,
                                          help="12억 이하 → 취득세 본세 최대 200만원 감면")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="input-section"><div class="section-label">대출 정보 (있을 경우)</div>', unsafe_allow_html=True)
            _init("f4_loan4", 0)
            f4_loan4 = st.number_input("대출금 (만원)", key="f4_loan4", min_value=0, step=1_000,
                                        help="근저당 설정 관련 비용 산정 기준")
            price_buttons("f4_loan4",
                          presets=(5_000, 1_000, -1_000, -5_000),
                          labels=("+5천", "+1천", "–1천", "–5천"))
            st.markdown('</div>', unsafe_allow_html=True)

            with st.expander("⚙️ 추가 비용 직접 입력"):
                st.caption("법무사 비용은 사무소마다 차이가 있으니 견적 확인 후 수정하세요")
                _init("f4_law_own", 35)
                f4_law_own = st.number_input("소유권이전 등기 법무사비 (만원)",
                                              key="f4_law_own", step=5, min_value=0,
                                              help="법무사 보수 + 등기신청 수수료 포함 추정치")
                _init("f4_law_mtg", 25 if f4_loan4 > 0 else 0)
                f4_law_mtg = st.number_input("근저당 설정 법무사비 (만원)",
                                              key="f4_law_mtg", step=5, min_value=0,
                                              help="대출 있을 때만 발생 (대출금 입력 후 직접 확인)")
                _init("f4_move4", 300)
                f4_move4   = st.number_input("이사비 (만원)", key="f4_move4",
                                              step=50, min_value=0)
                _init("f4_inter4", 0)
                f4_inter4  = st.number_input("인테리어/수리비 (만원)", key="f4_inter4",
                                              step=100, min_value=0,
                                              help="도배·장판·기타 입주 공사비")

        # ── 계산 + 결과 ───────────────────────────────────────
        with f4R:
            tax4    = calc_acquisition_tax(f4_price, f4_is_large4)
            broker4 = calc_brokerage(f4_price)
            stamp4_원 = calc_stamp_tax(f4_price)

            # 생애최초 감면: 주택가 12억 이하 → 취득세 본세 최대 200만원
            discount4 = 0
            if f4_is_first4 and f4_price <= 120_000:
                discount4 = min(tax4["base"], 2_000_000)

            # 항목 정의 (원 단위)
            CAT_COLOR = {
                "세금": "#F03C2E", "수수료": "#1B64DA",
                "등기": "#8B5CF6", "기타":   "#9CA3AF",
            }
            raw4 = [
                ("취득세 (본세)",         tax4["base"],           "세금"),
                ("지방교육세",            tax4["edu"],            "세금"),
                ("농어촌특별세",          tax4["agr"],            "세금"),
                ("중개보수",              broker4,                "수수료"),
                ("인지세 (매매계약서)",   stamp4_원,              "세금"),
                ("소유권이전 법무사비",   f4_law_own * 10_000,    "등기"),
                ("근저당설정 법무사비",   f4_law_mtg * 10_000,    "등기"),
                ("이사비",                f4_move4   * 10_000,    "기타"),
                ("인테리어/수리비",       f4_inter4  * 10_000,    "기타"),
            ]
            items4 = [(lbl, amt, cat) for lbl, amt, cat in raw4 if amt > 0]

            total_before4 = sum(a for _, a, _ in items4)
            total_after4  = total_before4 - discount4

            # ── 총비용 KPI ────────────────────────────────────
            if discount4 > 0:
                st.markdown(f"""
<div style="display:flex;gap:0.75rem;margin-bottom:0.9rem;">
  <div class="kpi-card neutral" style="flex:1;min-width:0;">
    <div class="kpi-label">감면 전 총비용</div>
    <div class="kpi-num" style="color:#9CA3AF;text-decoration:line-through;">{억만원(total_before4//10_000)}</div>
    <div class="kpi-sub">생애최초 감면 미적용</div>
  </div>
  <div class="kpi-card success" style="flex:1;min-width:0;">
    <div class="kpi-label">감면 후 총비용</div>
    <div class="kpi-num">{억만원(total_after4//10_000)}</div>
    <div class="kpi-sub">취득세 {discount4//10_000:,}만원 절감</div>
  </div>
  <div class="kpi-card neutral" style="flex:1;min-width:0;">
    <div class="kpi-label">취득세율 (본세)</div>
    <div class="kpi-num">{tax4["rate_pct"]}%</div>
    <div class="kpi-sub">매매가 대비 총비용 {total_after4/f4_price/100:.2f}%</div>
  </div>
</div>
""", unsafe_allow_html=True)
            else:
                over12 = f4_is_first4 and f4_price > 120_000
                st.markdown(f"""
<div style="display:flex;gap:0.75rem;margin-bottom:0.9rem;">
  <div class="kpi-card primary" style="flex:1;min-width:0;">
    <div class="kpi-label">총 취득 비용</div>
    <div class="kpi-num">{억만원(total_before4//10_000)}</div>
    <div class="kpi-sub">매매가 대비 {total_before4/f4_price/100:.2f}%</div>
  </div>
  <div class="kpi-card neutral" style="flex:1;min-width:0;">
    <div class="kpi-label">취득세율 (본세)</div>
    <div class="kpi-num">{tax4["rate_pct"]}%</div>
    <div class="kpi-sub">{'12억 초과 — 감면 불가' if over12 else '생애최초 미선택'}</div>
  </div>
</div>
""", unsafe_allow_html=True)
                if over12:
                    st.markdown(
                        alert("⚠️ 주택가 12억 초과 — 생애최초 취득세 감면 적용 불가", "warn"),
                        unsafe_allow_html=True,
                    )

            # ── 항목별 상세 ──────────────────────────────────
            section("취득 비용 상세 내역")
            for lbl, amt, cat in items4:
                color = CAT_COLOR[cat]
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;'
                    f'padding:0.32rem 0.4rem 0.32rem 0;border-bottom:1px solid #F3F4F6;">'
                    f'<div style="display:flex;align-items:center;gap:0.45rem;">'
                    f'<span style="width:7px;height:7px;border-radius:50%;'
                    f'background:{color};display:inline-block;flex-shrink:0;"></span>'
                    f'<span style="font-size:0.84rem;color:#374151;">{lbl}</span>'
                    f'<span class="badge" style="background:{color}1A;color:{color};'
                    f'font-size:0.66rem;">{cat}</span>'
                    f'</div>'
                    f'<span style="font-size:0.9rem;font-weight:700;color:#191F28;">'
                    f'{amt/10_000:,.0f}만원</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            if discount4 > 0:
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;'
                    f'padding:0.32rem 0.4rem 0.32rem 0;border-bottom:1px solid #BBF7D0;">'
                    f'<div style="display:flex;align-items:center;gap:0.45rem;">'
                    f'<span style="width:7px;height:7px;border-radius:50%;background:#00C73C;'
                    f'display:inline-block;flex-shrink:0;"></span>'
                    f'<span style="font-size:0.84rem;color:#15803D;font-weight:600;">'
                    f'생애최초 취득세 감면</span>'
                    f'<span class="badge badge-green" style="font-size:0.66rem;">절세</span>'
                    f'</div>'
                    f'<span style="font-size:0.9rem;font-weight:700;color:#15803D;">'
                    f'−{discount4//10_000:,}만원</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:0.55rem 0;'
                f'font-size:1rem;font-weight:800;border-top:2px solid #E5E8EB;margin-top:0.2rem;">'
                f'<span>최종 합계</span>'
                f'<span style="color:#1B64DA;">{억만원(total_after4//10_000)}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── 비용 구성 수평 바 차트 ────────────────────────
            section("비용 구성")
            bar_lbls4  = [lbl for lbl, _, _ in items4]
            bar_vals4  = [a / 10_000 for _, a, _ in items4]
            bar_clrs4  = [CAT_COLOR[cat] for _, _, cat in items4]

            fig_h4 = go.Figure(go.Bar(
                y=bar_lbls4, x=bar_vals4,
                orientation="h",
                marker_color=bar_clrs4,
                text=[f"{v:,.0f}만" for v in bar_vals4],
                textposition="outside",
                width=0.6,
            ))
            fig_h4.update_layout(
                xaxis_title="만원",
                height=max(180, len(items4) * 36 + 40),
                margin=dict(l=0, r=70, t=10, b=0),
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(size=11), showlegend=False,
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_h4, use_container_width=True)

            # ── 취득세 계산 근거 + 절세 팁 ───────────────────
            with st.expander("💡 취득세 계산 근거 & 절세 포인트"):
                st.markdown(f"""
**취득세율 체계 (현행)**
| 주택 가격 | 취득세율 |
|-----------|---------|
| 6천만원 이하 | 1.0% |
| 6천만 ~ 9천만원 | 1.0% ~ 3.0% (점진 증가) |
| 9천만원 초과 | 3.0% |

> 적용 세율: **{tax4["rate_pct"]}%** (매매가 {억만원(f4_price)} 기준)

**추가 세목**
- 지방교육세: 취득세 본세 × **10%**
- 농어촌특별세: 취득세 본세 × **20%** (전용 85㎡ 초과 주택)

**절세 포인트**
- ✅ **생애최초 감면**: 12억 이하 주택 → 취득세 본세 최대 **200만원** 감면 (소득 무관)
- ✅ **전용 85㎡ 이하** 선택 시 농어촌특별세 (취득세×20%) 절감
- ✅ **정책대출 활용** 시 국민주택채권 의무매입 면제 또는 할인 가능
- ℹ️ 인지세는 매도인·매수인 각 50% 부담이 관행
""")
                if discount4 > 0:
                    st.markdown(
                        alert(f"✅ 생애최초 감면 {discount4//10_000:,}만원 적용 중 — "
                              f"실 납부 취득세 {(tax4['base']-discount4)//10_000:,}만원", "ok"),
                        unsafe_allow_html=True,
                    )

    # ── 푸터 후 조기 종료 ───────────────────────────────────
    st.markdown("""
<div style="margin-top:2rem;padding-top:1rem;border-top:1px solid #E5E8EB;
     display:flex;justify-content:space-between;align-items:center;">
  <span style="font-size:0.75rem;color:#9CA3AF;">
    ⚠️ 본 계산기는 참고용입니다. 실제 대출 한도·세금은 금융기관·세무사 확인 필수.<br>
    규제 기준: 2025.10.15 주택시장 안정화 + 스트레스 DSR 3단계 (2025.12.31 공시)
  </span>
  <span style="font-size:0.75rem;color:#D1D5DB;">오늘: """ + date.today().strftime("%Y.%m.%d") + """</span>
</div>
""", unsafe_allow_html=True)
    st.stop()


# ════════════════════════════════════════════════════════════
# 갈아타기 계산기 (기존)
# ════════════════════════════════════════════════════════════

st.markdown("""
<div style="margin-bottom:0.8rem;">
  <span style="font-size:0.85rem;color:#9CA3AF;">
    대출 시뮬레이터 · 갈아타기 손익 · 이사 일정 역산 &nbsp;|&nbsp;
    2025.10 주택시장 안정화 + 스트레스 DSR 3단계 기준
  </span>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["  💰 대출 시뮬레이터  ", "  🔄 갈아타기 손익  ", "  📅 이사 일정 역산  "])


# ═══════════════════════════════════════════════════════════
# TAB 1 — 대출 시뮬레이터
# ═══════════════════════════════════════════════════════════

with tab1:
    col_L, col_R = st.columns([1, 1.15], gap="large")

    # ── 입력 ───────────────────────────────────────────────
    with col_L:

        # 현재 집
        st.markdown('<div class="input-section"><div class="section-label">현재 집</div>', unsafe_allow_html=True)
        _init("cur_price", 70_000);  _init("cur_loan", 20_000)
        c1, c2 = st.columns(2)
        with c1:
            cur_price = st.number_input("예상 매도가 (만원)", key="cur_price", min_value=0, step=500)
            price_buttons("cur_price")
        with c2:
            cur_loan = st.number_input("잔여 대출 (만원)", key="cur_loan", min_value=0, step=500)
            price_buttons("cur_loan",
                          presets=(5_000, 1_000, -1_000, -5_000),
                          labels=("+5천", "+1천", "–1천", "–5천"))
        st.markdown('</div>', unsafe_allow_html=True)

        # 목표 집
        st.markdown('<div class="input-section"><div class="section-label">목표 집</div>', unsafe_allow_html=True)
        _init("tgt_price", 100_000);  _init("own_cash", 5_000)
        t1, t2 = st.columns(2)
        with t1:
            tgt_price = st.number_input("매수 희망가 (만원)", key="tgt_price", min_value=1_000, step=500)
            price_buttons("tgt_price")
        with t2:
            own_cash = st.number_input("추가 보유 현금 (만원)", key="own_cash", min_value=0, step=500)
            price_buttons("own_cash",
                          presets=(5_000, 1_000, -1_000, -5_000),
                          labels=("+5천", "+1천", "–1천", "–5천"))
        st.markdown('</div>', unsafe_allow_html=True)

        # 대출 조건
        st.markdown('<div class="input-section"><div class="section-label">대출 조건</div>', unsafe_allow_html=True)
        lc1, lc2 = st.columns(2)
        region    = lc1.selectbox("지역",
            [REGION_REGULATED, REGION_METRO, REGION_LOCAL], index=1,
            help="규제지역: 서울 전역 + 경기 12곳(강남·서초·송파·용산 투기과열 포함)")
        ownership = lc2.selectbox("주택 보유",
            [OWN_NONE, OWN_ONE_COND, OWN_ONE, OWN_TWO_PLUS], index=1,
            help="처분조건부: 매수 후 6개월 내 기존 집 처분 조건부 대출")

        lc3, lc4 = st.columns(2)
        loan_type = lc3.selectbox("금리 유형", [LOAN_VARIABLE, LOAN_MIXED, LOAN_FIXED],
            help="변동형: 스트레스 금리 100% | 혼합형: 60% | 고정형: 0%")
        is_first  = lc4.checkbox("생애최초", help="규제지역도 LTV 70% 특례 적용")

        lc5, lc6 = st.columns([2, 1])
        loan_rate_pct = lc5.slider("대출 금리 (%)", 1.0, 10.0, 3.7, 0.05, format="%.2f%%")
        loan_years    = lc6.number_input("기간 (년)", value=30, min_value=1, max_value=50, step=5)
        st.markdown('</div>', unsafe_allow_html=True)

        # 고급 설정
        with st.expander("⚙️ 고급 설정 (DSR · 비용 · 신용대출)"):
            ex1, ex2 = st.columns(2)
            annual_income = ex1.number_input("연소득 (만원, DSR용)", value=8_000, step=500, min_value=0,
                                             help="세전 연소득 기준")
            moving_cost   = ex2.number_input("이사비 (만원)", value=300, step=50, min_value=0)
            is_large = st.checkbox("전용 85㎡ 초과 (농어촌특별세 추가)")

            st.divider()
            n_loans = int(st.number_input("기존 신용대출 건수 (DSR 합산)", value=0, min_value=0, max_value=5))
            ex_loans = []
            for i in range(n_loans):
                st.markdown(f"**신용대출 {i+1}**")
                sl1, sl2, sl3 = st.columns(3)
                bal  = sl1.number_input("잔여원금 (만원)", key=f"lb{i}", value=3_000, min_value=0, step=100)
                lr   = sl2.number_input("연금리 (%)", key=f"lr{i}", value=4.5, min_value=0.1, max_value=20.0, format="%.2f")
                lyr  = sl3.number_input("잔여만기 (년)", key=f"ly{i}", value=3, min_value=1, max_value=30)
                inst = st.checkbox("분할상환", key=f"li{i}")
                ex_loans.append({"bal": bal, "rate": lr/100, "yrs": lyr, "is_inst": inst})

    # ── 계산 ─────────────────────────────────────────────
    R = run_sim({
        "cur": cur_price, "cur_loan": cur_loan,
        "tgt": tgt_price, "cash": own_cash,
        "loan_rate": loan_rate_pct / 100, "loan_years": loan_years,
        "region": region, "ownership": ownership, "loan_type": loan_type,
        "is_first": is_first, "is_large": is_large,
        "income": annual_income, "moving": moving_cost, "ex_loans": ex_loans,
    })
    st.session_state["R"] = R
    st.session_state["P"] = {
        "cur_price": cur_price, "cur_loan": cur_loan, "tgt_price": tgt_price,
        "loan_rate": loan_rate_pct/100, "loan_years": loan_years, "moving": moving_cost,
    }

    # ── 결과 ─────────────────────────────────────────────
    with col_R:

        # 경고
        for kind, msg in R["warnings"]:
            st.markdown(alert(msg, kind), unsafe_allow_html=True)

        # ── 핵심 KPI 3개 — 단일 flex 블록 (컬럼 gap 영향 없이 정확히 1/3 분할) ──
        ltv_cls    = "success" if R["ltv_pct"] <= R["ltv_limit_pct"] * 0.9 else "warning"
        ltv_border = "#00C73C" if ltv_cls == "success" else "#FF6B00"
        st.markdown(f"""
        <div style="display:flex;gap:0.75rem;margin-bottom:0.9rem;">

          <div class="kpi-card primary" style="flex:1;min-width:0;">
            <div class="kpi-label">대출 가능 금액</div>
            <div class="kpi-num">{억만원(R["act_loan"])}</div>
            <div class="kpi-sub">필요 {억만원(R["need_loan"])}</div>
          </div>

          <div class="kpi-card neutral" style="flex:1;min-width:0;">
            <div class="kpi-label">월 상환액</div>
            <div class="kpi-num">{억만_원(R["monthly"])}</div>
            <div class="kpi-sub">스트레스 {억만_원(R["monthly_str"])}</div>
          </div>

          <div class="kpi-card {ltv_cls}" style="flex:1;min-width:0;">
            <div class="kpi-label">LTV</div>
            <div class="kpi-num">{R["ltv_pct"]}%</div>
            <div class="kpi-sub">한도 {int(R["ltv_limit_pct"])}%</div>
          </div>

        </div>
        """, unsafe_allow_html=True)

        # ── 자금 흐름 ─────────────────────────────────────
        section("자금 흐름")
        flow_gap  = tgt_price - R["total_avail"]
        gap_color = "#F03C2E" if flow_gap > 0 else "#00C73C"
        gap_bg    = "#FFF1F0" if flow_gap > 0 else "#F0FDF4"
        gap_word  = "부족" if flow_gap > 0 else "여유"
        gap_amt   = 억만원(flow_gap if flow_gap > 0 else -flow_gap)

        st.markdown(f"""
        <div style="display:flex;gap:0.5rem;align-items:stretch;flex-wrap:wrap;">
          <div class="flow-item" style="flex:1;min-width:0;">
            <div class="flow-label">매도 순수령</div>
            <div class="flow-value">{억만원(R["net_sell"])}</div>
          </div>
          <div style="display:flex;align-items:center;color:#9CA3AF;font-size:1.1rem;font-weight:700;flex-shrink:0;padding:0 0.2rem;" class="flow-op">＋</div>
          <div class="flow-item" style="flex:1;min-width:0;">
            <div class="flow-label">추가 현금</div>
            <div class="flow-value">{억만원(own_cash)}</div>
          </div>
          <div style="display:flex;align-items:center;color:#9CA3AF;font-size:1.1rem;font-weight:700;flex-shrink:0;padding:0 0.2rem;" class="flow-op">＝</div>
          <div class="flow-item" style="flex:1;min-width:0;">
            <div class="flow-label">총 가용 자금</div>
            <div class="flow-value">{억만원(R["total_avail"])}</div>
          </div>
          <div class="flow-op" style="display:flex;align-items:center;color:{gap_color};font-size:1.1rem;font-weight:700;flex-shrink:0;padding:0 0.2rem;">→</div>
          <div class="flow-item" style="flex:1;min-width:0;background:{gap_bg};border-color:{gap_color}50;">
            <div class="flow-label" style="white-space:nowrap;">목표가 대비</div>
            <div class="flow-value" style="color:{gap_color};">{gap_word} {gap_amt}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 비용 내역 ─────────────────────────────────────
        section("갈아타기 비용 구성")
        tax = R["tax"]
        cost_items = {
            "취득세": tax["base"] / 10_000,
            "지방교육세": tax["edu"] / 10_000,
            "중개수수료 (매도)": R["sell_fee"] / 10_000,
            "중개수수료 (매수)": R["buy_fee"] / 10_000,
            "이사비": moving_cost,
        }
        if tax["agr"]:
            cost_items["농어촌특별세"] = tax["agr"] / 10_000

        bc_l, bc_r = st.columns([1.2, 1])
        with bc_l:
            PIE_COLORS = ["#1B64DA","#60A5FA","#34D399","#A78BFA","#FB923C","#F472B6"]
            fig_donut = go.Figure(go.Pie(
                labels=list(cost_items.keys()),
                values=list(cost_items.values()),
                hole=0.62,
                # 차트 위에 라벨 없이 퍼센트만 — 잘림 방지
                textinfo="percent",
                textposition="inside",
                textfont=dict(size=10, color="white"),
                insidetextorientation="auto",
                marker=dict(colors=PIE_COLORS),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f}만원 (%{percent})<extra></extra>",
            ))
            fig_donut.update_layout(
                showlegend=False,
                height=220,
                margin=dict(l=10, r=10, t=10, b=10),
                annotations=[dict(
                    text=f"<b>{억만원(R['total_cost']//10_000)}</b>",
                    x=0.5, y=0.5, font_size=11, showarrow=False,
                )],
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        with bc_r:
            for nm, val in cost_items.items():
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;padding:0.25rem 0;'
                    f'border-bottom:1px solid #F3F4F6;font-size:0.82rem;">'
                    f'<span style="color:#6B7684;">{nm}</span>'
                    f'<span style="font-weight:600;">{val:,.0f}만</span></div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:0.4rem 0;'
                f'font-size:0.9rem;font-weight:700;margin-top:0.2rem;">'
                f'<span>합계</span><span style="color:#1B64DA;">{억만원(R["total_cost"]//10_000)}</span></div>',
                unsafe_allow_html=True,
            )

        # ── DSR ──────────────────────────────────────────
        if R["dsr"] is not None:
            section("DSR 분석")
            ok = R["dsr_ok"]
            bar_color = "#00C73C" if ok else "#F03C2E"
            bar_pct   = min(100, R["stress_dsr"])
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;font-size:0.82rem;color:#6B7684;margin-bottom:4px;">'
                f'<span>스트레스 DSR: <b style="color:#191F28;">{R["stress_dsr"]}%</b> '
                f'(+{R["stress_add_pct"]}%p 가산)</span>'
                f'<span>은행 한도 40%</span></div>'
                f'<div class="dsr-bar-wrap">'
                f'<div class="dsr-bar-fill" style="width:{bar_pct}%;background:{bar_color};"></div>'
                f'</div>'
                f'<div style="font-size:0.78rem;color:{bar_color};font-weight:600;margin-top:4px;">'
                f'{"✅ 한도 통과" if ok else "❌ 한도 초과"} &nbsp;|&nbsp; '
                f'실제 DSR {R["dsr"]}%</div>',
                unsafe_allow_html=True,
            )

        # ── 원리금 구성 차트 (상환 스케줄 요약) ──────────
        section("연간 상환 구성 (원리금 vs 이자)")
        amort = R["amort"]
        if amort:
            fig_am = go.Figure()
            fig_am.add_trace(go.Bar(
                x=[a["year"] for a in amort],
                y=[a["principal"] for a in amort],
                name="원금", marker_color="#1B64DA",
            ))
            fig_am.add_trace(go.Bar(
                x=[a["year"] for a in amort],
                y=[a["interest"] for a in amort],
                name="이자", marker_color="#BFDBFE",
            ))
            fig_am.update_layout(
                barmode="stack", height=200,
                xaxis_title="경과 년", yaxis_title="만원",
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(size=10),
            )
            st.plotly_chart(fig_am, use_container_width=True)

        # ── 금리 상승 시나리오 ────────────────────────────
        with st.expander("📈 금리 상승 시나리오"):
            sc_rows = [
                {"금리 변동": k, "적용 금리": f'{v["rate"]}%',
                 "월 상환액": 억만_원(v["pmt"]),
                 "증가액": f'+{억만_원(v["diff"])}'}
                for k, v in R["rate_scen"].items()
            ]
            st.dataframe(pd.DataFrame(sc_rows), use_container_width=True, hide_index=True)
            st.caption(f"현재 금리 {loan_rate_pct:.2f}% 기준 0.5~2.0%p 상승 시 월 상환액 변화")


# ═══════════════════════════════════════════════════════════
# TAB 2 — 갈아타기 손익
# ═══════════════════════════════════════════════════════════

with tab2:
    t2L, t2R = st.columns([1, 1.15], gap="large")

    with t2L:
        R2 = st.session_state.get("R")
        P2 = st.session_state.get("P", {})

        if R2:
            st.markdown(
                alert(f'💡 대출 시뮬레이터 연동 — 총 비용 <b>{억만_원(R2["total_cost"])}</b> · '
                      f'신규 대출 <b>{억만원(R2["act_loan"])}</b>', "info"),
                unsafe_allow_html=True,
            )
            base_cost = R2["total_cost"]
            new_loan  = R2["act_loan"]
            l_rate    = P2.get("loan_rate", 0.037)
        else:
            st.info("대출 시뮬레이터 탭에서 먼저 기본 정보를 입력해주세요.")
            base_cost = st.number_input("갈아타기 총 비용 (원)", value=15_000_000, step=1_000_000)
            new_loan  = st.number_input("신규 대출 (만원)", value=30_000, step=1_000)
            l_rate    = st.number_input("대출 금리 (%)", value=3.7, format="%.2f") / 100

        st.markdown('<div class="input-section"><div class="section-label">기대 수익</div>', unsafe_allow_html=True)
        _init("monthly_gain", 100)
        monthly_gain = st.number_input(
            "목표 집 기대 월 상승액 (만원)", key="monthly_gain", min_value=0, step=10,
            help="목표 집이 매월 평균 얼마나 오를지 (예: 연 1,200만 → 월 100만)",
        )
        price_buttons("monthly_gain",
                      presets=(100, 50, -50, -100),
                      labels=("+100", "+50", "–50", "–100"))
        opp_rate = st.slider("기회비용 금리 (%)", 0.5, 8.0, 2.5, 0.25, format="%.2f%%",
                             help="갈아타기 비용을 다른 곳에 투자했을 때의 기대 수익률")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="input-section"><div class="section-label">추가 비용</div>', unsafe_allow_html=True)
        extra = st.number_input("추가 비용 (만원, 인테리어 등)", value=0, step=100, min_value=0)
        total_cost2 = base_cost + extra * 10_000
        if extra > 0:
            st.caption(f"조정 후 총 비용: {억만_원(total_cost2)}")
        st.markdown('</div>', unsafe_allow_html=True)

    with t2R:
        BE = calc_breakeven(total_cost2, monthly_gain, new_loan, l_rate, opp_rate / 100)

        # ── 월 손익 구조 ─────────────────────────────────
        section("월별 손익 구조")
        mh1, mh2, mh3 = st.columns(3)
        interest_m = BE.get("interest", 0) or 0
        opp_m      = BE.get("opp", 0) or 0
        net_m      = BE.get("net", 0) or 0

        mh1.markdown(kpi_md("기대 월 상승",   f"{monthly_gain:,}만원", cls="primary"), unsafe_allow_html=True)
        mh2.markdown(kpi_md("월 이자 부담",    f"―{interest_m:,}만원", cls="neutral"), unsafe_allow_html=True)
        mh3.markdown(kpi_md("월 기회비용",     f"―{opp_m:,}만원",      cls="neutral"), unsafe_allow_html=True)

        net_cls = "success" if net_m > 0 else "danger"
        st.markdown(
            f'<div class="kpi-card {net_cls}" style="text-align:center;">'
            f'<div class="kpi-label">실질 월 이득 (이자·기회비용 차감 후)</div>'
            f'<div class="kpi-value" style="font-size:2rem;">{net_m:+,}만원 / 월</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── 손익분기 ─────────────────────────────────────
        if BE["months"] is not None:
            bm = BE["months"]
            by, bmo = int(bm // 12), int(bm % 12)
            st.markdown(
                f'<div class="be-box">'
                f'<div class="be-label">손익분기 기간 (기회비용·이자 차감 후)</div>'
                f'<div class="be-value">{by}년 {bmo}개월</div>'
                f'<div class="be-sub">{bm}개월 · {BE["note"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # 누적 손익 차트
            n_max = min(int(bm) + 37, 121)
            ms    = list(range(0, n_max))
            gain  = [monthly_gain * m for m in ms]
            cost  = [total_cost2 / 10_000 + (interest_m + opp_m) * m for m in ms]

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=ms, y=gain, name="누적 기대 상승",
                line=dict(color="#1B64DA", width=2.5),
                fill="tozeroy", fillcolor="rgba(27,100,218,0.07)",
            ))
            fig2.add_trace(go.Scatter(
                x=ms, y=cost, name="누적 비용",
                line=dict(color="#F03C2E", width=2, dash="dot"),
                fill="tozeroy", fillcolor="rgba(240,60,46,0.04)",
            ))
            fig2.add_vline(
                x=bm, line_dash="dash", line_color="#FF6B00",
                annotation_text=f"{bm:.0f}개월",
                annotation_font_color="#FF6B00",
            )
            fig2.update_layout(
                title="누적 손익 추이 (만원)",
                xaxis_title="경과 개월",
                yaxis_title="만원",
                height=280,
                margin=dict(l=0, r=0, t=36, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                plot_bgcolor="white", paper_bgcolor="white",
                hovermode="x unified", font=dict(size=11),
            )
            st.plotly_chart(fig2, use_container_width=True)

        else:
            st.markdown(
                f'<div class="be-box-fail">'
                f'<div class="be-label">손익분기 계산 결과</div>'
                f'<div class="be-value" style="font-size:1.4rem;">손익분기 불가</div>'
                f'<div class="be-sub">{BE.get("note","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if monthly_gain > 0:
                st.markdown(
                    alert(f"기대 상승({monthly_gain:,}만원)이 월 이자({interest_m:,}만원)"
                          f" + 기회비용({opp_m:,}만원)보다 작습니다. "
                          f"기대 상승액을 높이거나 대출·비용을 줄여보세요.", "warn"),
                    unsafe_allow_html=True,
                )

        # ── 결과 복사 ─────────────────────────────────────
        with st.expander("📋 결과 텍스트 복사"):
            bm_str = (f"{int(BE['months']//12)}년 {int(BE['months']%12)}개월 ({BE['months']}개월)"
                      if BE.get("months") else "손익분기 불가")
            summary = (
                f"[갈아타기 손익 계산]\n"
                f"총 비용: {억만_원(total_cost2)}\n"
                f"신규 대출: {억만원(new_loan)} @ {l_rate*100:.2f}%\n\n"
                f"기대 월 상승: {monthly_gain:,}만원\n"
                f"월 이자: {interest_m:,}만원 / 기회비용({opp_rate:.2f}%): {opp_m:,}만원\n"
                f"실질 월 이득: {net_m:+,}만원\n\n"
                f"손익분기: {bm_str}\n"
                f"---\n※ 참고용 계산입니다. 실제 세금·대출은 전문가 확인 필수."
            )
            st.code(summary, language=None)


# ═══════════════════════════════════════════════════════════
# TAB 3 — 이사 일정 역산
# ═══════════════════════════════════════════════════════════

with tab3:
    t3L, t3R = st.columns([1, 1.15], gap="large")

    with t3L:
        st.markdown('<div class="input-section"><div class="section-label">목표 입주 시기</div>', unsafe_allow_html=True)
        sc1, sc2 = st.columns(2)
        tgt_yr = int(sc1.number_input("년도", value=date.today().year + 1,
                                       min_value=date.today().year, max_value=date.today().year + 5))
        tgt_mo = int(sc2.selectbox("월", list(range(1, 13)), index=5, format_func=lambda x: f"{x}월"))
        st.markdown('</div>', unsafe_allow_html=True)

        P3 = st.session_state.get("P", {})
        st.markdown('<div class="input-section"><div class="section-label">기회비용 분석 (선택)</div>', unsafe_allow_html=True)
        cp3 = st.number_input("현재 집 가격 (만원)",
                               value=int(P3.get("cur_price", 70_000)), step=1_000, min_value=0,
                               help="기회비용 계산 기준 (연 2.5% 적용)")
        eg3 = st.number_input("목표 집 기대 월 상승액 (만원)", value=100, step=10, min_value=0,
                               help="지금 당장 갈아타지 않는 동안 매월 손해보는 기회비용")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            '<div style="font-size:0.78rem;color:#9CA3AF;line-height:1.7;">'
            '⏱ <b>통상 갈아타기 프로세스</b><br>'
            '매도 계약 → 잔금 (2개월) →<br>'
            '매수 계약 → 잔금 (2개월) → 입주<br>'
            '매도 잔금~매수 계약 간 2주 여유 포함'
            '</div>',
            unsafe_allow_html=True,
        )

    with t3R:
        S = calc_schedule(tgt_yr, tgt_mo, cp3, eg3)
        msg, kind = S["status"]

        # ── 상태 배너 ─────────────────────────────────────
        color_map = {
            "ok":     ("#15803D", "#F0FDF4", "#86EFAC"),
            "warn":   ("#92400E", "#FFFBEB", "#FDE68A"),
            "danger": ("#991B1B", "#FEF2F2", "#FECACA"),
            "urgent": ("#92400E", "#FFFBEB", "#FDE68A"),
        }
        tc, bg, bd = color_map.get(kind, ("#374151", "#F9FAFB", "#E5E7EB"))
        st.markdown(
            f'<div style="background:{bg};border:1px solid {bd};border-left:5px solid {tc};'
            f'padding:0.9rem 1.2rem;border-radius:12px;margin-bottom:1rem;">'
            f'<span style="font-size:1.05rem;font-weight:700;color:{tc};">{msg}</span>'
            f'&nbsp; <span style="color:#6B7684;font-size:0.9rem;">— 목표까지 <b>{S["left"]}개월</b> 남음</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── 타임라인 스텝 카드 ────────────────────────────
        section("역산 타임라인")
        today_str = date.today().strftime("%Y-%m")

        for icon, lbl, ym, desc in S["steps"]:
            if ym < today_str:
                card_cls = "done";  dot_cls = "dot-done"
            elif ym == today_str:
                card_cls = "active"; dot_cls = "dot-active"
            elif S["late"] and ym == S["steps"][0][2]:
                card_cls = "urgent"; dot_cls = "dot-urgent"
            else:
                card_cls = "";       dot_cls = "dot-future"

            badge = ""
            if ym < today_str:   badge = '<span class="badge badge-gray">완료/경과</span>'
            elif ym == today_str: badge = '<span class="badge badge-blue">📍 이번 달!</span>'

            st.markdown(
                f'<div class="step-card {card_cls}">'
                f'<div class="step-dot {dot_cls}">{icon}</div>'
                f'<div style="flex:1;">'
                f'<div class="step-content-label">{lbl} {badge}</div>'
                f'<div class="step-content-ym">{ym}</div>'
                f'<div class="step-content-desc">{desc}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        # ── 기회비용 ─────────────────────────────────────
        section("기회비용 분석")
        oc1, oc2 = st.columns(2)
        oc1.markdown(
            kpi_md("월 기회비용 (보유 시)",
                   f"{S['opp']:,}만원",
                   sub="현재 집 × 연 2.5% ÷ 12",
                   cls="neutral"),
            unsafe_allow_html=True,
        )
        net_cls3 = "success" if S["net"] > 0 else "warning"
        oc2.markdown(
            kpi_md("기회비용 차감 실질 월 이득",
                   f"{S['net']:+,}만원",
                   cls=net_cls3),
            unsafe_allow_html=True,
        )

        # ── 타임라인 시각화 (plotly) ──────────────────────
        section("타임라인 시각화")
        STEP_COLORS = {
            "done": "#D1D5DB", "active": "#1B64DA",
            "urgent": "#F03C2E", "future": "#60A5FA",
        }
        xs, ys, cs, ts = [], [], [], []
        for icon, lbl, ym, _ in S["steps"]:
            yr2, mo2 = map(int, ym.split("-"))
            xs.append(date(yr2, mo2, 1))
            ys.append(0)
            if ym < today_str:   cs.append(STEP_COLORS["done"])
            elif ym == today_str: cs.append(STEP_COLORS["active"])
            elif S["late"] and ym == S["steps"][0][2]: cs.append(STEP_COLORS["urgent"])
            else:                 cs.append(STEP_COLORS["future"])
            ts.append(f"{lbl}<br>{ym}")

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=xs, y=ys, mode="lines",
                                  line=dict(color="#E5E7EB", width=4),
                                  showlegend=False, hoverinfo="skip"))
        fig3.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers+text",
            marker=dict(size=22, color=cs, line=dict(color="white", width=2.5)),
            text=ts, textposition="top center",
            textfont=dict(size=10),
            showlegend=False,
            hovertemplate="%{text}<extra></extra>",
        ))
        fig3.add_shape(type="line", x0=date.today().isoformat(), x1=date.today().isoformat(),
                       y0=-0.8, y1=1.5, line=dict(dash="dash", color="#9CA3AF", width=1.5))
        fig3.update_layout(
            height=185,
            yaxis=dict(visible=False, range=[-0.8, 1.5]),
            xaxis=dict(showgrid=False, zeroline=False),
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════════
# 푸터
# ═══════════════════════════════════════════════════════════

st.markdown("""
<div style="margin-top:2rem;padding-top:1rem;border-top:1px solid #E5E8EB;
     display:flex;justify-content:space-between;align-items:center;">
  <span style="font-size:0.75rem;color:#9CA3AF;">
    ⚠️ 본 계산기는 참고용입니다. 실제 대출 한도·세금은 금융기관·세무사 확인 필수.<br>
    규제 기준: 2025.10.15 주택시장 안정화 + 스트레스 DSR 3단계 (2025.12.31 공시)
  </span>
  <span style="font-size:0.75rem;color:#D1D5DB;">오늘: """ + date.today().strftime("%Y.%m.%d") + """</span>
</div>
""", unsafe_allow_html=True)
