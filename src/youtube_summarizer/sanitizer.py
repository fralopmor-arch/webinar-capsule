import re

def sanitize_transcript(text: str) -> str:
    """
    Cleans raw transcript text by removing YouTube artifacts,
    normalizing whitespace, and cleaning up characters.
    """
    if not text:
        return ""
        
    # Remove common tags like [Music], [Applause], (Laughter)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    
    # Normalize unicode / zero-width spaces
    text = text.replace('\u200b', '')
    
    # Collapse multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    return text.strip()
