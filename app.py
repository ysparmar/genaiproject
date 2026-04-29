
# ── Language display names → backend keys
LANG_OPTIONS = {
    "English"                 : "English",
    "Hindi (हिंदी)"           : "Hindi",
    "English + Hindi"         : "Both",
    "Marathi (मराठी)"         : "Marathi",
    "Gujarati (ગુજરાતી)"      : "Gujarati",
    "Bengali (বাংলা)"         : "Bengali",
    "Tamil (தமிழ்)"           : "Tamil",
    "Telugu (తెలుగు)"         : "Telugu",
    "Kannada (ಕನ್ನಡ)"        : "Kannada",
    "Malayalam (മലയാളം)"     : "Malayalam",
}

import os, html
import streamlit as st
from dotenv import load_dotenv
from utils.analyzer import extract_text_from_pdf, extract_text_from_txt, segment_into_clauses, analyze_contract
from utils.report_generator import generate_pdf_report, final_recommendation

load_dotenv()
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

SAMPLE_CONTRACT = """
SERVICE AGREEMENT

1. PAYMENT TERMS
The Client shall pay the Service Provider within 7 days of invoice.
Late payments shall accrue interest at 24% per annum.
The Service Provider may suspend services without notice if payment is delayed.

2. INTELLECTUAL PROPERTY
All work product, inventions, and deliverables created under this agreement shall
be exclusively and irrevocably assigned to the Client. The Service Provider
waives all moral rights and claims perpetual license to showcase the work.

3. NON-COMPETE
The Service Provider agrees not to work for any competing business for a period
of 2 years after termination, within India, without prior written consent.
Violation shall result in liquidated damages of Rs. 5,00,000.

4. TERMINATION
The Client may terminate this agreement at any time, at their sole discretion,
without notice and without any compensation to the Service Provider for work
in progress or future expected earnings.

5. CONFIDENTIALITY
Both parties agree to maintain confidentiality of proprietary information shared
during the term of this agreement and for 3 years thereafter.

6. GOVERNING LAW
Any dispute arising from this agreement shall be subject to binding arbitration
only and the Service Provider waives the right to pursue class action or jury trial.

7. LIABILITY
The Client's liability shall be limited to the fees paid in the last 30 days.
The Client is not liable for any indirect, consequential, or incidental damages.

8. PAYMENT SCHEDULE
The Service Provider shall be paid Rs. 50,000 per month for services rendered.
Payment is non-refundable under all circumstances.
"""

st.set_page_config(page_title="AI Contract Risk Analyzer", page_icon="⚖️", layout="wide", initial_sidebar_state="expanded")

# ════════════════════════════════════════════════════
#  PREMIUM CSS — Legal-tech SaaS dark theme
#  Colors: #E63939 High Risk | #F57C00 Warning | #2E7D32 Safe
#  Background: #0F1117 | Cards: #1E222B
# ════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #0F1117 !important;
    color: #E8EAF0 !important;
    -webkit-font-smoothing: antialiased;
}
#MainMenu, footer, header { visibility: hidden; }
.main .block-container { padding: 2rem 2.5rem 4rem !important; max-width: 1200px !important; }

