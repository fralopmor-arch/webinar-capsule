import os
import sys
from pathlib import Path

# Ensure src directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamlit.web.cli import main as streamlit_main

def application(environ, start_response):
    """Fallback WSGI wrapper for Vercel deployment detection."""
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    start_response(status, headers)
    return [b"Webinar Capsule Streamlit App Serverless Endpoint"]

app = application

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app.py"]
    streamlit_main()

