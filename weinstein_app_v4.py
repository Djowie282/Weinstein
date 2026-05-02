"""
Weinstein Stage Screener v4
============================
Tabs: Screener | All Stocks | Portfolio | Dashboard
Features: dark/light toggle, market cap, AI universe, login, portfolio tracking
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import StringIO
import json
import hashlib
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Weinstein Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

DARK = st.session_state.dark_mode

if DARK:
    BG       = "#14171f"
    CARD     = "#1e2130"
    BORDER   = "#2e3347"
    TEXT     = "#dde3f0"
    SUBTEXT  = "#8892aa"
    GREEN    = "#4ade80"
    YELLOW   = "#fbbf24"
    RED      = "#f87171"
    BLUE     = "#60a5fa"
    ACCENT   = "#3b5bdb"
else:
    BG       = "#f6f8fa"
    CARD     = "#ffffff"
    BORDER   = "#d0d7de"
    TEXT     = "#1f2328"
    SUBTEXT  = "#656d76"
    GREEN    = "#1a7f37"
    YELLOW   = "#9a6700"
    RED      = "#cf222e"
    BLUE     = "#0969da"
    ACCENT   = "#0550ae"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;600;700;800&display=swap');

    .stApp {{ background-color: {BG}; }}
    .block-container {{ padding: 1.5rem 2rem 3rem 2rem; max-width: 100% !important; }}
    html, body, [class*="css"] {{ color: {TEXT}; font-family: 'Syne', sans-serif; }}
    h1 {{ font-family: 'Syne', sans-serif; font-weight: 800; color: {TEXT}; font-size: 2rem; margin-bottom: 0; }}
    h2, h3 {{ font-family: 'Syne', sans-serif; font-weight: 700; color: {TEXT}; }}
    .stTabs [data-baseweb="tab-list"] {{ background: {CARD}; border-radius: 8px; padding: 4px; border: 1px solid {BORDER}; gap: 4px; }}
    .stTabs [data-baseweb="tab"] {{ background: transparent; color: {SUBTEXT}; border-radius: 6px; font-weight: 600; padding: 8px 20px; }}
    .stTabs [aria-selected="true"] {{ background: {ACCENT}; color: white; }}
    .stDataFrame {{ border: 1px solid {BORDER}; border-radius: 8px; overflow: hidden; }}
    .stDataFrame table {{ width: 100%; }}
    div[data-testid="metric-container"] {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px; padding: 1rem; }}
    .stButton button {{ background: {ACCENT}; color: white; border: none; border-radius: 6px; font-weight: 600; }}
    .stButton button:hover {{ opacity: 0.85; }}
    .stSelectbox select, .stTextInput input, .stNumberInput input {{
        background: {CARD}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 6px;
    }}

    /* Signal cards */
    .card-premium {{ background: linear-gradient(135deg, rgba(63,185,80,0.12), {CARD});
        border-left: 3px solid {GREEN}; border: 1px solid rgba(63,185,80,0.3);
        padding: 12px 16px; border-radius: 8px; margin: 6px 0; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }}
    .card-early {{ background: linear-gradient(135deg, rgba(210,153,34,0.12), {CARD});
        border-left: 3px solid {YELLOW}; border: 1px solid rgba(210,153,34,0.3);
        padding: 12px 16px; border-radius: 8px; margin: 6px 0; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }}
    .card-s2 {{ background: {CARD}; border-left: 3px solid {BLUE}; border: 1px solid {BORDER};
        padding: 12px 16px; border-radius: 8px; margin: 4px 0; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }}
    .card-warn {{ background: {CARD}; border-left: 3px solid {RED};
        padding: 12px 16px; border-radius: 8px; margin: 6px 0; }}

    /* Stage badges */
    .badge-s2 {{ background: rgba(63,185,80,0.2); color: {GREEN}; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }}
    .badge-s3 {{ background: rgba(210,153,34,0.2); color: {YELLOW}; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }}
    .badge-s4 {{ background: rgba(248,81,73,0.2); color: {RED}; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }}
    .badge-s1 {{ background: rgba(88,166,255,0.2); color: {BLUE}; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }}

    .regime-ok   {{ color: {GREEN}; font-weight: 700; font-size: 1rem; }}
    .regime-warn {{ color: {RED};   font-weight: 700; font-size: 1rem; }}
    .regime-caution {{ color: {YELLOW}; font-weight: 700; font-size: 1rem; }}
    .subtext {{ color: {SUBTEXT}; font-size: 0.82rem; }}
    .mono {{ font-family: 'JetBrains Mono', monospace; }}
    .footer {{ color: {SUBTEXT}; font-size: 0.72rem; text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid {BORDER}; }}

    /* Dashboard */
    .perf-pos {{ color: {GREEN}; font-weight: 700; font-family: 'JetBrains Mono', monospace; }}
    .perf-neg {{ color: {RED};   font-weight: 700; font-family: 'JetBrains Mono', monospace; }}
    .asset-row {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px;
        padding: 12px 16px; margin: 6px 0; display: flex; justify-content: space-between; }}

    input[type="password"], input[type="text"] {{ background: {CARD} !important; color: {TEXT} !important; }}

    /* Stretch tables */
    .stDataFrame {{ width: 100% !important; }}
    [data-testid="stDataFrame"] > div {{ width: 100% !important; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

SMA_WEEKS            = 50
RS_MA_WEEKS          = 10
SMA_SLOPE_LOOKBACK   = 10
BREAKOUT_LOOKBACK    = 52
MAX_ABOVE_SMA        = 0.30
RECENT_CROSS_WEEKS   = 8
VOLUME_AVG_WEEKS     = 26
VOLUME_BREAKOUT_MULT = 1.5
BASE_RANGE_PCT       = 0.15
SWING_LOOKBACK_WEEKS = 8
YEARS_OF_DATA        = 4
BENCHMARK            = "SPY"
SLOPE_THRESHOLD      = 0.0005   # aligned threshold for both stage label + sma_rising

SECTORS = {
    "XLK": "Technology", "XLF": "Financials", "XLE": "Energy",
    "XLV": "Health Care", "XLI": "Industrials", "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples", "XLU": "Utilities", "XLRE": "Real Estate",
    "XLB": "Materials", "XLC": "Communication Services",
}

# Sector ETF → stocks (expanded universe)
SECTOR_STOCKS = {
    "XLK":  ["AAPL","NVDA","MSFT","AVGO","ORCL","CRM","AMD","ACN","ADBE","CSCO",
              "NOW","PANW","FTNT","SNPS","CDNS","AMAT","KLAC","LRCX","MU","TXN","QCOM",
              "ANET","MCHP","ADI","MRVL","ON","ZS","NET","DDOG","MDB","SNOW","PLTR","CRWD"],
    "XLF":  ["BRK-B","JPM","V","MA","BAC","GS","MS","WFC","SPGI","BLK",
              "AXP","C","USB","PNC","TFC","SCHW","COF","CME","ICE","MMC",
              "AON","MET","PRU","AFL","ALL","TRV","RJF","MTB"],
    "XLE":  ["XOM","CVX","COP","EOG","SLB","MPC","PSX","OXY","VLO","WMB",
              "HES","KMI","OKE","BKR","DVN","HAL","CTRA","OVV","EQT",
              "TPL","AR","RRC","MTDR","MUR","PR"],
    "XLV":  ["LLY","UNH","JNJ","ABBV","MRK","TMO","ABT","DHR","PFE","AMGN",
              "ISRG","BMY","ELV","MDT","GILD","CVS","REGN","VRTX","BSX","CI",
              "HCA","ZTS","BDX","SYK","EW","BIIB","IDXX","IQV","DXCM","MRNA"],
    "XLI":  ["GE","RTX","CAT","HON","UPS","DE","BA","LMT","MMM","ETN",
              "NOC","GD","EMR","PH","ITW","CSX","NSC","UNP","FDX","WM",
              "TT","JCI","ROK","PCAR","CMI","AME","GWW","FAST","ODFL","RSG"],
    "XLY":  ["AMZN","TSLA","HD","MCD","NKE","LOW","SBUX","TJX","BKNG","CMG",
              "ABNB","MAR","GM","F","ORLY","AZO","ROST","BBY","YUM","RCL",
              "LULU","DECK","ULTA","DG","DLTR","LEN","DHI","NVR","POOL"],
    "XLP":  ["PG","COST","KO","PEP","WMT","PM","MDLZ","CL","MO","GIS",
              "STZ","KMB","KHC","KR","SYY","KDP","HSY","CHD","EL","MNST",
              "TGT","CLX","MKC","HRL","CAG","K","TSN","ADM"],
    "XLU":  ["NEE","SO","DUK","AEP","SRE","D","EXC","XEL","PEG","ED",
              "WEC","EIX","AWK","ETR","DTE","FE","ES","AEE","PPL","CMS",
              "ATO","VST","CEG","NI","EVRG","LNT","PNW"],
    "XLRE": ["PLD","AMT","EQIX","WELL","SPG","PSA","O","DLR","CCI","VICI",
              "AVB","EXR","EQR","MAA","SBAC","INVH","ESS","ARE","UDR","VTR",
              "KIM","REG","FRT","HST","BXP","IRM","OHI","WPC"],
    "XLB":  ["LIN","SHW","FCX","ECL","APD","NEM","DD","CTVA","DOW","PPG",
              "NUE","STLD","VMC","MLM","CF","MOS","RPM","IFF","ALB","FMC",
              "AVY","BALL","IP","PKG","AMCR","EMN","OLN"],
    "XLC":  ["META","GOOGL","GOOG","NFLX","TMUS","DIS","VZ","T","CMCSA","EA",
              "TTWO","MTCH","OMC","IPG","CHTR","FOXA","WBD","PARA","LYV",
              "ROKU","PINS","SNAP","RBLX","TTD"],
}

# Pure AI/tech universe (ETFs + stocks) – shown as separate category
AI_UNIVERSE = {
    # AI Infrastructure ETFs
    "BOTZ": "AI & Robotics ETF", "AIQ": "AI ETF", "ROBO": "Robotics ETF",
    "ARKQ": "ARK Autonomous", "THNQ": "AI ETF (Robo Global)", "KOMP": "S&P Kensho",
    # Semiconductors (AI angle)
    "NVDA": "Nvidia", "AMD": "AMD", "AVGO": "Broadcom", "AMAT": "Applied Materials",
    "ASML": "ASML", "KLAC": "KLA Corp", "LRCX": "Lam Research", "MRVL": "Marvell",
    "MU": "Micron", "ON": "ON Semiconductor", "SMCI": "Super Micro",
    "ARM": "ARM Holdings", "CRWV": "CoreWeave",
    # AI Software / Cloud
    "MSFT": "Microsoft", "GOOGL": "Alphabet", "META": "Meta", "CRM": "Salesforce",
    "NOW": "ServiceNow", "PLTR": "Palantir", "SNOW": "Snowflake",
    "DDOG": "Datadog", "MDB": "MongoDB", "NET": "Cloudflare",
    "ZS": "Zscaler", "CRWD": "CrowdStrike", "PANW": "Palo Alto",
    "ORCL": "Oracle", "IBM": "IBM",
    # Robotics / Agentic
    "PATH": "UiPath", "AMBA": "Ambarella", "IONQ": "IonQ",
    "QUBT": "Quantum Computing", "RGTI": "Rigetti",
    # AI ETF broader
    "SMH": "VanEck Semiconductors ETF", "SOXX": "iShares Semiconductor ETF",
    "XLK": "Technology Sector ETF", "QQQ": "Nasdaq 100 ETF",
}


# ─────────────────────────────────────────────
# AUTH (simple, session-based)
# ─────────────────────────────────────────────

USERS = {
    "joey": hashlib.sha256("weinstein2026".encode()).hexdigest(),
    # Add more users: "username": sha256("password").hexdigest()
}

def check_login(user, pw):
    return USERS.get(user) == hashlib.sha256(pw.encode()).hexdigest()

def login_wall():
    st.markdown(f"<h2>🔒 Portfolio Dashboard</h2>", unsafe_allow_html=True)
    st.markdown(f"<p class='subtext'>Private access only. Contact the admin to get an account.</p>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("login"):
            user = st.text_input("Username")
            pw   = st.text_input("Password", type="password")
            ok   = st.form_submit_button("Log in", use_container_width=True)
            if ok:
                if check_login(user, pw):
                    st.session_state.logged_in   = True
                    st.session_state.current_user = user
                    st.rerun()
                else:
                    st.error("Invalid credentials")


# ─────────────────────────────────────────────
# PORTFOLIO STORAGE (session_state, JSON-ready)
# ─────────────────────────────────────────────

if "portfolios" not in st.session_state:
    # Pre-load Joey's portfolio from screenshots
    st.session_state.portfolios = {
        "joey": [
            {"ticker": "RIVN",  "shares": 1, "avg_cost": 0, "notes": "LEAPS 2027/2028"},
            {"ticker": "MU",    "shares": 1, "avg_cost": 0, "notes": ""},
            {"ticker": "ARM",   "shares": 1, "avg_cost": 0, "notes": ""},
            {"ticker": "RKLB",  "shares": 1, "avg_cost": 0, "notes": ""},
            {"ticker": "CRWV",  "shares": 1, "avg_cost": 0, "notes": ""},
            {"ticker": "BEPC",  "shares": 1, "avg_cost": 0, "notes": ""},
            {"ticker": "BMBL",  "shares": 1, "avg_cost": 0, "notes": ""},
            {"ticker": "SOFI",  "shares": 1, "avg_cost": 0, "notes": ""},
            {"ticker": "UBER",  "shares": 1, "avg_cost": 0, "notes": ""},
            {"ticker": "FOUR",  "shares": 1, "avg_cost": 0, "notes": ""},
            {"ticker": "RBRK",  "shares": 1, "avg_cost": 0, "notes": ""},
            {"ticker": "EOSE",  "shares": 1, "avg_cost": 0, "notes": ""},
        ]
    }


# ─────────────────────────────────────────────
# DATA & INDICATORS
# ─────────────────────────────────────────────

def fetch_weekly(ticker, years=YEARS_OF_DATA):
    end   = datetime.today()
    start = end - timedelta(weeks=years * 52 + 10)
    df = yf.download(ticker, start=start, end=end, interval="1wk",
                     auto_adjust=True, progress=False)
    if df.empty: return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

@st.cache_data(ttl=3600)

@st.cache_data(ttl=24*3600)
def get_sector(ticker):
    MANUAL = {
        "RIVN": "Consumer Discretionary", "RKLB": "Industrials",
        "CRWV": "Technology", "BMBL": "Communication Services",
        "BEPC": "Utilities", "SOFI": "Financials",
        "UBER": "Industrials", "FOUR": "Financials",
        "RBRK": "Technology", "EOSE": "Energy",
        "ARM":  "Technology", "MU":   "Technology",
        "SMCI": "Technology", "IONQ": "Technology",
        "PATH": "Technology", "AMBA": "Technology",
    }
    if ticker in MANUAL:
        return MANUAL[ticker]
    try:
        info = yf.Ticker(ticker).info
        return info.get("sector") or info.get("industry") or "-"
    except:
        return "-"

def get_mcap(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        mc = getattr(info, "market_cap", None)
        if mc and mc > 0:
            if mc >= 1e12: return f"${mc/1e12:.1f}T"
            if mc >= 1e9:  return f"${mc/1e9:.1f}B"
            if mc >= 1e6:  return f"${mc/1e6:.0f}M"
    except: pass
    return "n/a"

@st.cache_data(ttl=300)
def get_price_today(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        return round(float(info.last_price), 2)
    except: return None

def sma(s, w): return s.rolling(w).mean()

def sma_slope(s, lb):
    v = s.dropna().iloc[-lb:]
    if len(v) < lb: return np.nan
    slope, _ = np.polyfit(np.arange(len(v)), v.values, 1)
    return slope / v.iloc[-1]

def rs_line(a, b):
    c = pd.concat([a, b], axis=1).dropna()
    return c.iloc[:, 0] / c.iloc[:, 1]

def rs_score(rs, w=RS_MA_WEEKS):
    if len(rs) < w + 5: return np.nan
    rm = sma(rs, w)
    if pd.isna(rm.iloc[-1]) or rm.iloc[-1] == 0: return np.nan
    above = (rs.iloc[-1] / rm.iloc[-1]) - 1
    past  = rs.iloc[-(w+1)]
    if past == 0 or pd.isna(past): return np.nan
    return round((above + (rs.iloc[-1]/past - 1)) * 100, 2)

def detect_cross(price, ma, weeks):
    c = pd.concat([price, ma], axis=1).dropna().iloc[-(weeks+5):]
    if len(c) < 2: return -1
    above = (c.iloc[:,0] > c.iloc[:,1]).values
    for i in range(len(above)-1, 0, -1):
        if above[i] and not above[i-1]:
            w = len(above)-1-i
            return w if w <= weeks else -1
    return -1

def base_len(close, ma, cross_wks):
    """
    Measure base as: weeks from the last time price was at/above the breakout
    level, going backwards from the breakout point.
    This captures Weinstein's visual base (e.g. ARM's 2-year consolidation)
    rather than just the ±15% SMA band.
    Falls back to SMA-band method if no recent cross.
    """
    if cross_wks < 0:
        # No recent breakout: use SMA band method
        c = pd.concat([close, ma], axis=1).dropna()
        if c.empty: return 0
        idx = len(c) - 1
        weeks = 0
        for i in range(idx, -1, -1):
            p, m = c.iloc[i, 0], c.iloc[i, 1]
            if pd.isna(m) or m == 0: break
            if abs(p / m - 1) <= BASE_RANGE_PCT: weeks += 1
            else: break
        return weeks

    # Breakout-based method: find when price was last at the breakout level
    breakout_idx = len(close) - 1 - cross_wks
    if breakout_idx < 5: return 0
    breakout_price = float(close.iloc[breakout_idx])
    # Walk backwards from breakout: find last week price was >= 90% of breakout price
    # That marks the END of the prior trend (start of the base)
    base_start = 0
    for i in range(breakout_idx - 1, -1, -1):
        p = float(close.iloc[i])
        if p >= breakout_price * 0.92:
            base_start = i
            break
    return breakout_idx - base_start

def bq(w):
    if w < 15: return "Short"
    if w < 40: return "Medium"
    if w < 80: return "Long"
    return "V.Long"

def bo_vol(volume, cross_wks):
    if cross_wks < 0: return None
    idx = len(volume)-1-cross_wks
    if idx < VOLUME_AVG_WEEKS: return None
    bv = float(volume.iloc[idx])
    bl = float(volume.iloc[idx-VOLUME_AVG_WEEKS:idx].mean())
    return round(bv/bl, 2) if bl > 0 else None

def rec_vol(volume, wb=4):
    if len(volume) < VOLUME_AVG_WEEKS+wb: return None
    bl = float(volume.iloc[-(VOLUME_AVG_WEEKS+wb):-wb].mean())
    rc = float(volume.iloc[-wb:].mean())
    return round(rc/bl, 2) if bl > 0 else None

def calc_stop(close, ma):
    cp = float(close.iloc[-1]); cm = float(ma.iloc[-1])
    sl = float(close.iloc[-SWING_LOOKBACK_WEEKS:].min())
    cands = [v for v in [cm, sl] if v < cp and not pd.isna(v)]
    if not cands: return None, None
    stop = max(cands)
    return round(stop, 2), round((stop/cp - 1)*100, 1)

def stage_label(price, ma, slope):
    """Aligned: uses same SLOPE_THRESHOLD as sma_rising."""
    if pd.isna(ma.iloc[-1]) or pd.isna(slope): return "Unknown"
    ab = price.iloc[-1] > ma.iloc[-1]
    if ab and slope > SLOPE_THRESHOLD:      return "Stage 2"
    if ab and slope <= SLOPE_THRESHOLD:     return "Stage 3"
    if not ab and slope < -SLOPE_THRESHOLD: return "Stage 4"
    return "Stage 1"

def evaluate(df, spx_close):
    r = dict(price=None, sma50w=None, pct_above=None, mcap="n/a",
             above_sma=False, sma_rising=False, rs_up=False,
             near_high=False, not_extended=False,
             rs=None, stage="Unknown", cross=-1, early=False,
             vol=None, vol_ok=False, base_w=0, base_q="Short",
             stop=None, risk=None, score=0, label="Not Stage 2",
             early_sig=False, premium=False)
    if df.empty or len(df) < SMA_WEEKS+5: return r
    close = df["Close"]; volume = df["Volume"]
    ma50  = sma(close, SMA_WEEKS)
    cp, cm = float(close.iloc[-1]), float(ma50.iloc[-1])
    if pd.isna(cm): return r
    r["price"] = round(cp, 2); r["sma50w"] = round(cm, 2)
    pct = (cp/cm)-1; r["pct_above"] = round(pct*100, 1)
    slope = sma_slope(ma50, SMA_SLOPE_LOOKBACK)
    r["above_sma"]    = cp > cm
    r["sma_rising"]   = not pd.isna(slope) and slope > SLOPE_THRESHOLD
    rs = rs_line(close, spx_close)
    sc = rs_score(rs)
    r["rs"] = sc; r["rs_up"] = not pd.isna(sc) and sc > 0
    wh = float(close.iloc[-BREAKOUT_LOOKBACK:].max())
    r["near_high"]     = (cp/wh)-1 >= -0.15
    r["not_extended"]  = 0 < pct < MAX_ABOVE_SMA
    r["stage"]         = stage_label(close, ma50, slope)
    cross = detect_cross(close, ma50, RECENT_CROSS_WEEKS)
    r["cross"] = cross; r["early"] = 0 <= cross <= RECENT_CROSS_WEEKS
    bv = bo_vol(volume, cross) if cross >= 0 else None
    rv = rec_vol(volume, 4)
    r["vol"]    = bv if bv is not None else rv
    r["vol_ok"] = r["vol"] is not None and r["vol"] >= VOLUME_BREAKOUT_MULT
    bw = base_len(close, ma50, cross)
    r["base_w"] = bw; r["base_q"] = bq(bw)
    r["stop"], r["risk"] = calc_stop(close, ma50)
    r["score"] = sum([r["above_sma"], r["sma_rising"], r["rs_up"], r["near_high"], r["not_extended"]])
    labels = {5:"STRONG Stage 2", 4:"Stage 2", 3:"Borderline"}
    r["label"] = labels.get(r["score"], "Not Stage 2")
    r["early_sig"] = r["early"] and r["sma_rising"] and r["rs_up"] and r["vol_ok"]
    r["premium"]   = r["early_sig"] and bw >= 40
    return r


# ─────────────────────────────────────────────
# CACHED SCANS
# ─────────────────────────────────────────────

@st.cache_data(ttl=6*3600, show_spinner=False)
def scan_sectors():
    spx_df = fetch_weekly(BENCHMARK)
    if spx_df.empty: return None, None, None
    spx_close = spx_df["Close"]
    spx_ev    = evaluate(spx_df, spx_close)
    spx_ev["ticker"] = "SPY"; spx_ev["name"] = "S&P 500"
    rows = []
    for tk, nm in SECTORS.items():
        df = fetch_weekly(tk)
        if df.empty: continue
        ev = evaluate(df, spx_close)
        ev["ticker"] = tk; ev["name"] = nm
        rows.append(ev)
    sec_df = pd.DataFrame(rows).sort_values(["score","rs"], ascending=[False,False]).reset_index(drop=True)
    return spx_ev, sec_df, spx_close

@st.cache_data(ttl=6*3600, show_spinner=False)
def scan_sector_stocks(spx_close_json):
    spx_close = pd.read_json(StringIO(spx_close_json), typ="series")
    results = {}
    for tk, stocks in SECTOR_STOCKS.items():
        rows = []
        for s in stocks:
            df = fetch_weekly(s)
            if df.empty: continue
            ev = evaluate(df, spx_close)
            ev["ticker"] = s
            rows.append(ev)
        if rows:
            results[tk] = pd.DataFrame(rows).sort_values(
                ["premium","early_sig","score","rs"], ascending=[False,False,False,False]
            ).reset_index(drop=True)
    return results

@st.cache_data(ttl=6*3600, show_spinner=False)
def scan_ai_universe(spx_close_json):
    spx_close = pd.read_json(StringIO(spx_close_json), typ="series")
    rows = []
    for tk, nm in AI_UNIVERSE.items():
        df = fetch_weekly(tk)
        if df.empty: continue
        ev = evaluate(df, spx_close)
        ev["ticker"] = tk; ev["name"] = nm
        rows.append(ev)
    return pd.DataFrame(rows).sort_values(["premium","early_sig","score","rs"], ascending=[False,False,False,False]).reset_index(drop=True)

@st.cache_data(ttl=6*3600, show_spinner=False)
def scan_tickers(tickers_json, spx_close_json):
    tickers   = json.loads(tickers_json)
    spx_close = pd.read_json(StringIO(spx_close_json), typ="series")
    rows = []
    for tk in tickers:
        df = fetch_weekly(tk)
        if df.empty: continue
        ev = evaluate(df, spx_close)
        ev["ticker"] = tk
        rows.append(ev)
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["score","rs"], ascending=[False,False]).reset_index(drop=True)


# ─────────────────────────────────────────────
# DISPLAY HELPERS
# ─────────────────────────────────────────────

def rs_tag(score):
    if score is None or (isinstance(score, float) and np.isnan(score)): return "n/a"
    if score >= 15:  return "▲▲ Strong bull"
    if score >= 5:   return "▲ Bullish"
    if score >= -3:  return "→ Neutral"
    if score >= -15: return "▼ Bearish"
    return "▼▼ Strong bear"

def rs_color_hex(score):
    if score is None or (isinstance(score, float) and np.isnan(score)): return SUBTEXT
    if score >= 15:  return GREEN
    if score >= 5:   return "#88cc88"
    if score >= -3:  return SUBTEXT
    if score >= -15: return "#cc8844"
    return RED

def stage_badge(stage):
    if "Stage 2" in stage: return f'<span class="badge-s2">● S2</span>'
    if "Stage 3" in stage: return f'<span class="badge-s3">● S3</span>'
    if "Stage 4" in stage: return f'<span class="badge-s4">● S4</span>'
    if "Stage 1" in stage: return f'<span class="badge-s1">● S1</span>'
    return f'<span class="badge-s1">?</span>'

def sig_icon(r):
    if r.get("premium"):   return "🟢 PREMIUM"
    if r.get("early_sig"): return "🟡 EARLY"
    if r.get("score",0) >= 4: return "🔵 S2"
    return ""

def fmt(v, sfx="", d=2):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "–"
    return f"{v:.{d}f}{sfx}"

def make_sector_table(df):
    rows = []
    for _, r in df.iterrows():
        vol = r["vol"]
        cross = f"{int(r['cross'])}w" if r.get("cross",-1) >= 0 else "–"
        rows.append({
            "Sector":   r.get("name", r.get("ticker","")),
            "Price":    fmt(r["price"]),
            "%>SMA":    fmt(r["pct_above"],"%",1),
            "RS":       fmt(r["rs"],"",1),
            "RS Trend": rs_tag(r["rs"]),
            "Vol":      fmt(vol,"x",1),
            "Base":     f"{r['base_w']}w",
            "Cross":    cross,
            "Score":    f"{r['score']}/5",
            "Label":    r["label"],
            "Signal":   sig_icon(r),
        })
    return pd.DataFrame(rows)

def make_stock_table(df, show_mcap=False):
    rows = []
    for _, r in df.iterrows():
        vol = r["vol"]
        cross = f"{int(r['cross'])}w" if r.get("cross",-1) >= 0 else "–"
        row = {
            "Ticker":   r["ticker"],
            "Price":    fmt(r["price"]),
            "%>SMA":    fmt(r["pct_above"],"%",1),
            "RS":       fmt(r["rs"],"",1),
            "RS Trend": rs_tag(r["rs"]),
            "Vol":      fmt(vol,"x",1),
            "Base":     f"{r['base_w']}w ({r['base_q']})",
            "Cross":    cross,
            "Stop":     fmt(r["stop"]),
            "Risk":     fmt(r["risk"],"%",1),
            "Stage":    r["stage"],
            "Signal":   sig_icon(r),
        }
        if show_mcap:
            row["Mkt Cap"] = r.get("mcap","n/a")
        rows.append(row)
    return pd.DataFrame(rows)

def signal_card(r, name=""):
    tag  = "PREMIUM" if r.get("premium") else "EARLY"
    cls  = "card-premium" if r.get("premium") else "card-early"
    col  = GREEN if r.get("premium") else YELLOW
    cross = f"{r['cross']}w ago" if r.get("cross",-1) >= 0 else "–"
    nm = name or r.get("name", r.get("ticker",""))
    return f"""
    <div class="{cls}">
      <span style="color:{col};font-weight:700">{tag}</span> &nbsp;
      <strong>{r['ticker']}</strong> {nm} &nbsp;|&nbsp;
      Crossed {cross} &nbsp;|&nbsp; Base {r['base_w']}w ({r['base_q']}) &nbsp;|&nbsp;
      RS {fmt(r['rs'],'',1)} &nbsp;|&nbsp; Vol {fmt(r['vol'],'x',1)} &nbsp;|&nbsp;
      Stop {fmt(r['stop'])} ({fmt(r['risk'],'%',1)})
    </div>"""


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

col_title, col_controls = st.columns([4, 1])
with col_title:
    st.markdown("# 📈 Weinstein Stage Screener")
    st.markdown(f"<span class='subtext'>50w SMA · Relative Strength vs SPX · Volume · Base Length · Stop Levels</span>", unsafe_allow_html=True)

with col_controls:
    mode_label = "☀️ Light" if DARK else "🌙 Dark"
    if st.button(mode_label, use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ─────────────────────────────────────────────
# LOAD CORE DATA
# ─────────────────────────────────────────────

with st.spinner("Loading market data..."):
    spx_ev, sec_df, spx_close = scan_sectors()

if spx_ev is None:
    st.error("Could not load SPY data. Check your internet connection.")
    st.stop()

spx_close_json = spx_close.to_json()

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────

tab_screener, tab_ai, tab_all, tab_portfolio, tab_dashboard = st.tabs([
    "🏦 Sector Screener",
    "🤖 AI Universe",
    "📋 All Stocks",
    "💼 My Portfolio",
    "🔒 Dashboard",
])


# ═══════════════════════════════════════════════
# TAB 1: SECTOR SCREENER
# ═══════════════════════════════════════════════

with tab_screener:

    # Market regime
    st.markdown("### Market Regime")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("SPY Stage",   spx_ev["stage"])
    c2.metric("Price",       fmt(spx_ev["price"]))
    c3.metric("50w SMA",     fmt(spx_ev["sma50w"]))
    c4.metric("% above SMA", fmt(spx_ev["pct_above"],"%",1))
    c5.metric("Stage Score", f"{spx_ev['score']}/5")

    pct = spx_ev.get("pct_above") or 0
    if spx_ev["stage"] not in ("Stage 2",):
        st.markdown(f'<p class="regime-warn">⚠ SPY is not in Stage 2. Per Weinstein, all buy signals should be ignored.</p>', unsafe_allow_html=True)
    elif pct > 10:
        st.markdown(f'<p class="regime-caution">⚡ SPY in Stage 2 but extended ({pct:.1f}% above SMA). EARLY signals rare. Wait for pullback or sector rotation.</p>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="regime-ok">✓ SPY in Stage 2. Buy signals are valid.</p>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Sector Ranking")
    sec_display = make_sector_table(sec_df)
    st.dataframe(sec_display, use_container_width=True, hide_index=True, height=450)

    # Early signals
    st.markdown("---")
    st.markdown("### Early Signals (Sectors)")
    early_secs = sec_df[sec_df["early_sig"]]
    if early_secs.empty:
        st.markdown(f'<div class="card-warn"><strong style="color:{YELLOW}">No fresh sector signals.</strong> Market is mid-trend or extended. Re-check after a 5%+ pullback or sector rotation.</div>', unsafe_allow_html=True)
    else:
        for _, r in early_secs.iterrows():
            st.markdown(signal_card(r, r["name"]), unsafe_allow_html=True)

    # Stocks per sector
    st.markdown("---")
    st.markdown("### Stocks within Top Sectors")
    st.markdown(f"<span class='subtext'>Only stocks with Stage 2 score ≥ 4 shown. Sorted by signal quality.</span>", unsafe_allow_html=True)

    with st.spinner("Scanning stocks in top sectors..."):
        stock_results = scan_sector_stocks(spx_close_json)

    master_premium, master_early = [], []

    for _, sec in sec_df[sec_df["score"] >= 3].head(5).iterrows():
        tk  = sec["ticker"]
        stk = stock_results.get(tk, pd.DataFrame())

        icon  = "🟢" if sec.get("premium") else "🟡" if sec.get("early_sig") else "📊"
        label = f"{icon} {tk} — {sec['name']}  |  RS {fmt(sec['rs'],'',1)}  |  {sec['label']}  |  Base {sec['base_w']}w"
        expanded = bool(sec.get("early_sig") or sec.get("premium"))

        with st.expander(label, expanded=expanded):
            if stk.empty or len(stk[stk["score"] >= 4]) == 0:
                st.caption("No stocks meet Stage 2 threshold in this sector.")
            else:
                filtered = stk[stk["score"] >= 4].head(12)
                tbl = make_stock_table(filtered)
                st.dataframe(tbl, use_container_width=True, hide_index=True)

                for _, r in filtered.iterrows():
                    if r.get("premium"):   master_premium.append((r, sec["name"]))
                    elif r.get("early_sig"): master_early.append((r, sec["name"]))

    # Master shortlist
    st.markdown("---")
    st.markdown("### Master Shortlist — All Signals")
    if not master_premium and not master_early:
        st.info("No PREMIUM or EARLY signals today. Market is mid-trend. Re-run after next sector rotation or pullback.")
    else:
        if master_premium:
            st.markdown("#### 🟢 Premium Signals")
            for r, sname in master_premium:
                st.markdown(signal_card(r, sname), unsafe_allow_html=True)
        if master_early:
            st.markdown("#### 🟡 Early Signals")
            for r, sname in master_early:
                st.markdown(signal_card(r, sname), unsafe_allow_html=True)

    # Legend
    with st.expander("📖 Legend"):
        st.markdown(f"""
