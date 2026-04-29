# ============================================================
#  AI CONTRACT RISK ANALYZER
#  app.py  —  Main Streamlit Application
#
#  Author   : Nikhil Parmar
#  License  : MIT
#
#  HOW IT WORKS (for presentation / viva):
#  ────────────────────────────────────────
#  1. User selects their role (Student / Freelancer / Tenant / Employee)
#  2. User uploads a PDF or TXT contract file
#  3. PyMuPDF extracts raw text from the PDF
#  4. Text is split into logical clauses (sentences / paragraphs)
#  5. Each clause is pre-screened with keyword rules (fast, offline)
#  6. All clauses sent together to Groq LLM (LLaMA-3.1-70b) for
#     deep semantic analysis
#  7. LLM returns structured data: risk level, explanation,
#     consequence, action suggestion, and safer rewrite
#  8. Results displayed in a beautiful dashboard with risk cards
#  9. User can download a professional PDF report
# ============================================================

import os
import streamlit as st
from dotenv import load_dotenv

# ── Import our custom modules ──────────────────────────────
from utils.analyzer import (
    extract_text_from_pdf,
    extract_text_from_txt,
    segment_into_clauses,
    analyze_contract,
)
from utils.report_generator import generate_pdf_report, final_recommendation

# ── Load API key ────────────────────────────────────────────
# Strategy:
#   1. Try Streamlit Secrets first  → used when deployed on Streamlit Cloud
#   2. Fall back to .env file       → used when running locally
# This way the same code works BOTH locally and in production.
load_dotenv()  # loads .env if present (no-op on Streamlit Cloud)
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]   # Streamlit Cloud secrets
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # local .env fallback


# ══════════════════════════════════════════════════════════
#  PAGE CONFIGURATION
#  Must be the FIRST Streamlit call in the script.
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Contract Risk Analyzer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════
#  CUSTOM CSS — Premium Dark Theme
#  All visual styling lives here. We inject raw CSS using
#  st.markdown with unsafe_allow_html=True.
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #0F1117 !important;
    color: #E8EAF0 !important;
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Main container ── */
.main .block-container {
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1200px !important;
}

