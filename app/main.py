import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import TextItem, URLItem, ClaimItem
from app.utils.hf_classifier import classify_text_hf_api
from app.utils.fact_check_google import check_google_fact_api
from app.verify_service import fetch_and_extract, extract_candidate_claims
import google.generativeai as genai

# ============================================================
# 🔹 Configure Gemini
# ============================================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Declare model name once
GEMINI_MODEL_NAME = "models/gemini-2.5-flash"
# ============================================================
# 🔹 FastAPI App Setup
# ============================================================
app = FastAPI(title="Fake News & Fact-Check API (with Gemini AI)")

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8082"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "✅ Fake News API Running"}


# ============================================================
# 🔹 Helper — Gemini Call
# ============================================================
def generate_with_gemini(prompt: str) -> str:
    """Safely call Gemini with Markdown-style response."""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Gemini error: {e}")


# ============================================================
# ✅ VERIFY TEXT
# ============================================================
@app.post("/verify/text")
def verify_text(item: TextItem):
    text = item.text
    verification = {"input_type": "text", "verified": False, "method": None}

    # 1️⃣ Google Fact Check API
    fact_result = check_google_fact_api(text)
    if fact_result and "error" not in fact_result:
        verification.update({
            "verified": True,
            "method": "Google Fact Check",
            "result": fact_result
        })
    else:
        # 2️⃣ Gemini AI Analysis
        try:
            gemini_prompt = f"""
            You are a fact-checking AI assistant. Analyze the following text:
            ---
            {text}
            ---
            Return a **Markdown-formatted summary** including:
            - **Verdict:** true / misleading / uncertain
            - **Reasoning:** bullet points
            - **General facts or context**
            """
            gemini_text = generate_with_gemini(gemini_prompt)
            verification.update({
                "method": "Gemini AI Analysis",
                "result": {"gemini_output": gemini_text}
            })
        except Exception as e:
            # 3️⃣ Fallback — Hugging Face
            ml_result = classify_text_hf_api(text)
            verification.update({
                "method": "Hugging Face Model",
                "result": ml_result,
                "warning": f"Gemini unavailable: {e}"
            })

    # 🧠 Final Explanation
    try:
        explanation_prompt = f"""
        Explain the following verification result **in simple Markdown** for a normal reader:

        {verification['result']}
        """
        verification["gemini_explanation"] = generate_with_gemini(explanation_prompt)
    except Exception as e:
        verification["gemini_explanation"] = f"⚠️ Gemini explanation failed: {e}"

    return verification


# ============================================================
# ✅ VERIFY CLAIM
# ============================================================
@app.post("/verify/claim")
def verify_claim(item: ClaimItem):
    claim = item.claim
    verification = {"input_type": "claim", "verified": False, "method": None}

    # 1️⃣ Google Fact Check API
    fact_result = check_google_fact_api(claim)
    if fact_result and "error" not in fact_result:
        verification.update({
            "verified": True,
            "method": "Google Fact Check",
            "result": fact_result
        })
    else:
        # 2️⃣ Gemini AI Analysis
        try:
            gemini_prompt = f"""
            Evaluate this factual claim:
            ---
            "{claim}"
            ---
            Return a **Markdown-formatted fact-check** including:
            - **Verdict:** True / Misleading / False / Unclear
            - **Supporting reasoning**
            - **References or context**
            """
            gemini_text = generate_with_gemini(gemini_prompt)
            verification.update({
                "method": "Gemini AI Analysis",
                "result": {"gemini_output": gemini_text}
            })
        except Exception as e:
            # 3️⃣ Fallback
            ml_result = classify_text_hf_api(claim)
            verification.update({
                "method": "Hugging Face Model",
                "result": ml_result,
                "warning": f"Gemini unavailable: {e}"
            })

    # 🧠 Final Explanation
    try:
        explanation_prompt = f"""
        Summarize this fact-check **in simple Markdown** so any user can understand:
        {verification['result']}
        """
        verification["gemini_explanation"] = generate_with_gemini(explanation_prompt)
    except Exception as e:
        verification["gemini_explanation"] = f"⚠️ Gemini explanation failed: {e}"

    return verification


# ============================================================
# ✅ VERIFY URL
# ============================================================
@app.post("/verify/url")
def verify_url(item: URLItem):
    url = item.url
    if not url.lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    try:
        meta = fetch_and_extract(url)
        title = meta.get("title", "Untitled Page")
        text = meta.get("text", "")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch or parse URL: {e}")

    claims = extract_candidate_claims(title, text)

    return {
        "input_type": "url",
        "verified": False,
        "method": "Local Extraction Only",
        "result": None,
        "warning": "No external verification applied yet.",
        "title": title,
        "claims_checked": claims
    }
