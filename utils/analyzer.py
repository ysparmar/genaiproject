# ============================================================
# AI Contract Risk Analyzer — Clause Analysis Engine
# utils/analyzer.py
#
# This module handles:
#   1. PDF & text extraction (PyMuPDF)
#   2. Clause segmentation (rule-based sentence splitting)
#   3. Keyword-based risk pre-classification
#   4. Groq LLM call for deep semantic analysis
#   5. Parsing the structured LLM response into Python dicts
# ============================================================

import re
import fitz  # PyMuPDF — reads PDF bytes and extracts text
from groq import Groq


# ── Risk keyword dictionaries ──────────────────────────────
# These trigger an initial flag BEFORE we send to the LLM.
# Makes the analysis faster and more reliable.

HIGH_RISK_KEYWORDS = [
    "indemnify", "indemnification", "unlimited liability", "waive all rights",
    "irrevocable", "perpetual license", "sole discretion", "unilateral",
    "automatic renewal", "non-compete", "non-solicitation", "liquidated damages",
    "penalty clause", "forfeit", "without notice", "termination without cause",
    "exclusive rights", "intellectual property assignment", "assign all rights",
    "governing law", "jurisdiction", "arbitration only", "class action waiver",
    "no refund", "non-refundable", "lock-in period",
]

WARNING_KEYWORDS = [
    "may terminate", "at our discretion", "subject to change", "modify at any time",
    "best efforts", "reasonable efforts", "force majeure", "limitation of liability",
    "as-is", "no warranty", "disclaimer", "confidential", "non-disclosure",
    "delayed payment", "interest on late payment", "right to audit",
    "data sharing", "third party", "sublicense",
]


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Reads a PDF uploaded via Streamlit (file-like object),
    extracts all text page by page using PyMuPDF, and returns
    a single cleaned string.
    """
    pdf_bytes = uploaded_file.read()          # read raw bytes from uploaded file
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")  # open in-memory PDF
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text())    # extract plain text from each page
    doc.close()
    raw_text = "\n".join(pages_text)
    return clean_text(raw_text)


def extract_text_from_txt(uploaded_file) -> str:
    """
    Reads a plain-text file uploaded via Streamlit and returns
    a cleaned string.
    """
    raw_bytes = uploaded_file.read()
    # Try UTF-8 first; fall back to latin-1 for older legal docs
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("latin-1")
    return clean_text(raw_text)


def clean_text(text: str) -> str:
    """
    Remove excessive whitespace, blank lines, and non-printable
    characters that appear in scanned/digitized PDFs.
    """
    text = re.sub(r'\r\n', '\n', text)              # normalize line endings
    text = re.sub(r'[ \t]+', ' ', text)             # collapse horizontal whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)          # collapse multiple blank lines
    text = ''.join(ch for ch in text if ch.isprintable() or ch == '\n')
    return text.strip()


def segment_into_clauses(text: str) -> list[str]:
    """
    Splits the contract text into individual clauses/sentences.

    Strategy:
      1. Split on numbered headings  (1. / 1.1 / Clause 1:)
      2. Split on double newlines (paragraph breaks)
      3. Final split on sentence boundaries (. followed by capital letter)
      4. Filter out very short fragments (< 30 chars) — likely headers/noise
    """
    # Step 1 — split on numbered clause markers
    parts = re.split(r'(?m)^(?:\d+[\.\)]\s|\bClause\s+\d+\b)', text)

    clauses = []
    for part in parts:
        # Step 2 — split each part on paragraph breaks
        paragraphs = re.split(r'\n\s*\n', part)
        for para in paragraphs:
            para = para.strip()
            if len(para) > 30:          # ignore very short noise
                clauses.append(para)

    # If no structure was found, fall back to sentence splitting
    if len(clauses) <= 1:
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        clauses = [s.strip() for s in sentences if len(s.strip()) > 30]

    return clauses[:50]   # cap at 50 clauses to keep analysis fast


def keyword_prescreen(clause: str) -> str:
    """
    Quick keyword scan before the LLM call.
    Returns 'HIGH RISK', 'WARNING', or 'SAFE'.

    This gives an immediate signal and also helps the LLM
    focus on the right areas.
    """
    lower = clause.lower()
    for kw in HIGH_RISK_KEYWORDS:
        if kw in lower:
            return "HIGH RISK"
    for kw in WARNING_KEYWORDS:
        if kw in lower:
            return "WARNING"
    return "SAFE"


def build_llm_prompt(user_role: str, clauses: list[str]) -> str:
    """
    Constructs the structured prompt we send to the Groq LLM.

    We number each clause and ask the model to return a
    machine-parseable block per clause so we can split it later.
    """
    numbered_clauses = "\n\n".join(
        f"[CLAUSE {i+1}]\n{c}" for i, c in enumerate(clauses)
    )

    prompt = f"""User role: {user_role}

