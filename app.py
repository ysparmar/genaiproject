# ── Language display names → backend keys
LANG_OPTIONS = {
    "English"                    : "English",
    "Hindi (हिंदी)"              : "Hindi",
    "English + Hindi"            : "Both",
    "Marathi (मराठी)"            : "Marathi",
    "Gujarati (ગુજરાતી)"         : "Gujarati",
    "Bengali (বাংলা)"            : "Bengali",
    "Tamil (தமிழ்)"              : "Tamil",
    "Telugu (తెలుగు)"            : "Telugu",
    "Kannada (ಕನ್ನಡ)"           : "Kannada",
    "Malayalam (മലയാളം)"        : "Malayalam",
}

import os
import html
import streamlit as st
from dotenv import load_dotenv
from utils.analyzer import (
    extract_text_from_pdf, extract_text_from_txt,
    segment_into_clauses, analyze_contract,
)
from utils.report_generator import generate_pdf_report, final_recommendation

# ── API Key (works both locally via .env AND on Streamlit Cloud via secrets)
load_dotenv()
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── Sample contract for demo/testing
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

# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Contract Risk Analyzer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════
#  PREMIUM CSS — Clean Legal-Tech Dark Theme
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #0B0D17 !important;
    color: #E2E8F6 !important;
}
#MainMenu, footer, header { visibility: hidden; }
.main .block-container { padding: 1.5rem 2.5rem 3rem !important; max-width: 1280px !important; }

