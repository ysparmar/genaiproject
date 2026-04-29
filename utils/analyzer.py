# ============================================================
# AI Contract Risk Analyzer — Clause Analysis Engine
# utils/analyzer.py
#
# WHAT THIS FILE DOES (for viva/presentation):
#   1. Extracts text from PDF (PyMuPDF) or TXT files
#   2. Splits contract into logical clauses (regex-based)
#   3. Pre-screens each clause with keyword rules (fast, offline)
#   4. Sends all clauses to Groq LLM for deep semantic analysis
#   5. Parses the structured LLM response into Python dicts
#   6. Supports English + Hindi dual-language output
# ============================================================

import re
import fitz  # PyMuPDF — reads PDFs and extracts plain text
from groq import Groq


# ── High-risk legal keywords ───────────────────────────────
# Instant red flag triggers before any LLM call
HIGH_RISK_KEYWORDS = [
    "indemnify", "indemnification", "unlimited liability", "waive all rights",
    "irrevocable", "perpetual license", "sole discretion", "unilateral",
    "automatic renewal", "non-compete", "non-solicitation", "liquidated damages",
    "penalty clause", "forfeit", "without notice", "termination without cause",
    "exclusive rights", "intellectual property assignment", "assign all rights",
    "arbitration only", "class action waiver", "no refund", "non-refundable",
    "lock-in period", "governing law",
]

# ── Warning-level keywords ─────────────────────────────────
WARNING_KEYWORDS = [
    "may terminate", "at our discretion", "subject to change", "modify at any time",
    "best efforts", "reasonable efforts", "force majeure", "limitation of liability",
    "as-is", "no warranty", "disclaimer", "confidential", "non-disclosure",
    "delayed payment", "interest on late payment", "right to audit",
    "data sharing", "third party", "sublicense",
]


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract plain text from an uploaded PDF file using PyMuPDF."""
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = [page.get_text() for page in doc]
    doc.close()
    return clean_text("\n".join(pages_text))


def extract_text_from_txt(uploaded_file) -> str:
    """Extract text from an uploaded TXT file."""
    raw_bytes = uploaded_file.read()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("latin-1")
    return clean_text(raw_text)


def clean_text(text: str) -> str:
    """Remove noise: extra whitespace, blank lines, non-printable chars."""
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = ''.join(ch for ch in text if ch.isprintable() or ch == '\n')
    return text.strip()


def segment_into_clauses(text: str) -> list[str]:
    """
    Splits contract text into individual clauses.
    Strategy: numbered headings → paragraphs → sentence fallback.
    """
    parts = re.split(r'(?m)^(?:\d+[\.\)]\s|\bClause\s+\d+\b)', text)
    clauses = []
    for part in parts:
        for para in re.split(r'\n\s*\n', part):
            para = para.strip()
            if len(para) > 30:
                clauses.append(para)

    if len(clauses) <= 1:
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        clauses = [s.strip() for s in sentences if len(s.strip()) > 30]

    return clauses[:50]


def keyword_prescreen(clause: str) -> str:
    """Quick offline keyword scan. Returns HIGH RISK / WARNING / SAFE."""
    lower = clause.lower()
    for kw in HIGH_RISK_KEYWORDS:
        if kw in lower:
            return "HIGH RISK"
    for kw in WARNING_KEYWORDS:
        if kw in lower:
            return "WARNING"
    return "SAFE"


def build_llm_prompt(user_role: str, clauses: list[str], language: str) -> str:
    """
    Build the structured prompt for the Groq LLM.
    Supports English-only or English+Hindi output.
    """
    numbered_clauses = "\n\n".join(
        f"[CLAUSE {i+1}]\n{c}" for i, c in enumerate(clauses)
    )

    # Language instruction injected into prompt
    if language == "Hindi":
        lang_instruction = (
            "Provide EXPLANATION, CONSEQUENCE, ACTION, and REWRITE in HINDI only. "
            "Use simple Hindi that a common person can understand."
        )
    elif language == "Both":
        lang_instruction = (
            "Provide EXPLANATION, CONSEQUENCE, ACTION, and REWRITE in BOTH English and Hindi. "
            "Format: first English, then a line break, then 'हिंदी:' followed by Hindi translation."
        )
    else:
        lang_instruction = "Provide all output in English only."

    prompt = f"""User role: {user_role}
