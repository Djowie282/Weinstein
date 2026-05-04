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
    st.session_state.dark_mode = False

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
# ── Finviz-style industry categories with representative stocks ──
# Grouped by Finviz sector for easy navigation
FINVIZ_INDUSTRIES = {
    # ── TECHNOLOGY ──
    "Semiconductors":                ["NVDA","AMD","AVGO","QCOM","TXN","MCHP","ADI","AMAT","LRCX","KLAC","ASML","ARM","MU","SMCI","ON","MRVL","INTC","NXPI","STM","SWKS"],
    "Semiconductor Equipment":       ["AMAT","LRCX","KLAC","ASML","ONTO","UCTT","ICHR","ACLS","AMKR","COHU"],
    "Software - Application":        ["CRM","NOW","ADBE","INTU","CDNS","SNPS","ANSS","PTC","MANH","PCTY","PAYC","DOCU","ZI","SMAR","APPF"],
    "Software - Infrastructure":     ["MSFT","ORCL","PLTR","MDB","DDOG","SNOW","NET","ZS","CRWD","PANW","FTNT","OKTA","CYBR","S","TENB"],
    "Computer Hardware":             ["AAPL","HPQ","HPE","DELL","NTAP","PSTG","WDC","STX","NTNX","PEGA"],
    "Information Technology Services":["ACN","IBM","INFY","WIT","CTSH","DXC","EPAM","GLOB","EXLS","KFRC"],
    "Internet Content & Information": ["GOOGL","META","PINS","SNAP","RBLX","MTCH","IAC","ZD","CARG","TRUE"],
    "Electronic Components":         ["TE","APH","GLW","FLEX","PLXS","BHE","CTS","VICR","NTGR","TTMI"],
    "Electronics & Computer Distribution":["AVGO","ARW","AVT","SNX","SCSC","NSIT","PC","AMSWA"],
    "Scientific & Technical Instruments":["TMO","DHR","A","WAT","METTLER","FTV","ROPER","BMI","NOVT","OSIS","MKS"],
    "Communication Equipment":       ["CSCO","JNPR","ANET","CIEN","VIAV","CALX","ALOHA","INFN","COMM","SATS"],

    # ── HEALTHCARE ──
    "Drug Manufacturers - Major":    ["LLY","JNJ","MRK","ABBV","PFE","AMGN","BMY","GILD","BIIB","REGN","VRTX","MRNA","AZN","NVO","RHHBY"],
    "Drug Manufacturers - Specialty":["JAZZ","INVA","SUPN","PRGO","MNKD","HZNP","IMVT","ARWR","ALNY","IONS"],
    "Biotechnology":                 ["MRNA","BIIB","REGN","VRTX","ALNY","BMRN","EXEL","ROIV","KRTX","RCKT","ARWR","IONS","SRPT","FOLD","PTGX"],
    "Medical Devices":               ["ISRG","MDT","BSX","EW","SYK","BDX","ZBH","HOLX","NVST","INSP","NARI","SWAV","IRTC","AXNX","NVRO"],
    "Medical Instruments & Supplies":["ABT","BAX","BDX","DXCM","PODD","TNDM","ITGR","NVCR","MMSI","ICUI"],
    "Health Information Services":   ["UNH","CI","CVS","HUM","MOH","CNC","ELV","HCA","THC","UHS","ACAD","PGNY"],
    "Diagnostics & Research":        ["TMO","DHR","IQV","ILMN","A","QGEN","EXAS","NEO","GH","NTRA","FLGT","OCDX"],
    "Healthcare Plans":              ["UNH","ELV","CI","HUM","MOH","CNC","OSCR","CLOV"],

    # ── FINANCIALS ──
    "Banks - Major":                 ["JPM","BAC","WFC","C","GS","MS","USB","PNC","TFC","COF","KEY","RF","FITB","HBAN","CFG"],
    "Banks - Regional":              ["ZION","MTB","BOKF","EWBC","FFIN","IBOC","CVBF","WAFD","HTLF","BANR","SFNC","RBCAA"],
    "Asset Management":              ["BLK","APO","KKR","BX","CG","ARES","BAM","OWL","STEP","BLUE"],
    "Insurance - Life":              ["MET","PRU","AFL","LNC","UNM","GL","FG","NWLI","PFG","COOP"],
    "Insurance - Property & Casualty":["PGR","ALL","TRV","CB","HIG","MKL","CINF","WRB","RLI","ERIE"],
    "Financial Data & Stock Exchanges":["SPGI","MCO","CME","ICE","MSCI","NDAQ","TW","CBOE","MKTX","EVR"],
    "Credit Services":               ["V","MA","AXP","COF","DFS","SYF","ALLY","OMF","WEX","AFRM","UPST","LC"],
    "Capital Markets":               ["GS","MS","SCHW","RJF","SF","LPLA","VIRT","MKTX","PIPR","HLI"],
    "Insurance - Specialty":         ["AON","MMC","WTW","AJG","BRO","RYAN","ERIE","PLMR","KINGSWAY"],
    "Mortgage Finance":              ["FNMA","FMCC","RKT","UWMC","PFSI","GHLD","HMC","LDI","WSFS"],

    # ── CONSUMER DISCRETIONARY ──
    "Auto Manufacturers":            ["TSLA","GM","F","RIVN","LCID","STLA","TM","HMC","NIO","LI","XPEV","MBLY"],
    "Auto Parts":                    ["APTV","BWA","ALV","GT","LEA","MGA","GNTX","MODV","FOX","DORMAN","MPAA"],
    "Specialty Retail":              ["HD","LOW","ORLY","AZO","AAP","TSCO","WSM","RH","BBWI","URBN","ANF","AEO"],
    "Internet Retail":               ["AMZN","BKNG","EXPE","ABNB","W","ETSY","EBAY","CHWY","OLLI","VTRS","WISH"],
    "Restaurants":                   ["MCD","SBUX","CMG","YUM","QSR","DPZ","WING","TXRH","DRI","JACK","SHAK","CAVA"],
    "Apparel Retail":                ["NKE","LULU","DECK","ONON","CROX","SKX","VFC","HBI","UA","PVH","G-III"],
    "Apparel Manufacturing":         ["NKE","VFC","HBI","UA","PVH","RL","GOOS","MNST","HARL","DBRN"],
    "Home Improvement Retail":       ["HD","LOW","WSM","RH","ARHS","HVBT","BCPC","TILE","FBHS","MASCO"],
    "Furnishings & Fixtures":        ["WSM","RH","ETSY","HNI","KNL","SCS","LESL","FLXS","UFI","DXPE"],
    "Leisure":                       ["MAR","HLT","H","IHG","WH","WYNDM","EXPE","BKNG","ABNB","RCL","CCL","NCLH","LVS","MGM","WYNN","CZR"],
    "Gambling":                      ["LVS","MGM","WYNN","CZR","BYD","PENN","DKNG","FLUT","RSI","BALY"],
    "Travel Services":               ["BKNG","EXPE","ABNB","TRIP","VTRS","TVTX","UAL","DAL","AAL","JBLU","LUV","ULCC"],

    # ── CONSUMER STAPLES ──
    "Discount Stores":               ["WMT","COST","TGT","DG","DLTR","BIG","FIVE","PSMT","OLLI"],
    "Household & Personal Products": ["PG","CL","CHD","KMB","ENR","SPB","COTY","ELF","HIMS","KENVUE","NUS"],
    "Beverages - Non-Alcoholic":     ["KO","PEP","MNST","FIZZ","COKE","NOS","CELH","REED","PRMW"],
    "Beverages - Alcoholic":         ["STZ","BUD","TAP","SAM","ABEV","DEO","BF-B","MGPI","EAST","CASK"],
    "Beverages - Brewers":           ["SAM","TAP","BUD","ABEV","CRAFT","BREW","BEVE"],
    "Food Distribution":             ["SYY","USFD","PFGC","CHEF","CASY","ARMK","JACK","DINE","FAT"],
    "Farm Products":                 ["ADM","BG","INGR","CALM","SMFG","SAFM","VITL","TWNK","JJSF","LWAY"],
    "Packaged Foods":                ["MDLZ","GIS","K","CPB","SJM","CAG","HRL","MKC","TSCO","POST","LANC","SLAB"],
    "Tobacco":                       ["PM","MO","BTI","VGR","SWMA","TPB","XXII"],
    "Confectioners":                 ["HSY","TR","RMCF","CACAO","SOUR","KFRC"],
    "Grocery Stores":                ["KR","ACI","WINN","VLGEA","CASY","IMKTA","NGVC","SPTN"],

    # ── ENERGY ──
    "Oil & Gas E&P":                 ["XOM","CVX","COP","EOG","OXY","DVN","FANG","MRO","APA","AR","RRC","EQT","CNX","SM","MTDR","CTRA","VTLE","CHK"],
    "Oil & Gas Integrated":          ["XOM","CVX","BP","SHEL","TTE","E","EQNR","IMO","SU"],
    "Oil & Gas Midstream":           ["WMB","OKE","KMI","EPD","ET","MPLX","PAA","TRGP","DT","HESM"],
    "Oil & Gas Refining & Marketing":["MPC","VLO","PSX","PBF","DKL","DINO","PARR","CALUMET"],
    "Oil & Gas Drilling":            ["HP","NBR","PD","PTEN","NR","OIS","WTTR","NINE","BAS","KLX"],
    "Oil & Gas Equipment & Services":["SLB","HAL","BKR","NOV","FTI","WHD","NE","VAL","RIG","BORR","DO","NR"],
    "Uranium":                       ["CCJ","UEC","UUUU","DNN","URG","EU","BQSSF","NXE","ENCUF","PALAF"],
    "Coal":                          ["BTU","ARCH","CEIX","AMR","METC","HNRG","SXC","FELP","NACCO"],
    "Renewable Utilities":           ["NEE","BEP","BEPC","FSLR","ENPH","RUN","NOVA","ARRY","CSIQ","SEDG"],

    # ── INDUSTRIALS ──
    "Aerospace & Defense":           ["LMT","RTX","NOC","GD","BA","HII","L3H","TDG","HEI","AXON","KTOS","RKLB","RDW","ASTS"],
    "Airlines":                      ["UAL","DAL","AAL","LUV","JBLU","ALK","ULCC","HA","ATSG","SKYW"],
    "Trucking":                      ["ODFL","SAIA","XPO","WERN","JBHT","KNX","ARCB","MRTN","HTLD","USX"],
    "Railroads":                     ["UNP","CSX","NSC","CP","CN","WAB","GATX","RAIL","TRN","GBX"],
    "Integrated Freight & Logistics":["FDX","UPS","XPO","GXO","CHRW","ECHO","HUBG","EXPD","FWRD","ATSG"],
    "Engineering & Construction":    ["PWR","MTZ","MYR","PRIM","ROAD","GBCI","GVP","ARGAN","TPVG"],
    "Farm & Heavy Construction Machinery":["DE","CAT","AGCO","CNHI","OSK","ACCO","LNN","TITN","MNTX"],
    "Industrial Distribution":       ["GWW","FAST","MSC","AIT","GIC","SIC","DNOW","LAWS","RUSHA"],
    "Business Equipment & Supplies": ["AOS","SNA","SWK","TTC","MTW","NVRI","KMT","SPXC","NWC","BRC"],
    "Metal Fabrication":             ["NUE","STLD","CMC","RS","ATI","HWM","CRS","TKR","OSI","WOR"],
    "Specialty Industrial Machinery":["EMR","ROK","ITW","IEX","ROP","FLS","GNRC","ESCO","MIDD","WTS"],
    "Tools & Accessories":           ["SNA","SWK","KMT","WSO","NWC","BRC","ROLL","CPRT","BMBL","LPX"],

    # ── MATERIALS ──
    "Chemicals":                     ["LIN","APD","ECL","DD","EMN","RPM","IFF","ALB","FMC","CF","MOS","OLN","CC","TROX","HUN"],
    "Specialty Chemicals":           ["ECL","RPM","IFF","ALB","FMC","AVNT","ASCMA","PLL","LTHM","SQM","CEMI"],
    "Agricultural Inputs":           ["CTVA","MOS","CF","NTR","ANDE","ICL","KRNT","MBCN","LIQT"],
    "Steel":                         ["NUE","STLD","CMC","CLF","X","MT","TS","ZEUS","USAP","GHM"],
    "Aluminum":                      ["AA","CENX","KALU","MTAL","RYES","NACCO","SXCL","PLLA","ALUM"],
    "Copper":                        ["FCX","SCCO","HBM","TECK","CS","CPER","CPPM","RIO","BHP"],
    "Gold":                          ["NEM","GOLD","AEM","AGI","KGC","AU","EGO","IAG","PAAS","WPM","FNV","RGLD"],
    "Silver":                        ["WPM","PAAS","MAG","AG","SSRM","HL","EXK","SILV","CDE","FSM"],
    "Other Industrial Metals":       ["MP","LTHM","LAC","PLL","SQM","ALB","GFAI","NOVV","CLNE"],
    "Building Materials":            ["SHW","VMC","MLM","EXP","LPX","UFPI","DOOR","NCI","BLDP","BLDR"],
    "Paper & Paper Products":        ["IP","PKG","SON","SLGN","GPK","BERY","RANPAK","ATR","PHIBRO"],
    "Lumber & Wood Production":      ["WY","PCH","RYN","PL","LPX","UFPI","UFP","BCC","WEYCO"],

    # ── REAL ESTATE ──
    "REIT - Industrial":             ["PLD","REXR","EGP","FR","LXP","STAG","ILPT","TRNO","COLD","GLP"],
    "REIT - Retail":                 ["SPG","O","KIM","REG","FRT","SRC","EPRT","NNN","RPAI","SITC"],
    "REIT - Residential":            ["EQR","AVB","MAA","ESS","CPT","NMD","INVH","AMH","UDR","IRT"],
    "REIT - Office":                 ["BXP","VNO","SLG","HIW","CUZ","DEA","PGRE","ESRT","ALX","PDM"],
    "REIT - Healthcare":             ["WELL","VTR","OHI","PEAK","HR","NHI","LTC","SBRA","CSH","GMRE"],
    "REIT - Hotel & Motel":          ["HST","RHP","PK","APLE","CLDT","SHO","RLJ","XHR","INN","BHR"],
    "REIT - Specialty":              ["AMT","CCI","SBAC","EQIX","DLR","CONE","QTS","IRM","LADR","SAFE"],
    "REIT - Mortgage":               ["AGNC","NLY","STWD","BXMT","RC","GPMT","KREF","TWO","MFA","ARR"],
    "Real Estate Services":          ["CBRE","JLL","CWK","RMAX","EXPI","DOUG","OPEN","COMP","HHC","FPH"],

    # ── UTILITIES ──
    "Utilities - Regulated Electric":["NEE","SO","DUK","AEP","XEL","EXC","ED","SRE","D","PEG","AEE","WEC","ETR","DTE","FE","ES","PPL","CMS","OGE","EVRG","LNT"],
    "Utilities - Renewable":         ["NEE","BEP","BEPC","AES","CWEN","NOVA","ARRY","RUN","FSLR","ENPH","SEDG"],
    "Utilities - Regulated Gas":     ["SRE","NI","ATO","ONE","SPOK","WEC","NW","SR","NJR","SWX","NFG","CPK"],
    "Utilities - Regulated Water":   ["AWK","WTRG","MSEX","YORW","SJW","GWRS","ARTNA","CTWS","PESI"],
    "Utilities - Diversified":       ["AES","D","ETR","EVRG","PNW","NWE","CLNE","AVA","IDACORP","UT"],
    "Utilities - Independent Power": ["VST","CEG","NRG","AES","CWEN","CLNE","AMPE","GEN","MGEE","OTTA"],

    # ── COMMUNICATION SERVICES ──
    "Telecom Services":              ["T","VZ","TMUS","LUMN","USM","TDS","ATN","SHEN","CNSL","OOMA","NTLS"],
    "Entertainment":                 ["DIS","NFLX","WBD","PARA","FOX","FOXA","LGF-A","AMC","CNK","IMAX","LYV","MSG","MSGE"],
    "Publishing":                    ["NYT","GCI","MDP","NWSA","NWS","OMC","IPG","PRTS","QUAD","LSC"],
    "Advertising Agencies":          ["OMC","IPG","PUBM","TTD","MGNI","IAS","DV","CRIT","TBLA","APPS"],

    # ── ADDITIONAL HIGH-INTEREST ──
    "Electronic Gaming & Multimedia":["ATVI","EA","TTWO","RBLX","U","PLTK","GRVY","DDI","GMBL","SKLZ"],
    "Medical Distribution":          ["MCK","ABC","CAH","PDCO","HSIC","OMCL","NXRT","MDRX","HCSG","HWAY"],
    "Staffing & Employment":         ["ADP","PAYX","MAN","KFY","KELYA","HHAX","RCMT","HCI","TBI","CDW"],
    "Waste Management":              ["WM","RSG","CWST","SRCL","ARIS","CLH","ECOL","HCCI","GDYN","GFL"],

    # ── MISSING FINVIZ CATEGORIES ──
    "Luxury Goods":                  ["LVMUY","CPRI","TPR","RL","PVH","MOV","FOSL","COTY","ELF","RARE"],
    "Grocery Stores":                ["KR","ACI","VLGEA","WINN","IMKTA","NGVC","SPTN","CASY","ALDI"],
    "REIT - Diversified":            ["W","LAND","EPRT","FCPT","SRC","GTY","GOOD","PINE","GIPR","NLCP"],
    "Insurance - Reinsurance":       ["RNR","ACGL","MKL","GLRE","PRNB","PRE","STRS","TPRE","TNL"],
    "Real Estate - Development":     ["TOL","LEN","DHI","NVR","PHM","MDC","TMHC","MTH","LGIH","SKY"],
    "Education & Training Services": ["CHGG","LRN","PRDO","STRA","GHC","LOPE","LAUR","ATGE","COUR","DUOL"],
    "Conglomerates":                 ["BRK-B","GE","MMM","HON","ITW","EMR","SIC","CODI","SPLP","ACCO"],
    "Banks - Diversified":           ["JPM","BAC","WFC","C","USB","PNC","TFC","COF","KEY","RF","FITB"],
    "Consumer Electronics":          ["AAPL","SONO","HEAR","KOSS","VIZIO","GPRO","IRBT","VOXX","DXPE"],
    "Shell Companies":               ["SPAC","PSTH","AJAX","BOWX","CCIV","ACAM","HCAC","IPOF","GSAH"],
    "Thermal Coal":                  ["BTU","ARCH","CEIX","AMR","METC","HNRG","SXC","FELP","NACCO"],
    "Coking Coal":                   ["AMR","ARCH","CEIX","METC","SXC","HCC","NACCO","FELP","ACI"],
    "Residential Construction":      ["DHI","LEN","TOL","PHM","NVR","MDC","TMHC","MTH","LGIH","CVCO"],
    "Other Precious Metals & Mining":["NEM","GOLD","AEM","AGI","MP","LTHM","LAC","PLL","SQM","UUUU"],
    "Pollution & Treatment Controls":["CLH","RSG","WM","CWST","SRCL","ECOL","NVRI","HCCI","PESI","GFL"],
    "Medical Care Facilities":       ["HCA","THC","UHS","CYH","SGRY","AMSF","AKAM","ADUS","ENSG","BKD"],
    "Solar":                         ["FSLR","ENPH","RUN","NOVA","ARRY","CSIQ","SEDG","SPWR","MAXN","JKS"],
    "Security & Protection Services":["AXON","MSA","ALLE","SWK","NSSC","NAPCO","IronNet","ARLO","IDEX","SSTI"],
    "Broadcasting":                  ["NFLX","DIS","WBD","PARA","FOX","FOXA","AMC","LGF-A","IMAX","SGBX"],
    "Packaging & Containers":        ["IP","PKG","SON","SLGN","GPK","BERY","RANPAK","ATR","CLGX","CCK"],
    "Auto & Truck Dealerships":      ["AN","KMX","LAD","PAG","ABG","RUSHA","HLIT","SAH","CVNA","CAR"],
    "Insurance - Diversified":       ["AIG","MET","PRU","AFL","LNC","GL","UNM","FG","NWLI","COOP"],
    "Furnishings, Fixtures & Appliances":["WSM","RH","ETH","LESL","HNI","KNL","SCS","FLXS","UFI","DXPE"],
    "Beverages - Wineries & Distilleries":["STZ","BATRA","MGPI","EAST","CASK","WVVI","BWLD","LAWS","BCPC"],
    "Personal Services":             ["HNHPF","CSV","SCI","HRB","SFM","PRSC","FRG","MGRC","CLVT","EFSC"],
    "Recreational Vehicles":         ["THO","WGO","PII","HOG","BC","MCFT","PATK","DOOO","MVST","LCII"],
    "Pharmaceutical Retailers":      ["CVS","WBA","RAD","HIBB","PETQ","HIMS","TDOC","CERT","EGRX","ASRT"],
    "Airports & Air Services":       ["CLCO","ATSG","AAR","SKYW","MESA","RJET","VLRS","OMAB","ASUR","PAGS"],
    "Insurance Brokers":             ["AON","MMC","WTW","AJG","BRO","RYAN","ERIE","PLMR","KNSL","KINGSWAY"],
    "Consulting Services":           ["MCK","ACN","BAH","CACI","SAIC","LDOS","ICF","EXLS","HURN","PRGS"],
    "Footwear & Accessories":        ["NKE","DECK","ONON","CROX","SKX","BOOT","CALM","GIL","VST","BIRD"],
    "Department Stores":             ["M","KSS","JWN","DDS","BIG","BURL","TJX","ROST","OLLI","FIVE"],
    "Specialty Business Services":   ["BR","CSGP","DNB","EFX","EXPN","FICO","INFO","MMS","TRI","VRSK"],
    "Real Estate - Diversified":     ["CBRE","JLL","CWK","RMAX","EXPI","DOUG","OPEN","COMP","HHC","FPH"],
    "Resorts & Casinos":             ["LVS","MGM","WYNN","CZR","BYD","PENN","DKNG","FLUT","RSI","BALY"],
    "Medical Instruments & Supplies":["ABT","BAX","BDX","DXCM","PODD","TNDM","ITGR","NVCR","MMSI","ICUI"],
    "Other Precious Metals":         ["WPM","PAAS","MAG","AG","SSRM","HL","EXK","SILV","CDE","FSM"],
    "Specialty Chemicals - Advanced":["ALB","LTHM","LAC","PLL","SQM","MP","LIVENT","AVNT","ASCMA","CEMI"],
}

