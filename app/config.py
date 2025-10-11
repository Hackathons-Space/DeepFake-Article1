import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL_NAME = "mrm8488/bert-tiny-finetuned-fake-news-detection"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL_NAME}"