/* ── HERO HEADER ── */
.hero {
    background: linear-gradient(160deg, #161A24 0%, #0F1117 60%, #1A0F24 100%);
    border: 1px solid #252A35;
    border-top: 3px solid #E63939;
    border-radius: 12px;
    padding: 2.8rem 2.4rem 2.4rem;
    margin-bottom: 1.8rem;
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: '';
    position: absolute; right: -40px; top: -40px;
    width: 240px; height: 240px;
    background: radial-gradient(circle, rgba(230,57,57,0.06) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.hero-eyebrow {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 2.5px;
    text-transform: uppercase; color: #E63939;
    margin-bottom: 0.75rem;
}
.hero-title {
    font-size: 2.6rem; font-weight: 800; letter-spacing: -1px;
    color: #F1F3F9; line-height: 1.15; margin-bottom: 0.6rem;
}
.hero-title span { color: #E63939; }
.hero-sub { font-size: 1rem; color: #6B7280; font-weight: 400; max-width: 500px; }

/* ── PRIVACY NOTICE ── */
.privacy-notice {
    display: flex; align-items: center; gap: 0.6rem;
    background: rgba(46,125,50,0.06); border: 1px solid rgba(46,125,50,0.2);
    border-radius: 8px; padding: 0.6rem 1rem;
    font-size: 0.78rem; color: #66BB6A; margin-bottom: 1.5rem;
}

/* ── SECTION HEADING ── */
.section-heading {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #4B5563;
    margin: 2rem 0 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1E222B;
}

/* ── DASHBOARD GRID ── */
.dash-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1rem; margin-bottom: 1.5rem;
}
.dash-card {
    background: #1E222B; border-radius: 10px;
    padding: 1.4rem 1.2rem; text-align: center;
    border: 1px solid #252A35;
    transition: transform 0.15s, box-shadow 0.15s;
    position: relative; overflow: hidden;
}
.dash-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.4); }
.dash-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.dc-total::before { background: #3B82F6; }
.dc-safe::before  { background: #2E7D32; }
.dc-warn::before  { background: #F57C00; }
.dc-high::before  { background: #E63939; }
.dash-num {
    font-size: 2.8rem; font-weight: 800; line-height: 1; margin-bottom: 0.25rem;
}
.dc-total .dash-num { color: #60A5FA; }
.dc-safe  .dash-num { color: #4CAF50; }
.dc-warn  .dash-num { color: #FF9800; }
.dc-high  .dash-num { color: #EF5350; }
.dash-label { font-size: 0.7rem; color: #6B7280; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase; }

/* ── RECOMMENDATION BANNER ── */
.rec-card {
    border-radius: 10px; padding: 1.4rem 1.6rem;
    display: flex; align-items: center; gap: 1.2rem;
    margin-bottom: 2rem;
}
.rec-icon-wrap { font-size: 2.2rem; flex-shrink: 0; }
.rec-label { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.2rem; }
.rec-detail { font-size: 0.85rem; opacity: 0.78; }
.rec-safe    { background: rgba(46,125,50,0.1);  border: 1px solid rgba(46,125,50,0.35);  }
.rec-warn    { background: rgba(245,124,0,0.1);  border: 1px solid rgba(245,124,0,0.35);  }
.rec-danger  { background: rgba(230,57,57,0.1);  border: 1px solid rgba(230,57,57,0.35);  }
.rec-safe   .rec-label { color: #4CAF50; }
.rec-warn   .rec-label { color: #FF9800; }
.rec-danger .rec-label { color: #EF5350; }

/* ── CLAUSE CARD ── */
.clause-card {
    background: #1E222B;
    border: 1px solid #252A35;
    border-left: 4px solid;
    border-radius: 10px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.4rem;
    position: relative;
    transition: box-shadow 0.2s;
}
.clause-card:hover { box-shadow: 0 4px 24px rgba(0,0,0,0.45); }
.c-high    { border-left-color: #E63939; }
.c-warning { border-left-color: #F57C00; }
.c-safe    { border-left-color: #2E7D32; }

.clause-toprow {
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 1rem;
}
.clause-num { font-size: 0.62rem; font-weight: 700; letter-spacing: 2px; color: #4B5563; text-transform: uppercase; }
.risk-badge {
    font-size: 0.66rem; font-weight: 700; padding: 4px 12px;
    border-radius: 6px; letter-spacing: 0.8px; text-transform: uppercase;
}
.badge-high    { background: rgba(230,57,57,0.15);  color: #EF5350; border: 1px solid rgba(230,57,57,0.4); }
.badge-warning { background: rgba(245,124,0,0.15);  color: #FF9800; border: 1px solid rgba(245,124,0,0.4); }
.badge-safe    { background: rgba(46,125,50,0.12);  color: #4CAF50; border: 1px solid rgba(46,125,50,0.35); }

.clause-text-quote {
    font-size: 0.83rem; color: #4B5563; line-height: 1.6;
    font-style: italic;
    border-left: 2px solid #252A35; padding-left: 1rem;
    margin-bottom: 1.5rem;
}

.field-label {
    font-size: 0.61rem; font-weight: 700; letter-spacing: 1.8px;
    text-transform: uppercase; color: #6B7280; margin-bottom: 0.35rem;
}
.field-value {
    font-size: 0.9rem; line-height: 1.75; color: #D1D5DB;
    margin-bottom: 1.3rem;
    white-space: pre-wrap;
}
.rewrite-block {
    background: rgba(59,130,246,0.05);
    border: 1px solid rgba(59,130,246,0.18);
    border-radius: 8px; padding: 1.1rem 1.3rem;
    font-size: 0.88rem; line-height: 1.75;
    color: #93C5FD; white-space: pre-wrap; margin-top: 0.3rem;
}
.field-divider { border: none; border-top: 1px solid #252A35; margin: 1rem 0; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #0A0C12 !important;
    border-right: 1px solid #1E222B !important;
}
.sb-logo {
    font-size: 1rem; font-weight: 700; color: #F1F3F9;
    padding-bottom: 1.2rem; margin-bottom: 1.2rem;
    border-bottom: 1px solid #1E222B;
    display: flex; align-items: center; gap: 0.5rem;
}
.sb-dot { width: 8px; height: 8px; border-radius: 50%; background: #E63939; flex-shrink: 0; }
.sb-section { font-size: 0.6rem; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #4B5563; margin: 1.5rem 0 0.5rem; }

/* ── BUTTONS ── */
.stButton > button {
    background: #E63939 !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; font-size: 0.9rem !important;
    padding: 0.65rem 1.4rem !important; width: 100% !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 2px 12px rgba(230,57,57,0.3) !important;
    transition: opacity 0.15s, box-shadow 0.15s !important;
}
.stButton > button:hover { opacity: 0.88 !important; box-shadow: 0 4px 20px rgba(230,57,57,0.45) !important; }
.stDownloadButton > button {
    background: rgba(46,125,50,0.1) !important; color: #4CAF50 !important;
    border: 1px solid rgba(46,125,50,0.35) !important;
    border-radius: 8px !important; font-weight: 600 !important; width: 100% !important;
}

/* ── STREAMLIT COMPONENTS ── */
.stProgress > div > div { background: #E63939 !important; }
.stFileUploader { background: #1E222B !important; border-radius: 8px !important; }
.stTabs [data-baseweb="tab-list"] {
    background: #1E222B; border-radius: 8px; gap: 2px; padding: 4px;
    border: 1px solid #252A35;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px !important; color: #4B5563 !important;
    font-size: 0.82rem !important; font-weight: 500 !important;
    padding: 0.45rem 1rem !important;
}
.stTabs [aria-selected="true"] { background: #252A35 !important; color: #E8EAF0 !important; }
div[data-testid="stMarkdownContainer"] p { color: #9CA3AF; }
.stSelectbox > div > div { background: #1E222B !important; border-color: #252A35 !important; }
[data-testid="stCheckbox"] { color: #9CA3AF; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sb-logo"><div class="sb-dot"></div>Contract Analyzer</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section">Your Role</div>', unsafe_allow_html=True)
    user_role = st.selectbox("role", [
        "Student", "Freelancer / Consultant", "Tenant / House Renter",
        "Employee / Job Seeker", "Business Owner / Entrepreneur",
        "Startup Founder", "NRI / Overseas Indian", "Senior Citizen",
        "Other (General User)",
    ], label_visibility="collapsed")

    st.markdown('<div class="sb-section">Output Language</div>', unsafe_allow_html=True)
    lang_display = st.selectbox("lang", list(LANG_OPTIONS.keys()), label_visibility="collapsed")
    lang_key = LANG_OPTIONS[lang_display]

    st.markdown('<div class="sb-section">API Status</div>', unsafe_allow_html=True)
    if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
        st.success("✅ API key loaded")
    else:
        st.error("❌ API key not found\nAdd GROQ_API_KEY to .env")

    st.markdown("---")
    with st.expander("How It Works"):
        st.markdown("""
1. Select **role** and **language**
2. Upload a **PDF or TXT** contract
3. Click **Analyze Contract**
4. View clause-by-clause risk results
5. Download **PDF report**

**Risk Levels:**
🔴 HIGH RISK — Reject or negotiate
🟡 WARNING — Review carefully
🟢 SAFE — Generally fair
        """)
    st.markdown(
        "<small style='color:#374151;'>AI-powered · Indian Contract Law<br>Built with ❤️ by college students</small>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════
def badge_css(level):
    return {"HIGH RISK": "badge-high", "WARNING": "badge-warning", "SAFE": "badge-safe"}.get(level, "badge-safe")

def card_css(level):
    return {"HIGH RISK": "c-high", "WARNING": "c-warning", "SAFE": "c-safe"}.get(level, "c-safe")

def level_icon(level):
    return {"HIGH RISK": "❌", "WARNING": "⚠️", "SAFE": "✅"}.get(level, "•")


def render_clause_card(r: dict):
    """
    Renders one clause analysis card.
    html.escape() on ALL LLM text prevents raw HTML tags from appearing.
    """
    lv   = r["risk_level"]
    num  = r["clause_number"]
    icon = level_icon(lv)

    raw   = html.escape(r["clause_text"][:280] + ("…" if len(r["clause_text"]) > 280 else ""))
    expl  = html.escape(r["explanation"])
    cons  = html.escape(r["consequence"])
    act   = html.escape(r["action"])
    rew   = html.escape(r["rewrite"])

    st.markdown(f"""
<div class="clause-card {card_css(lv)}">
  <div class="clause-toprow">
    <span class="clause-num">Clause {num}</span>
    <span class="risk-badge {badge_css(lv)}">{icon} {lv}</span>
  </div>
  <div class="clause-text-quote">"{raw}"</div>
  <div class="field-label">📌 What It Means</div>
  <div class="field-value">{expl}</div>
  <hr class="field-divider"/>
  <div class="field-label">⚡ Consequence</div>
  <div class="field-value">{cons}</div>
  <hr class="field-divider"/>
  <div class="field-label">🔧 What To Do</div>
  <div class="field-value">{act}</div>
  <hr class="field-divider"/>
  <div class="field-label">✏️ Safer Version</div>
  <div class="rewrite-block">{rew}</div>
</div>
""", unsafe_allow_html=True)


def render_dashboard(results: list):
    high  = sum(1 for r in results if r["risk_level"] == "HIGH RISK")
    warn  = sum(1 for r in results if r["risk_level"] == "WARNING")
    safe  = sum(1 for r in results if r["risk_level"] == "SAFE")
    total = len(results)

    # ── Metric cards
    st.markdown(f"""
<div class="dash-grid">
  <div class="dash-card dc-total">
    <div class="dash-num">{total}</div>
    <div class="dash-label">Total Clauses</div>
  </div>
  <div class="dash-card dc-safe">
    <div class="dash-num">{safe}</div>
    <div class="dash-label">Safe</div>
  </div>
  <div class="dash-card dc-warn">
    <div class="dash-num">{warn}</div>
    <div class="dash-label">Warning</div>
  </div>
  <div class="dash-card dc-high">
    <div class="dash-num">{high}</div>
    <div class="dash-label">High Risk</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Recommendation
    rec_label, rec_detail = final_recommendation(results)
    if high == 0 and warn <= 2:
        r_css, r_icon = "rec-safe", "✅"
    elif high <= 2:
        r_css, r_icon = "rec-warn", "⚠️"
    else:
        r_css, r_icon = "rec-danger", "❌"

    st.markdown(f"""
<div class="rec-card {r_css}">
  <div class="rec-icon-wrap">{r_icon}</div>
  <div>
    <div class="rec-label">{html.escape(rec_label)}</div>
    <div class="rec-detail">{html.escape(rec_detail)}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">⚖️ AI-Powered Legal Analysis</div>
  <div class="hero-title">Contract <span>Risk</span> Analyzer</div>
  <div class="hero-sub">Upload any contract and get an instant, clause-by-clause risk breakdown in plain language.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-notice">
  🔒 <strong>Privacy First</strong> &nbsp;—&nbsp; Documents are processed in-memory only and never stored or shared.
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-heading">Upload Contract</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload", type=["pdf", "txt"], label_visibility="collapsed")
use_sample    = st.checkbox("Use sample contract (demo mode)", value=False)

st.markdown("<br>", unsafe_allow_html=True)
analyze_clicked = st.button("🔍  Analyze Contract", use_container_width=True)

# ── Analysis pipeline
if analyze_clicked:
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        st.error("❌ No API key. Add GROQ_API_KEY to your .env file.")
        st.stop()
    if not uploaded_file and not use_sample:
        st.warning("Please upload a contract or enable demo mode.")
        st.stop()

    with st.spinner("Extracting text from document…"):
        if use_sample:
            contract_text = SAMPLE_CONTRACT
        elif uploaded_file.type == "application/pdf":
            contract_text = extract_text_from_pdf(uploaded_file)
        else:
            contract_text = extract_text_from_txt(uploaded_file)

    if len(contract_text.strip()) < 80:
        st.error("Could not extract enough text. Try a different file.")
        st.stop()

    st.success(f"✅ Extracted {len(contract_text):,} characters")

    with st.spinner("Segmenting into clauses…"):
        clauses = segment_into_clauses(contract_text)

    st.info(f"Found **{len(clauses)} clauses** — running AI analysis ({lang_key})…")

    bar = st.progress(0, text="Analyzing with AI…")
    try:
        results = analyze_contract(GROQ_API_KEY, user_role, clauses, lang_key)
        bar.progress(100, text="Analysis complete")
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        st.stop()

    st.session_state["results"]   = results
    st.session_state["user_role"] = user_role

# ── Results display
if "results" in st.session_state:
    results   = st.session_state["results"]
    user_role = st.session_state["user_role"]

    st.markdown("---")
    st.markdown('<div class="section-heading">Risk Dashboard</div>', unsafe_allow_html=True)
    render_dashboard(results)

    # PDF export
    st.markdown('<div class="section-heading">Export Report</div>', unsafe_allow_html=True)
    with st.spinner("Generating PDF…"):
        pdf_bytes = generate_pdf_report(results, user_role)
    st.download_button(
        "⬇️  Download Full PDF Report",
        data=pdf_bytes, file_name="contract_risk_analysis.pdf",
        mime="application/pdf", use_container_width=True,
    )

    st.markdown("---")
    st.markdown('<div class="section-heading">Clause-by-Clause Analysis</div>', unsafe_allow_html=True)

    n_high = sum(1 for r in results if r["risk_level"] == "HIGH RISK")
    n_warn = sum(1 for r in results if r["risk_level"] == "WARNING")
    n_safe = sum(1 for r in results if r["risk_level"] == "SAFE")

    tab_all, tab_high, tab_warn, tab_safe = st.tabs([
        f"All  ({len(results)})",
        f"High Risk  ({n_high})",
        f"Warning  ({n_warn})",
        f"Safe  ({n_safe})",
    ])
    with tab_all:
        st.markdown("")
        for r in results:
            render_clause_card(r)
    with tab_high:
        st.markdown("")
        hrs = [r for r in results if r["risk_level"] == "HIGH RISK"]
        if hrs:
            for r in hrs: render_clause_card(r)
        else:
            st.success("No HIGH RISK clauses found.")
    with tab_warn:
        st.markdown("")
        wrs = [r for r in results if r["risk_level"] == "WARNING"]
        if wrs:
            for r in wrs: render_clause_card(r)
        else:
            st.success("No WARNING clauses found.")
    with tab_safe:
        st.markdown("")
        srs = [r for r in results if r["risk_level"] == "SAFE"]
        if srs:
            for r in srs: render_clause_card(r)
        else:
            st.info("No purely SAFE clauses.")

# ── Footer
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#374151;font-size:0.72rem;padding:0.5rem 0'>"
    "⚖️ AI Contract Risk Analyzer &nbsp;·&nbsp; Free to use &nbsp;·&nbsp; Built with ❤️ by college students<br>"
    "<em>AI-generated analysis only — not legal advice. Consult a qualified lawyer before signing.</em>"
    "</div>",
    unsafe_allow_html=True
)
