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

/* KPI 카드 행 컨테이너 */
.kpi-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 0.9rem;
    align-content: flex-start;
}
.kpi-row .kpi-card {
    flex: 1 1 0;
    min-width: 0;
    margin-bottom: 0;
}

.kpi-label { font-size: 0.76rem; font-weight: 500; color: #6B7684; margin-bottom: 0.3rem; }

/* KPI 큰 숫자 */
.kpi-num {
    font-size: 1.35rem;
    font-weight: 800;
    color: #191F28;
    line-height: 1.25;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
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
    flex: 1 1 0;
    min-width: 0;
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

/* ══════════════════════════════════════════
   반응형: 태블릿+모바일 (960px 이하)
   ══════════════════════════════════════════ */
@media (max-width: 960px) {

    /* ─── 1순위: 탭 bar 가로 스크롤 ─── */
    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none !important;
        border-radius: 10px !important;
        padding: 4px !important;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none !important; }
    .stTabs [data-baseweb="tab"] {
        white-space: nowrap !important;
        flex-shrink: 0 !important;
        font-size: 0.75rem !important;
        padding: 0.35rem 0.7rem !important;
    }

    /* ─── 2순위: Plotly 차트 높이 제한 ─── */
    [data-testid="stPlotlyChart"] > div { max-height: 260px !important; }
    [data-testid="stPlotlyChart"] iframe { max-height: 260px !important; }

    /* ─── 3순위: 슬라이더 + 기간 레이아웃 ─── */
    [data-testid="stSlider"] { width: 100% !important; }
    [data-testid="stSlider"] > div { padding: 0 0.25rem !important; }

    /* ─── st.columns → 세로 스택 ─── */
    [data-testid="stHorizontalBlock"] {
        display: block !important;
    }
    [data-testid="stHorizontalBlock"] > div {
        display: block !important;
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        flex: none !important;
        margin-bottom: 0.5rem !important;
    }

    /* ─── 퀵버튼: Python에서 2×2 그리드로 렌더링하므로 CSS 불필요
         각 버튼 행(st.columns(2))은 세로 스택되어 2행이 되고
         각 행 안의 2개 버튼은 가로 배치됨 ─── */
    button[data-testid="stBaseButton-secondary"] {
        width: 100% !important;
        padding: 0 4px !important;
        font-size: 0.75rem !important;
    }

    /* ─── 기타 위젯 ─── */
    [data-testid="stNumberInput"] { width: 100% !important; min-width: 0 !important; }
    [data-testid="stNumberInput"] > div { width: 100% !important; min-width: 0 !important; }
    [data-testid="stNumberInput"] input { min-width: 0 !important; width: 100% !important; }

    /* ─── KPI 폰트 축소 ─── */
    .kpi-num      { font-size: 0.92rem !important; }
    .kpi-value    { font-size: 0.92rem !important; }
    .kpi-value-md { font-size: 0.82rem !important; }
    .kpi-label    { font-size: 0.7rem !important; }
    .kpi-sub      { font-size: 0.68rem !important; word-break: keep-all; }

    /* ─── 정책대출 카드: 세로 1열 ─── */
    .loan-cards-row {
        flex-direction: column !important;
        gap: 0.6rem !important;
    }
    .loan-cards-row .kpi-card {
        flex: none !important;
        width: 100% !important;
        min-width: 0 !important;
    }

    /* ─── 자금 흐름 2×2 ─── */
    .flow-op { display: none !important; }
    .flow-item {
        flex: 0 0 calc(50% - 0.4rem) !important;
        text-align: left !important;
        padding: 0.5rem 0.7rem !important;
    }
    .flow-label { white-space: normal !important; }

    /* ─── 가로 스크롤 방지 ─── */
    .main .block-container {
        overflow-x: hidden !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* ─── KPI 카드 행: 2열 래핑 ─── */
    .kpi-row .kpi-card {
        flex: 0 0 calc(50% - 0.375rem) !important;
        max-width: calc(50% - 0.375rem) !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    /* ─── DSR 바 텍스트 줄바꿈 ─── */
    .dsr-bar-wrap { margin-top: 2px !important; }
}

/* ══════════════════════════════════════════
   소폰 (480px 이하) — KPI 카드 1열
   ══════════════════════════════════════════ */
@media (max-width: 480px) {
    .kpi-row .kpi-card {
        flex: 0 0 100% !important;
        max-width: 100% !important;
    }
    .block-container {
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.68rem !important;
        padding: 0.3rem 0.5rem !important;
    }
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

def calc_acquisition_tax(price, is_large, ownership=None, region=None):
    """주택 취득세 계산.
    ownership / region 전달 시 다주택 중과세율 자동 적용 (2020.08 대책 기준).
      · 1주택(처분조건부) 또는 무주택 → 일반세율
      · 기존 1주택 + 규제지역 취득    → 2주택 8%
      · 기존 2주택+ (규제/수도권)     → 3주택+ 12%
      · 기존 2주택+ (지방)            → 3주택+ 8%
    """
    pa = price / 10_000
    # ── 다주택 중과 판단 ──────────────────────────────────
    if ownership == OWN_ONE and region == REGION_REGULATED:
        rate = 0.08          # 규제지역 2번째 주택
        surcharge = True
    elif ownership == OWN_TWO_PLUS and region in (REGION_REGULATED, REGION_METRO):
        rate = 0.12          # 규제지역·수도권 3번째+ 주택
        surcharge = True
    elif ownership == OWN_TWO_PLUS and region == REGION_LOCAL:
        rate = 0.08          # 지방 3번째+ 주택
        surcharge = True
    else:
        # 일반세율 (무주택 / 처분조건부 / 비규제 2주택)
        if price <= 60_000:    rate = 0.01
        elif price <= 90_000:  rate = max(0.01, min(0.03, (pa * 2/3 - 3) / 100))
        else:                  rate = 0.03
        surcharge = False
    base = price * 10_000 * rate
    edu  = base * 0.1
    agr  = base * 0.2 if is_large else 0
    return {"base": round(base), "edu": round(edu), "agr": round(agr),
            "total": round(base + edu + agr), "rate_pct": round(rate * 100, 2),
            "surcharge": surcharge}

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
        if ownership == OWN_TWO_PLUS:
            _ltv0_reason = "2주택 이상 보유자는 규제지역·수도권에서 추가 주담대 원칙 금지"
            _ltv0_tip    = "기존 주택 1채를 처분 후 무주택·1주택 조건으로 신청하거나, 지방 비규제지역 주택 검토"
        elif ownership == OWN_ONE and region == REGION_REGULATED:
            _ltv0_reason = "규제지역 1주택자는 일반 주담대 불가"
            _ltv0_tip    = "'1주택(처분조건부)' 선택 시 매수 후 6개월 내 기존 주택 처분 약정으로 LTV 40% 적용 가능"
        else:
            _ltv0_reason = "선택한 지역·보유 조건에서 주담대 LTV 0%"
            _ltv0_tip    = "지역·보유 현황을 다시 확인하세요"
        warnings.append(("danger",
            f"⛔ 주택담보대출 불가 — {_ltv0_reason}.<br>"
            f"<span style='font-size:0.82rem;'>💡 {_ltv0_tip}</span>"))

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
    mortgage_dsr = credit_dsr = stress_mortgage_dsr = None
    if income > 0:
        inc_원             = income * 10_000
        mortgage_dsr       = round(monthly     * 12 / inc_원 * 100, 1)
        stress_mortgage_dsr= round(monthly_str * 12 / inc_원 * 100, 1)
        credit_dsr         = round(ex_annual        / inc_원 * 100, 1) if ex_annual else 0.0
        dsr                = round((monthly * 12 + ex_annual) / inc_원 * 100, 1)
        stress_dsr         = round((monthly_str * 12 + ex_annual) / inc_원 * 100, 1)
        dsr_ok             = stress_dsr <= DSR_BANK * 100
        if not dsr_ok:
            _credit_note = (f" + 신용대출 {credit_dsr}%p" if credit_dsr else "")
            warnings.append(("warn",
                f"⚠️ 스트레스 DSR {stress_dsr}% > 은행 한도 40% 초과 "
                f"(주담대 {stress_mortgage_dsr}%{_credit_note} | 가산 금리 +{round(stress_add*100,2)}%p 반영) "
                f"— 실제 DSR {dsr}%{'는 40% 이내이지만 스트레스 기준 적용' if dsr <= 40 else '도 초과'}"))


    tax   = calc_acquisition_tax(tgt, is_large, ownership=ownership, region=region)
    sf    = calc_brokerage(cur)
    bf    = calc_brokerage(tgt)
    total_cost = tax["total"] + sf + bf + moving * 10_000
    if tax.get("surcharge"):
        warnings.append(("warn",
            f"⚠️ 다주택 취득세 중과 {tax['rate_pct']}% 적용 — "
            f"취득세 {tax['base']//10_000:,}만원 (일반세율 대비 대폭 증가). "
            f"처분조건부 취득 또는 증여·상속 여부 세무사 확인 권장"))

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
        "mortgage_dsr": mortgage_dsr, "stress_mortgage_dsr": stress_mortgage_dsr,
        "credit_dsr": credit_dsr, "ex_annual_만": round(ex_annual / 10_000) if ex_annual else 0,
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
                   loan_rate, loan_years, loan_type, ex_loans=None):
    """보유 현금 + 소득 → 최대 구매 가능 금액 역산 (LTV / DSR 두 제약 중 낮은 값)
    취득비용(취득세+중개수수료)도 동일 현금에서 지출되므로 반복 수렴으로 역산.
    ex_loans: 기존 신용대출 목록 — DSR 여유분에서 차감.
    """
    if ex_loans is None:
        ex_loans = []
    ltv        = _get_ltv(region, ownership, is_first)
    stress_add = _stress_addon(region, loan_type)
    stress_rate = loan_rate + stress_add

    # 기존 신용대출 연간 DSR 기여분 (원 단위) — 스트레스 미가산
    ex_annual = sum(_credit_dsr(l["bal"], l["rate"], l["yrs"], l["is_inst"]) for l in ex_loans)

    def _solve(avail_cash):
        """주어진 가용 현금으로 LTV·DSR 역산 → (max_price, actual_loan, binding)"""
        # ① LTV 제약: price × (1 - ltv) ≤ avail_cash  →  price ≤ avail_cash / (1 - ltv)
        if ltv <= 0:
            p_ltv, l_ltv = avail_cash, 0
        elif ltv >= 1:
            p_ltv, l_ltv = 999_999, 999_999 - avail_cash
        else:
            p_ltv = int(avail_cash / (1 - ltv))
            l_ltv = p_ltv - avail_cash
            ceiling = _get_ceiling(p_ltv, region)
            if ceiling and l_ltv > ceiling:
                l_ltv = ceiling
                p_ltv = avail_cash + ceiling

        # ② DSR 제약 — 신용대출 DSR 차감 후 주담대 가용 한도 산출
        p_dsr, l_dsr = p_ltv, l_ltv
        if income > 0 and stress_rate > 0 and loan_years > 0:
            total_annual_budget  = income * 10_000 * DSR_BANK          # 연간 40% 한도 (원)
            mortgage_annual_budget = max(0, total_annual_budget - ex_annual)  # 신용대출 차감
            max_monthly = mortgage_annual_budget / 12
            if max_monthly <= 0:
                # 신용대출만으로 DSR 40% 초과 → 주담대 불가
                l_dsr, p_dsr = 0, avail_cash
            else:
                r = stress_rate / 12;  n = loan_years * 12
                factor  = r * (1 + r) ** n / ((1 + r) ** n - 1)
                l_dsr   = int(max_monthly / factor) // 10_000
                p_dsr   = avail_cash + l_dsr
                ceiling2 = _get_ceiling(p_dsr, region)
                if ceiling2 and l_dsr > ceiling2:
                    l_dsr = ceiling2
                    p_dsr = avail_cash + ceiling2

        # ③ 두 제약 중 타이트한 쪽
        if p_ltv <= p_dsr:
            return p_ltv, l_ltv, "LTV"
        else:
            return p_dsr, l_dsr, "DSR"

    # 취득비용이 가격에 비례하므로 3회 반복으로 수렴
    effective_cash = cash
    for _ in range(4):
        max_price, actual_loan, binding = _solve(effective_cash)
        if max_price <= 0:
            break
        _tax_tmp  = calc_acquisition_tax(max_price, False, ownership=ownership, region=region)
        tax_total = _tax_tmp["total"]
        # 생애최초 취득세 감면: 12억 이하 → 최대 200만원 차감
        if is_first and max_price <= 120_000 and not _tax_tmp.get("surcharge"):
            first_discount = min(2_000_000, _tax_tmp["base"])
            tax_total = max(0, tax_total - first_discount)
        acq_만 = (tax_total + calc_brokerage(max_price)) // 10_000
        effective_cash = max(1, cash - acq_만)

    actual_loan = max(0, actual_loan)
    max_price   = max(0, max_price)
    down_pmt    = max(0, max_price - actual_loan)

    monthly     = _monthly_pmt(actual_loan * 10_000, loan_rate, loan_years)
    monthly_str = _monthly_pmt(actual_loan * 10_000, stress_rate, loan_years)

    dsr = stress_dsr_val = None
    credit_dsr_pct = round(ex_annual / (income * 10_000) * 100, 1) if income > 0 and ex_annual else 0.0
    if income > 0 and monthly > 0:
        inc_원          = income * 10_000
        dsr             = round((monthly * 12 + ex_annual) / inc_원 * 100, 1)
        stress_dsr_val  = round((monthly_str * 12 + ex_annual) / inc_원 * 100, 1)

    tax       = calc_acquisition_tax(max_price, False, ownership=ownership, region=region)
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
        "credit_dsr"     : credit_dsr_pct,
        "ex_annual_만"   : round(ex_annual / 10_000) if ex_annual else 0,
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
# 양도소득세 계산 엔진
# ═══════════════════════════════════════════════════════════

_TRANSFER_BRACKETS = [
    (14_000_000,    0.06,          0),
    (50_000_000,    0.15,  1_260_000),
    (88_000_000,    0.24,  5_760_000),
    (150_000_000,   0.35, 15_440_000),
    (300_000_000,   0.38, 19_940_000),
    (500_000_000,   0.40, 25_940_000),
    (1_000_000_000, 0.42, 35_940_000),
    (float("inf"),  0.45, 65_940_000),
]

def _transfer_income_tax(base_만: float) -> float:
    """과세표준(만원) → 소득세(만원)"""
    base = base_만 * 10_000
    for limit, rate, deduction in _TRANSFER_BRACKETS:
        if base <= limit:
            return max(0.0, (base * rate - deduction) / 10_000)
    return max(0.0, (base * 0.45 - 65_940_000) / 10_000)

def calc_transfer_tax(
    acquire_price: float,   # 취득가액 (만원)
    transfer_price: float,  # 양도가액 (만원)
    acquire_cost: float,    # 취득 필요경비 (만원)
    other_cost: float,      # 기타 필요경비 (만원)
    acquire_date,           # datetime.date
    transfer_date,          # datetime.date
    ownership: str,         # "1주택" / "2주택 이상"
    reside_years: float,    # 실거주 기간 (년)
    is_regulated: bool,     # 취득 당시 조정대상지역 여부
) -> dict:
    from dateutil.relativedelta import relativedelta as _rd
    delta = _rd(transfer_date, acquire_date)
    holding_years = delta.years + delta.months / 12

    total_cost  = acquire_cost + other_cost
    gain        = transfer_price - acquire_price - total_cost

    base = {
        "holding_years": holding_years,
        "gain": gain,
        "total_cost": total_cost,
        "transfer_price": transfer_price,
        "acquire_price": acquire_price,
    }

    if gain <= 0:
        return {**base, "no_gain": True, "is_exempt": False,
                "taxable_gain": 0, "ltg_rate": 0, "ltg_deduction": 0,
                "income": 0, "tax_base": 0, "income_tax": 0,
                "local_tax": 0, "total_tax": 0, "effective_rate": 0,
                "exempt_reason": None, "high_price": False}

    is_one = (ownership == "1주택")
    holding_ok = holding_years >= 2
    reside_ok  = (reside_years >= 2) if (is_one and is_regulated) else True
    is_exempt  = is_one and holding_ok and reside_ok
    high_price = transfer_price > 120_000  # 12억 초과 고가주택

    # 과세 양도차익 (비과세 안분)
    if is_exempt and not high_price:
        taxable_gain  = 0.0
        exempt_reason = "1세대 1주택 비과세 (전액)"
    elif is_exempt and high_price:
        taxable_gain  = gain * (transfer_price - 120_000) / transfer_price
        exempt_reason = "1세대 1주택 고가주택 — 12억 초과분만 과세"
    else:
        taxable_gain  = gain
        exempt_reason = None

    if taxable_gain <= 0:
        return {**base, "no_gain": False, "is_exempt": True,
                "taxable_gain": 0, "ltg_rate": 0, "ltg_deduction": 0,
                "income": 0, "tax_base": 0, "income_tax": 0,
                "local_tax": 0, "total_tax": 0, "effective_rate": 0,
                "exempt_reason": exempt_reason, "high_price": high_price}

    # 장기보유특별공제
    if holding_years < 3:
        ltg_rate = 0.0
    elif is_one and reside_years >= 2:
        hold_r   = min(int(holding_years), 10) * 0.04
        reside_r = min(int(reside_years),  10) * 0.04
        ltg_rate = min(hold_r + reside_r, 0.80)
    else:
        ltg_rate = min(int(holding_years), 15) * 0.02

    ltg_deduction = taxable_gain * ltg_rate
    income        = taxable_gain - ltg_deduction
    basic_ded     = 250.0
    tax_base      = max(0.0, income - basic_ded)
    income_tax    = _transfer_income_tax(tax_base)
    local_tax     = income_tax * 0.1
    total_tax     = income_tax + local_tax

    return {**base, "no_gain": False, "is_exempt": is_exempt,
            "exempt_reason": exempt_reason, "high_price": high_price,
            "taxable_gain": taxable_gain,
            "ltg_rate": ltg_rate, "ltg_deduction": ltg_deduction,
            "income": income, "basic_ded": basic_ded,
            "tax_base": tax_base, "income_tax": income_tax,
            "local_tax": local_tax, "total_tax": total_tax,
            "effective_rate": total_tax / gain}


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
    """빠른 금액 조정 버튼 — 2열 그리드로 렌더링 (presets 수 무관)"""
    pairs  = list(zip(presets, labels))
    per_row = 2
    n_rows  = (len(pairs) + per_row - 1) // per_row
    rows    = [st.columns(per_row, gap="small") for _ in range(n_rows)]
    for i, (amt, lbl) in enumerate(pairs):
        rows[i // per_row][i % per_row].button(
            lbl,
            key=f"_pb_{key}_{i}",
            on_click=_make_delta_fn(key, amt),
            use_container_width=True,
        )


# ═══════════════════════════════════════════════════════════
# URL 공유 헬퍼
# ═══════════════════════════════════════════════════════════

_region_opts = [REGION_REGULATED, REGION_METRO, REGION_LOCAL]
_own_opts    = [OWN_NONE, OWN_ONE_COND, OWN_ONE, OWN_TWO_PLUS]
_type_opts   = [LOAN_VARIABLE, LOAN_MIXED, LOAN_FIXED]


def _load_query_params():
    """URL 쿼리 파라미터 → session_state 초기화 (첫 로드 시 1회만)"""
    if "_qp_loaded" in st.session_state:
        return
    st.session_state["_qp_loaded"] = True
    qp = st.query_params
    if not qp:
        return
    # 모드
    if "m" in qp:
        st.session_state["calc_mode"] = (
            "🏠 첫 집 마련 계산기" if qp["m"] == "f" else "🔄 갈아타기 계산기"
        )
    # 정수 키
    for k in ["cur_price", "cur_loan", "tgt_price", "own_cash",
              "f1_cash", "f1_income", "loan_years", "f1_loan_years"]:
        if k in qp:
            try: st.session_state[k] = int(qp[k])
            except: pass
    # 실수 키 (슬라이더)
    for k, lo, hi in [("loan_rate", 1.0, 10.0), ("f1_loan_rate", 1.0, 10.0)]:
        if k in qp:
            try: st.session_state[k] = max(lo, min(hi, float(qp[k])))
            except: pass
    # 불리언 키
    for k in ["is_first", "f1_is_first"]:
        if k in qp:
            st.session_state[k] = (qp[k] == "1")
    # 문자열 키 (selectbox)
    for k, valid in [("region", _region_opts), ("ownership", _own_opts), ("loan_type", _type_opts),
                     ("f1_region", _region_opts), ("f1_ownership", _own_opts), ("f1_loan_type", _type_opts)]:
        if k in qp and qp[k] in valid:
            st.session_state[k] = qp[k]

_load_query_params()

_RESET_KEYS = [
    "cur_price","cur_loan","tgt_price","own_cash",
    "region","ownership","loan_type","is_first","loan_rate","loan_years",
    "f1_cash","f1_income","f1_region","f1_ownership","f1_loan_type",
    "f1_is_first","f1_loan_rate","f1_loan_years",
    "f2_income","f2_price","f2_years","f2_is_first2","f2_newlywed","f2_newborn",
    "f3_jeonse","f3_opp","f3_price","f3_loan3","f3_loan_rate","f3_appr","f3_hold",
    "f4_price","f4_loan4","f4_law_own","f4_law_mtg","f4_move4","f4_inter4",
    "monthly_gain","_qp_loaded",
]

def _reset_all():
    for k in _RESET_KEYS:
        st.session_state.pop(k, None)
    st.query_params.clear()

def _snapshot(R, cur_price, tgt_price, region, ownership, loan_type,
              is_first, loan_rate_pct, loan_years, label):
    """갈아타기 탭1 시나리오 스냅샷 딕셔너리"""
    return {
        "label":       label,
        "현재 집 매도가":  억만원(cur_price),
        "목표 매수가":    억만원(tgt_price),
        "대출 가능":     억만원(R["act_loan"]),
        "월 상환":      억만_원(R["monthly"]),
        "스트레스 월상환": 억만_원(R["monthly_str"]),
        "LTV":         f"{R['ltv_pct']}% (한도 {R['ltv_limit_pct']}%)",
        "스트레스 DSR":  f"{R['stress_dsr']}%" if R["stress_dsr"] else "—",
        "갈아타기 비용":  억만원(R["total_cost"] // 10_000),
        "조건":         f"{region} · {loan_rate_pct:.2f}% · {int(loan_years)}년 · {ownership}",
    }

def _make_ics(steps):
    """타임라인 스텝 → .ics 캘린더 파일 문자열"""
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0",
        "PRODID:-//부동산 계산기//KR", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
    ]
    for icon, lbl, ym, desc in steps:
        yr, mo = map(int, ym.split("-"))
        dt     = f"{yr}{mo:02d}01"
        dt_end = f"{yr}{mo:02d}02"
        lines += [
            "BEGIN:VEVENT",
            f"DTSTART;VALUE=DATE:{dt}",
            f"DTEND;VALUE=DATE:{dt_end}",
            f"SUMMARY:{lbl}",
            f"DESCRIPTION:{desc}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


# ═══════════════════════════════════════════════════════════
# 정책 기준 상수
# ═══════════════════════════════════════════════════════════

POLICY_BASE_DATE = "2025년 10월 기준"

POLICY_ITEMS = [
    ("LTV 한도",        "규제지역 50% · 비규제 70% · 생애최초 80%",             "2024.09"),
    ("DSR 규제",        "스트레스 DSR 3단계 — 은행권 가산금리 적용",             "2025.07"),
    ("대출 한도 상한",  "은행권 주담대 최대 5억 (수도권 · 규제지역)",             "2025.07"),
    ("취득세 일반",     "6억↓ 1%, 6~9억 1~3%, 9억↑ 3%",                       "2020.08"),
    ("취득세 중과",     "규제지역 2주택 8%, 3주택+ 12%, 지방 3주택 8%",          "2023.12"),
    ("생애최초 감면",   "12억 이하 취득세 본세 최대 200만원 감면",               "2023.01"),
    ("디딤돌 대출",     "소득 7천만원↓, 최대 5억, 금리 2.35~3.95%",             "2024.11"),
    ("보금자리론",      "소득 1억↓, 최대 6억, 금리 3.95~4.55%",                "2024.11"),
    ("특례보금자리",    "종료 (2024.01 이후 신규 접수 없음)",                    "2024.01"),
]

def _policy_expander():
    with st.expander(f"📋 적용 정책 기준 — {POLICY_BASE_DATE}  (클릭하여 상세 보기)", expanded=False):
        rows = "".join(
            f'<tr>'
            f'<td style="padding:0.28rem 0.6rem 0.28rem 0;font-weight:600;color:#374151;'
            f'white-space:nowrap;font-size:0.82rem;">{cat}</td>'
            f'<td style="padding:0.28rem 0.6rem;color:#374151;font-size:0.82rem;">{detail}</td>'
            f'<td style="padding:0.28rem 0 0.28rem 0.6rem;color:#9CA3AF;font-size:0.75rem;'
            f'white-space:nowrap;">{since}</td>'
            f'</tr>'
            for cat, detail, since in POLICY_ITEMS
        )
        st.markdown(
            f'<table style="width:100%;border-collapse:collapse;">'
            f'<thead><tr>'
            f'<th style="text-align:left;padding:0.2rem 0.6rem 0.4rem 0;font-size:0.75rem;'
            f'color:#9CA3AF;font-weight:500;">항목</th>'
            f'<th style="text-align:left;padding:0.2rem 0.6rem 0.4rem 0.6rem;font-size:0.75rem;'
            f'color:#9CA3AF;font-weight:500;">내용</th>'
            f'<th style="text-align:left;padding:0.2rem 0 0.4rem 0.6rem;font-size:0.75rem;'
            f'color:#9CA3AF;font-weight:500;">시행</th>'
            f'</tr></thead>'
            f'<tbody>{rows}</tbody></table>',
            unsafe_allow_html=True,
        )
        st.caption("⚠️ 정책 변경 시 수동 업데이트됩니다. 최신 정보는 국토교통부·금융위원회 공식 사이트에서 확인하세요.")


# ═══════════════════════════════════════════════════════════
# 헤더 + 모드 토글
# ═══════════════════════════════════════════════════════════

hdr_l, hdr_r = st.columns([5, 1])
hdr_l.markdown(
    '<div style="margin-bottom:0.7rem;">'
    '<span style="font-size:1.7rem;font-weight:900;color:#191F28;">🏠 부동산 계산기</span>'
    '</div>',
    unsafe_allow_html=True,
)
hdr_r.button(
    "↺ 초기화",
    key="_reset_btn",
    on_click=_reset_all,
    help="모든 입력값을 기본값으로 되돌립니다",
    use_container_width=True,
)

mode = st.radio(
    "계산기 모드",
    ["🔄 갈아타기 계산기", "🏠 첫 집 마련 계산기"],
    horizontal=True,
    label_visibility="collapsed",
    key="calc_mode",
)

_policy_expander()

# ── 페이지 타이틀 동적 변경 ──────────────────────────────────
_page_title = "첫 집 마련 계산기" if mode == "🏠 첫 집 마련 계산기" else "갈아타기 계산기"
st.markdown(
    f'<script>window.parent.document.title="{_page_title} | 부동산 계산기";</script>',
    unsafe_allow_html=True,
)

# ════════════════════════════════════════════════════════════
# 첫 집 마련 계산기
# ════════════════════════════════════════════════════════════
if mode == "🏠 첫 집 마련 계산기":

    ftab1, ftab2, ftab3, ftab4, ftab5 = st.tabs([
        "  💰 구매 가능 예산  ",
        "  🏦 정책대출 비교  ",
        "  ⚖️ 전세 vs 매매  ",
        "  📋 취득 비용 상세  ",
        "  💸 양도소득세  ",
    ])

    # ── Tab 1: 구매 가능 예산 역산 ──────────────────────────
    with ftab1:
        st.caption("📋 LTV 2024.09 · 스트레스 DSR 2025.07 · 대출 상한 5억 2025.07 · 생애최초 감면 2023.01")
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

            with st.expander("💳 기존 신용대출 (DSR 차감)"):
                st.caption("보유 중인 신용대출이 있으면 입력하세요 — 최대 구매 가능 금액 산정 시 DSR에서 차감됩니다.")
                _init("f1_n_loans", 0)
                f1_n_loans = int(st.number_input("신용대출 건수", key="f1_n_loans",
                                                  min_value=0, max_value=5))
                f1_ex_loans = []
                for i in range(f1_n_loans):
                    st.markdown(f"**신용대출 {i+1}**")
                    fa1, fa2, fa3 = st.columns(3)
                    _init(f"f1_lb{i}", 3_000); _init(f"f1_lr{i}", 4.5); _init(f"f1_ly{i}", 3)
                    f1_bal  = fa1.number_input("잔여원금 (만원)", key=f"f1_lb{i}", min_value=0, step=100)
                    f1_lr   = fa2.number_input("연금리 (%)", key=f"f1_lr{i}",
                                               min_value=0.1, max_value=20.0, format="%.2f")
                    f1_lyr  = fa3.number_input("잔여만기 (년)", key=f"f1_ly{i}",
                                               min_value=1, max_value=30)
                    f1_inst = st.checkbox("분할상환", key=f"f1_li{i}")
                    f1_ex_loans.append({"bal": f1_bal, "rate": f1_lr/100,
                                        "yrs": f1_lyr, "is_inst": f1_inst})

        with f1R:
            try:
                FA = calc_max_price(
                    cash=f1_cash, income=f1_income,
                    region=f1_region, ownership=f1_ownership, is_first=f1_is_first,
                    loan_rate=f1_loan_rate_pct / 100, loan_years=f1_loan_years,
                    loan_type=f1_loan_type, ex_loans=f1_ex_loans,
                )
            except Exception as _e:
                st.markdown(
                    alert(f"⛔ 계산 오류 — 입력값을 확인해주세요. ({type(_e).__name__})", "danger"),
                    unsafe_allow_html=True,
                )
                st.stop()

            # ── KPI 3개 ──────────────────────────────────────
            bind_bc, bind_lbl = (
                ("badge-orange", "DSR 제약") if FA["binding"] == "DSR"
                else ("badge-blue", "LTV 제약")
            )
            st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card primary">
    <div class="kpi-label">최대 구매 가능</div>
    <div class="kpi-num">{억만원(FA["max_price"])}</div>
    <div class="kpi-sub"><span class="badge {bind_bc}">{bind_lbl}</span></div>
  </div>
  <div class="kpi-card neutral">
    <div class="kpi-label">필요 대출</div>
    <div class="kpi-num">{억만원(FA["actual_loan"])}</div>
    <div class="kpi-sub">LTV {FA["ltv_pct"]}% (한도 {FA["ltv_limit_pct"]}%)</div>
  </div>
  <div class="kpi-card neutral">
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
                    f'{"✅ 스트레스 DSR 한도 통과" if dsr_ok else "❌ 스트레스 DSR 한도 초과"}'
                    f' &nbsp;|&nbsp; 일반 DSR(참고) {FA["dsr"]}%</div>',
                    unsafe_allow_html=True,
                )
                _fa_cdsr = FA.get("credit_dsr") or 0
                _fa_ex만 = FA.get("ex_annual_만") or 0
                if _fa_cdsr > 0:
                    _fa_mdsr = round((FA["stress_dsr"] or 0) - _fa_cdsr, 1)
                    st.markdown(
                        f'<div style="margin-top:0.5rem;padding:0.45rem 0.7rem;background:#F9FAFB;'
                        f'border-radius:8px;font-size:0.8rem;color:#374151;">'
                        f'<div style="font-weight:600;margin-bottom:0.25rem;color:#6B7684;">스트레스 DSR 구성</div>'
                        f'<div style="display:flex;justify-content:space-between;">'
                        f'<span>🏠 주담대 (스트레스 적용)</span><span><b>{_fa_mdsr}%</b></span></div>'
                        f'<div style="display:flex;justify-content:space-between;margin-top:0.1rem;">'
                        f'<span>💳 신용대출 <span style="color:#9CA3AF;font-size:0.74rem;">'
                        f'(연 {_fa_ex만:,}만원)</span></span>'
                        f'<span><b>{_fa_cdsr}%</b></span></div>'
                        f'<div style="display:flex;justify-content:space-between;margin-top:0.25rem;'
                        f'padding-top:0.25rem;border-top:1px solid #E5E8EB;font-weight:700;">'
                        f'<span>합계</span>'
                        f'<span style="color:{dsr_color};">{FA["stress_dsr"]}%</span></div>'
                        f'</div>',
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
  <div class="flow-item">
    <div class="flow-label">자기자본</div>
    <div class="flow-value">{억만원(FA["down_payment"])}</div>
  </div>
  <div style="display:flex;align-items:center;color:#9CA3AF;font-size:1.1rem;font-weight:700;flex-shrink:0;padding:0 0.2rem;" class="flow-op">＋</div>
  <div class="flow-item">
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
                    ex_loans=f1_ex_loans,
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
        st.caption("📋 디딤돌 2024.11 · 보금자리론 2024.11 · 특례보금자리 2024.01 종료")
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
                                         help="2023.1.1 이후 출생·입양 자녀 + 대출 신청일 기준 2세 미만. 해당 여부는 은행 확인 필요")
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
                f'<div class="loan-cards-row" style="display:flex;gap:0.75rem;align-items:stretch;">'
                f'{_card_dd}{_card_bg}{_card_nb}'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── 전부 부적격 시 대안 안내 ──────────────────────
            if not (dd_ok or bg_ok or nb_ok):
                # 부적격 사유 분석
                _alts = []
                if f2_income > 8_500:
                    _alts.append("소득이 모든 정책대출 한도(최대 1.3억)를 초과합니다.")
                    _alts.append("👉 <b>일반 주택담보대출</b>(은행 변동·고정금리)을 비교해보세요.")
                elif f2_price > 90_000:
                    _alts.append("주택가가 모든 정책대출 한도(최대 9억)를 초과합니다.")
                    _alts.append("👉 <b>9억 이하 주택</b>으로 조건 조정 또는 일반 주담대 검토.")
                else:
                    _alts.append("현재 조건에서는 정책대출 적격 상품이 없습니다.")
                    _alts.append("👉 소득·주택가 조건을 조정하거나 일반 주담대를 검토하세요.")
                st.markdown(
                    f'<div class="alert alert-warn" style="margin-top:0.7rem;">'
                    f'<b>⚠️ 적격 정책대출 없음</b><br>'
                    + "<br>".join(_alts) +
                    f'<br><span style="font-size:0.8rem;color:#92400E;">※ 은행별 일반 주담대 금리는 시중은행 앱·금융감독원 금리비교 서비스에서 확인하세요.</span>'
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
        st.caption("📋 기회비용 기준금리 연 2.5% (예금 평균) · 전세가율 지역별 시세 반영 필요")
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
            _opp_ref = (
                "예금 (2025.04 기준 약 3.0~3.5%)" if f3_opp_rate <= 3.5
                else "주식·ETF (장기 기대 수익률 4~7%)" if f3_opp_rate <= 6.0
                else "고위험 자산 수준"
            )
            st.caption(f"현재 설정 {f3_opp_rate:.2f}% → 참고: {_opp_ref}")
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
<div class="kpi-row">
  <div class="kpi-card neutral">
    <div class="kpi-label">전세 월 기회비용</div>
    <div class="kpi-num">{jeonse_m:,.0f}만원</div>
    <div class="kpi-sub">보증금 × {f3_opp_rate:.2f}% ÷ 12</div>
  </div>
  <div class="kpi-card neutral">
    <div class="kpi-label">매매 월 순비용</div>
    <div class="kpi-num">{buy_net_m:+,.0f}만원</div>
    <div class="kpi-sub">이자 + 유지비 − 상승분</div>
  </div>
  <div class="kpi-card {adv_cls}">
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
        st.caption("📋 취득세 일반 2020.08 · 중과세율 2023.12 · 생애최초 감면 2023.01 · 인지세 2024.01")
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

            f4c, f4d = st.columns(2)
            f4_ownership4 = f4c.selectbox("현재 보유 주택 수", _own_opts,
                                           key="f4_ownership4",
                                           help="다주택자는 취득세 중과세율 적용")
            f4_region4    = f4d.selectbox("취득 지역", _region_opts,
                                           key="f4_region4",
                                           help="규제지역·수도권 여부에 따라 세율 차이")
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
            tax4    = calc_acquisition_tax(f4_price, f4_is_large4,
                                            ownership=f4_ownership4, region=f4_region4)
            broker4 = calc_brokerage(f4_price)
            stamp4_원 = calc_stamp_tax(f4_price)

            # 생애최초 감면: 주택가 12억 이하, 중과세율 미적용 시만
            discount4 = 0
            if f4_is_first4 and f4_price <= 120_000 and not tax4.get("surcharge"):
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
<div class="kpi-row">
  <div class="kpi-card neutral">
    <div class="kpi-label">감면 전 총비용</div>
    <div class="kpi-num" style="color:#9CA3AF;text-decoration:line-through;">{억만원(total_before4//10_000)}</div>
    <div class="kpi-sub">생애최초 감면 미적용</div>
  </div>
  <div class="kpi-card success">
    <div class="kpi-label">감면 후 총비용</div>
    <div class="kpi-num">{억만원(total_after4//10_000)}</div>
    <div class="kpi-sub">취득세 {discount4//10_000:,}만원 절감</div>
  </div>
  <div class="kpi-card neutral">
    <div class="kpi-label">취득세율 (본세)</div>
    <div class="kpi-num">{tax4["rate_pct"]}%</div>
    <div class="kpi-sub">매매가 대비 총비용 {total_after4/f4_price/100:.2f}%</div>
  </div>
</div>
""", unsafe_allow_html=True)
            else:
                over12 = f4_is_first4 and f4_price > 120_000
                st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card primary">
    <div class="kpi-label">총 취득 비용</div>
    <div class="kpi-num">{억만원(total_before4//10_000)}</div>
    <div class="kpi-sub">매매가 대비 {total_before4/f4_price/100:.2f}%</div>
  </div>
  <div class="kpi-card neutral">
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

            if tax4.get("surcharge"):
                st.markdown(
                    alert(f"⚠️ 다주택 취득세 중과 {tax4['rate_pct']}% 적용 — "
                          f"처분조건부 취득 또는 증여·상속 여부 세무사 확인 권장", "warn"),
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

    # ── 결과 공유 ──────────────────────────────────────────
    with st.expander("🔗 현재 조건 공유"):
        if st.button("📋 공유 링크 생성 (URL 업데이트)", key="_share_f"):
            st.query_params.update({
                "m":             "f",
                "f1_cash":       str(int(f1_cash)),
                "f1_income":     str(int(f1_income)),
                "f1_region":     f1_region,
                "f1_ownership":  f1_ownership,
                "f1_loan_type":  f1_loan_type,
                "f1_is_first":   "1" if f1_is_first else "0",
                "f1_loan_rate":  str(round(f1_loan_rate_pct, 2)),
                "f1_loan_years": str(int(f1_loan_years)),
            })
            st.success("✅ URL이 업데이트됐습니다 — 주소창의 URL을 복사해서 공유하세요!")
        summary_f = (
            f"📊 첫 집 마련 분석\n"
            f"보유 현금: {억만원(f1_cash)} | 연소득: {억만원(f1_income)}\n"
            f"────────────────────────\n"
            f"최대 구매 가능: {억만원(FA['max_price'])} ({FA['binding']} 제약)\n"
            f"필요 대출: {억만원(FA['actual_loan'])} (LTV {FA['ltv_pct']}% / 한도 {FA['ltv_limit_pct']}%)\n"
            f"월 상환: {억만_원(FA['monthly'])} | 스트레스 {억만_원(FA['monthly_str'])}\n"
            f"────────────────────────\n"
            f"지역: {f1_region} | 보유: {f1_ownership} | 금리유형: {f1_loan_type}\n"
            f"금리: {f1_loan_rate_pct:.2f}% | 기간: {int(f1_loan_years)}년 | 생애최초: {'예' if f1_is_first else '아니오'}\n"
            f"※ 참고용 계산입니다. 실제 대출·세금은 전문가 확인 필수."
        )
        st.code(summary_f, language=None)

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
    # ── Tab 5: 양도소득세 ─────────────────────────────────────
    with ftab5:
        st.caption("📋 1세대1주택 비과세 · 고가주택 안분 · 장기보유특별공제 · 기본세율 | 2025년 세법 기준")

        t5L, t5R = st.columns([1, 1.35], gap="large")

        with t5L:
            # ── 양도 정보 ───────────────────────────────────────
            st.markdown('<div class="input-section"><div class="section-label">양도 정보</div>', unsafe_allow_html=True)
            _init("t5_acquire",  30_000)
            _init("t5_transfer", 60_000)
            t5_acquire  = st.number_input("취득가액 (만원)", key="t5_acquire",  min_value=100, step=1_000)
            t5_transfer = st.number_input("양도가액 (만원)", key="t5_transfer", min_value=100, step=1_000)
            price_buttons("t5_transfer")
            t5c1, t5c2 = st.columns(2)
            t5_acquire_date  = t5c1.date_input("취득일", key="t5_acq_date",  value=date(2018, 1, 1))
            t5_transfer_date = t5c2.date_input("양도일", key="t5_trf_date",  value=date.today())
            st.markdown('</div>', unsafe_allow_html=True)

            # ── 주택 상태 ───────────────────────────────────────
            st.markdown('<div class="input-section"><div class="section-label">주택 상태</div>', unsafe_allow_html=True)
            _t5_own = ["1주택", "2주택 이상"]
            _init("t5_own", "1주택")
            t5_own = st.selectbox("보유 주택 수", _t5_own, key="t5_own",
                                  help="2주택 이상은 장기보유특별공제 일반 세율 적용")
            if t5_own == "1주택":
                t5a, t5b = st.columns(2)
                _init("t5_regulated", True)
                t5_regulated = t5a.checkbox("조정대상지역 취득", key="t5_regulated", value=True,
                                            help="2017.8.3 이후 조정대상지역 취득 시 거주 2년 요건 추가")
                _init("t5_reside", 2.0)
                t5_reside = t5b.number_input("실거주 기간 (년)", key="t5_reside",
                                              min_value=0.0, max_value=50.0, step=0.5, format="%.1f")
            else:
                t5_regulated = False
                t5_reside    = 0.0
            st.markdown('</div>', unsafe_allow_html=True)

            # ── 필요경비 ────────────────────────────────────────
            st.markdown('<div class="input-section"><div class="section-label">필요경비</div>', unsafe_allow_html=True)
            _init("t5_acq_cost",   0)
            _init("t5_other_cost", 0)
            t5_acq_cost   = st.number_input("취득 관련 비용 (만원)", key="t5_acq_cost",   min_value=0, step=100,
                                             help="취득세 + 취득 시 중개수수료 + 법무사수수료")
            t5_other_cost = st.number_input("기타 필요경비 (만원)",  key="t5_other_cost", min_value=0, step=100,
                                             help="자본적 지출(인테리어·리모델링 등) + 양도 시 중개수수료")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── 결과 ────────────────────────────────────────────────
        with t5R:
            if t5_transfer_date <= t5_acquire_date:
                st.markdown(alert("⚠️ 양도일이 취득일보다 빠를 수 없습니다.", "warn"), unsafe_allow_html=True)
            else:
                try:
                    T = calc_transfer_tax(
                        acquire_price  = t5_acquire,
                        transfer_price = t5_transfer,
                        acquire_cost   = t5_acq_cost,
                        other_cost     = t5_other_cost,
                        acquire_date   = t5_acquire_date,
                        transfer_date  = t5_transfer_date,
                        ownership      = t5_own,
                        reside_years   = t5_reside,
                        is_regulated   = t5_regulated,
                    )
                except Exception as _e:
                    st.markdown(alert(f"⛔ 계산 오류 ({type(_e).__name__})", "danger"), unsafe_allow_html=True)
                    T = None

                if T is not None:
                    hy = int(T["holding_years"])
                    hm = int((T["holding_years"] % 1) * 12)

                    if T["no_gain"]:
                        st.markdown(alert("ℹ️ 양도차익이 없어 납부세액이 없습니다.", "warn"), unsafe_allow_html=True)

                    elif T["is_exempt"] and T["total_tax"] == 0:
                        st.markdown(f"""
<div style="background:#E8F9EE;border-left:4px solid #00C73C;border-radius:12px;padding:1.1rem 1.3rem;margin-bottom:1rem;">
  <div style="font-size:0.82rem;font-weight:700;color:#00853A;">✅ 비과세 대상</div>
  <div style="font-size:0.78rem;color:#2D7A46;margin-top:0.25rem;">{T["exempt_reason"]}</div>
  <div style="font-size:1.6rem;font-weight:900;color:#00853A;margin-top:0.5rem;">납부 세액 없음</div>
  <div style="font-size:0.78rem;color:#2D7A46;margin-top:0.3rem;">양도차익 {T["gain"]:,.0f}만원 전액 비과세</div>
</div>
""", unsafe_allow_html=True)

                    else:
                        # 고가주택 안내
                        if T.get("exempt_reason"):
                            st.markdown(alert(f"⚠️ {T['exempt_reason']}", "warn"), unsafe_allow_html=True)

                        # KPI 3개
                        st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card danger">
    <div class="kpi-label">최종 납부세액</div>
    <div class="kpi-num" style="color:#F03C2E;">{억만원(int(T["total_tax"]))}</div>
    <div class="kpi-sub">소득세 + 지방소득세(10%)</div>
  </div>
  <div class="kpi-card neutral">
    <div class="kpi-label">실효세율</div>
    <div class="kpi-num">{T["effective_rate"]*100:.1f}%</div>
    <div class="kpi-sub">납부세액 ÷ 양도차익</div>
  </div>
  <div class="kpi-card neutral">
    <div class="kpi-label">보유기간</div>
    <div class="kpi-num">{hy}년 {hm}개월</div>
    <div class="kpi-sub">장기보유공제 {T["ltg_rate"]*100:.0f}%</div>
  </div>
</div>
""", unsafe_allow_html=True)

                        # 계산 과정
                        def _row(lbl, val_만, style="normal"):
                            if style == "header":
                                bg, fw, fc = "#F0F7FF", "700", "#1B64DA"
                            elif style == "total":
                                bg, fw, fc = "#FFF0F0", "800", "#F03C2E"
                            else:
                                bg, fw, fc = "#FFFFFF", "500", "#191F28"
                            sign = "−" if val_만 < 0 else ""
                            val_str = f"{sign}{abs(val_만):,.0f}만원"
                            return (f'<div style="display:flex;justify-content:space-between;align-items:center;'
                                    f'padding:0.4rem 0.8rem;background:{bg};border-radius:6px;margin-bottom:2px;">'
                                    f'<span style="font-size:0.8rem;color:#6B7684;">{lbl}</span>'
                                    f'<span style="font-size:0.83rem;font-weight:{fw};color:{fc};">{val_str}</span>'
                                    f'</div>')

                        html = '<div style="margin-top:0.5rem;">'
                        html += _row("양도가액",            T["transfer_price"])
                        html += _row("(−) 취득가액",        -T["acquire_price"])
                        html += _row("(−) 필요경비 합계",   -T["total_cost"])
                        html += _row("= 양도차익",           T["gain"],          "header")
                        if T.get("exempt_reason"):
                            ratio = (T["transfer_price"] - 120_000) / T["transfer_price"] * 100
                            html += (f'<div style="padding:0.35rem 0.8rem;font-size:0.76rem;color:#FF6B00;">'
                                     f'↳ 12억 초과 안분비율 {ratio:.1f}% 적용</div>')
                            html += _row("= 과세 양도차익",  T["taxable_gain"],  "header")
                        if T["ltg_rate"] > 0:
                            html += _row(f"(−) 장기보유특별공제 ({T['ltg_rate']*100:.0f}%)", -T["ltg_deduction"])
                        html += _row("= 양도소득금액",       T["income"],        "header")
                        html += _row("(−) 기본공제",         -T["basic_ded"])
                        html += _row("= 과세표준",           T["tax_base"],      "header")
                        html += _row("소득세",               T["income_tax"])
                        html += _row("지방소득세 (10%)",     T["local_tax"])
                        html += _row("= 최종 납부세액",      T["total_tax"],     "total")
                        html += '</div>'
                        st.markdown(html, unsafe_allow_html=True)

                        st.caption("※ 본 계산은 참고용입니다. 다주택 중과·비과세 예외 등 복잡한 케이스는 세무사 확인 필수.")

    st.stop()


# ════════════════════════════════════════════════════════════
# 갈아타기 계산기 (기존)
# ════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs(["  💰 대출 시뮬레이터  ", "  🔄 갈아타기 손익  ", "  📅 이사 일정 역산  "])


# ═══════════════════════════════════════════════════════════
# TAB 1 — 대출 시뮬레이터
# ═══════════════════════════════════════════════════════════

with tab1:
    st.caption("📋 LTV 2024.09 · 스트레스 DSR 2025.07 · 대출 상한 5억 2025.07")
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
            own_cash = st.number_input("별도 보유 현금 (만원)", key="own_cash", min_value=0, step=500,
                                       help="매도 순수령금 외에 추가로 보유한 현금·예금 (전세보증금, 저축 등)")
            price_buttons("own_cash",
                          presets=(5_000, 1_000, -1_000, -5_000),
                          labels=("+5천", "+1천", "–1천", "–5천"))
        # ── 목표가 시세 참고 ───────────────────────────────
        if tgt_price >= 200_000:
            _ctx = "서울 강남·용산·성수 등 최상급지 수준"
        elif tgt_price >= 120_000:
            _ctx = "서울 주요 지역 (마포·서초·송파 등) 수준"
        elif tgt_price >= 80_000:
            _ctx = "서울 외곽·분당·판교·과천 수준"
        elif tgt_price >= 50_000:
            _ctx = "경기 주요 도시·서울 외곽 수준"
        elif tgt_price >= 30_000:
            _ctx = "경기·인천 일반 지역 수준"
        else:
            _ctx = "지방 도시 수준"
        st.markdown(
            f'<div style="font-size:0.78rem;color:#6B7684;background:#F9FAFB;'
            f'border-radius:8px;padding:0.5rem 0.8rem;margin:0.3rem 0 0.6rem;">'
            f'💡 <b>{억만원(tgt_price)}</b> → {_ctx} (2024~2025 시장 기준)'
            f'&nbsp;&nbsp;'
            f'<a href="https://rt.molit.go.kr/" target="_blank" style="color:#1B64DA;">실거래가 조회 →</a>'
            f'&nbsp;'
            f'<a href="https://asil.kr/" target="_blank" style="color:#1B64DA;">아실 →</a>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # 대출 조건
        st.markdown('<div class="input-section"><div class="section-label">대출 조건</div>', unsafe_allow_html=True)
        lc1, lc2 = st.columns(2)
        region    = lc1.selectbox("지역",
            [REGION_REGULATED, REGION_METRO, REGION_LOCAL], index=1, key="region",
            help="규제지역: 서울 전역 + 경기 12곳(강남·서초·송파·용산 투기과열 포함)")
        ownership = lc2.selectbox("주택 보유",
            [OWN_NONE, OWN_ONE_COND, OWN_ONE, OWN_TWO_PLUS], index=1, key="ownership",
            help="처분조건부: 매수 후 6개월 내 기존 집 처분 조건부 대출")

        lc3, lc4 = st.columns(2)
        loan_type = lc3.selectbox("금리 유형", [LOAN_VARIABLE, LOAN_MIXED, LOAN_FIXED], key="loan_type",
            help="변동형: 스트레스 금리 100% | 혼합형: 60% | 고정형: 0%")
        is_first  = lc4.checkbox("생애최초", key="is_first", help="규제지역도 LTV 70% 특례 적용")

        lc5, lc6 = st.columns([2, 1])
        loan_rate_pct = lc5.slider("대출 금리 (%)", 1.0, 10.0, 3.7, 0.05, format="%.2f%%", key="loan_rate")
        loan_years    = lc6.number_input("기간 (년)", value=30, min_value=1, max_value=50, step=5, key="loan_years")
        st.markdown('</div>', unsafe_allow_html=True)

        # 고급 설정
        with st.expander("⚙️ 고급 설정 (DSR · 비용 · 신용대출)"):
            ex1, ex2 = st.columns(2)
            _init("t1_income", 8_000); _init("t1_moving", 300)
            annual_income = ex1.number_input("연소득 (만원, DSR용)", key="t1_income", step=500, min_value=0,
                                             help="세전 연소득 기준")
            moving_cost   = ex2.number_input("이사비 (만원)", key="t1_moving", step=50, min_value=0)
            is_large = st.checkbox("전용 85㎡ 초과 (농어촌특별세 추가)", key="t1_is_large")

            st.divider()
            _init("t1_n_loans", 0)
            n_loans = int(st.number_input("기존 신용대출 건수 (DSR 합산)", key="t1_n_loans",
                                          min_value=0, max_value=5,
                                          help="보유 중인 신용대출·마이너스통장 건수"))
            ex_loans = []
            for i in range(n_loans):
                st.markdown(f"**신용대출 {i+1}**")
                sl1, sl2, sl3 = st.columns(3)
                _init(f"lb{i}", 3_000); _init(f"lr{i}", 4.5); _init(f"ly{i}", 3)
                bal  = sl1.number_input("잔여원금 (만원)", key=f"lb{i}", min_value=0, step=100)
                lr   = sl2.number_input("연금리 (%)", key=f"lr{i}", min_value=0.1, max_value=20.0, format="%.2f",
                                        help="비분할상환: DSR = 원금/min(잔여만기,10년)+이자 (규제 기준)")
                lyr  = sl3.number_input("잔여만기 (년)", key=f"ly{i}", min_value=1, max_value=30)
                inst = st.checkbox("분할상환", key=f"li{i}")
                ex_loans.append({"bal": bal, "rate": lr/100, "yrs": lyr, "is_inst": inst})

    # ── 계산 ─────────────────────────────────────────────
    try:
        R = run_sim({
            "cur": cur_price, "cur_loan": cur_loan,
            "tgt": tgt_price, "cash": own_cash,
            "loan_rate": loan_rate_pct / 100, "loan_years": loan_years,
            "region": region, "ownership": ownership, "loan_type": loan_type,
            "is_first": is_first, "is_large": is_large,
            "income": annual_income, "moving": moving_cost, "ex_loans": ex_loans,
        })
    except Exception as _e:
        with col_R:
            st.markdown(
                alert(f"⛔ 계산 오류 — 입력값을 확인해주세요. ({type(_e).__name__})", "danger"),
                unsafe_allow_html=True,
            )
        st.stop()
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
        <div class="kpi-row">

          <div class="kpi-card primary">
            <div class="kpi-label">대출 가능 금액</div>
            <div class="kpi-num">{억만원(R["act_loan"])}</div>
            <div class="kpi-sub">필요 {억만원(R["need_loan"])}</div>
          </div>

          <div class="kpi-card neutral">
            <div class="kpi-label">월 상환액</div>
            <div class="kpi-num">{억만_원(R["monthly"])}</div>
            <div class="kpi-sub">스트레스 {억만_원(R["monthly_str"])}</div>
          </div>

          <div class="kpi-card {ltv_cls}">
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
          <div class="flow-item">
            <div class="flow-label">매도 순수령</div>
            <div class="flow-value">{억만원(R["net_sell"])}</div>
          </div>
          <div style="display:flex;align-items:center;color:#9CA3AF;font-size:1.1rem;font-weight:700;flex-shrink:0;padding:0 0.2rem;" class="flow-op">＋</div>
          <div class="flow-item">
            <div class="flow-label">추가 현금</div>
            <div class="flow-value">{억만원(own_cash)}</div>
          </div>
          <div style="display:flex;align-items:center;color:#9CA3AF;font-size:1.1rem;font-weight:700;flex-shrink:0;padding:0 0.2rem;" class="flow-op">＝</div>
          <div class="flow-item">
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
            ok        = R["dsr_ok"]
            bar_color = "#00C73C" if ok else "#F03C2E"
            bar_pct   = min(100, R["stress_dsr"])

            # 스트레스 DSR 게이지
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;font-size:0.82rem;color:#6B7684;margin-bottom:4px;">'
                f'<span>스트레스 DSR: <b style="color:#191F28;">{R["stress_dsr"]}%</b> '
                f'(+{R["stress_add_pct"]}%p 가산)</span>'
                f'<span>은행 한도 40%</span></div>'
                f'<div class="dsr-bar-wrap">'
                f'<div class="dsr-bar-fill" style="width:{bar_pct}%;background:{bar_color};"></div>'
                f'</div>'
                f'<div style="font-size:0.78rem;color:{bar_color};font-weight:600;margin-top:4px;">'
                f'{"✅ 스트레스 DSR 한도 통과" if ok else "❌ 스트레스 DSR 한도 초과"}'
                f'&nbsp;|&nbsp;일반 DSR(참고) {R["dsr"]}%</div>',
                unsafe_allow_html=True,
            )

            # DSR 구성 breakdown
            _m_dsr  = R.get("stress_mortgage_dsr") or 0
            _c_dsr  = R.get("credit_dsr") or 0
            _ex_만  = R.get("ex_annual_만") or 0
            if _c_dsr > 0:
                st.markdown(
                    f'<div style="margin-top:0.55rem;padding:0.5rem 0.7rem;background:#F9FAFB;'
                    f'border-radius:8px;font-size:0.8rem;color:#374151;">'
                    f'<div style="font-weight:600;margin-bottom:0.3rem;color:#6B7684;">스트레스 DSR 구성</div>'
                    f'<div style="display:flex;justify-content:space-between;">'
                    f'<span>🏠 주담대 (스트레스 금리 적용)</span><span><b>{_m_dsr}%</b></span></div>'
                    f'<div style="display:flex;justify-content:space-between;margin-top:0.15rem;">'
                    f'<span>💳 신용대출 합산 <span style="color:#9CA3AF;font-size:0.74rem;">'
                    f'(연 {_ex_만:,}만원 — 원금/잔여만기+이자 기준)</span></span>'
                    f'<span><b>{_c_dsr}%</b></span></div>'
                    f'<div style="display:flex;justify-content:space-between;margin-top:0.3rem;'
                    f'padding-top:0.3rem;border-top:1px solid #E5E8EB;font-weight:700;">'
                    f'<span>합계</span><span style="color:{bar_color};">{R["stress_dsr"]}%</span></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if not ok and R["dsr"] <= 40:
                    st.caption(
                        "💡 일반 DSR은 40% 이내지만, 변동형 주담대에 스트레스 금리가 가산되어 "
                        "한도를 초과합니다. 고정형·혼합형으로 변경하거나 대출 금액을 줄이면 통과 가능합니다."
                    )
                st.caption(
                    "ℹ️ 비분할상환 신용대출 DSR = 잔여원금 ÷ min(잔여만기, 10년) + 연이자 "
                    "(금융위원회 DSR 산정 기준 — 실제 납입액보다 보수적으로 산정)"
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
        section("금리 상승 리스크")
        _sc1 = R["rate_scen"].get("+1.0%p", {})
        _sc2 = R["rate_scen"].get("+2.0%p", {})
        if _sc1 and R["monthly"] > 0:
            _diff1 = _sc1.get("diff", 0)
            _diff2 = _sc2.get("diff", 0)
            _risk_cls = "warning" if _diff1 > 30 else "neutral"
            st.markdown(f"""
<div style="display:flex;gap:0.75rem;margin-bottom:0.5rem;">
  <div class="kpi-card {_risk_cls}">
    <div class="kpi-label">금리 +1%p 시 월 상환 증가</div>
    <div class="kpi-value-md">+{억만_원(_diff1)}</div>
    <div class="kpi-sub">{_sc1.get("rate",0):.2f}% 적용 → {억만_원(_sc1.get("pmt",0))}</div>
  </div>
  <div class="kpi-card danger">
    <div class="kpi-label">금리 +2%p 시 월 상환 증가</div>
    <div class="kpi-value-md">+{억만_원(_diff2)}</div>
    <div class="kpi-sub">{_sc2.get("rate",0):.2f}% 적용 → {억만_원(_sc2.get("pmt",0))}</div>
  </div>
</div>
""", unsafe_allow_html=True)
        with st.expander("📈 전체 금리 시나리오 보기"):
            sc_rows = [
                {"금리 변동": k, "적용 금리": f'{v["rate"]}%',
                 "월 상환액": 억만_원(v["pmt"]),
                 "증가액": f'+{억만_원(v["diff"])}'}
                for k, v in R["rate_scen"].items()
            ]
            st.dataframe(pd.DataFrame(sc_rows), use_container_width=True, hide_index=True)
            st.caption(f"현재 금리 {loan_rate_pct:.2f}% 기준 0.5~2.0%p 상승 시 월 상환액 변화")

    # ── A/B 시나리오 비교 ──────────────────────────────────
    with st.expander("📊 시나리오 A/B 비교"):
        _sv1, _sv2, _sv3 = st.columns([1, 1, 1])
        if _sv1.button("💾 A안으로 저장", key="_save_a", use_container_width=True):
            st.session_state["_scenario_a"] = _snapshot(
                R, cur_price, tgt_price, region, ownership,
                loan_type, is_first, loan_rate_pct, loan_years, "A안"
            )
            st.toast("✅ A안 저장 완료!")
        if _sv2.button("💾 B안으로 저장", key="_save_b", use_container_width=True):
            st.session_state["_scenario_b"] = _snapshot(
                R, cur_price, tgt_price, region, ownership,
                loan_type, is_first, loan_rate_pct, loan_years, "B안"
            )
            st.toast("✅ B안 저장 완료!")
        if _sv3.button("🗑 초기화", key="_clear_sc", use_container_width=True):
            st.session_state.pop("_scenario_a", None)
            st.session_state.pop("_scenario_b", None)

        _sa = st.session_state.get("_scenario_a")
        _sb = st.session_state.get("_scenario_b")
        if _sa or _sb:
            _metric_keys = ["현재 집 매도가","목표 매수가","대출 가능","월 상환",
                            "스트레스 월상환","LTV","스트레스 DSR","갈아타기 비용","조건"]
            _cmp_rows = [
                {"항목": m,
                 "A안 📌" if _sa else "A안": (_sa.get(m, "—") if _sa else "—"),
                 "B안 📌" if _sb else "B안": (_sb.get(m, "—") if _sb else "—")}
                for m in _metric_keys
            ]
            st.dataframe(pd.DataFrame(_cmp_rows), use_container_width=True, hide_index=True)
            if not _sa:
                st.caption("A안을 아직 저장하지 않았습니다.")
            if not _sb:
                st.caption("B안을 아직 저장하지 않았습니다.")
        else:
            st.caption("조건을 설정한 뒤 'A안 저장' → 조건 변경 후 'B안 저장' 순서로 비교하세요.")

    # ── 결과 공유 ──────────────────────────────────────────
    with st.expander("🔗 결과 공유"):
        if st.button("📋 공유 링크 생성 (URL 업데이트)", key="_share_g"):
            st.query_params.update({
                "m": "g",
                "cur_price": str(int(cur_price)),
                "cur_loan":  str(int(cur_loan)),
                "tgt_price": str(int(tgt_price)),
                "own_cash":  str(int(own_cash)),
                "region":    region,
                "ownership": ownership,
                "loan_type": loan_type,
                "is_first":  "1" if is_first else "0",
                "loan_rate": str(round(loan_rate_pct, 2)),
                "loan_years": str(int(loan_years)),
            })
            st.success("✅ URL이 업데이트됐습니다 — 주소창의 URL을 복사해서 공유하세요!")
        dsr_str = (
            f"DSR {R['dsr']}% / 스트레스 DSR {R['stress_dsr']}%"
            if R["dsr"] is not None else "DSR 정보 없음 (소득 미입력)"
        )
        summary_g = (
            f"📊 갈아타기 분석\n"
            f"현재 집: 매도가 {억만원(cur_price)} | 잔여대출 {억만원(cur_loan)}\n"
            f"목표 집: 매수가 {억만원(tgt_price)} | 추가현금 {억만원(own_cash)}\n"
            f"────────────────────────\n"
            f"대출 가능: {억만원(R['act_loan'])} (LTV {R['ltv_pct']}% / 한도 {R['ltv_limit_pct']}%)\n"
            f"월 상환: {억만_원(R['monthly'])} | 스트레스 {억만_원(R['monthly_str'])}\n"
            f"{dsr_str}\n"
            f"갈아타기 총 비용: {억만원(R['total_cost'] // 10_000)}\n"
            f"────────────────────────\n"
            f"지역: {region} | 보유: {ownership} | 금리유형: {loan_type}\n"
            f"금리: {loan_rate_pct:.2f}% | 기간: {int(loan_years)}년\n"
            f"※ 참고용 계산입니다. 실제 대출·세금은 전문가 확인 필수."
        )
        st.code(summary_g, language=None)


# ═══════════════════════════════════════════════════════════
# TAB 2 — 갈아타기 손익
# ═══════════════════════════════════════════════════════════

with tab2:
    st.caption("📋 취득세 일반 2020.08 · 중과세율 2023.12 · 생애최초 감면 2023.01 · 중개보수 2021.10")
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
            st.markdown(
                '<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-left:4px solid #1B64DA;'
                'border-radius:10px;padding:0.9rem 1.1rem;margin-bottom:0.8rem;">'
                '<b style="color:#1B64DA;">① 먼저 "대출 시뮬레이터" 탭을 입력하세요</b><br>'
                '<span style="font-size:0.83rem;color:#374151;">'
                '탭1에서 현재 집·목표 집·대출 조건을 입력하면 이 탭에 자동 연동됩니다.'
                '</span></div>',
                unsafe_allow_html=True,
            )
            base_cost = st.number_input("갈아타기 총 비용 (원)", value=15_000_000, step=1_000_000)
            new_loan  = st.number_input("신규 대출 (만원)", value=30_000, step=1_000, min_value=0)
            l_rate    = st.number_input("대출 금리 (%)", value=3.7, format="%.2f") / 100

        st.markdown('<div class="input-section"><div class="section-label">기대 수익</div>', unsafe_allow_html=True)
        _init("monthly_gain", 0)
        monthly_gain = st.number_input(
            "목표 집 기대 월 상승액 (만원)", key="monthly_gain", min_value=0, step=10,
            help="목표 집이 매월 평균 얼마나 오를지 (예: 연 1,200만 → 월 100만)",
        )
        price_buttons("monthly_gain",
                      presets=(100, 50, -50, -100),
                      labels=("+100", "+50", "–50", "–100"))
        if monthly_gain > 0:
            _tgt = st.session_state.get("tgt_price", 0)
            if _tgt > 0:
                _annual_rate = monthly_gain * 12 / _tgt * 100
                st.caption(
                    f"연 {monthly_gain*12:,}만원 상승 = "
                    f"목표가 {억만원(_tgt)} 기준 **연 {_annual_rate:.1f}% 상승률**"
                )
            else:
                st.caption(f"연 {monthly_gain*12:,}만원 상승 (탭1에서 목표가 입력 시 상승률 자동 계산)")
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
    st.caption("📋 이사 일정 역산 — 별도 정책 기준 없음 (사용자 입력 기반)")
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
        net_cls3 = "success" if S["net"] > 0 else "warning"
        st.markdown(f"""
<div style="display:flex;gap:0.75rem;align-items:stretch;">
  <div class="kpi-card neutral" style="flex:1;min-width:0;display:flex;flex-direction:column;">
    <div class="kpi-label">월 기회비용 (보유 시)</div>
    <div class="kpi-value-md">{S['opp']:,}만원</div>
    <div class="kpi-sub">현재 집 × 연 2.5% ÷ 12</div>
  </div>
  <div class="kpi-card {net_cls3}" style="flex:1;min-width:0;display:flex;flex-direction:column;">
    <div class="kpi-label">기회비용 차감 실질 월 이득</div>
    <div class="kpi-value-md">{S['net']:+,}만원</div>
    <div class="kpi-sub">&nbsp;</div>
  </div>
</div>
""", unsafe_allow_html=True)

        # ── 타임라인 시각화 (plotly) ──────────────────────
        section("타임라인 시각화")
        STEP_COLORS = {
            "done": "#D1D5DB", "active": "#1B64DA",
            "urgent": "#F03C2E", "future": "#60A5FA",
        }

        def _step_color(ym):
            if ym < today_str:   return STEP_COLORS["done"]
            elif ym == today_str: return STEP_COLORS["active"]
            elif S["late"] and ym == S["steps"][0][2]: return STEP_COLORS["urgent"]
            else:                 return STEP_COLORS["future"]

        xs_pts = []
        cs_pts = []
        hover_txts = []
        for icon, lbl, ym, desc in S["steps"]:
            yr2, mo2 = map(int, ym.split("-"))
            xs_pts.append(date(yr2, mo2, 1))
            cs_pts.append(_step_color(ym))
            hover_txts.append(f"{icon} {lbl}<br>{ym}<br>{desc}")

        fig3 = go.Figure()

        # 연결선
        fig3.add_trace(go.Scatter(
            x=xs_pts, y=[0] * len(xs_pts), mode="lines",
            line=dict(color="#E5E7EB", width=5),
            showlegend=False, hoverinfo="skip",
        ))

        # 도트
        fig3.add_trace(go.Scatter(
            x=xs_pts, y=[0] * len(xs_pts), mode="markers",
            marker=dict(size=30, color=cs_pts, line=dict(color="white", width=3)),
            showlegend=False,
            customdata=hover_txts,
            hovertemplate="%{customdata}<extra></extra>",
        ))

        # 라벨 — 홀짝 교차 배치 (겹침 방지)
        for i, (icon, lbl, ym, desc) in enumerate(S["steps"]):
            yr2, mo2 = map(int, ym.split("-"))
            x_pt = date(yr2, mo2, 1)
            color = _step_color(ym)
            above = (i % 2 == 0)
            y_label    =  1.1 if above else -1.1
            y_conn_end =  0.65 if above else -0.65
            y_conn_st  =  0.22 if above else -0.22

            # 점선 연결
            fig3.add_shape(
                type="line", x0=x_pt, x1=x_pt,
                y0=y_conn_st, y1=y_conn_end,
                line=dict(color=color, width=1.5, dash="dot"),
            )
            # 박스 라벨
            fig3.add_annotation(
                x=x_pt, y=y_label,
                text=f"<b>{lbl}</b><br>{ym}",
                showarrow=False,
                font=dict(size=10, color="#374151"),
                align="center",
                bgcolor="white",
                bordercolor=color,
                borderwidth=2,
                borderpad=5,
                yanchor="middle",
            )

        # 오늘 기준선
        fig3.add_vline(x=date.today(), line=dict(dash="dash", color="#9CA3AF", width=1.5))
        fig3.add_annotation(
            x=date.today(), y=1.85, text="오늘",
            showarrow=False, font=dict(size=9, color="#9CA3AF"), yanchor="bottom",
        )

        fig3.update_layout(
            height=300,
            yaxis=dict(visible=False, range=[-1.85, 1.95]),
            xaxis=dict(showgrid=False, zeroline=False, tickformat="%y.%m"),
            margin=dict(l=10, r=10, t=15, b=10),
            plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig3, use_container_width=True)

        # ── 캘린더 내보내기 ───────────────────────────────
        section("캘린더 내보내기")
        _ics_content = _make_ics(S["steps"])
        st.download_button(
            label="📅 구글 캘린더 / 애플 캘린더에 추가 (.ics)",
            data=_ics_content.encode("utf-8"),
            file_name="이사일정.ics",
            mime="text/calendar",
            use_container_width=True,
            help=".ics 파일을 열면 구글·애플·아웃룩 캘린더에 자동으로 일정이 추가됩니다",
        )
        st.caption("📌 파일 다운로드 후 더블클릭 → 캘린더 앱에서 '가져오기' 선택")


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