# Flat lookup: ticker → industry
TICKER_TO_INDUSTRY = {}
for ind, tks in FINVIZ_INDUSTRIES.items():
    for tk in tks:
        if tk not in TICKER_TO_INDUSTRY:
            TICKER_TO_INDUSTRY[tk] = ind


# ─────────────────────────────────────────────
# AUTH (simple, session-based)
# ─────────────────────────────────────────────

# ── AUTH SYSTEM ──
# st.cache_resource = server-level singleton shared across ALL user sessions.
# This means invite codes and registered accounts persist across different browsers
# as long as the Streamlit server keeps running.

_ADMIN_HASH  = hashlib.sha256("weinstein2026".encode()).hexdigest()
_ROGER_HASH  = hashlib.sha256("roger123".encode()).hexdigest()

@st.cache_resource
def get_shared_auth():
    """Shared auth store — same object for every visitor on this server."""
    return {
        "users": {
            "joey":  {"pw": _ADMIN_HASH, "role": "admin"},
            "roger": {"pw": _ROGER_HASH, "role": "user"},
        },
        "invite_codes": {},  # code -> {"used": bool, "created_by": str}
    }

def check_login(user, pw):
    db = get_shared_auth()
    entry = db["users"].get(user)
    return entry and entry["pw"] == hashlib.sha256(pw.encode()).hexdigest()