| Term | Meaning |
|---|---|
| RS Score | >+15 Strong bull · +5..15 Bullish · -3..+5 Neutral · -15..-3 Bearish · <-15 Strong bear |
| Vol | Breakout-week volume vs 26w avg. ≥1.5x = confirmed. If no recent breakout: 4w avg vs 26w avg |
| Base | Weeks of consolidation. <15 Short · 15-40 Medium · 40-80 Long · 80+ Very Long |
| Cross | Weeks ago price crossed above 50w SMA |
| Stop | Suggested stop = max(50w SMA, 8w swing low) |
| Risk | % below current price that stop sits |
| Stage 3 + S2 score | Stock is above SMA (→ score ≥4) but SMA slope is flat/declining (→ Stage 3). The SMA just stopped rising. This is a yellow flag: position exists but momentum is fading. |
| PREMIUM | Early breakout + base ≥40w. Weinstein's ideal setup |
| EARLY | Recent crossover + rising SMA + RS up + volume confirmed |
| S2 | Stage 2 (4-5 of 5) but no fresh entry — you're late to this move |
        """)
        st.markdown(f"<p class='subtext'>Inspect weekly chart for each PREMIUM/EARLY name. Tight flat base = good. Wide choppy = skip.</p>", unsafe_allow_html=True)

    st.markdown(f"<p class='subtext'>Data cached 6h · Last scan: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC · Weekly closes (Fri)</p>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# TAB 2: AI UNIVERSE
# ═══════════════════════════════════════════════

with tab_ai:
    st.markdown("### 🤖 AI & Semiconductor Universe")
    st.markdown(f"<span class='subtext'>{len(AI_UNIVERSE)} stocks & ETFs filtered through Weinstein Stage criteria. AI infrastructure, chips, cloud, robotics, quantum.</span>", unsafe_allow_html=True)

    # Timeframe context toggle
    col_tf1, col_tf2 = st.columns([3,1])
    with col_tf2:
        show_all_ai = st.toggle("Show all (incl. Stage 1/3/4)", value=False)

    with st.spinner("Scanning AI universe..."):
        ai_df = scan_ai_universe(spx_close_json)

    if not show_all_ai:
        ai_filtered = ai_df[ai_df["score"] >= 3]
    else:
        ai_filtered = ai_df

    # Early/Premium signals first
    ai_signals = ai_df[ai_df["early_sig"] | ai_df["premium"]]
    if not ai_signals.empty:
        st.markdown("#### Signals in AI Universe")
        for _, r in ai_signals.iterrows():
            nm = AI_UNIVERSE.get(r["ticker"], "")
            st.markdown(signal_card(r, nm), unsafe_allow_html=True)
        st.markdown("---")

    # Full table
    st.markdown(f"#### Full AI Ranking ({len(ai_filtered)} names)")
    rows = []
    for _, r in ai_filtered.iterrows():
        vol = r["vol"]
        cross = f"{int(r['cross'])}w" if r.get("cross",-1) >= 0 else "–"
        rows.append({
            "Ticker":   r["ticker"],
            "Name":     AI_UNIVERSE.get(r["ticker"], r.get("name","")),
            "Price":    fmt(r["price"]),
            "%>SMA":    fmt(r["pct_above"],"%",1),
            "RS":       fmt(r["rs"],"",1),
            "RS Trend": rs_tag(r["rs"]),
            "Vol":      fmt(vol,"x",1),
            "Base":     f"{r['base_w']}w",
            "Cross":    cross,
            "Stop":     fmt(r["stop"]),
            "Risk":     fmt(r["risk"],"%",1),
            "Stage":    r["stage"],
            "Score":    f"{r['score']}/5",
            "Signal":   sig_icon(r),
        })
    ai_tbl = pd.DataFrame(rows)
    st.dataframe(ai_tbl, use_container_width=True, hide_index=True, height=600)

    st.markdown(f"<p class='subtext'>Stage 3 + high score = above SMA but momentum fading. Stage 2 + EARLY = active breakout with volume. Always check weekly chart.</p>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# TAB 3: ALL STOCKS
# ═══════════════════════════════════════════════

with tab_all:
    st.markdown("### 📋 All Stocks — Cross-Sector View")
    st.markdown(f"<span class='subtext'>All ~290 stocks across 11 sectors. Shows sector context + Weinstein stage per stock.</span>", unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        min_score = st.selectbox("Min Stage 2 Score", [0,1,2,3,4,5], index=2)
    with col_f2:
        sig_filter = st.selectbox("Signal filter", ["All","PREMIUM only","EARLY+","Stage 2+"])
    with col_f3:
        sec_filter = st.selectbox("Sector", ["All"] + list(SECTORS.values()))

    with st.spinner("Compiling all stocks..."):
        all_rows = []
        for sec_tk, sec_name in SECTORS.items():
            stk = stock_results.get(sec_tk, pd.DataFrame())
            if stk.empty: continue
            for _, r in stk.iterrows():
                r2 = r.to_dict()
                r2["sector"] = sec_name
                r2["sec_tk"] = sec_tk
                all_rows.append(r2)

    if all_rows:
        all_df = pd.DataFrame(all_rows)
        # Filter
        all_df = all_df[all_df["score"] >= min_score]
        if sig_filter == "PREMIUM only":
            all_df = all_df[all_df["premium"]]
        elif sig_filter == "EARLY+":
            all_df = all_df[all_df["early_sig"] | all_df["premium"]]
        elif sig_filter == "Stage 2+":
            all_df = all_df[all_df["score"] >= 4]
        if sec_filter != "All":
            all_df = all_df[all_df["sector"] == sec_filter]

        all_df = all_df.sort_values(["premium","early_sig","score","rs"], ascending=[False,False,False,False]).reset_index(drop=True)

        display_rows = []
        for _, r in all_df.iterrows():
            vol   = r["vol"]
            cross = f"{int(r['cross'])}w" if r.get("cross",-1) >= 0 else "–"
            display_rows.append({
                "Ticker":  r["ticker"],
                "Sector":  r.get("sector",""),
                "Price":   fmt(r["price"]),
                "%>SMA":   fmt(r["pct_above"],"%",1),
                "RS":      fmt(r["rs"],"",1),
                "RS Trend":rs_tag(r["rs"]),
                "Sec RS":  rs_tag(sec_df[sec_df["ticker"]==r.get("sec_tk","")]["rs"].values[0] if r.get("sec_tk","") in sec_df["ticker"].values else None),
                "Vol":     fmt(vol,"x",1),
                "Base":    f"{r['base_w']}w",
                "Cross":   cross,
                "Stop":    fmt(r["stop"]),
                "Risk":    fmt(r["risk"],"%",1),
                "Stage":   r["stage"],
                "Score":   f"{r['score']}/5",
                "Signal":  sig_icon(r),
            })

        disp = pd.DataFrame(display_rows)
        st.markdown(f"<span class='subtext'>{len(disp)} stocks shown</span>", unsafe_allow_html=True)
        st.dataframe(disp, use_container_width=True, hide_index=True, height=700)
    else:
        st.info("Scan the Sector Screener tab first to load stock data.")


# ═══════════════════════════════════════════════
# TAB 4: MY PORTFOLIO
# ═══════════════════════════════════════════════

with tab_portfolio:
    st.markdown("### 💼 Portfolio Analyzer")
    st.markdown(f"<span class='subtext'>Enter your tickers to see their Weinstein stage, RS, sector, and stop levels.</span>", unsafe_allow_html=True)

    col_input, col_btn = st.columns([4,1])
    with col_input:
        default_tickers = "RIVN, RKLB, MU, ARM, CRWV, BEPC, BMBL, SOFI, UBER, FOUR, RBRK, EOSE"
        tickers_raw = st.text_input("Your tickers (comma-separated)", value=default_tickers)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_port = st.button("Scan portfolio", use_container_width=True)

    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]

    # Sector mapping for common stocks
    TICKER_SECTOR = {}
    for sec_tk, stocks in SECTOR_STOCKS.items():
        for s in stocks:
            TICKER_SECTOR[s] = SECTORS.get(sec_tk, sec_tk)
    for tk in AI_UNIVERSE:
        if tk not in TICKER_SECTOR:
            TICKER_SECTOR[tk] = "AI/Tech"

    with st.spinner(f"Scanning {len(tickers)} positions..."):
        port_df = scan_tickers(json.dumps(tickers), spx_close_json)

    if port_df.empty:
        st.warning("Could not load data for the provided tickers. Check ticker symbols.")
    else:
        # Summary metrics
        n_s2 = len(port_df[port_df["score"] >= 4])
        n_s4 = len(port_df[port_df["stage"].str.contains("Stage 4", na=False)])
        n_sig= len(port_df[port_df["early_sig"] | port_df["premium"]])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Positions",     len(port_df))
        m2.metric("In Stage 2",    n_s2, f"{n_s2/len(port_df)*100:.0f}%")
        m3.metric("In Stage 4",    n_s4, delta=f"{n_s4} avoid" if n_s4 > 0 else "None", delta_color="inverse")
        m4.metric("Buy signals",   n_sig)

        st.markdown("---")
        st.markdown("#### Position Detail")

        rows = []
        for _, r in port_df.iterrows():
            tk    = r["ticker"]
            sec   = TICKER_SECTOR.get(tk) or get_sector(tk)
            vol   = r["vol"]
            cross = f"{int(r['cross'])}w" if r.get("cross",-1) >= 0 else "–"

            # Stage color note
            stage_note = ""
            if "Stage 4" in r["stage"]: stage_note = "⚠ SELL CANDIDATE"
            elif "Stage 3" in r["stage"]: stage_note = "⚡ WATCH CLOSELY"

            rows.append({
                "Ticker":   tk,
                "Sector":   sec,
                "Price":    fmt(r["price"]),
                "%>SMA":    fmt(r["pct_above"],"%",1),
                "RS":       fmt(r["rs"],"",1),
                "RS Trend": rs_tag(r["rs"]),
                "Vol":      fmt(vol,"x",1),
                "Base":     f"{r['base_w']}w",
                "Stage":    r["stage"],
                "Score":    f"{r['score']}/5",
                "Stop":     fmt(r["stop"]),
                "Risk":     fmt(r["risk"],"%",1),
                "Signal":   sig_icon(r) if sig_icon(r) else stage_note,
            })

        port_tbl = pd.DataFrame(rows)
        st.dataframe(port_tbl, use_container_width=True, hide_index=True)

        # Warnings
        st.markdown("---")
        stage4 = port_df[port_df["stage"].str.contains("Stage 4", na=False)]
        stage3 = port_df[port_df["stage"].str.contains("Stage 3", na=False)]

        if not stage4.empty:
            st.markdown("#### ⚠️ Stage 4 Positions — Weinstein says exit")
            for _, r in stage4.iterrows():
                st.markdown(f"""<div class="card-warn">
                    <strong style="color:{RED}">STAGE 4</strong> &nbsp;
                    <strong>{r['ticker']}</strong> &nbsp;|&nbsp; Price {fmt(r['price'])} &nbsp;|&nbsp;
                    {fmt(r['pct_above'],'%',1)} vs SMA &nbsp;|&nbsp; RS {fmt(r['rs'],'',1)} ({rs_tag(r['rs'])})
                </div>""", unsafe_allow_html=True)

        if not stage3.empty:
            st.markdown("#### ⚡ Stage 3 Positions — Monitor for deterioration")
            for _, r in stage3.iterrows():
                st.markdown(f"""<div class="card-warn">
                    <strong style="color:{YELLOW}">STAGE 3</strong> &nbsp;
                    <strong>{r['ticker']}</strong> &nbsp;|&nbsp; Price {fmt(r['price'])} &nbsp;|&nbsp;
                    {fmt(r['pct_above'],'%',1)} vs SMA &nbsp;|&nbsp; RS {fmt(r['rs'],'',1)} ({rs_tag(r['rs'])})
                </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# TAB 5: DASHBOARD (login-protected)
