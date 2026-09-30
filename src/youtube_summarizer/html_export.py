import html
import markdown
from typing import Optional, Dict, Any
from datetime import datetime

def generate_html_capsule(
    video_id: str,
    title: str,
    summary_markdown: str,
    transcript: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Generates a complete, self-contained standalone HTML Webinar Capsule.
    
    Includes an embedded YouTube video player, formatted AI summary,
    collapsible transcript, and metadata.
    """
    safe_title = html.escape(title or "Webinar Capsule")
    safe_video_id = html.escape(video_id or "")
    meta = metadata or {}
    
    # Convert markdown summary to HTML
    html_summary = markdown.markdown(
        summary_markdown or "",
        extensions=["fenced_code", "tables", "nl2br"]
    )
    
    # Metadata badges
    model_name = html.escape(str(meta.get("model", "AI Assistant")))
    word_count = meta.get("word_count", len((summary_markdown or "").split()))
    elapsed = meta.get("elapsed_seconds")
    date_str = datetime.now().strftime("%B %d, %Y")
    
    safe_transcript = html.escape(transcript or "")
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title} - Webinar Capsule</title>
  <style>
    :root {{
      --bg-color: #0F172A;
      --card-bg: #1E293B;
      --card-border: #334155;
      --text-main: #F8FAFC;
      --text-muted: #94A3B8;
      --accent: #6366F1;
      --accent-hover: #4F46E5;
      --accent-light: rgba(99, 102, 241, 0.15);
      --code-bg: #0b1120;
    }}

    @media (prefers-color-scheme: light) {{
      :root {{
        --bg-color: #F8FAFC;
        --card-bg: #FFFFFF;
        --card-border: #E2E8F0;
        --text-main: #0F172A;
        --text-muted: #64748B;
        --accent: #4F46E5;
        --accent-hover: #4338CA;
        --accent-light: rgba(79, 70, 229, 0.08);
        --code-bg: #F1F5F9;
      }}
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-color);
      color: var(--text-main);
      line-height: 1.6;
      padding: 2rem 1rem;
    }}

    .container {{
      max-width: 960px;
      margin: 0 auto;
    }}

    header {{
      margin-bottom: 2rem;
    }}

    .badge {{
      display: inline-block;
      background: var(--accent-light);
      color: var(--accent);
      border: 1px solid var(--accent);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 0.75rem;
    }}

    h1.title {{
      font-size: 2rem;
      font-weight: 800;
      margin-bottom: 0.75rem;
      line-height: 1.25;
    }}

    .meta-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      font-size: 0.875rem;
      color: var(--text-muted);
      align-items: center;
      margin-bottom: 1.5rem;
    }}

    .meta-item {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }}

    .actions-bar {{
      display: flex;
      gap: 0.75rem;
      margin-bottom: 2rem;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-size: 0.875rem;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      border: 1px solid var(--card-border);
      background: var(--card-bg);
      color: var(--text-main);
      transition: all 0.2s ease;
    }}

    .btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
    }}

    .btn-primary {{
      background: var(--accent);
      color: #FFFFFF !important;
      border-color: var(--accent);
    }}

    .btn-primary:hover {{
      background: var(--accent-hover);
    }}

    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.75rem;
      margin-bottom: 2rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    }}

    .video-container {{
      position: relative;
      padding-bottom: 56.25%; /* 16:9 aspect ratio */
      height: 0;
      overflow: hidden;
      border-radius: 8px;
      background: #000;
      margin-bottom: 1rem;
    }}

    .video-container iframe {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      border: 0;
    }}

    .card h2 {{
      font-size: 1.35rem;
      font-weight: 700;
      margin-bottom: 1.25rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}

    /* Markdown Summary Typography */
    .summary-content {{
      font-size: 1rem;
      line-height: 1.75;
    }}

    .summary-content h1, .summary-content h2, .summary-content h3, .summary-content h4 {{
      color: var(--text-main);
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      font-weight: 700;
    }}

    .summary-content h1 {{ font-size: 1.5rem; }}
    .summary-content h2 {{ font-size: 1.25rem; }}
    .summary-content h3 {{ font-size: 1.1rem; }}

    .summary-content p {{
      margin-bottom: 1rem;
    }}

    .summary-content ul, .summary-content ol {{
      margin-left: 1.5rem;
      margin-bottom: 1rem;
    }}

    .summary-content li {{
      margin-bottom: 0.4rem;
    }}

    .summary-content blockquote {{
      border-left: 4px solid var(--accent);
      padding: 0.5rem 1rem;
      margin: 1rem 0;
      background: var(--accent-light);
      border-radius: 0 6px 6px 0;
      color: var(--text-muted);
      font-style: italic;
    }}

    .summary-content code {{
      background: var(--code-bg);
      padding: 0.2rem 0.4rem;
      border-radius: 4px;
      font-size: 0.875em;
      font-family: ui-monospace, SFMono-Regular, "JetBrains Mono", Menlo, Consolas, monospace;
    }}

    .summary-content pre {{
      background: var(--code-bg);
      padding: 1rem;
      border-radius: 8px;
      overflow-x: auto;
      margin: 1rem 0;
    }}

    .summary-content pre code {{
      background: transparent;
      padding: 0;
    }}

    /* Collapsible Transcript */
    details.transcript-accordion {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem;
      margin-bottom: 2rem;
    }}

    details.transcript-accordion summary {{
      font-weight: 700;
      font-size: 1.1rem;
      cursor: pointer;
      list-style: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
      user-select: none;
    }}

    details.transcript-accordion summary::-webkit-details-marker {{
      display: none;
    }}

    details.transcript-accordion summary::after {{
      content: "▼";
      font-size: 0.8rem;
      color: var(--text-muted);
      transition: transform 0.2s ease;
    }}

    details[open].transcript-accordion summary::after {{
      transform: rotate(180deg);
    }}

    .transcript-box {{
      margin-top: 1rem;
      max-height: 400px;
      overflow-y: auto;
      background: var(--code-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 1rem;
      font-size: 0.875rem;
      line-height: 1.6;
      white-space: pre-wrap;
      color: var(--text-muted);
    }}

    footer {{
      text-align: center;
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-top: 3rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--card-border);
    }}

    @media print {{
      body {{
        background: #fff;
        color: #000;
      }}
      .actions-bar, .video-card {{
        display: none !important;
      }}
      .card {{
        box-shadow: none;
        border: 1px solid #ccc;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <span class="badge">⚡ Webinar Capsule</span>
      <h1 class="title">{safe_title}</h1>
      
      <div class="meta-bar">
        <span class="meta-item">📅 {date_str}</span>
        <span class="meta-item">🤖 Model: <strong>{model_name}</strong></span>
        <span class="meta-item">📝 Words: <strong>{word_count:,}</strong></span>
        {f'<span class="meta-item">⚡ Processed in: <strong>{elapsed}s</strong></span>' if elapsed else ''}
      </div>

      <div class="actions-bar">
        {f'<a class="btn btn-primary" href="https://www.youtube.com/watch?v={safe_video_id}" target="_blank" rel="noopener noreferrer">▶ Watch on YouTube</a>' if safe_video_id else ''}
        <button class="btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
      </div>
    </header>

    <!-- Embedded Video Player -->
    {f'''<section class="card video-card">
      <h2>🎬 Video Playback</h2>
      <div class="video-container">
        <iframe 
          src="https://www.youtube-nocookie.com/embed/{safe_video_id}" 
          title="{safe_title}" 
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
          allowfullscreen>
        </iframe>
      </div>
    </section>''' if safe_video_id else ''}

    <!-- AI Executive Summary -->
    <section class="card">
      <h2>✨ Executive Summary</h2>
      <div class="summary-content">
        {html_summary}
      </div>
    </section>

    <!-- Collapsible Transcript -->
    {f'''<details class="transcript-accordion">
      <summary>📜 View Full Sanitized Transcript</summary>
      <div class="transcript-box">
{safe_transcript}
      </div>
    </details>''' if safe_transcript else ''}

    <footer>
      Generated with <strong>Webinar Capsule</strong> &bull; AI YouTube Intelligence Pipeline
    </footer>
  </div>
</body>
</html>"""
    return html_content
