import sys
from pathlib import Path

# Add project root to PYTHONPATH so "from src.youtube_summarizer..." works
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)