Language instruction: {lang_instruction}

You are an expert Indian contract lawyer. Analyze EACH clause strictly using this format:

CLAUSE_START
CLAUSE_NUMBER: <number>
RISK_LEVEL: <SAFE | WARNING | HIGH RISK>
EXPLANATION: <1-2 sentence plain explanation>
CONSEQUENCE: <financial estimate in rupees, legal risk, or practical scenario>
ACTION: <what to change, delete, or ask the other party>
REWRITE: <a fairer, balanced rewritten version>
CLAUSE_END

Rules:
- NEVER use HTML tags in your response. Plain text only.
- Never give actual legal advice. Only analysis and suggestions.
- Base analysis on Indian Contract Act 1872.
- Mention real rupee amounts where relevant (e.g. Rs. 50,000).
- Adjust risk severity for role: {user_role}
- Keep CONSEQUENCE and ACTION brief for SAFE clauses.

Contract clauses to analyze:

{numbered_clauses}
"""
    return prompt


def parse_llm_response(response_text: str, clauses: list[str], prescreens: list[str]) -> list[dict]:
    """
    Parse the structured LLM output into a list of Python dicts.
    Gracefully falls back to pre-screen risk if LLM block is missing.
    """
    blocks = re.split(r'CLAUSE_START', response_text)
    blocks = [b for b in blocks if 'CLAUSE_NUMBER' in b]

    parsed_map = {}
    for block in blocks:
        try:
            num_match  = re.search(r'CLAUSE_NUMBER:\s*(\d+)', block)
            risk_match = re.search(r'RISK_LEVEL:\s*(SAFE|WARNING|HIGH RISK)', block)
            exp_match  = re.search(r'EXPLANATION:\s*(.+?)(?=CONSEQUENCE:|$)', block, re.DOTALL)
            con_match  = re.search(r'CONSEQUENCE:\s*(.+?)(?=ACTION:|$)', block, re.DOTALL)
            act_match  = re.search(r'ACTION:\s*(.+?)(?=REWRITE:|$)', block, re.DOTALL)
            rew_match  = re.search(r'REWRITE:\s*(.+?)(?=CLAUSE_END|$)', block, re.DOTALL)

            if not num_match:
                continue

            num = int(num_match.group(1))
            parsed_map[num] = {
                "risk_level":  risk_match.group(1).strip() if risk_match else None,
                "explanation": exp_match.group(1).strip()  if exp_match  else "—",
                "consequence": con_match.group(1).strip()  if con_match  else "—",
                "action":      act_match.group(1).strip()  if act_match  else "—",
                "rewrite":     rew_match.group(1).strip()  if rew_match  else "—",
            }
        except Exception:
            continue

    results = []
    for i, clause in enumerate(clauses):
        parsed = parsed_map.get(i + 1, {})
        results.append({
            "clause_number": i + 1,
            "clause_text":   clause,
            "risk_level":    parsed.get("risk_level") or prescreens[i],
            "explanation":   parsed.get("explanation", "Analysis unavailable."),
            "consequence":   parsed.get("consequence", "—"),
            "action":        parsed.get("action", "—"),
            "rewrite":       parsed.get("rewrite", clause),
        })

    return results


def analyze_contract(api_key: str, user_role: str, clauses: list[str], language: str = "English") -> list[dict]:
    """
    Main function: pre-screen → build prompt → call Groq → parse → return results.

    Args:
        api_key   : Groq API key
        user_role : Selected user role (Student / Freelancer / Tenant / Employee)
        clauses   : List of contract clauses
        language  : Output language — "English", "Hindi", or "Both"

    Returns:
        List of dicts with clause analysis data
    """
    # Step 1: fast keyword pre-screen (no API call)
    prescreens = [keyword_prescreen(c) for c in clauses]

    # Step 2: build prompt with language preference
    prompt = build_llm_prompt(user_role, clauses, language)

    # Step 3: call Groq (LLaMA-3.3-70b)
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert Indian contract lawyer who explains things in simple, "
                    "clear, practical language. Follow Indian Contract Act 1872. "
                    "Be honest and helpful. Never give actual legal advice. "
                    "CRITICAL: Never use HTML tags in your output. Plain text only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=8000,
    )

    raw_output = response.choices[0].message.content

    # Step 4: parse and return
    return parse_llm_response(raw_output, clauses, prescreens)