You are an expert Indian contract lawyer. Analyze EACH clause below strictly following this output format for every single clause:

CLAUSE_START
CLAUSE_NUMBER: <number>
RISK_LEVEL: <SAFE | WARNING | HIGH RISK>
EXPLANATION: <1-2 sentence plain English explanation>
CONSEQUENCE: <financial estimate in ₹, legal risk, or practical scenario>
ACTION: <what to change, delete, or ask the other party>
REWRITE: <a fairer, balanced rewritten version of this clause>
CLAUSE_END

Rules:
- Never give actual legal advice. Only analysis and suggestions.
- Base analysis on Indian Contract Act 1872.
- For SAFE clauses, keep CONSEQUENCE and ACTION brief.
- Be practical and specific — mention real ₹ amounts where possible.
- Adjust severity based on user role: {user_role}

Contract clauses to analyze:

{numbered_clauses}
"""
    return prompt


def parse_llm_response(response_text: str, clauses: list[str], prescreens: list[str]) -> list[dict]:
    """
    Parses the structured LLM output into a list of result dicts.

    Each dict has keys:
      clause_text, risk_level, explanation, consequence, action, rewrite

    Falls back to the keyword pre-screen risk level if the LLM
    didn't return a clean block for a clause.
    """
    results = []

    # Split on our markers
    blocks = re.split(r'CLAUSE_START', response_text)
    blocks = [b for b in blocks if 'CLAUSE_NUMBER' in b]

    # Build a lookup: clause_number → parsed dict
    parsed_map = {}
    for block in blocks:
        try:
            num_match = re.search(r'CLAUSE_NUMBER:\s*(\d+)', block)
            risk_match = re.search(r'RISK_LEVEL:\s*(SAFE|WARNING|HIGH RISK)', block)
            exp_match = re.search(r'EXPLANATION:\s*(.+?)(?=CONSEQUENCE:|$)', block, re.DOTALL)
            con_match = re.search(r'CONSEQUENCE:\s*(.+?)(?=ACTION:|$)', block, re.DOTALL)
            act_match = re.search(r'ACTION:\s*(.+?)(?=REWRITE:|$)', block, re.DOTALL)
            rew_match = re.search(r'REWRITE:\s*(.+?)(?=CLAUSE_END|$)', block, re.DOTALL)

            if not num_match:
                continue

            num = int(num_match.group(1))
            parsed_map[num] = {
                "risk_level": risk_match.group(1).strip() if risk_match else None,
                "explanation": exp_match.group(1).strip() if exp_match else "—",
                "consequence": con_match.group(1).strip() if con_match else "—",
                "action": act_match.group(1).strip() if act_match else "—",
                "rewrite": rew_match.group(1).strip() if rew_match else "—",
            }
        except Exception:
            continue  # skip malformed blocks silently

    # Assemble final list aligned with original clauses
    for i, clause in enumerate(clauses):
        clause_num = i + 1
        parsed = parsed_map.get(clause_num, {})
        results.append({
            "clause_number": clause_num,
            "clause_text": clause,
            # Use LLM risk level; fall back to keyword pre-screen
            "risk_level": parsed.get("risk_level") or prescreens[i],
            "explanation": parsed.get("explanation", "Analysis unavailable."),
            "consequence": parsed.get("consequence", "—"),
            "action": parsed.get("action", "—"),
            "rewrite": parsed.get("rewrite", clause),
        })

    return results


def analyze_contract(api_key: str, user_role: str, clauses: list[str]) -> list[dict]:
    """
    Main orchestration function.

    Steps:
      1. Pre-screen each clause with keywords
      2. Build the LLM prompt
      3. Call Groq API (Llama-3.1-70b-versatile)
      4. Parse the structured response
      5. Return list of result dicts
    """
    # Step 1: keyword pre-screen (fast, no API call)
    prescreens = [keyword_prescreen(c) for c in clauses]

    # Step 2: build prompt
    prompt = build_llm_prompt(user_role, clauses)

    # Step 3: call Groq
    client = Groq(api_key=api_key)
    chat_response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert Indian contract lawyer who explains things in simple, "
                    "clear, practical language. Follow Indian Contract Act 1872 and common practices. "
                    "Be honest and helpful. Never give actual legal advice — only analysis and suggestions."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,       # low temp = more consistent structured output
        max_tokens=8000,
    )

    raw_output = chat_response.choices[0].message.content

    # Step 4: parse
    results = parse_llm_response(raw_output, clauses, prescreens)
    return results