# ═══════════════════════════════════════════════

@st.cache_data(ttl=3600)
def get_portfolio_history(tickers_json, period="1y"):
    """Fetch daily closing prices for portfolio tickers."""
    tickers = json.loads(tickers_json)
    end   = datetime.today()
    start = end - timedelta(days=365)
    try:
        raw = yf.download(tickers, start=start, end=end,
                          auto_adjust=True, progress=False)["Close"]
        if isinstance(raw, pd.Series):
            raw = raw.to_frame(tickers[0])
        return raw.ffill()
    except:
        return pd.DataFrame()

def calc_period_return(hist, tickers, cost_map, label):
    """Calculate portfolio return over a period relative to today."""
    if hist.empty: return None
    periods = {"1D": 1, "1W": 5, "1M": 21, "3M": 63, "YTD": None}
    n = periods.get(label)
    if label == "YTD":
        start_of_year = pd.Timestamp(datetime.today().year, 1, 1)
        hist_filtered = hist[hist.index >= start_of_year]
        if hist_filtered.empty: return None
        start_prices = hist_filtered.iloc[0]
    elif n is None:
        return None
    else:
        if len(hist) < n + 1: return None
        start_prices = hist.iloc[-(n+1)]
    end_prices = hist.iloc[-1]
    total_start = 0; total_end = 0
    for tk in tickers:
        if tk not in hist.columns: continue
        sh, ac = cost_map.get(tk, (1, 1))
        sp = float(start_prices.get(tk, 0)) if tk in start_prices.index else 0
        ep = float(end_prices.get(tk, 0)) if tk in end_prices.index else 0
        if sp > 0 and ep > 0:
            total_start += sp * sh
            total_end   += ep * sh
    if total_start == 0: return None
    return (total_end / total_start - 1) * 100

