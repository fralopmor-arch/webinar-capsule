import os
from dotenv import load_dotenv

load_dotenv()

def get_gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set in .env file")
    return key