/* ── Hero header ── */
.hero-header {
    background: linear-gradient(135deg, #1A1D2E 0%, #0F1117 50%, #1a0a2e 100%);
    border: 1px solid #2A2D3E;
    border-radius: 16px;
    padding: 2.5rem 2rem;
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #4F8EF7, #8B5CF6, #E63939);
}
.hero-title {
    font-size: 2.6rem; font-weight: 800; letter-spacing: -0.5px;
    background: linear-gradient(135deg, #4F8EF7, #8B5CF6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 0.5rem;
}
.hero-tagline {
    font-size: 1.05rem; color: #9CA3AF; font-weight: 400;
}

/* ── Section headings ── */
.section-title {
    font-size: 1.1rem; font-weight: 700; color: #4F8EF7;
    letter-spacing: 0.5px; text-transform: uppercase;
    margin: 1.5rem 0 0.75rem;
    display: flex; align-items: center; gap: 0.5rem;
}

/* ── Risk Cards ── */
.risk-card {
    border-radius: 12px; padding: 1.2rem 1.4rem;
    margin-bottom: 1rem; border: 1px solid transparent;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    position: relative; overflow: hidden;
}
.risk-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
.risk-card::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
}
.risk-HIGH { background: rgba(230,57,57,0.08); border-color: rgba(230,57,57,0.3); }
.risk-HIGH::before { background: #E63939; }
.risk-WARNING { background: rgba(245,124,0,0.08); border-color: rgba(245,124,0,0.3); }
.risk-WARNING::before { background: #F57C00; }
.risk-SAFE { background: rgba(46,125,50,0.08); border-color: rgba(46,125,50,0.3); }
.risk-SAFE::before { background: #2E7D32; }

.clause-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 0.8rem;
}
.clause-number { font-size: 0.75rem; color: #9CA3AF; font-weight: 500; letter-spacing: 1px; }
.risk-badge {
    font-size: 0.7rem; font-weight: 700; padding: 3px 10px;
    border-radius: 20px; letter-spacing: 0.5px;
}
.badge-HIGH    { background: rgba(230,57,57,0.2);  color: #E63939; border: 1px solid #E63939; }
.badge-WARNING { background: rgba(245,124,0,0.2);  color: #F57C00; border: 1px solid #F57C00; }
.badge-SAFE    { background: rgba(46,125,50,0.2);  color: #4CAF50; border: 1px solid #4CAF50; }

.clause-text {
    font-size: 0.82rem; color: #9CA3AF; line-height: 1.5;
    border-left: 2px solid #2A2D3E; padding-left: 0.75rem;
    margin-bottom: 1rem; font-style: italic;
}
.detail-label {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px;
    text-transform: uppercase; margin-bottom: 0.25rem;
    display: flex; align-items: center; gap: 0.35rem;
}
.detail-value {
    font-size: 0.875rem; line-height: 1.6; color: #D1D5DB;
    margin-bottom: 0.75rem; padding-left: 0.5rem;
}
.rewrite-box {
    background: rgba(79,142,247,0.06); border: 1px solid rgba(79,142,247,0.2);
    border-radius: 8px; padding: 0.75rem 1rem;
    font-size: 0.85rem; line-height: 1.6; color: #A5C8FF;
}

/* ── Dashboard metric cards ── */
.metric-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.metric-card {
    flex: 1; min-width: 130px; border-radius: 12px;
    padding: 1rem; text-align: center;
    border: 1px solid #2A2D3E; background: #1A1D2E;
}
.metric-value { font-size: 2rem; font-weight: 800; }
.metric-label { font-size: 0.75rem; color: #9CA3AF; margin-top: 0.2rem; }
.metric-high  .metric-value { color: #E63939; }
.metric-warn  .metric-value { color: #F57C00; }
.metric-safe  .metric-value { color: #4CAF50; }
.metric-total .metric-value { color: #4F8EF7; }

/* ── Recommendation banner ── */
.rec-banner {
    border-radius: 12px; padding: 1.2rem 1.5rem;
    text-align: center; margin: 1.5rem 0;
}
.rec-banner h3 { font-size: 1.3rem; font-weight: 800; margin-bottom: 0.3rem; }
.rec-banner p  { font-size: 0.9rem; opacity: 0.85; }
.rec-safe    { background: rgba(46,125,50,0.15);  border: 1px solid #2E7D32; }
.rec-warning { background: rgba(245,124,0,0.15);  border: 1px solid #F57C00; }
.rec-danger  { background: rgba(230,57,57,0.15);  border: 1px solid #E63939; }

/* ── Privacy notice ── */
.privacy-notice {
    background: rgba(79,142,247,0.06); border: 1px solid rgba(79,142,247,0.2);
    border-radius: 8px; padding: 0.6rem 1rem; font-size: 0.78rem;
    color: #9CA3AF; text-align: center; margin-bottom: 1rem;
}

/* ── Sidebar styling ── */
[data-testid="stSidebar"] {
    background: #1A1D2E !important;
    border-right: 1px solid #2A2D3E !important;
}
[data-testid="stSidebar"] .stMarkdown { color: #E8EAF0 !important; }

/* ── Streamlit widgets ── */
.stButton > button {
    background: linear-gradient(135deg, #4F8EF7, #6B5CF7) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    font-size: 0.95rem !important; padding: 0.6rem 1.5rem !important;
    transition: opacity 0.2s ease !important;
    width: 100% !important;
}
.stButton > button:hover { opacity: 0.88 !important; }
.stDownloadButton > button {
    background: rgba(46,125,50,0.15) !important;
    color: #4CAF50 !important; border: 1px solid #4CAF50 !important;
    border-radius: 8px !important; font-weight: 600 !important;
    width: 100% !important;
}
.stFileUploader {
    background: #1A1D2E !important; border-radius: 10px !important;
}
.stProgress > div > div { background: linear-gradient(90deg, #4F8EF7, #8B5CF6) !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #1A1D2E !important;
    border: 1px solid #2A2D3E !important;
    border-radius: 8px !important;
    color: #E8EAF0 !important;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  HELPER FUNCTIONS — UI Rendering
# ══════════════════════════════════════════════════════════

def render_hero():
    """Render the top hero banner with app title and tagline."""
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">⚖️ AI Contract Risk Analyzer</div>
        <div class="hero-tagline">
            Upload any contract → Get instant, clear risk analysis in plain English
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_privacy_notice():
    """Show the privacy banner so users know their data is safe."""
    st.markdown("""
    <div class="privacy-notice">
        🔒 <strong>Privacy First:</strong> Your documents are processed only for this analysis.
        They are <strong>never stored or shared</strong> anywhere.
    </div>
    """, unsafe_allow_html=True)


def risk_css_class(level: str) -> str:
    """Map risk level string to its CSS class suffix."""
    return {"HIGH RISK": "HIGH", "WARNING": "WARNING", "SAFE": "SAFE"}.get(level, "SAFE")


def risk_icon(level: str) -> str:
    """Return an emoji icon for each risk level."""
    return {"HIGH RISK": "❌", "WARNING": "⚠️", "SAFE": "✅"}.get(level, "•")


def render_clause_card(result: dict):
    """
    Render a single clause analysis as a styled HTML card.

    The card shows:
      - Clause number + risk badge
      - Original clause text (truncated)
      - Explanation, Consequence, Action, Safer Rewrite
    """
    level = result["risk_level"]
    css   = risk_css_class(level)
    icon  = risk_icon(level)
    num   = result["clause_number"]
    text  = result["clause_text"][:250] + ("…" if len(result["clause_text"]) > 250 else "")

    st.markdown(f"""
    <div class="risk-card risk-{css}">
        <div class="clause-header">
            <span class="clause-number">CLAUSE {num}</span>
            <span class="risk-badge badge-{css}">{icon} {level}</span>
        </div>
        <div class="clause-text">"{text}"</div>

        <div class="detail-label">📌 What it means</div>
        <div class="detail-value">{result["explanation"]}</div>

        <div class="detail-label">⚡ Consequence</div>
        <div class="detail-value">{result["consequence"]}</div>

        <div class="detail-label">🔧 What to do</div>
        <div class="detail-value">{result["action"]}</div>

        <div class="detail-label">✏️ Safer version</div>
        <div class="rewrite-box">{result["rewrite"]}</div>
    </div>
    """, unsafe_allow_html=True)


def render_dashboard(results: list[dict]):
    """
    Render the Final Decision Dashboard:
      - Metric cards (total / safe / warning / high risk)
      - Overall recommendation banner
    """
    high  = sum(1 for r in results if r["risk_level"] == "HIGH RISK")
    warn  = sum(1 for r in results if r["risk_level"] == "WARNING")
    safe  = sum(1 for r in results if r["risk_level"] == "SAFE")
    total = len(results)

    # Metric cards
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card metric-total">
            <div class="metric-value">{total}</div>
            <div class="metric-label">Total Clauses</div>
        </div>
        <div class="metric-card metric-safe">
            <div class="metric-value">{safe}</div>
            <div class="metric-label">✅ Safe</div>
        </div>
        <div class="metric-card metric-warn">
            <div class="metric-value">{warn}</div>
            <div class="metric-label">⚠ Warning</div>
        </div>
        <div class="metric-card metric-high">
            <div class="metric-value">{high}</div>
            <div class="metric-label">❌ High Risk</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Recommendation banner
    rec_label, rec_detail = final_recommendation(results)
    if high == 0 and warn <= 2:
        css_class = "rec-safe"
    elif high <= 2:
        css_class = "rec-warning"
    else:
        css_class = "rec-danger"

    st.markdown(f"""
    <div class="rec-banner {css_class}">
        <h3>{rec_label}</h3>
        <p>{rec_detail}</p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
#  SIDEBAR
#  Contains: role selection, API key check, how-to guide
# ══════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ⚖️ Contract Analyzer")
    st.markdown("---")

    # ── Role Selection ──────────────────────────────────
    # The LLM adjusts risk severity based on this role.
    st.markdown("### 👤 Your Role")
    user_role = st.selectbox(
        label="Select your role",
        options=["Student", "Freelancer", "Tenant", "Employee / Job Seeker"],
        help="Risk severity and consequences are adjusted based on your role.",
        label_visibility="collapsed"
    )

    st.markdown("---")

    # ── API Key Status ──────────────────────────────────
    st.markdown("### 🔑 API Key Status")
    if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
        st.success("✅ Groq API key loaded from .env")
    else:
        st.error("❌ No API key found!\nCreate a `.env` file with `GROQ_API_KEY=...`")
        st.info("Get a free key at [console.groq.com](https://console.groq.com)")

    st.markdown("---")

    # ── How It Works ────────────────────────────────────
    with st.expander("📖 How It Works", expanded=False):
        st.markdown("""
1. **Select your role** above
2. **Upload** a PDF or TXT contract
3. Click **Analyze Contract**
4. View the **clause-by-clause** risk analysis
5. **Download** a professional PDF report

**Risk Levels:**
- 🔴 **HIGH RISK** — Dangerous clause, negotiate or reject
- 🟡 **WARNING** — Needs attention, ask questions
- 🟢 **SAFE** — Generally fair clause
        """)

    st.markdown("---")
    st.markdown(
        "<small style='color:#6B7280;'>Powered by Groq LLaMA-3.1-70b<br>"
        "Based on Indian Contract Act 1872</small>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════
#  MAIN CONTENT AREA
# ══════════════════════════════════════════════════════════

render_hero()
render_privacy_notice()

# ── File Upload Section ──────────────────────────────────
st.markdown('<div class="section-title">📄 Upload Contract</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    label="Upload your contract (PDF or TXT)",
    type=["pdf", "txt"],
    help="Maximum recommended size: 5 MB. Scanned PDFs may not extract correctly.",
    label_visibility="collapsed"
)

# ── Sample Contract Option ──────────────────────────────
use_sample = st.checkbox(
    "🧪 Use sample contract (for demo / testing)",
    value=False
)

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
Violation shall result in liquidated damages of ₹5,00,000.

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
The Service Provider shall be paid ₹50,000 per month for services rendered. 
Payment is non-refundable under all circumstances.
"""

# ── Analyze Button ───────────────────────────────────────
st.markdown("")  # spacing
analyze_clicked = st.button("🔍 Analyze Contract", use_container_width=True)

# ── Analysis Logic ───────────────────────────────────────
if analyze_clicked:
    # Validate: need API key
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        st.error("❌ Please set your GROQ_API_KEY in the .env file before analyzing.")
        st.stop()

    # Validate: need file or sample
    if not uploaded_file and not use_sample:
        st.warning("⚠️ Please upload a contract file or check 'Use sample contract'.")
        st.stop()

    # ── Step 1: Extract Text ─────────────────────────────
    with st.spinner("📄 Extracting text from contract…"):
        if use_sample:
            contract_text = SAMPLE_CONTRACT
        elif uploaded_file.type == "application/pdf":
            contract_text = extract_text_from_pdf(uploaded_file)
        else:
            contract_text = extract_text_from_txt(uploaded_file)

    if not contract_text or len(contract_text.strip()) < 100:
        st.error("❌ Could not extract enough text from the document. Try a different file.")
        st.stop()

    st.success(f"✅ Extracted {len(contract_text):,} characters from contract.")

    # ── Step 2: Segment into Clauses ─────────────────────
    with st.spinner("✂️ Segmenting contract into clauses…"):
        clauses = segment_into_clauses(contract_text)

    st.info(f"📋 Found **{len(clauses)} clauses** to analyze.")

    # ── Step 3: AI Analysis via Groq ─────────────────────
    with st.spinner(f"🤖 Analyzing with LLaMA-3.1-70b for role: **{user_role}**… (may take 30–60s)"):
        progress_bar = st.progress(0, text="Sending clauses to Groq AI…")
        try:
            results = analyze_contract(GROQ_API_KEY, user_role, clauses)
            progress_bar.progress(100, text="Analysis complete!")
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            st.info("Common fixes: Check your API key · Reduce file size · Try again in a moment.")
            st.stop()

    # Store results in Streamlit session state so they persist
    # across re-renders (e.g., when user downloads the report).
    st.session_state["results"]   = results
    st.session_state["user_role"] = user_role


# ── Display Results (if available) ──────────────────────
if "results" in st.session_state:
    results   = st.session_state["results"]
    user_role = st.session_state["user_role"]

    st.markdown("---")

    # ── Final Decision Dashboard ─────────────────────────
    st.markdown('<div class="section-title">📊 Final Decision Dashboard</div>', unsafe_allow_html=True)
    render_dashboard(results)

    # ── Download PDF Report ──────────────────────────────
    st.markdown('<div class="section-title">📥 Export Report</div>', unsafe_allow_html=True)
    with st.spinner("Generating PDF report…"):
        pdf_bytes = generate_pdf_report(results, user_role)

    st.download_button(
        label="⬇️ Download Full PDF Report",
        data=pdf_bytes,
        file_name="contract_risk_analysis.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.markdown("---")

    # ── Clause-by-Clause Analysis ─────────────────────────
    # Filter tabs: All / High Risk Only / Warnings Only / Safe
    st.markdown('<div class="section-title">📋 Clause-by-Clause Analysis</div>', unsafe_allow_html=True)

    tab_all, tab_high, tab_warn, tab_safe = st.tabs([
        f"All ({len(results)})",
        f"❌ High Risk ({sum(1 for r in results if r['risk_level']=='HIGH RISK')})",
        f"⚠ Warning ({sum(1 for r in results if r['risk_level']=='WARNING')})",
        f"✅ Safe ({sum(1 for r in results if r['risk_level']=='SAFE')})",
    ])

    with tab_all:
        for r in results:
            render_clause_card(r)

    with tab_high:
        high_results = [r for r in results if r["risk_level"] == "HIGH RISK"]
        if high_results:
            for r in high_results:
                render_clause_card(r)
        else:
            st.success("🎉 No HIGH RISK clauses found!")

    with tab_warn:
        warn_results = [r for r in results if r["risk_level"] == "WARNING"]
        if warn_results:
            for r in warn_results:
                render_clause_card(r)
        else:
            st.success("🎉 No WARNING clauses found!")

    with tab_safe:
        safe_results = [r for r in results if r["risk_level"] == "SAFE"]
        if safe_results:
            for r in safe_results:
                render_clause_card(r)
        else:
            st.info("No purely SAFE clauses detected.")

    # ── Raw Contract Text (collapsible) ──────────────────
    st.markdown("---")
    with st.expander("📄 View Raw Extracted Contract Text"):
        if use_sample or "results" in st.session_state:
            st.text_area(
                "Extracted Text",
                value=SAMPLE_CONTRACT if use_sample else "",
                height=300,
                disabled=True,
                label_visibility="collapsed"
            )


# ── Footer ───────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center; color:#6B7280; font-size:0.78rem; padding: 0.5rem 0;'>
        ⚖️ AI Contract Risk Analyzer &nbsp;|&nbsp;
        Powered by Groq LLaMA-3.1-70b &nbsp;|&nbsp;
        Based on Indian Contract Act 1872<br>
        ⚠️ <em>This tool provides AI-generated analysis only — not legal advice.
        Always consult a qualified lawyer before signing.</em>
    </div>
    """,
    unsafe_allow_html=True
)
