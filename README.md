# ⚖️ AI Contract Risk Analyzer

> **"Upload any contract → Get instant, clear risk analysis in plain English"**

A professional, AI-powered legal-tech tool built with **Streamlit + Groq (LLaMA-3.1-70b) + PyMuPDF**.
Analyzes contracts clause by clause, flags risks, explains consequences in plain English, and generates a downloadable PDF report.

---

## 🔒 CRITICAL SECURITY WARNING

> ⚠️ **NEVER commit your `.env` file or API key to GitHub or any public repository.**
> ⚠️ **NEVER share your API key with anyone.**
> ⚠️ Your `.env` file is listed in `.gitignore` — keep it that way.
>
> If you accidentally expose your key, **immediately revoke it** at [console.groq.com](https://console.groq.com) and generate a new one.

---

## 🚀 Features

| Feature | Description |
|---|---|
| **Document Upload** | PDF and TXT contracts supported |
| **Clause Segmentation** | Auto-splits contract into logical clauses |
| **Hybrid Risk Detection** | Keyword rules + Groq LLM semantic analysis |
| **Plain English Explanations** | No legal jargon |
| **🔥 Consequence Engine** | Financial estimates (₹), legal risks, real-life scenarios |
| **Action Suggestions** | What to change, delete, or negotiate |
| **Safer Rewrites** | Balanced alternative clause text |
| **Role Personalization** | Student / Freelancer / Tenant / Employee modes |
| **Final Dashboard** | Overall recommendation: Safe / Review / Do Not Sign |
| **PDF Report** | Professional downloadable report via ReportLab |

---

## 📁 Project Structure

```
ai-contract-risk-analyzer/
├── app.py                  # Main Streamlit application
├── utils/
│   ├── __init__.py
│   ├── analyzer.py         # PDF extraction, clause segmentation, Groq AI
│   └── report_generator.py # ReportLab PDF report generation
├── requirements.txt
├── .env.example            # Template — copy to .env and add your key
├── .env                    # ⚠️ NEVER commit this file!
├── .gitignore
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone / Download the project

```bash
git clone https://github.com/your-username/ai-contract-risk-analyzer.git
cd ai-contract-risk-analyzer
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

```bash
# Copy the example env file
cp .env.example .env
```

Open `.env` in any text editor and replace the placeholder:

```env
GROQ_API_KEY=gsk_your_actual_key_here
```

Get a **free** Groq API key at: [https://console.groq.com](https://console.groq.com)

### 5. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 🎯 How to Use

1. **Select your role** in the sidebar (Student / Freelancer / Tenant / Employee)
2. **Upload a contract** (PDF or TXT) — or check "Use sample contract" for demo
3. Click **Analyze Contract**
4. View results in the **clause-by-clause** tabs (All / High Risk / Warning / Safe)
5. Check the **Final Decision Dashboard** for the overall recommendation
6. **Download the PDF report** for a professional summary

---

## 🧠 How It Works (Technical)

```
PDF/TXT Upload
     │
     ▼
PyMuPDF Text Extraction
     │
     ▼
Clause Segmentation (regex + paragraph splitting)
     │
     ▼
Keyword Pre-screening (offline, instant)
     │
     ▼
Groq API Call (LLaMA-3.1-70b-versatile)
  - System: Expert Indian Contract Lawyer persona
  - User:   All clauses + user role in structured format
     │
     ▼
Response Parser (regex → Python dicts)
     │
     ▼
Streamlit Dashboard + ReportLab PDF
```

---

## 🎨 Risk Color Scheme

| Level | Color | Meaning |
|---|---|---|
| ✅ SAFE | `#2E7D32` Green | Clause is generally fair |
| ⚠ WARNING | `#F57C00` Orange | Needs attention / negotiation |
| ❌ HIGH RISK | `#E63939` Red | Dangerous — negotiate or reject |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `groq` | Groq API client (LLaMA-3.1-70b) |
| `PyMuPDF` | PDF text extraction |
| `python-dotenv` | Secure API key loading from .env |
| `reportlab` | Professional PDF report generation |

---

## 🔐 Privacy & Data Policy

- Your documents are **processed in-memory only** during the session.
- Documents are **never stored** on any server or database.
- Documents are **never shared** with third parties beyond the Groq API for analysis.
- The Groq API processes data per their [Privacy Policy](https://groq.com/privacy-policy/).

---

## ⚠️ Disclaimer

This tool provides **AI-generated analysis for informational purposes only**.
It does **not** constitute legal advice. Always consult a qualified legal professional
before signing any contract.

---

## 📄 License

MIT License — Free to use, modify, and distribute.

---

*Built with ❤️ using Groq LLaMA-3.1-70b | Indian Contract Act 1872*
