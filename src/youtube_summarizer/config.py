import os
from dotenv import load_dotenv

load_dotenv()

def get_deepseek_api_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise ValueError("DEEPSEEK_API_KEY not set in .env file")
    return key

def get_gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise ValueError("DEEPSEEK_API_KEY not set in .env file")
    return key
