import requests
from fastapi import HTTPException
from app.config import HF_API_URL, HF_TOKEN

HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def classify_text_hf_api(text: str) -> dict:
    """Classify text using Hugging Face fake news model."""
    payload = {"inputs": text}
    response = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Hugging Face API error: {response.text}")

    data = response.json()
    try:
        if isinstance(data, list):
            preds = data[0] if isinstance(data[0], list) else data
            best = max(preds, key=lambda x: x["score"])
            label_map = {"LABEL_0": "FAKE", "LABEL_1": "REAL"}
            return {"label": label_map.get(best["label"], best["label"]),
                    "confidence": round(best["score"] * 100, 2)}
        else:
            raise ValueError("Unexpected response format from Hugging Face API.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing error: {e}")