def is_admin(user):
    db = get_shared_auth()
    return db["users"].get(user, {}).get("role") == "admin"

def gen_invite_code(created_by):
    import secrets as sec
    db   = get_shared_auth()
    code = sec.token_urlsafe(8)
    db["invite_codes"][code] = {"used": False, "created_by": created_by}
    return code

def login_wall():
    st.markdown(f"<h2>🔒 Portfolio Dashboard</h2>", unsafe_allow_html=True)
    auth_tab, reg_tab = st.tabs(["Log in", "Register with invite code"])

    with auth_tab:
        col1, col2 = st.columns([1, 2])
        with col1:
            with st.form("login"):
                user = st.text_input("Username")
                pw   = st.text_input("Password", type="password")
                ok   = st.form_submit_button("Log in", use_container_width=True)
                if ok:
                    if check_login(user, pw):
                        st.session_state.logged_in    = True
                        st.session_state.current_user = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password")

    with reg_tab:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"<p class='subtext'>You need an invite code from an existing user.</p>",
                        unsafe_allow_html=True)
            with st.form("register"):
                inv_code  = st.text_input("Invite code")
                new_user  = st.text_input("Choose username")
                new_pw    = st.text_input("Choose password", type="password")
                new_pw2   = st.text_input("Repeat password", type="password")
                reg_ok    = st.form_submit_button("Create account", use_container_width=True)
                if reg_ok:
                    db = get_shared_auth()
                    code_entry = db["invite_codes"].get(inv_code)
                    if not code_entry:
                        st.error("Invalid invite code")
                    elif code_entry["used"]:
                        st.error("This invite code has already been used")
                    elif not new_user or len(new_user) < 3:
                        st.error("Username must be at least 3 characters")
                    elif new_user in db["users"]:
                        st.error("Username already taken")
                    elif new_pw != new_pw2:
                        st.error("Passwords do not match")
                    elif len(new_pw) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        db["users"][new_user] = {
                            "pw": hashlib.sha256(new_pw.encode()).hexdigest(),
                            "role": "user",
                        }
                        db["invite_codes"][inv_code]["used"] = True
                        # Init empty portfolio for new user
                        if "portfolios" not in st.session_state:
                            st.session_state.portfolios = {}
                        st.session_state.portfolios[new_user] = []
                        st.success(f"✅ Account created! You can now log in as **{new_user}**.")


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

