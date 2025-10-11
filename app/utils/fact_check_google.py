# app/utils/fact_check_google.py
import os
import requests

def check_google_fact_api(text_or_claim: str):
    """
    Query Google Fact Check Tools API for a text or claim.
    Returns the first claim review found or an error dict.
    """
    if not text_or_claim or not text_or_claim.strip():
        return {"error": "Empty text or claim provided"}

    query = text_or_claim[:200]  # limit query to first 200 chars
    api_key = os.getenv("GOOGLE_FACTCHECK_API_KEY")
    if not api_key:
        return {"error": "Missing GOOGLE_FACTCHECK_API_KEY in environment"}

    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": query,
        "key": api_key,
        "pageSize": 5
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        claims = data.get("claims", [])
        if not claims:
            return None  # no fact check found

        # Take the first claim with a review
        claim = claims[0]
        review = claim.get("claimReview", [{}])[0]

        return {
            "claim": claim.get("text", ""),
            "rating": review.get("textualRating", "Unknown"),
            "publisher": review.get("publisher", {}).get("name", "Unknown"),
            "source": review.get("url", "")
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}