/* ── HERO ── */
.hero {
    background: linear-gradient(135deg, #111829 0%, #0B0D17 55%, #180A2E 100%);
    border: 1px solid #2A3560;
    border-radius: 20px;
    padding: 3rem 2rem 2.5rem;
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 60px rgba(99,102,241,0.08);
}
.hero::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6366F1, #A855F7, #06B6D4, #10B981);
}
.hero::after {
    content: '';
    position: absolute; top: -60px; right: -60px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.hero-badge {
    display: inline-block;
    background: rgba(99,102,241,0.15);
    border: 1px solid rgba(99,102,241,0.4);
    color: #A5B4FC;
    font-size: 0.7rem; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase;
    padding: 5px 16px; border-radius: 20px; margin-bottom: 1rem;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3rem; font-weight: 700; letter-spacing: -1.5px;
    background: linear-gradient(135deg, #FFFFFF 0%, #C7D2FE 50%, #A5B4FC 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 0.7rem; line-height: 1.1;
}
.hero-sub { font-size: 1rem; color: #6B7DB3; max-width: 540px; margin: 0 auto; }

/* ── PRIVACY BAR ── */
.privacy-bar {
    background: rgba(6,182,212,0.07);
    border: 1px solid rgba(6,182,212,0.22);
    border-radius: 10px; padding: 0.6rem 1.2rem;
    font-size: 0.78rem; color: #67E8F9; text-align: center; margin-bottom: 1.5rem;
}

/* ── SECTION LABELS ── */
.sec-label {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #818CF8;
    margin: 1.8rem 0 0.7rem;
}

/* ── METRICS GRID ── */
.metrics-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1rem; margin-bottom: 1.5rem;
}
.metric-box {
    border-radius: 16px; padding: 1.3rem 1rem;
    text-align: center; position: relative; overflow: hidden;
    transition: transform 0.2s;
}
.metric-box:hover { transform: translateY(-2px); }
.m-total { background: linear-gradient(135deg,#1E2560,#111829); border: 1px solid #2A3580; }
.m-safe  { background: linear-gradient(135deg,#052E16,#0B1B10); border: 1px solid #166534; }
.m-warn  { background: linear-gradient(135deg,#451A03,#1C0F02); border: 1px solid #92400E; }
.m-high  { background: linear-gradient(135deg,#450A0A,#1C0505); border: 1px solid #991B1B; }
.metric-val {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem; font-weight: 700; line-height: 1; margin-bottom: 0.3rem;
}
.m-total .metric-val { color: #818CF8; }
.m-safe  .metric-val { color: #4ADE80; }
.m-warn  .metric-val { color: #FCD34D; }
.m-high  .metric-val { color: #F87171; }
.metric-lbl { font-size: 0.72rem; color: #94A3B8; font-weight: 500; letter-spacing: 0.5px; }

/* ── RECOMMENDATION BANNER ── */
.rec-banner {
    border-radius: 14px; padding: 1.3rem 1.8rem;
    margin-bottom: 1.5rem; display: flex; align-items: center; gap: 1rem;
}
.rec-icon { font-size: 2rem; }
.rec-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.2rem; }
.rec-desc  { font-size: 0.85rem; opacity: 0.8; }
.rec-safe    { background: rgba(74,222,128,0.07); border: 1px solid rgba(74,222,128,0.3); }
.rec-warning { background: rgba(252,211,77,0.07); border: 1px solid rgba(252,211,77,0.3); }
.rec-danger  { background: rgba(248,113,113,0.07); border: 1px solid rgba(248,113,113,0.3); }
.rec-safe    .rec-title { color: #4ADE80; }
.rec-warning .rec-title { color: #FCD34D; }
.rec-danger  .rec-title { color: #F87171; }

/* ── CLAUSE CARDS ── */
.clause-card {
    background: #111828;
    border: 1px solid #1E2A45;
    border-radius: 16px; padding: 1.8rem 2rem;
    margin-bottom: 1.5rem; position: relative; overflow: hidden;
    transition: border-color 0.25s, box-shadow 0.25s;
}
.clause-card:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
.clause-card::before {
    content: '';
    position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
    border-radius: 4px 0 0 4px;
}
.card-HIGH    { border-color: rgba(248,113,113,0.35); }
.card-HIGH::before    { background: linear-gradient(180deg,#EF4444,#F87171); }
.card-WARNING { border-color: rgba(252,211,77,0.35); }
.card-WARNING::before { background: linear-gradient(180deg,#F59E0B,#FCD34D); }
.card-SAFE    { border-color: rgba(74,222,128,0.3); }
.card-SAFE::before    { background: linear-gradient(180deg,#10B981,#4ADE80); }

.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.card-num { font-size: 0.65rem; font-weight: 700; letter-spacing: 2px; color: #4B5E8A; text-transform: uppercase; }
.risk-pill { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.8px; padding: 4px 14px; border-radius: 20px; text-transform: uppercase; }
.pill-HIGH    { background: rgba(239,68,68,0.18);  color: #FCA5A5; border: 1px solid rgba(239,68,68,0.5); }
.pill-WARNING { background: rgba(245,158,11,0.18); color: #FDE68A; border: 1px solid rgba(245,158,11,0.5); }
.pill-SAFE    { background: rgba(16,185,129,0.15); color: #6EE7B7; border: 1px solid rgba(16,185,129,0.4); }

.clause-quote {
    font-size: 0.83rem; color: #3D5273; line-height: 1.65;
    border-left: 2px solid #1E2A45; padding-left: 1rem;
    margin-bottom: 1.5rem; margin-top: 0.5rem; font-style: italic;
}
.detail-row { margin-bottom: 1.3rem; }
.detail-key {
    font-size: 0.63rem; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: #818CF8; margin-bottom: 0.4rem;
}
.detail-val { font-size: 0.88rem; line-height: 1.75; color: #CBD5E1; white-space: pre-wrap; }
.rewrite-box {
    background: rgba(99,102,241,0.07);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 10px; padding: 1.1rem 1.3rem; margin-top: 0.4rem;
    font-size: 0.86rem; line-height: 1.75; color: #C7D2FE; white-space: pre-wrap;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #080A12 !important;
    border-right: 1px solid #141B30 !important;
}
.sidebar-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.15rem; font-weight: 700; color: #E2E8F6;
    margin-bottom: 1.5rem; padding-bottom: 1rem;
    border-bottom: 1px solid #141B30;
}
.sidebar-section {
    font-size: 0.63rem; font-weight: 700; letter-spacing: 1.8px;
    text-transform: uppercase; color: #818CF8; margin: 1.3rem 0 0.5rem;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 0.93rem !important; padding: 0.65rem 1.5rem !important;
    width: 100% !important; letter-spacing: 0.3px !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.35) !important;
    transition: opacity 0.2s, box-shadow 0.2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; box-shadow: 0 6px 28px rgba(99,102,241,0.5) !important; }
.stDownloadButton > button {
    background: rgba(16,185,129,0.1) !important; color: #4ADE80 !important;
    border: 1px solid rgba(74,222,128,0.35) !important;
    border-radius: 10px !important; font-weight: 600 !important; width: 100% !important;
}
.stProgress > div > div { background: linear-gradient(90deg,#6366F1,#A855F7) !important; }
.stFileUploader { background: #111828 !important; border-radius: 12px !important; }
.stTabs [data-baseweb="tab-list"] { background: #111828; border-radius: 10px; gap: 4px; padding: 4px; border: 1px solid #1E2A45; }
.stTabs [data-baseweb="tab"] { border-radius: 8px !important; color: #4B5E8A !important; font-size: 0.83rem !important; font-weight: 500 !important; }
.stTabs [aria-selected="true"] { background: #1E2A45 !important; color: #A5B4FC !important; }
div[data-testid="stMarkdownContainer"] p { color: #CBD5E1; }
</style>
""", unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sidebar-logo">⚖️ Contract Analyzer</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Your Role</div>', unsafe_allow_html=True)
    user_role = st.selectbox(
        "role",
        [
            "Student",
            "Freelancer / Consultant",
            "Tenant / House Renter",
            "Employee / Job Seeker",
            "Business Owner / Entrepreneur",
            "Startup Founder",
            "NRI / Overseas Indian",
            "Senior Citizen",
            "Other (General User)",
        ],
        label_visibility="collapsed"
    )

    st.markdown('<div class="sidebar-section">Output Language</div>', unsafe_allow_html=True)
    lang_display = st.selectbox(
        "lang", list(LANG_OPTIONS.keys()), label_visibility="collapsed"
    )
    lang_key = LANG_OPTIONS[lang_display]

    st.markdown('<div class="sidebar-section">API Status</div>', unsafe_allow_html=True)
    if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
        st.success("✅ API key loaded")
    else:
        st.error("❌ API key not found\nAdd GROQ_API_KEY to .env")

    st.markdown("---")
    with st.expander("📖 How It Works"):
        st.markdown("""
1. Select your **role** + **language**
2. Upload a **PDF or TXT** contract
3. Click **Analyze Contract**
4. View results by risk tab
5. Download **PDF report**

**Risk Levels:**
🔴 HIGH RISK — Negotiate or reject  
🟡 WARNING — Ask questions  
🟢 SAFE — Generally fair
        """)
    st.markdown(
        "<small style='color:#334155;'>AI-powered · Indian Contract Law<br>Built with ❤️ by college students</small>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════
def css_class(level: str) -> str:
    return {"HIGH RISK": "HIGH", "WARNING": "WARNING", "SAFE": "SAFE"}.get(level, "SAFE")

def pill_icon(level: str) -> str:
    return {"HIGH RISK": "❌", "WARNING": "⚠️", "SAFE": "✅"}.get(level, "•")

def render_clause_card(r: dict):
    """
    Render a single clause card.
    CRITICAL: html.escape() is applied to ALL LLM-generated text
    before inserting into HTML — this prevents raw tags from appearing.
    """
    level = r["risk_level"]
    css   = css_class(level)
    icon  = pill_icon(level)
    num   = r["clause_number"]

    # ── Escape all dynamic content to prevent HTML injection / broken tags ──
    raw_text    = html.escape(r["clause_text"][:300] + ("…" if len(r["clause_text"]) > 300 else ""))
    explanation = html.escape(r["explanation"])
    consequence = html.escape(r["consequence"])
    action      = html.escape(r["action"])
    rewrite     = html.escape(r["rewrite"])

    st.markdown(f"""
<div class="clause-card card-{css}">
  <div class="card-top">
    <span class="card-num">Clause {num}</span>
    <span class="risk-pill pill-{css}">{icon} {level}</span>
  </div>
  <div class="clause-quote">"{raw_text}"</div>
  <div class="detail-row">
    <div class="detail-key">📌 What It Means</div>
    <div class="detail-val">{explanation}</div>
  </div>
  <div class="detail-row">
    <div class="detail-key">⚡ Consequence</div>
    <div class="detail-val">{consequence}</div>
  </div>
  <div class="detail-row">
    <div class="detail-key">🔧 What To Do</div>
    <div class="detail-val">{action}</div>
  </div>
  <div class="detail-key">✏️ Safer Version</div>
  <div class="rewrite-box">{rewrite}</div>
</div>
""", unsafe_allow_html=True)


def render_dashboard(results: list[dict]):
    high  = sum(1 for r in results if r["risk_level"] == "HIGH RISK")
    warn  = sum(1 for r in results if r["risk_level"] == "WARNING")
    safe  = sum(1 for r in results if r["risk_level"] == "SAFE")
    total = len(results)

    st.markdown(f"""
<div class="metrics-grid">
  <div class="metric-box m-total">
    <div class="metric-val">{total}</div>
    <div class="metric-lbl">Total Clauses</div>
  </div>
  <div class="metric-box m-safe">
    <div class="metric-val">{safe}</div>
    <div class="metric-lbl">✅ Safe</div>
  </div>
  <div class="metric-box m-warn">
    <div class="metric-val">{warn}</div>
    <div class="metric-lbl">⚠ Warning</div>
  </div>
  <div class="metric-box m-high">
    <div class="metric-val">{high}</div>
    <div class="metric-lbl">❌ High Risk</div>
  </div>
</div>
""", unsafe_allow_html=True)

    rec_label, rec_detail = final_recommendation(results)
    if high == 0 and warn <= 2:
        css_r, icon_r = "rec-safe", "✅"
    elif high <= 2:
        css_r, icon_r = "rec-warning", "⚠️"
    else:
        css_r, icon_r = "rec-danger", "❌"

    # Escape recommendation text too
    rec_label_esc  = html.escape(rec_label)
    rec_detail_esc = html.escape(rec_detail)

    st.markdown(f"""
<div class="rec-banner {css_r}">
  <div class="rec-icon">{icon_r}</div>
  <div>
    <div class="rec-title">{rec_label_esc}</div>
    <div class="rec-desc">{rec_detail_esc}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="hero-badge">⚖️ Legal AI · Indian Contract Act 1872</div>
  <div class="hero-title">AI Contract Risk Analyzer</div>
  <div class="hero-sub">Upload any contract — get instant risk analysis in plain English or Hindi</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="privacy-bar">
  🔒 Privacy First — Your documents are processed in-memory only and are never stored or shared.
</div>
""", unsafe_allow_html=True)

# ── Upload ──
st.markdown('<div class="sec-label">📄 Upload Contract</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Upload contract", type=["pdf", "txt"], label_visibility="collapsed"
)
use_sample = st.checkbox("🧪 Use sample contract (for demo)", value=False)

st.markdown("")
analyze_clicked = st.button("🔍 Analyze Contract", use_container_width=True)

# ── Analysis ──
if analyze_clicked:
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        st.error("❌ Set your GROQ_API_KEY in .env before analyzing.")
        st.stop()
    if not uploaded_file and not use_sample:
        st.warning("⚠️ Upload a contract or check 'Use sample contract'.")
        st.stop()

    with st.spinner("📄 Extracting text…"):
        if use_sample:
            contract_text = SAMPLE_CONTRACT
        elif uploaded_file.type == "application/pdf":
            contract_text = extract_text_from_pdf(uploaded_file)
        else:
            contract_text = extract_text_from_txt(uploaded_file)

    if not contract_text or len(contract_text.strip()) < 80:
        st.error("❌ Could not extract enough text. Try a different file.")
        st.stop()

    st.success(f"✅ Extracted {len(contract_text):,} characters.")

    with st.spinner("✂️ Segmenting into clauses…"):
        clauses = segment_into_clauses(contract_text)

    st.info(f"📋 Found **{len(clauses)} clauses** — analyzing ({lang_key})…")

    progress = st.progress(0, text="Sending to AI engine…")
    try:
        results = analyze_contract(GROQ_API_KEY, user_role, clauses, lang_key)
        progress.progress(100, text="Analysis complete!")
    except Exception as e:
        st.error(f"❌ Analysis failed: {e}")
        st.info("Check API key · Reduce file size · Try again.")
        st.stop()

    st.session_state["results"]   = results
    st.session_state["user_role"] = user_role

# ── Display Results ──
if "results" in st.session_state:
    results   = st.session_state["results"]
    user_role = st.session_state["user_role"]

    st.markdown("---")
    st.markdown('<div class="sec-label">📊 Final Decision Dashboard</div>', unsafe_allow_html=True)
    render_dashboard(results)

    # PDF Download
    st.markdown('<div class="sec-label">📥 Export</div>', unsafe_allow_html=True)
    with st.spinner("Generating PDF…"):
        pdf_bytes = generate_pdf_report(results, user_role)
    st.download_button(
        "⬇️ Download Full PDF Report",
        data=pdf_bytes,
        file_name="contract_risk_analysis.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown('<div class="sec-label">📋 Clause-by-Clause Analysis</div>', unsafe_allow_html=True)

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
            st.success("No HIGH RISK clauses found!")
    with tab_warn:
        st.markdown("")
        wrs = [r for r in results if r["risk_level"] == "WARNING"]
        if wrs:
            for r in wrs: render_clause_card(r)
        else:
            st.success("No WARNING clauses found!")
    with tab_safe:
        st.markdown("")
        srs = [r for r in results if r["risk_level"] == "SAFE"]
        if srs:
            for r in srs: render_clause_card(r)
        else:
            st.info("No purely SAFE clauses.")

# ── Footer ──
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#1E293B;font-size:0.75rem;padding:0.5rem 0'>"
    "⚖️ AI Contract Risk Analyzer · Free to use · Built with ❤️ by college students<br>"
    "<em>AI-generated analysis only — not legal advice. Consult a qualified lawyer before signing.</em>"
    "</div>",
    unsafe_allow_html=True
)