tab_screener, tab_industries, tab_all, tab_dashboard = st.tabs([
    "🏦 Sectors",
    "🔍 Industries",
    "📋 All Stocks",
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
# TAB 2: INDUSTRIES (Finviz-style)
# ═══════════════════════════════════════════════

@st.cache_data(ttl=6*3600, show_spinner=False)
def scan_industry(industry_name, tickers_json, spx_close_json):
    """Scan all stocks in a given industry."""
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
    return pd.DataFrame(rows).sort_values(
        ["premium","early_sig","score","rs"], ascending=[False,False,False,False]
    ).reset_index(drop=True)

def export_tradingview(tickers):
    """Generate TradingView-compatible watchlist string."""
    return ",".join(tickers)

def export_tradingview_lines(tickers):
    """One ticker per line for TradingView import."""
    return "\n".join(tickers)

with tab_industries:
    st.markdown("### 🔍 Industry Screener")
    st.markdown(f"<span class='subtext'>{len(FINVIZ_INDUSTRIES)} industries · {sum(len(v) for v in FINVIZ_INDUSTRIES.values())} stocks · Weinstein Stage Analysis · RS vs SPX</span>", unsafe_allow_html=True)

    # ── Search bar ──
    st.markdown("---")
    search_col, btn_col = st.columns([4, 1])
    with search_col:
        search_query = st.text_input("🔎 Search stock or industry", placeholder="e.g. NVDA, ARM, Semiconductors, Energy...")
    with btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        do_search = st.button("Analyze", use_container_width=True)

    if search_query and (do_search or len(search_query) > 1):
        q = search_query.strip().upper()
        spx_close_s = pd.read_json(StringIO(spx_close_json), typ="series")

        # Check if it's a ticker
        matching_industry = TICKER_TO_INDUSTRY.get(q)
        industry_matches  = [ind for ind in FINVIZ_INDUSTRIES if search_query.lower() in ind.lower()]

        # Ticker check: try fetching data first.
        # A ticker like ARM, FARM, CHARM could match industry names containing those letters.
        # We always try the stock analysis first; fall back to industry only if data is empty.
        looks_like_ticker = len(q) <= 6 and q.isalpha()

        if q and (looks_like_ticker or not industry_matches):
            # Single stock analysis
            st.markdown(f"#### 📊 Weinstein Analysis: {q}")
            with st.spinner(f"Analyzing {q}..."):
                df = fetch_weekly(q)
                if df.empty:
                    st.error(f"Could not find data for {q}. Check the ticker symbol.")
                else:
                    r = evaluate(df, spx_close_s)
                    r["ticker"] = q
                    ind_name = TICKER_TO_INDUSTRY.get(q, "–")
                    stage    = r["stage"]

                    # Find sector RS context
                    sec_name_found = "–"
                    sec_rs_val     = None
                    for sec_tk, sec_name in SECTORS.items():
                        if sec_name.lower() in ind_name.lower() or ind_name.lower() in sec_name.lower():
                            sec_row = sec_df[sec_df["ticker"] == sec_tk]
                            if not sec_row.empty:
                                sec_rs_val     = sec_row.iloc[0]["rs"]
                                sec_name_found = sec_name
                                break

                    # ── METRICS ROW ──
                    a1,a2,a3,a4 = st.columns(4)
                    a1.metric("Stage",     stage)
                    a2.metric("Score",     f"{r['score']}/5")
                    a3.metric("RS vs SPX", fmt(r['rs'],'',1))
                    a4.metric("%>50w SMA", fmt(r['pct_above'],'%',1))

                    b1,b2,b3,b4 = st.columns(4)
                    b1.metric("Price",   fmt(r["price"]))
                    b2.metric("50w SMA", fmt(r["sma50w"]))
                    b3.metric("Stop",    fmt(r["stop"]))
                    b4.metric("Risk",    fmt(r["risk"],"%",1))

                    st.markdown("---")

                    # ── WEINSTEIN CHECKLIST ──
                    st.markdown("#### ✅ Weinstein Checklist")

                    def check_row(passed, label, detail):
                        icon = "✅" if passed else "❌"
                        color = GREEN if passed else RED
                        return f'<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 12px;margin:4px 0;background:{CARD};border-radius:8px;border:1px solid {BORDER}"><span style="font-size:1.1rem;margin-top:1px">{icon}</span><div><strong style="color:{color}">{label}</strong><br><span style="color:{SUBTEXT};font-size:0.82rem">{detail}</span></div></div>'

                    # 1. Price above 50w SMA
                    pct = r["pct_above"] or 0
                    detail_sma = f"Price {fmt(r['price'])} is {fmt(pct,'%',1)} {'above' if pct >= 0 else 'below'} the 50w SMA ({fmt(r['sma50w'])})"
                    st.markdown(check_row(r["above_sma"], "Price above 50-week SMA", detail_sma), unsafe_allow_html=True)

                    # 2. SMA rising
                    detail_slope = f"50w SMA is {'rising (positive slope)' if r['sma_rising'] else 'flat or declining — key warning sign'}. Weinstein: the MA must be trending up for a valid Stage 2."
                    st.markdown(check_row(r["sma_rising"], "50-week SMA is rising", detail_slope), unsafe_allow_html=True)

                    # 3. RS vs SPX
                    rs_val = r["rs"]
                    rs_str = fmt(rs_val, "", 1) if rs_val is not None else "n/a"
                    detail_rs = f"RS score: {rs_str} — {rs_tag(rs_val)}. "
                    if rs_val is not None:
                        if rs_val >= 5:
                            detail_rs += "Stock is outperforming the S&P 500. Weinstein looks for RS line making new highs alongside price."
                        elif rs_val >= -3:
                            detail_rs += "Stock moving in line with the market. Ideal setups show RS leading, not lagging."
                        else:
                            detail_rs += "Stock is underperforming the market. Weinstein avoids buying weak RS stocks even if price looks good."
                    st.markdown(check_row(r["rs_up"], "Relative Strength vs SPX positive", detail_rs), unsafe_allow_html=True)

                    # 4. Near 52-week high
                    detail_high = f"Price is {fmt(r['pct_above'],'%',1)} vs 50w SMA. {'Within 15% of 52w high — stock is near breakout zone.' if r['near_high'] else 'More than 15% below 52w high — stock is not near a breakout.'}"
                    st.markdown(check_row(r["near_high"], "Price near 52-week high (within 15%)", detail_high), unsafe_allow_html=True)

                    # 5. Not overextended
                    detail_ext = f"{fmt(pct,'%',1)} above 50w SMA. "
                    if 0 < pct < 15:
                        detail_ext += "Ideal entry zone — close to SMA, low risk."
                    elif 15 <= pct < 30:
                        detail_ext += "Extended but still acceptable. Risk is higher — consider waiting for a pullback."
                    elif pct >= 30:
                        detail_ext += "Overextended. Weinstein would wait for a consolidation before entering."
                    else:
                        detail_ext += "Below SMA — not in Stage 2 territory."
                    st.markdown(check_row(r["not_extended"], "Not overextended (<30% above SMA)", detail_ext), unsafe_allow_html=True)

                    # 6. Volume on breakout
                    vol = r["vol"]
                    vol_pass = r["vol_ok"]
                    detail_vol = f"Volume ratio: {fmt(vol,'x',1)} vs 26-week average. "
                    if vol is None:
                        detail_vol += "No volume data available."
                    elif vol >= 2.0:
                        detail_vol += "Excellent — strong institutional buying confirmed."
                    elif vol >= 1.5:
                        detail_vol += "Good — above-average volume confirms the move."
                    elif vol >= 1.0:
                        detail_vol += "Average — move lacks volume conviction. Weinstein wants to see 2x+ on breakout week."
                    else:
                        detail_vol += "Weak — below average volume is a red flag. Could be a false breakout."
                    st.markdown(check_row(vol_pass, "Breakout on above-average volume (≥1.5x)", detail_vol), unsafe_allow_html=True)

                    # 7. Base quality
                    bw = r["base_w"]
                    bq_pass = bw >= 15
                    detail_base = f"Base length: {bw} weeks ({r['base_q']}). "
                    if bw >= 80:
                        detail_base += "Very long base — exceptional setup. The longer the base, the bigger the potential move."
                    elif bw >= 40:
                        detail_base += "Long base — high quality setup. Weinstein's ideal scenario."
                    elif bw >= 15:
                        detail_base += "Medium base — acceptable. More time consolidating would increase conviction."
                    else:
                        detail_base += "Short base — low quality. Weinstein prefers minimum 15 weeks of consolidation."
                    st.markdown(check_row(bq_pass, "Base ≥15 weeks (longer = better)", detail_base), unsafe_allow_html=True)

                    # 8. Sector context
                    sec_bullish = sec_rs_val is not None and sec_rs_val > 0
                    detail_sec = f"Sector: {sec_name_found}. "
                    if sec_rs_val is not None:
                        detail_sec += f"Sector RS: {fmt(sec_rs_val,'',1)} ({rs_tag(sec_rs_val)}). "
                        if sec_bullish:
                            detail_sec += "Weinstein: always prefer stocks in leading sectors. Sector tailwind confirmed."
                        else:
                            detail_sec += "Weinstein: buying a stock in a weak sector is rowing against the tide."
                    else:
                        detail_sec += "Sector data not available."
                    st.markdown(check_row(sec_bullish, "Sector is bullish vs SPX", detail_sec), unsafe_allow_html=True)

                    # ── VERDICT ──
                    st.markdown("---")
                    st.markdown("#### 🧠 Verdict")

                    score = r["score"]
                    checks_passed = sum([
                        r["above_sma"], r["sma_rising"], r["rs_up"],
                        r["near_high"], r["not_extended"], vol_pass,
                        bq_pass, sec_bullish
                    ])

                    if "Stage 2" in stage and score >= 4:
                        if r.get("premium"):
                            verdict_color = GREEN
                            verdict = f"**🟢 PREMIUM SETUP** — {q} is in a textbook Weinstein Stage 2 breakout with a long base of {bw} weeks. This is the type of setup Weinstein writes about: price above a rising 50w SMA, strong RS, volume confirmation, and a solid base. All 5 core criteria met ({score}/5). Early entry window still open."
                        elif r.get("early_sig"):
                            verdict_color = GREEN
                            verdict = f"**🟢 EARLY STAGE 2** — {q} just crossed above its 50w SMA recently ({r['cross']}w ago) with {fmt(vol,'x',1)} volume. The SMA is turning up and RS is positive. This is the sweet spot Weinstein targets: get in early in Stage 2 before the crowd notices. Risk is well-defined with a stop at {fmt(r['stop'])} ({fmt(r['risk'],'%',1)} below current price)."
                        else:
                            verdict_color = BLUE
                            verdict = f"**🔵 STAGE 2 — LATE ENTRY** — {q} is in Stage 2 uptrend with {score}/5 criteria met, but the move is already underway (price is {fmt(pct,'%',1)} above the 50w SMA). Weinstein would still hold an existing position here, but a fresh entry carries more risk. Wait for a pullback toward the SMA for a better risk/reward."
                    elif "Stage 1" in stage:
                        verdict_color = BLUE
                        if bw >= 40:
                            verdict = f"**🔵 STAGE 1 — WATCH LIST** — {q} is building a {bw}-week base (Stage 1). This is exactly where Weinstein wants you to put it on your watchlist. A long base means energy is building. The trigger: a high-volume weekly close above the 50w SMA with the SMA starting to turn up. Not yet — but getting interesting."
                        else:
                            verdict = f"**🔵 STAGE 1 — TOO EARLY** — {q} is in Stage 1 basing with only {bw} weeks of consolidation. Weinstein says: be patient. There is nothing to do here yet. Set an alert for when price breaks above {fmt(r['sma50w'])} on volume."
                    elif "Stage 3" in stage:
                        verdict_color = YELLOW
                        verdict = f"**🟡 STAGE 3 — CAUTION** — {q} is in Stage 3 topping. The 50w SMA is flattening after a run-up. Weinstein treats this as a sell zone for existing holders, not a buy zone. If you hold this stock, tighten your stop. If you don't, stay away — the best gains are already in."
                    else:  # Stage 4
                        verdict_color = RED
                        verdict = f"**🔴 STAGE 4 — AVOID** — {q} is in a Stage 4 downtrend. Price is below a declining 50w SMA. Weinstein's rule is absolute: never buy a stock in Stage 4, regardless of how cheap it looks. {'High RS (' + fmt(rs_val, '', 1) + ') suggests a temporary bounce — this is a dead cat bounce, not a reversal.' if rs_val and rs_val > 5 else 'Wait for a full Stage 1 base to form before considering this stock again.'}"

                    st.markdown(f'<div style="background:{CARD};border-left:4px solid {verdict_color};border:1px solid {verdict_color}33;border-radius:10px;padding:16px 20px;line-height:1.7">{verdict}<br><br><span style="color:{SUBTEXT};font-size:0.8rem">Checklist: {checks_passed}/8 criteria met · Industry: {ind_name} · Base: {bw}w · Stop: {fmt(r["stop"])} · Risk: {fmt(r["risk"],"%",1)}</span></div>', unsafe_allow_html=True)

                    if sig_icon(r):
                        st.success(f"Active signal: {sig_icon(r)}")

                    st.markdown(f"<br><span class='subtext'>TradingView: <code>{q}</code></span>", unsafe_allow_html=True)

        elif industry_matches and not looks_like_ticker:
            st.markdown(f"#### Industries matching '{search_query}'")
            for ind in industry_matches[:5]:
                tks = FINVIZ_INDUSTRIES[ind]
                st.markdown(f"**{ind}** — {len(tks)} stocks: {', '.join(tks[:8])}{'...' if len(tks)>8 else ''}")

    st.markdown("---")

    # ── Industry overview table ──
    ind_hdr, ind_ctrl = st.columns([3,2])
    with ind_hdr:
        st.markdown("#### All Industries")
    with ind_ctrl:
        min_ind_score = st.selectbox("Min score filter", [0,1,2,3,4], index=0,
                                      key="ind_score_filter",
                                      label_visibility="collapsed")
        show_only_signals = st.checkbox("Signals only", value=False)

    # Build summary table (uses cached sector data for speed; full per-industry scan on click)
    ind_summary = []
    for ind_name, tks in FINVIZ_INDUSTRIES.items():
        ind_summary.append({
            "Industry": ind_name,
            "Stocks":   len(tks),
            "Tickers":  ", ".join(tks[:5]) + ("..." if len(tks)>5 else ""),
        })
    ind_sum_df = pd.DataFrame(ind_summary)
    st.dataframe(ind_sum_df, use_container_width=True, hide_index=True, height=400)

    st.markdown("---")

    # ── Drill-down: click to scan industry ──
    st.markdown("#### Drill into an Industry")
    drill_col1, drill_col2 = st.columns([3,1])
    with drill_col1:
        selected_industry = st.selectbox(
            "Select industry to scan",
            list(FINVIZ_INDUSTRIES.keys()),
            key="industry_drill"
        )
    with drill_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_industry_btn = st.button("🔍 Scan Industry", use_container_width=True)

    if scan_industry_btn or st.session_state.get("last_scanned_industry") == selected_industry:
        st.session_state["last_scanned_industry"] = selected_industry
        tks = FINVIZ_INDUSTRIES[selected_industry]
        with st.spinner(f"Scanning {selected_industry} ({len(tks)} stocks)..."):
            ind_df = scan_industry(selected_industry, json.dumps(tks), spx_close_json)

        if not ind_df.empty:
            # Signals summary
            premiums = ind_df[ind_df["premium"]]
            earlys   = ind_df[ind_df["early_sig"]]
            s2s      = ind_df[ind_df["score"] >= 4]

            m1,m2,m3,m4 = st.columns(4)
            m1.metric(f"{selected_industry}", f"{len(ind_df)} stocks")
            m2.metric("Premium signals", len(premiums))
            m3.metric("Early signals",   len(earlys))
            m4.metric("Stage 2+",        len(s2s))

            # Signal cards
            for _, r in premiums.iterrows():
                st.markdown(signal_card(r), unsafe_allow_html=True)
            for _, r in earlys.iterrows():
                st.markdown(signal_card(r), unsafe_allow_html=True)

            # Full table
            disp_df = ind_df if not show_only_signals else ind_df[ind_df["score"] >= min_ind_score]
            rows = []
            for _, r in disp_df.iterrows():
                vol   = r["vol"]
                cross = f"{int(r['cross'])}w" if r.get("cross",-1) >= 0 else "–"
                rows.append({
                    "Ticker":  r["ticker"],
                    "Price":   fmt(r["price"]),
                    "%>SMA":   fmt(r["pct_above"],"%",1),
                    "RS":      fmt(r["rs"],"",1),
                    "RS Trend":rs_tag(r["rs"]),
                    "Vol":     fmt(vol,"x",1),
                    "Base":    f"{r['base_w']}w",
                    "Cross":   cross,
                    "Stop":    fmt(r["stop"]),
                    "Risk":    fmt(r["risk"],"%",1),
                    "Stage":   r["stage"],
                    "Score":   f"{r['score']}/5",
                    "Signal":  sig_icon(r),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # ── Export to TradingView ──
            st.markdown("---")
            st.markdown("#### 📤 Export to TradingView")
            exp_col1, exp_col2, exp_col3 = st.columns(3)
            all_tks    = ind_df["ticker"].tolist()
            signal_tks = ind_df[ind_df["score"] >= 4]["ticker"].tolist()
            early_tks  = ind_df[ind_df["early_sig"] | ind_df["premium"]]["ticker"].tolist()

            with exp_col1:
                st.markdown("**All stocks in industry**")
                tv_all = export_tradingview(all_tks)
                st.code(tv_all, language=None)
                st.download_button("⬇️ Download (.txt)", export_tradingview_lines(all_tks),
                                   file_name=f"TV_{selected_industry.replace(' ','_')}_all.txt",
                                   mime="text/plain", key="dl_all")
            with exp_col2:
                st.markdown("**Stage 2+ stocks only**")
                tv_s2 = export_tradingview(signal_tks) if signal_tks else "No Stage 2 stocks"
                st.code(tv_s2, language=None)
                if signal_tks:
                    st.download_button("⬇️ Download (.txt)", export_tradingview_lines(signal_tks),
                                       file_name=f"TV_{selected_industry.replace(' ','_')}_s2.txt",
                                       mime="text/plain", key="dl_s2")
            with exp_col3:
                st.markdown("**EARLY/PREMIUM signals**")
                tv_early = export_tradingview(early_tks) if early_tks else "No signals right now"
                st.code(tv_early, language=None)
                if early_tks:
                    st.download_button("⬇️ Download (.txt)", export_tradingview_lines(early_tks),
                                       file_name=f"TV_{selected_industry.replace(' ','_')}_signals.txt",
                                       mime="text/plain", key="dl_early")

            st.markdown(f"<p class='subtext'>TradingView: Chart → Watchlist → Import → paste the comma-separated list, or use the .txt download and import as file.</p>", unsafe_allow_html=True)


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
                          auto_adjust=False, progress=False)["Close"]
        if isinstance(raw, pd.Series):
            raw = raw.to_frame(tickers[0])
        # Drop incomplete today bar (market still open)
        if len(raw) > 1 and raw.index[-1].date() == datetime.today().date():
            raw = raw.iloc[:-1]
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

        # ── ADMIN: INVITE MANAGEMENT ──
        if is_admin(user):
            with st.expander("👤 Manage invites & users"):
                inv_col1, inv_col2 = st.columns(2)
                with inv_col1:
                    st.markdown("**Generate invite link**")
                    if st.button("🔗 Generate new invite code", use_container_width=True):
                        code = gen_invite_code(user)
                        st.session_state["last_invite"] = code
                    if st.session_state.get("last_invite"):
                        c = st.session_state["last_invite"]
                        st.code(c)
                        st.caption("Share this code. It can only be used once.")

                with inv_col2:
                    st.markdown("**Active invite codes**")
                    db    = get_shared_auth()
                    codes = db["invite_codes"]
                    if codes:
                        for c, v in codes.items():
                            status = "✅ used" if v["used"] else "⏳ pending"
                            st.markdown(f"`{c}` — {status}")
                    else:
                        st.caption("No codes generated yet.")

                st.markdown("**Registered users**")
                db = get_shared_auth()
                for u, data in db["users"].items():
                    st.markdown(f"• `{u}` ({data.get('role','user')})")

        # ── MANAGE POSITIONS ──
        with st.expander("➕ Manage positions"):

            # --- BUY / ADD ---
            st.markdown("**Buy / Add shares**")
            col_a, col_b, col_c, col_d = st.columns(4)
            new_tk   = col_a.text_input("Ticker").upper().strip()
            new_sh   = col_b.number_input("Shares", min_value=0.0, step=0.01, value=1.0)
            new_cost = col_c.number_input("Avg cost ($)", min_value=0.0, step=0.01, value=0.0)
            new_note = col_d.text_input("Notes")
            if st.button("➕ Add / Buy", use_container_width=True):
                if new_tk:
                    existing = next((p for p in portfolio if p["ticker"] == new_tk), None)
                    if existing:
                        old_sh = existing["shares"]; old_cost = existing["avg_cost"]
                        new_total_sh = old_sh + new_sh
                        if new_cost > 0 and old_cost > 0:
                            new_avg = (old_sh * old_cost + new_sh * new_cost) / new_total_sh
                        elif new_cost > 0:
                            new_avg = new_cost
                        else:
                            new_avg = old_cost
                        existing["shares"] = new_total_sh
                        existing["avg_cost"] = round(new_avg, 4)
                        if new_note: existing["notes"] = new_note
                        st.success(f"Updated {new_tk}: {new_total_sh:.2f} sh @ ${new_avg:.2f} avg")
                    else:
                        portfolio.append({"ticker": new_tk, "shares": new_sh,
                                          "avg_cost": new_cost, "notes": new_note})
                        st.success(f"Added {new_tk}")
                    st.session_state.portfolios[user] = portfolio
                    st.rerun()

            st.markdown("---")

            # --- SELL (partial or full) ---
            st.markdown("**Sell shares**")
            tickers_in_port = [p["ticker"] for p in portfolio]
            if tickers_in_port:
                sell_col1, sell_col2, sell_col3 = st.columns(3)
                sell_tk = sell_col1.selectbox("Ticker to sell", tickers_in_port)
                pos_to_sell = next((p for p in portfolio if p["ticker"] == sell_tk), None)
                max_sh = pos_to_sell["shares"] if pos_to_sell else 1.0
                sell_sh = sell_col2.number_input(
                    f"Shares (max {max_sh:.2f})", min_value=0.01,
                    max_value=float(max_sh), step=0.01, value=float(max_sh)
                )
                sell_full = sell_col3.checkbox("Sell entire position", value=(sell_sh >= max_sh))

                if st.button("🔴 Sell shares", use_container_width=True):
                    if pos_to_sell:
                        if sell_full or sell_sh >= max_sh:
                            st.session_state[f"confirm_delete_{sell_tk}"] = True
                        else:
                            pos_to_sell["shares"] = round(max_sh - sell_sh, 4)
                            st.session_state.portfolios[user] = portfolio
                            st.success(f"Sold {sell_sh:.2f} sh of {sell_tk}. Remaining: {pos_to_sell['shares']:.2f} sh")
                            st.rerun()

                # Confirm full delete
                if st.session_state.get(f"confirm_delete_{sell_tk}"):
                    st.warning(f"⚠️ Remove **{sell_tk}** entirely from your portfolio?")
                    c_yes, c_no = st.columns(2)
                    if c_yes.button("✅ Yes, remove", key=f"yes_{sell_tk}"):
                        portfolio[:] = [p for p in portfolio if p["ticker"] != sell_tk]
                        st.session_state.portfolios[user] = portfolio
                        st.session_state.pop(f"confirm_delete_{sell_tk}", None)
                        st.success(f"Removed {sell_tk}")
                        st.rerun()
                    if c_no.button("❌ Cancel", key=f"no_{sell_tk}"):
                        st.session_state.pop(f"confirm_delete_{sell_tk}", None)
                        st.rerun()

            st.markdown("---")

            # --- CURRENT POSITIONS LIST ---
            if portfolio:
                st.markdown("**Current positions**")
                for i, pos in enumerate(portfolio):
                    c1,c2,c3,c4,c5 = st.columns([2,1,2,3,1])
                    c1.markdown(f"**{pos['ticker']}**")
                    c2.markdown(f"{pos['shares']:.2f} sh")
                    c3.markdown(f"Avg ${pos['avg_cost']:.2f}" if pos['avg_cost'] > 0 else "–")
                    c4.markdown(pos.get("notes",""))
                    # Delete with confirmation
                    if c5.button("🗑", key=f"del_{i}_{pos['ticker']}"):
                        st.session_state[f"confirm_delete_{pos['ticker']}_{i}"] = True
                    if st.session_state.get(f"confirm_delete_{pos['ticker']}_{i}"):
                        st.warning(f"Remove **{pos['ticker']}**?")
                        y, n = st.columns(2)
                        if y.button("Yes", key=f"y_{i}"):
                            portfolio.pop(i)
                            st.session_state.portfolios[user] = portfolio
                            st.session_state.pop(f"confirm_delete_{pos['ticker']}_{i}", None)
                            st.rerun()
                        if n.button("No", key=f"n_{i}"):
                            st.session_state.pop(f"confirm_delete_{pos['ticker']}_{i}", None)
                            st.rerun()

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

                # ── CONTROLS ROW ──
                ctrl1, ctrl2, ctrl3 = st.columns([3, 2, 1])
                with ctrl1:
                    period_options = ["1W", "1M", "YTD", "1Y", "5Y", "Max"]
                    chart_period = st.radio("Period", period_options, index=3,
                                            horizontal=True, label_visibility="collapsed")
                with ctrl2:
                    compare_spx = st.checkbox("Compare vs S&P 500", value=False)
                with ctrl3:
                    hide_values = st.toggle("Hide $", value=False)

                # ── CHART + DISTRIBUTION SIDE BY SIDE ──
                chart_col, dist_col = st.columns([3, 2])

                @st.cache_data(ttl=3600)
                def get_chart_history(tickers_json, years):
                    tks = json.loads(tickers_json)
                    all_tks = list(set(tks + ["SPY"]))
                    end   = datetime.today()
                    start = end - timedelta(days=int(years * 365))
                    try:
                        raw = yf.download(all_tks, start=start, end=end,
                                          auto_adjust=False, progress=False)["Close"]
                        if isinstance(raw, pd.Series):
                            raw = raw.to_frame(all_tks[0])
                        # Drop today if market still open
                        if len(raw) > 1:
                            raw = raw.iloc[:-1] if raw.index[-1].date() == datetime.today().date() else raw
                        return raw.ffill()
                    except:
                        return pd.DataFrame()

                period_years = {"1W": 0.1, "1M": 0.2, "YTD": 1,
                                "1Y": 1, "5Y": 5, "Max": 10}
                chart_hist = get_chart_history(json.dumps(tickers),
                                               period_years.get(chart_period, 1))

                with chart_col:
                    st.markdown("#### Performance")
                    if not chart_hist.empty:
                        base_val = sum(
                            cost_map.get(tk, (1,0))[0] * cost_map.get(tk, (1,0))[1]
                            for tk in tickers if cost_map.get(tk,(1,0))[1] > 0
                        )
                        if base_val > 0:
                            now = pd.Timestamp.today()
                            if chart_period == "1W":   cut = now - pd.Timedelta(weeks=1)
                            elif chart_period == "1M": cut = now - pd.DateOffset(months=1)
                            elif chart_period == "YTD":cut = pd.Timestamp(now.year,1,1)
                            elif chart_period == "1Y": cut = now - pd.DateOffset(years=1)
                            elif chart_period == "5Y": cut = now - pd.DateOffset(years=5)
                            else:                      cut = chart_hist.index[0]

                            h = chart_hist[chart_hist.index >= cut]
                            if h.empty: h = chart_hist

                            # Portfolio line
                            daily_vals = pd.Series(0.0, index=h.index)
                            for tk in tickers:
                                if tk not in h.columns: continue
                                sh, ac = cost_map.get(tk, (1, 0))
                                if ac > 0:
                                    daily_vals += h[tk].ffill() * sh

                            sv = float(daily_vals.iloc[0])
                            pct_series = (daily_vals / sv - 1) * 100 if sv > 0 else daily_vals * 0
                            # Smooth with rolling avg (window scales with data length)
                            win = max(1, len(pct_series) // 30)
                            pct_smooth = pct_series.rolling(win, min_periods=1, center=True).mean()

                            pct_smooth = pct_smooth.round(2)
                            end_val    = float(pct_smooth.iloc[-1])
                            line_color = "#4ade80" if end_val >= 0 else "#f87171"
                            fill_color = "rgba(74,222,128,0.07)" if end_val >= 0 else "rgba(248,113,113,0.07)"

                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=pct_smooth.index, y=pct_smooth.values,
                                mode="lines", name="Portfolio",
                                line=dict(color=line_color, width=2.5, shape="spline", smoothing=0.8),
                                fill="tozeroy", fillcolor=fill_color,
                                hovertemplate="%{x|%b %d %Y}<br><b>%{y:+.2f}%</b><extra></extra>",
                            ))

                            # SPX comparison
                            if compare_spx and "SPY" in h.columns:
                                spy = h["SPY"].ffill()
                                spy_pct = (spy / float(spy.iloc[0]) - 1) * 100
                                spy_smooth = spy_pct.rolling(win, min_periods=1, center=True).mean().round(2)
                                fig.add_trace(go.Scatter(
                                    x=spy_smooth.index, y=spy_smooth.values,
                                    mode="lines", name="S&P 500",
                                    line=dict(color="#475569", width=1.8,
                                              shape="spline", smoothing=0.8, dash="dot"),
                                    hovertemplate="%{x|%b %d %Y}<br>SPX <b>%{y:+.2f}%</b><extra></extra>",
                                ))

                            fig.add_hline(y=0, line_dash="dash",
                                          line_color="rgba(200,200,200,0.2)", line_width=1)

                            yaxis_cfg = dict(
                                showgrid=True, gridcolor=BORDER, zeroline=False,
                                tickformat="+.1f", ticksuffix="%",
                                color=SUBTEXT, tickfont=dict(size=11),
                            )
                            if hide_values:
                                yaxis_cfg["tickformat"] = ""
                                yaxis_cfg["showticklabels"] = False

                            fig.update_layout(
                                height=300, margin=dict(l=0,r=0,t=10,b=0),
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                font=dict(color=TEXT, family="Syne"),
                                xaxis=dict(showgrid=False, color=SUBTEXT,
                                           tickfont=dict(size=10), zeroline=False),
                                yaxis=yaxis_cfg,
                                legend=dict(bgcolor="rgba(0,0,0,0)",
                                            font=dict(color=TEXT, size=11),
                                            orientation="h", yanchor="bottom",
                                            y=1.02, xanchor="right", x=1),
                                hovermode="x unified",
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Add avg costs per position to see the performance chart.")
                    else:
                        st.caption("Performance history unavailable.")

                # ── DISTRIBUTION (compact, next to chart) ──
                with dist_col:
                    dist_hdr, dist_toggle = st.columns([2, 1])
                    with dist_hdr:
                        st.markdown("#### Distribution")
                    with dist_toggle:
                        dist_mode = st.radio("Show", ["P&L", "Today"],
                                             horizontal=True, label_visibility="collapsed")

                    if position_data:
                        tree_labels = [pd_["r"]["ticker"] for pd_ in position_data if pd_["val"] > 0]
                        tree_values = [pd_["val"] for pd_ in position_data if pd_["val"] > 0]

                        if dist_mode == "Today":
                            # Use fast_info for live last_price vs previous_close
                            # This matches TradingView / broker daily % exactly
                            today_changes = []
                            for pd_ in position_data:
                                if pd_["val"] <= 0: continue
                                tk = pd_["r"]["ticker"]
                                try:
                                    fi   = yf.Ticker(tk).fast_info
                                    prev = getattr(fi, "previous_close", None)
                                    last = getattr(fi, "last_price", None)
                                    if prev and last and float(prev) > 0:
                                        today_changes.append(round((float(last)/float(prev) - 1)*100, 2))
                                    else:
                                        today_changes.append(0.0)
                                except:
                                    today_changes.append(0.0)
                            tree_colors   = today_changes
                            custom_labels = [f"{c:+.2f}%" for c in today_changes]
                        else:
                            tree_pnl    = [pd_["pnl_pct"] for pd_ in position_data if pd_["val"] > 0]
                            tree_colors = [p if p is not None else 0 for p in tree_pnl]
                            custom_labels = [f"{p:+.1f}%" if p is not None else "–" for p in tree_pnl]
                            if hide_values:
                                custom_labels = ["" for _ in custom_labels]

                        fig2 = go.Figure(go.Treemap(
                            labels=tree_labels,
                            parents=[""] * len(tree_labels),
                            values=tree_values,
                            customdata=[[c] for c in custom_labels],
                            texttemplate="<b>%{label}</b><br>%{customdata[0]}",
                            marker=dict(
                                colors=tree_colors,
                                colorscale=[[0,"#7f1d1d"],[0.45,"#1e2130"],[1,"#14532d"]],
                                cmid=0, showscale=False,
                            ),
                        ))
                        fig2.update_layout(
                            height=300, margin=dict(l=0,r=0,t=0,b=0),
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
                    if pnl is not None and not hide_values:
                        pc = GREEN if pnl >= 0 else RED
                        sign = "+" if pnl >= 0 else ""
                        pnl_html = f'<span style="color:{pc};font-weight:700">{sign}${pnl:,.0f} ({pnl_pct:+.1f}%)</span>'

                    sig = sig_icon(r)
                    price_str = "———" if hide_values else f"${r['price'] or 0:,.2f}"

                    with cols3[i % 3]:
                        st.markdown(f"""
                        <div style="background:{CARD};border:1px solid {BORDER};border-radius:10px;
                             padding:14px 16px;margin-bottom:10px;">
                          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                            <span style="font-size:1.1rem;font-weight:800">{s_dot} {tk}</span>
                            <span style="color:{SUBTEXT};font-size:0.8rem">{sh:.0f} sh</span>
                          </div>
                          <div style="font-size:1.4rem;font-weight:700;margin-bottom:2px">{price_str}</div>
                          <div style="font-size:0.82rem;margin-bottom:8px">{pnl_html if pnl_html else ""}</div>
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
