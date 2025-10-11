import os
import requests
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def check_google_fact_api(query: str):
    """Use Google Fact Check REST API directly."""
    endpoint = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {"query": query, "key": GOOGLE_API_KEY}
    try:
        response = requests.get(endpoint, params=params)
        data = response.json()
        if "claims" in data and len(data["claims"]) > 0:
            claim = data["claims"][0]
            review = claim.get("claimReview", [{}])[0]
            return {
                "source": "Google Fact Check",
                "claim": claim.get("text"),
                "rating": review.get("textualRating", "Unknown"),
                "publisher": review.get("publisher", {}).get("name", "Unknown"),
                "url": review.get("url", ""),
            }
    except Exception as e:
        print("Fact Check API Error:", e)
    return None