with tab_dashboard:
    if not st.session_state.get("logged_in"):
        login_wall()
    else:
        import plotly.graph_objects as go
        import plotly.express as px

        user      = st.session_state.current_user
        portfolio = st.session_state.portfolios.get(user, [])

        col_dash, col_logout = st.columns([5,1])
        with col_dash:
            st.markdown(f"### 🏛 Portfolio Dashboard — {user.title()}")
        with col_logout:
            if st.button("Log out"):
                st.session_state.logged_in = False
                st.rerun()

        # Manage positions
        with st.expander("➕ Manage positions"):
            col_a, col_b, col_c, col_d = st.columns(4)
            new_tk   = col_a.text_input("Ticker").upper().strip()
            new_sh   = col_b.number_input("Shares", min_value=0.0, step=0.01, value=1.0)
            new_cost = col_c.number_input("Avg cost ($)", min_value=0.0, step=0.01, value=0.0)
            new_note = col_d.text_input("Notes")
            if st.button("Add position"):
                if new_tk:
                    portfolio.append({"ticker": new_tk, "shares": new_sh,
                                      "avg_cost": new_cost, "notes": new_note})
                    st.session_state.portfolios[user] = portfolio
                    st.success(f"Added {new_tk}")
                    st.rerun()
            if portfolio:
                for i, pos in enumerate(portfolio):
                    c1,c2,c3,c4,c5 = st.columns([2,1,2,3,1])
                    c1.markdown(f"**{pos['ticker']}**")
                    c2.markdown(f"{pos['shares']} sh")
                    c3.markdown(f"Avg ${pos['avg_cost']:.2f}" if pos['avg_cost'] > 0 else "–")
                    c4.markdown(pos.get("notes",""))
                    if c5.button("🗑", key=f"del_{i}"):
                        portfolio.pop(i); st.session_state.portfolios[user] = portfolio; st.rerun()

        if not portfolio:
            st.info("Add positions above to get started.")
        else:
            tickers   = [p["ticker"] for p in portfolio]
            cost_map  = {p["ticker"]: (p["shares"], p["avg_cost"]) for p in portfolio}

            with st.spinner("Loading portfolio..."):
                port_df  = scan_tickers(json.dumps(tickers), spx_close_json)
                hist     = get_portfolio_history(json.dumps(tickers))

            if port_df.empty:
                st.warning("Could not load data.")
            else:
                # ── Compute current values ──
                position_data = []
                total_value = 0; total_cost = 0

                for _, r in port_df.iterrows():
                    tk = r["ticker"]
                    sh, ac = cost_map.get(tk, (1, 0))
                    price = r["price"] or 0
                    val   = price * sh
                    cost  = ac * sh
                    pnl   = val - cost if ac > 0 else None
                    pnl_pct = (val/cost - 1)*100 if (ac > 0 and cost > 0) else None
                    total_value += val
                    if ac > 0: total_cost += cost
                    position_data.append({"r": r, "sh": sh, "ac": ac,
                                          "val": val, "pnl": pnl, "pnl_pct": pnl_pct})

                total_pnl     = total_value - total_cost if total_cost > 0 else None
                total_pnl_pct = (total_value/total_cost - 1)*100 if total_cost > 0 else None

                # ── Period returns ──
                periods = ["1D","1W","1M","3M","YTD"]
                period_rets = {p: calc_period_return(hist, tickers, cost_map, p) for p in periods}

                # ── TOP BAR METRICS ──
                st.markdown("---")
                cols = st.columns(7)
                cols[0].metric("Positions", len(portfolio))
                cols[1].metric("Total Value", f"${total_value:,.0f}" if total_value > 0 else "–")
                if total_pnl is not None:
                    cols[2].metric("Total P&L", f"${total_pnl:+,.0f}",
                                   f"{total_pnl_pct:+.1f}%",
                                   delta_color="normal")
                for i, p in enumerate(["1D","1W","1M","YTD"]):
                    ret = period_rets.get(p)
                    val_str = f"{ret:+.2f}%" if ret is not None else "–"
                    cols[3+i].metric(p, val_str,
                                     delta_color="normal" if ret and ret >= 0 else "inverse")

                st.markdown("---")

                # ── CHARTS ROW ──
                chart_col, dist_col = st.columns([3, 2])

                # Performance chart
                with chart_col:
                    st.markdown("#### Performance")
                    if not hist.empty:
                        # Compute combined portfolio value over time
                        port_hist = pd.Series(dtype=float)
                        base_val  = 0
                        for tk in tickers:
                            if tk not in hist.columns: continue
                            sh, ac = cost_map.get(tk, (1, 0))
                            if ac > 0:
                                base_val += ac * sh
                        if base_val > 0:
                            daily_vals = pd.Series(0.0, index=hist.index)
                            for tk in tickers:
                                if tk not in hist.columns: continue
                                sh, ac = cost_map.get(tk, (1, 0))
                                if ac > 0:
                                    daily_vals += hist[tk].fillna(method="ffill") * sh
                            pct_series = (daily_vals / base_val - 1) * 100
                            spx_hist = hist.get("SPY")
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=pct_series.index, y=pct_series.values,
                                mode="lines", name="Portfolio",
                                line=dict(color="#60a5fa", width=2),
                                fill="tozeroy",
                                fillcolor="rgba(96,165,250,0.08)"
                            ))
                            fig.add_hline(y=0, line_dash="dash",
                                          line_color="rgba(255,255,255,0.2)", line_width=1)
                            fig.update_layout(
                                height=280,
                                margin=dict(l=0,r=0,t=10,b=0),
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                font=dict(color=TEXT, family="Syne"),
                                xaxis=dict(showgrid=False, color=SUBTEXT, tickfont=dict(size=10)),
                                yaxis=dict(showgrid=True, gridcolor=BORDER,
                                           tickformat="+.1f", ticksuffix="%",
                                           color=SUBTEXT, tickfont=dict(size=10)),
                                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
                                hovermode="x unified",
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.caption("Add avg costs to see performance chart.")
                    else:
                        st.caption("Performance history unavailable.")

                # Distribution treemap
                with dist_col:
                    st.markdown("#### Distribution")
                    if position_data:
                        tree_labels  = [pd_["r"]["ticker"] for pd_ in position_data if pd_["val"] > 0]
                        tree_values  = [pd_["val"] for pd_ in position_data if pd_["val"] > 0]
                        tree_pnl     = [pd_["pnl_pct"] for pd_ in position_data if pd_["val"] > 0]
                        tree_colors  = []
                        for p in tree_pnl:
                            if p is None: tree_colors.append(0)
                            else: tree_colors.append(p)
                        fig2 = go.Figure(go.Treemap(
                            labels=tree_labels,
                            parents=[""] * len(tree_labels),
                            values=tree_values,
                            customdata=[[f"{p:+.1f}%" if p is not None else "–"] for p in tree_pnl],
                            texttemplate="<b>%{label}</b><br>%{customdata[0]}",
                            marker=dict(
                                colors=tree_colors,
                                colorscale=[[0,"#7f1d1d"],[0.5,"#1e2130"],[1,"#14532d"]],
                                cmid=0,
                                showscale=False,
                            ),
                        ))
                        fig2.update_layout(
                            height=280, margin=dict(l=0,r=0,t=0,b=0),
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="white", family="Syne", size=12),
                        )
                        st.plotly_chart(fig2, use_container_width=True)

                st.markdown("---")

                # ── POSITION GRID ──
                st.markdown("#### Positions")
                sorted_pos = sorted(position_data,
                                    key=lambda x: (x["r"]["score"], x["r"]["rs"] or -99),
                                    reverse=True)

                # 3-column grid
                cols3 = st.columns(3)
                for i, pd_ in enumerate(sorted_pos):
                    r       = pd_["r"]
                    tk      = r["ticker"]
                    sh      = pd_["sh"]
                    ac      = pd_["ac"]
                    val     = pd_["val"]
                    pnl     = pd_["pnl"]
                    pnl_pct = pd_["pnl_pct"]
                    stage   = r["stage"]

                    if "Stage 2" in stage:   s_color = GREEN;  s_dot = "🟢"
                    elif "Stage 3" in stage: s_color = YELLOW; s_dot = "🟡"
                    elif "Stage 4" in stage: s_color = RED;    s_dot = "🔴"
                    else:                    s_color = BLUE;   s_dot = "🔵"

                    pnl_html = ""
                    if pnl is not None:
                        pc = GREEN if pnl >= 0 else RED
                        sign = "+" if pnl >= 0 else ""
                        pnl_html = f'<span style="color:{pc};font-weight:700">{sign}${pnl:,.0f} ({pnl_pct:+.1f}%)</span>'

                    sig = sig_icon(r)

                    with cols3[i % 3]:
                        st.markdown(f"""
                        <div style="background:{CARD};border:1px solid {BORDER};border-radius:10px;
                             padding:14px 16px;margin-bottom:10px;">
                          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                            <span style="font-size:1.1rem;font-weight:800">{s_dot} {tk}</span>
                            <span style="color:{SUBTEXT};font-size:0.8rem">{sh:.0f} sh</span>
                          </div>
                          <div style="font-size:1.4rem;font-weight:700;margin-bottom:2px">${r['price'] or 0:,.2f}</div>
                          <div style="font-size:0.82rem;margin-bottom:8px">{pnl_html if pnl_html else f'<span style="color:{SUBTEXT}">No cost basis</span>'}</div>
                          <div style="font-size:0.78rem;color:{SUBTEXT};line-height:1.6">
                            <span style="color:{s_color}">{stage}</span> · Score {r['score']}/5<br>
                            RS {fmt(r['rs'],'',1)} · {fmt(r['pct_above'],'%',1)} vs SMA<br>
                            Stop: {fmt(r['stop'])} ({fmt(r['risk'],'%',1)})<br>
                            {f'<strong style="color:{GREEN}">{sig}</strong>' if sig else ''}
                          </div>
                        </div>""", unsafe_allow_html=True)

                # ── STAGE 4 WARNINGS ──
                s4_pos = [pd_ for pd_ in position_data if "Stage 4" in pd_["r"]["stage"]]
                if s4_pos:
                    st.markdown("---")
                    st.markdown("#### ⚠️ Action Required — Stage 4 Positions")
                    for pd_ in s4_pos:
                        r = pd_["r"]
                        note = ""
                        rs = r["rs"]
                        if rs is not None and not (isinstance(rs, float) and pd.isna(rs)) and rs > 5:
                            note = f" · <em>Note: High RS ({rs:+.0f}) = temporary bounce in downtrend, not a buy signal.</em>"
                        st.markdown(f"""<div class="card-warn">
                            <strong style="color:{RED}">STAGE 4 — EXIT</strong> &nbsp;
                            <strong>{r['ticker']}</strong> &nbsp;|&nbsp;
                            ${r['price'] or 0:,.2f} &nbsp;|&nbsp;
                            {fmt(r['pct_above'],'%',1)} vs SMA &nbsp;|&nbsp;
                            RS {fmt(r['rs'],'',1)} ({rs_tag(r['rs'])})
                            {note}
                        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────

st.markdown(f"""
<p class="footer">
  Weinstein Stage Screener v4 · Built on Stan Weinstein's Stage Analysis methodology ·
  Data via Yahoo Finance · Not financial advice · Weekly closes (Friday) ·
  Cache: 6h sectors, 1h prices · © 2026
</p>
""", unsafe_allow_html=True)
