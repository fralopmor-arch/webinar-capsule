from youtube_summarizer.html_export import generate_html_capsule

def test_generate_html_capsule_structure():
    video_id = "test_vid_123"
    title = "Test Webinar on AI Systems"
    summary = "## Overview\nThis is a *great* webinar about **agents**.\n\n- Key Point 1\n- Key Point 2"
    transcript = "00:00 Welcome to the webinar.\n00:10 Today we talk about AI."
    metadata = {
        "model": "deepseek-chat",
        "word_count": 350,
        "elapsed_seconds": 12.4
    }

    html = generate_html_capsule(
        video_id=video_id,
        title=title,
        summary_markdown=summary,
        transcript=transcript,
        metadata=metadata
    )

    # Basic validations
    assert "<!DOCTYPE html>" in html
    assert f"<title>{title} - Webinar Capsule</title>" in html
    assert f"https://www.youtube-nocookie.com/embed/{video_id}" in html
    assert "<strong>agents</strong>" in html
    assert "<em>great</em>" in html
    assert "<li>Key Point 1</li>" in html
    assert "00:00 Welcome to the webinar." in html
    assert "deepseek-chat" in html
    assert "12.4s" in html
