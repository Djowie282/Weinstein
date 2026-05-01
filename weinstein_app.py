"""
Weinstein Screener - Streamlit Web App
Run locally:  streamlit run weinstein_app.py
Deploy free:  https://streamlit.io/cloud
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Weinstein Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { color: #f0f0f0; font-family: 'Courier New', monospace; letter-spacing: 0.05em; }
    h2, h3 { color: #c8c8c8; }
    .signal-premium {
        background: linear-gradient(90deg, #1a3a1a, #0e1117);
        border-left: 3px solid #00ff88;
        padding: 0.6rem 1rem;
        border-radius: 4px;
        margin: 0.3rem 0;
        font-family: monospace;
    }
    .signal-early {
        background: linear-gradient(90deg, #2a2a1a, #0e1117);
        border-left: 3px solid #ffdd44;
        padding: 0.6rem 1rem;
        border-radius: 4px;
        margin: 0.3rem 0;
        font-family: monospace;
    }
    .market-ok { color: #00ff88; font-weight: bold; }
    .market-warn { color: #ff6644; font-weight: bold; }
    .market-caution { color: #ffdd44; font-weight: bold; }
    .stExpander { border: 1px solid #2a2a2a !important; }
    div[data-testid="metric-container"] {
        background: #1a1a2e;
        border: 1px solid #2a2a3e;
        border-radius: 6px;
        padding: 0.5rem 1rem;
    }
    .footer { color: #555; font-size: 0.75rem; text-align: center; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

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
MAX_STOCKS_SHOWN     = 12
MIN_STAGE2_SHOWN     = 4

SECTORS = {
    "XLK": "Technology", "XLF": "Financials", "XLE": "Energy",
    "XLV": "Health Care", "XLI": "Industrials", "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples", "XLU": "Utilities", "XLRE": "Real Estate",
    "XLB": "Materials", "XLC": "Communication Services",
}

SECTOR_STOCKS = {
    "XLK":  ["AAPL","NVDA","MSFT","AVGO","ORCL","CRM","AMD","ACN","ADBE","CSCO",
              "NOW","PANW","FTNT","SNPS","CDNS","AMAT","KLAC","LRCX","MU","TXN","QCOM",
              "ANET","MCHP","ADI","MRVL","ON","ZS","NET","DDOG","MDB","SNOW","PLTR","CRWD"],
    "XLF":  ["BRK-B","JPM","V","MA","BAC","GS","MS","WFC","SPGI","BLK",
              "AXP","C","USB","PNC","TFC","SCHW","COF","CME","ICE","MMC",
              "AON","MET","PRU","AFL","ALL","TRV","RJF","MTB"],
    "XLE":  ["XOM","CVX","COP","EOG","SLB","MPC","PSX","OXY","VLO","WMB",
              "HES","KMI","OKE","BKR","FANG","DVN","HAL","CTRA","OVV","EQT",
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


# ---------------------------------------------------------------------------
# Screener logic (cached 6 hours so visitors don't re-trigger scans)
# ---------------------------------------------------------------------------

def fetch_weekly(ticker, years=YEARS_OF_DATA):
    end   = datetime.today()
    start = end - timedelta(weeks=years * 52 + 10)
    df = yf.download(ticker, start=start, end=end, interval="1wk",
                     auto_adjust=True, progress=False)
    if df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()


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
    past  = rs.iloc[-(w + 1)]
    if past == 0 or pd.isna(past): return np.nan
    return round((above + (rs.iloc[-1] / past - 1)) * 100, 2)

def detect_cross(price, ma, weeks):
    c = pd.concat([price, ma], axis=1).dropna().iloc[-(weeks + 5):]
    if len(c) < 2: return -1
    above = (c.iloc[:, 0] > c.iloc[:, 1]).values
    for i in range(len(above) - 1, 0, -1):
        if above[i] and not above[i-1]:
            w = len(above) - 1 - i
            return w if w <= weeks else -1
    return -1

def base_len(close, ma, cross_wks, max_pct=BASE_RANGE_PCT):
    c = pd.concat([close, ma], axis=1).dropna()
    if c.empty: return 0
    idx = len(c) - 2 - cross_wks if cross_wks >= 0 else len(c) - 1
    if idx < 0: return 0
    weeks = 0
    for i in range(idx, -1, -1):
        p, m = c.iloc[i, 0], c.iloc[i, 1]
        if pd.isna(m) or m == 0: break
        if abs(p / m - 1) <= max_pct: weeks += 1
        else: break
    return weeks

def bq(w):
    if w < 15:  return "Short"
    if w < 40:  return "Medium"
    if w < 80:  return "Long"
    return "V.Long"

def bo_vol(volume, cross_wks):
    if cross_wks < 0: return None
    idx = len(volume) - 1 - cross_wks
    if idx < VOLUME_AVG_WEEKS: return None
    bv = float(volume.iloc[idx])
    bl = float(volume.iloc[idx - VOLUME_AVG_WEEKS:idx].mean())
    return round(bv / bl, 2) if bl > 0 else None

def rec_vol(volume, wb=4):
    if len(volume) < VOLUME_AVG_WEEKS + wb: return None
    bl = float(volume.iloc[-(VOLUME_AVG_WEEKS + wb):-wb].mean())
    rc = float(volume.iloc[-wb:].mean())
    return round(rc / bl, 2) if bl > 0 else None

def calc_stop(close, ma):
    cp = float(close.iloc[-1])
    cm = float(ma.iloc[-1])
    sl = float(close.iloc[-SWING_LOOKBACK_WEEKS:].min())
    cands = [v for v in [cm, sl] if v < cp and not pd.isna(v)]
    if not cands: return None, None
    stop = max(cands)
    return round(stop, 2), round((stop / cp - 1) * 100, 1)

def stage_label(price, ma, slope):
    if pd.isna(ma.iloc[-1]) or pd.isna(slope): return "Unknown"
    ab = price.iloc[-1] > ma.iloc[-1]
    if ab and slope > 0.001:     return "Stage 2"
    if ab and slope <= 0.001:    return "Stage 3"
    if not ab and slope < -0.001: return "Stage 4"
    return "Stage 1"

def evaluate(df, spx_close):
    r = dict(price=None, sma50w=None, pct_above=None,
             above_sma=False, sma_rising=False, rs_up=False,
             near_high=False, not_extended=False,
             rs=None, stage=None, cross=-1, early=False,
             vol=None, vol_ok=False, base_w=0, base_q="Short",
             stop=None, risk=None, score=0, label="Not Stage 2",
             early_sig=False, premium=False)
    if df.empty or len(df) < SMA_WEEKS + 5: return r
    close  = df["Close"]
    volume = df["Volume"]
    ma50   = sma(close, SMA_WEEKS)
    cp, cm = float(close.iloc[-1]), float(ma50.iloc[-1])
    if pd.isna(cm): return r
    r["price"] = round(cp, 2)
    r["sma50w"] = round(cm, 2)
    pct = (cp / cm) - 1
    r["pct_above"] = round(pct * 100, 1)
    r["above_sma"] = cp > cm
    slope = sma_slope(ma50, SMA_SLOPE_LOOKBACK)
    r["sma_rising"] = not pd.isna(slope) and slope > 0
    rs = rs_line(close, spx_close)
    sc = rs_score(rs)
    r["rs"] = sc
    r["rs_up"] = not pd.isna(sc) and sc > 0
    wh = float(close.iloc[-BREAKOUT_LOOKBACK:].max())
    r["near_high"] = (cp / wh) - 1 >= -0.15
    r["not_extended"] = 0 < pct < MAX_ABOVE_SMA
    r["stage"] = stage_label(close, ma50, slope)
    cross = detect_cross(close, ma50, RECENT_CROSS_WEEKS)
    r["cross"] = cross
    r["early"] = 0 <= cross <= RECENT_CROSS_WEEKS
    bv = bo_vol(volume, cross) if cross >= 0 else None
    rv = rec_vol(volume, 4)
    r["vol"] = bv if bv is not None else rv
    r["vol_ok"] = r["vol"] is not None and r["vol"] >= VOLUME_BREAKOUT_MULT
    bw = base_len(close, ma50, cross)
    r["base_w"] = bw
    r["base_q"] = bq(bw)
    r["stop"], r["risk"] = calc_stop(close, ma50)
    r["score"] = sum([r["above_sma"], r["sma_rising"], r["rs_up"], r["near_high"], r["not_extended"]])
    labels = {5: "STRONG Stage 2", 4: "Stage 2", 3: "Borderline"}
    r["label"] = labels.get(r["score"], "Not Stage 2")
    r["early_sig"] = r["early"] and r["sma_rising"] and r["rs_up"] and r["vol_ok"]
    r["premium"] = r["early_sig"] and bw >= 40
    return r


@st.cache_data(ttl=6*3600, show_spinner=False)
def run_full_scan():
    spx_df = fetch_weekly(BENCHMARK)
    if spx_df.empty:
        return None, None, None, None
    spx_close = spx_df["Close"]
    spx_ev    = evaluate(spx_df, spx_close)

    sec_rows = []
    for tk, nm in SECTORS.items():
        df = fetch_weekly(tk)
        if df.empty: continue
        ev = evaluate(df, spx_close)
        ev["ticker"] = tk
        ev["name"]   = nm
        sec_rows.append(ev)

    sec_df = pd.DataFrame(sec_rows).sort_values(
        ["score", "rs"], ascending=[False, False]).reset_index(drop=True)

    stock_results = {}
    for _, sec in sec_df[sec_df["score"] >= 3].head(5).iterrows():
        tk = sec["ticker"]
        rows = []
        for s in SECTOR_STOCKS.get(tk, []):
            df = fetch_weekly(s)
            if df.empty: continue
            ev = evaluate(df, spx_close)
            ev["ticker"] = s
            rows.append(ev)
        stk = pd.DataFrame(rows)
        stk = stk[stk["score"] >= MIN_STAGE2_SHOWN].sort_values(
            ["premium", "early_sig", "score", "rs"],
            ascending=[False, False, False, False]
        ).head(MAX_STOCKS_SHOWN).reset_index(drop=True)
        stock_results[tk] = stk

    return spx_ev, sec_df, stock_results, datetime.now()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rs_color(score):
    if score is None or pd.isna(score): return "#888"
    if score >= 15: return "#00ff88"
    if score >= 5:  return "#88ffaa"
    if score >= -3: return "#cccc88"
    if score >= -15: return "#ff9966"
    return "#ff4444"

def rs_tag(score):
    if score is None or pd.isna(score): return "n/a"
    if score >= 15:  return "STRONG bull"
    if score >= 5:   return "Bullish"
    if score >= -3:  return "Neutral"
    if score >= -15: return "Bearish"
    return "STRONG bear"

def fmt(v, sfx="", d=2):
    if v is None or (isinstance(v, float) and pd.isna(v)): return "n/a"
    return f"{v:.{d}f}{sfx}"

def sig_badge(row):
    if row.get("premium"): return "🟢 PREMIUM"
    if row.get("early_sig"): return "🟡 EARLY"
    if row.get("score", 0) >= 4: return "⚪ S2"
    return ""

def style_sec_table(df):
    display = pd.DataFrame({
        "Sector":  df["name"],
        "Price":   df["price"].apply(lambda x: fmt(x)),
        "%>SMA":   df["pct_above"].apply(lambda x: fmt(x, "%", 1)),
        "RS":      df["rs"].apply(lambda x: fmt(x, "", 1)),
        "RS Label": df["rs"].apply(rs_tag),
        "Vol":     df["vol"].apply(lambda x: fmt(x, "x", 1)),
        "Base":    df["base_w"].apply(lambda x: f"{x}w"),
        "Cross":   df["cross"].apply(lambda x: f"{x}w ago" if x >= 0 else "-"),
        "Score":   df["score"].apply(lambda x: f"{x}/5"),
        "Stage":   df["label"],
    })
    return display

def style_stk_table(df):
    display = pd.DataFrame({
        "Ticker":  df["ticker"],
        "Price":   df["price"].apply(lambda x: fmt(x)),
        "%>SMA":   df["pct_above"].apply(lambda x: fmt(x, "%", 1)),
        "RS":      df["rs"].apply(lambda x: fmt(x, "", 1)),
        "RS Label": df["rs"].apply(rs_tag),
        "Vol":     df["vol"].apply(lambda x: fmt(x, "x", 1)),
        "Base":    df["base_w"].apply(lambda x: f"{x}w"),
        "Cross":   df["cross"].apply(lambda x: f"{x}w ago" if x >= 0 else "-"),
        "Stop":    df["stop"].apply(lambda x: fmt(x)),
        "Risk":    df["risk"].apply(lambda x: fmt(x, "%", 1)),
        "Stage":   df["stage"],
        "Signal":  df.apply(sig_badge, axis=1),
    })
    return display


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.markdown("# 📈 Weinstein Stage Screener")
st.markdown("**50-week SMA | Relative Strength vs SPX | Volume | Base Length | Stops**")
st.markdown("---")

col_info, col_btn = st.columns([4, 1])
with col_btn:
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with st.spinner("Running scan... this takes 2 to 4 minutes on first load"):
    spx_ev, sec_df, stock_results, scan_time = run_full_scan()

if spx_ev is None:
    st.error("Could not fetch market data. Check your connection.")
    st.stop()

st.caption(f"Data cached at {scan_time.strftime('%Y-%m-%d %H:%M')} UTC | Refreshes every 6 hours | Weekly data (Friday close)")

# ---- MARKET REGIME ----

st.markdown("### Market Regime (SPY)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Stage", spx_ev["stage"])
c2.metric("Price", fmt(spx_ev["price"]))
c3.metric("50w SMA", fmt(spx_ev["sma50w"]), f"{fmt(spx_ev['pct_above'], '%', 1)} above")
c4.metric("Stage 2 Score", f"{spx_ev['score']}/5", spx_ev["label"])

pct = spx_ev.get("pct_above") or 0
if spx_ev["stage"] != "Stage 2":
    st.markdown('<p class="market-warn">⚠ SPY is not in Stage 2. Per Weinstein, ignore all buy signals.</p>', unsafe_allow_html=True)
elif pct > 8:
    st.markdown('<p class="market-caution">⚡ SPY is in Stage 2 but extended (&gt;8% above SMA). Fresh EARLY signals will be rare. Wait for pullback or sector rotation.</p>', unsafe_allow_html=True)
else:
    st.markdown('<p class="market-ok">✓ SPY is in early Stage 2. Buy signals are valid.</p>', unsafe_allow_html=True)

st.markdown("---")

# ---- SECTOR RANKING ----

st.markdown("### Sector Ranking")
sec_display = style_sec_table(sec_df)
st.dataframe(sec_display, use_container_width=True, hide_index=True)

# ---- EARLY / PREMIUM SIGNALS (sectors) ----

early_secs = sec_df[sec_df["early_sig"]]
st.markdown("---")
st.markdown("### Early Stage 2 Signals")

if early_secs.empty:
    st.info("No fresh sector signals right now. Market is mid-trend or extended. Re-run after a 5%+ pullback in SPY or when a new sector starts showing RS leadership.")
else:
    for _, r in early_secs.iterrows():
        tag = "PREMIUM" if r["premium"] else "EARLY"
        color = "#00ff88" if r["premium"] else "#ffdd44"
        st.markdown(f"""
        <div class="signal-{'premium' if r['premium'] else 'early'}">
            <strong style="color:{color}">{tag}</strong> &nbsp;
            <strong>{r['ticker']}</strong> {r['name']} &nbsp;|&nbsp;
            Crossed {r['cross']}w ago &nbsp;|&nbsp;
            Base {r['base_w']}w ({r['base_q']}) &nbsp;|&nbsp;
            RS {fmt(r['rs'],'',1)} ({rs_tag(r['rs'])}) &nbsp;|&nbsp;
            Vol {fmt(r['vol'],'x',1)}
        </div>""", unsafe_allow_html=True)

# ---- STOCKS PER SECTOR ----

st.markdown("---")
st.markdown("### Stocks within Top Sectors")
st.caption(f"Showing stocks with Stage 2 score >= {MIN_STAGE2_SHOWN}. Max {MAX_STOCKS_SHOWN} per sector. Sorted by signal quality.")

all_premium = []
all_early   = []

for _, sec in sec_df[sec_df["score"] >= 3].head(5).iterrows():
    tk = sec["ticker"]
    stk = stock_results.get(tk, pd.DataFrame())

    label = f"{'🟢' if sec['premium'] else '🟡' if sec['early_sig'] else '📊'} " \
            f"{tk} {sec['name']}  |  RS {fmt(sec['rs'],'',1)}  |  {sec['label']}  |  Base {sec['base_w']}w"

    with st.expander(label, expanded=sec.get("early_sig", False) or sec.get("premium", False)):
        if stk.empty:
            st.caption("No stocks meet Stage 2 threshold in this sector right now.")
        else:
            display = style_stk_table(stk)
            st.dataframe(display, use_container_width=True, hide_index=True)

            for _, r in stk.iterrows():
                if r.get("premium"):   all_premium.append((r["ticker"], tk, sec["name"], r))
                elif r.get("early_sig"): all_early.append((r["ticker"], tk, sec["name"], r))

# ---- MASTER SHORTLIST ----

st.markdown("---")
st.markdown("### Master Shortlist")

if not all_premium and not all_early:
    st.info("No PREMIUM or EARLY signals across all scanned stocks right now. The market is mid-trend. This is normal in extended bull markets. Run the screener again after the next sector rotation or pullback.")
else:
    if all_premium:
        st.markdown("#### 🟢 Premium Signals")
        for s, sec_t, sec_n, ev in all_premium:
            st.markdown(f"""
            <div class="signal-premium">
                <strong style="color:#00ff88">PREMIUM</strong> &nbsp;
                <strong>{s}</strong> ({sec_t} {sec_n}) &nbsp;|&nbsp;
                Crossed {ev['cross']}w ago &nbsp;|&nbsp;
                Base {ev['base_w']}w ({ev['base_q']}) &nbsp;|&nbsp;
                RS {fmt(ev['rs'],'',1)} &nbsp;|&nbsp;
                Stop {fmt(ev['stop'])} ({fmt(ev['risk'],'%',1)})
            </div>""", unsafe_allow_html=True)

    if all_early:
        st.markdown("#### 🟡 Early Signals")
        for s, sec_t, sec_n, ev in all_early:
            st.markdown(f"""
            <div class="signal-early">
                <strong style="color:#ffdd44">EARLY</strong> &nbsp;
                <strong>{s}</strong> ({sec_t} {sec_n}) &nbsp;|&nbsp;
                Crossed {ev['cross']}w ago &nbsp;|&nbsp;
                Base {ev['base_w']}w ({ev['base_q']}) &nbsp;|&nbsp;
                RS {fmt(ev['rs'],'',1)} &nbsp;|&nbsp;
                Stop {fmt(ev['stop'])} ({fmt(ev['risk'],'%',1)})
            </div>""", unsafe_allow_html=True)

# ---- LEGEND ----

with st.expander("Legend"):
    st.markdown("""
| Term | Meaning |
|---|---|
| RS Score | > +15 STRONG bull, +5..15 bullish, -3..+5 neutral, -15..-3 bearish, < -15 STRONG bear |
| Vol | Breakout-week volume vs 26w avg. >= 1.5x = confirmed |
| Base | Weeks of consolidation before breakout. < 15 short, 15-40 medium, 40-80 long, 80+ very long |
| Cross | Weeks ago that price crossed above 50w SMA |
| Stop | Suggested initial stop = max(50w SMA, 8w swing low) |
| Risk | % below current price that stop sits |
| PREMIUM | Early breakout + base 40+ weeks. Weinstein's gold setup |
| EARLY | Recent crossover + rising SMA + RS up + volume confirmed |
| S2 | Stage 2 (4 or 5 of 5) but you are late to the move |

**Important:** For each PREMIUM/EARLY name, inspect the weekly chart manually.
Tight flat base = good. Wide choppy base = skip. The screener cannot judge this.
    """)

st.markdown('<p class="footer">Built on Stan Weinstein\'s Stage Analysis methodology | Data via Yahoo Finance | Not financial advice</p>', unsafe_allow_html=True)
