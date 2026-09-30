import io
from docx import Document
from youtube_summarizer.docx_export import markdown_to_docx

def test_markdown_to_docx_generation():
    md = """# Webinar Title

This is a test summary with **bold**, *italic*, and `code`.

## Key Takeaways
- Point 1
- Point 2

1. Numbered item A
2. Numbered item B

> Important quote

```python
print("Hello world")
```
"""
    buf = markdown_to_docx(md, title="Test Video Title")
    assert isinstance(buf, io.BytesIO)
    data = buf.getvalue()
    assert len(data) > 0

    # Load back with python-docx to verify integrity
    doc = Document(io.BytesIO(data))
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    assert any("Test Video Title" in p for p in paragraphs)
    assert any("Webinar Title" in p for p in paragraphs)
    assert any("Key Takeaways" in p for p in paragraphs)
    assert any("Point 1" in p for p in paragraphs)
