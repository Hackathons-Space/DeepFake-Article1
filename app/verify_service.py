# save as verify_service.py
from newspaper import Article
from rapidfuzz import fuzz
import requests
import os


# -------------------------------
# Utility: fetch & extract text
# -------------------------------
def fetch_and_extract(url: str) -> dict:
    """Extract article text and metadata from a URL."""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        article = Article(url)
        article.set_html(response.text)
        article.parse()
        return {
            "title": article.title or "",
            "text": article.text or "",
            "image": article.top_image or ""
        }
    except Exception as e:
        raise RuntimeError(f"Failed to fetch or parse: {e}")

# -------------------------------
# Simple claim extraction
# -------------------------------
def extract_candidate_claims(title: str, text: str, max_claims=3):
    claims = [title.strip()] if title else []
    sentences = text.split(".")
    for s in sentences[:3]:
        s = s.strip()
        if s and len(s.split()) > 4:
            claims.append(s)
        if len(claims) >= max_claims:
            break
    return list(dict.fromkeys(claims))  # remove duplicates

# -------------------------------
# Fuzzy match helper (optional)
# -------------------------------
def best_fuzzy_match(claim: str, fact_checks: list):
    best, best_score = None, 0
    for fc in fact_checks:
        text = fc.get("text", "") or fc.get("claim", "")
        score = fuzz.token_set_ratio(claim, text)
        if score > best_score:
            best_score = score
            best = fc
    return best, best_score

# -------------------------------
# Google Fact Check API helper
# -------------------------------
def check_google_fact_api(url_or_text: str):
    """Query Google Fact Check API."""
    if url_or_text.startswith("http"):
        try:
            text = fetch_and_extract(url_or_text)["text"]
            query = text[:200]
        except Exception as e:
            return {"error": f"Failed to extract text: {e}"}
    else:
        query = url_or_text[:200]

    api_key = os.getenv("GOOGLE_FACTCHECK_API_KEY")
    if not api_key:
        return {"error": "Missing GOOGLE_FACTCHECK_API_KEY in environment"}

    base_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {"query": query, "key": api_key}

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "claims" in data and data["claims"]:
            claim = data["claims"][0]
            review = claim.get("claimReview", [{}])[0]
            return {
                "claim": claim.get("text", ""),
                "rating": review.get("textualRating", "Unknown"),
                "publisher": review.get("publisher", {}).get("name", "Unknown"),
                "source": review.get("url", "")
            }
        else:
            return None
    except Exception as e:
        return {"error": str(e)}
