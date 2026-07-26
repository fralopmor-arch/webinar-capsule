import os
import json
import time
import streamlit as st
from youtube_summarizer.transcript import parse_video_id, get_transcript, transcribe_audio_fallback, get_video_title
from youtube_summarizer.sanitizer import sanitize_transcript
from youtube_summarizer.storage import save_transcript, save_summary, load_transcript, transcript_exists, SUMMARIES_DIR
from youtube_summarizer.summarizer import GeminiSummarizer

# Page configuration
st.set_page_config(
    page_title="Webinar Capsule | AI YouTube Summarizer",
    page_icon=":material/movie:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
st.session_state.setdefault("summary_result", None)
st.session_state.setdefault("transcript_result", None)
st.session_state.setdefault("video_title", None)
st.session_state.setdefault("video_id", None)
st.session_state.setdefault("pipeline_metadata", {})

# Custom CSS Polish for Landing Hero & Premium SaaS Look
st.html("""
<style>
    /* Metric & Card Glassmorphic Touches */
    [data-testid="stHeader"] {
        background: transparent;
    }
    .hero-title {
        font-size: 2.4rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #818CF8 0%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        color: #818CF8;
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
</style>
""")

# Top Hero / Navigation Bar
with st.container():
    st.markdown('<span class="hero-badge">⚡ AI-POWERED WEBINAR INTELLIGENCE</span>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">Webinar Capsule</h1>', unsafe_allow_html=True)
    st.caption("Instantly extract, translate, and synthesize complex YouTube webinars into actionable executive summaries.")

st.space("small")

# Sidebar Configuration & Settings
with st.sidebar:
    st.header("Workspace Settings")
    st.space("small")
    
    selected_model = st.selectbox(
        "Gemini model",
        options=[
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash",
            "gemini-2.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-2.5-pro"
        ],
        index=0,
        help="Select the Google Gemini model to process and summarize the transcript."
    )
    
    available_languages = st.pills(
        "Preferred caption languages",
        options=["es", "en", "fr", "de", "it"],
        default=["es", "en"],
        selection_mode="multi",
        help="Prioritized order of transcript languages to search for on YouTube."
    )
    
    st.space("small")
    enable_whisper = st.toggle(
        "Enable Whisper fallback",
        value=True,
        help="Fallback to local audio transcription (faster-whisper) if no YouTube captions are available."
    )
    
    no_save_option = st.toggle(
        "Disable local caching",
        value=False,
        help="If enabled, raw transcripts and generated summaries will not be saved to disk."
    )
    
    st.space("large")
    with st.container(border=True):
        st.markdown("**Enterprise Features**")
        st.caption("• Automated Transcription\n• Multi-Language Synthesis\n• Structured Key Takeaways")

# Main Container Layout
col_input, col_preview = st.columns([7, 5])

with col_input:
    with st.container(border=True):
        st.subheader("Input Video")
        video_url = st.text_input(
            "YouTube Video URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any standard YouTube video URL or shortened link.",
            label_visibility="collapsed"
        )
        
        with st.container(horizontal=True, horizontal_alignment="left"):
            start_button = st.button(
                "Generate Summary",
                type="primary",
                icon=":material/auto_awesome:",
                disabled=not bool(video_url.strip())
            )

with col_preview:
    with st.container(border=True):
        st.subheader("Video Preview")
        if video_url.strip():
            try:
                vid_id = parse_video_id(video_url.strip())
                clean_url = f"https://www.youtube.com/watch?v={vid_id}"
                st.video(clean_url)
            except Exception:
                st.caption("Invalid or unsupported video URL for embed preview.")
        else:
            st.caption("Enter a valid YouTube URL above to view video preview.")

st.space("medium")

from youtube_summarizer.storage import save_transcript, save_summary, load_transcript, transcript_exists, check_user_rate_limit, record_user_request

# Get client IP / session ID
client_ip = "127.0.0.1"
try:
    if hasattr(st, "context") and hasattr(st.context, "headers"):
        client_ip = st.context.headers.get("x-forwarded-for", "127.0.0.1").split(",")[0]
except Exception:
    pass

st.session_state.setdefault("local_request_count", 0)

# Pipeline Execution Trigger
if start_button and video_url.strip():
    start_time = time.time()
    st.session_state["summary_result"] = None
    st.session_state["transcript_result"] = None
    st.session_state["video_title"] = None
    st.session_state["video_id"] = None
    st.session_state["pipeline_metadata"] = {}
    
    # Real-time 0-100% Progress Bar
    progress_bar = st.progress(0, text="🚀 Initializing intelligence pipeline (0%)...")
    
    with st.status("Processing YouTube video...", expanded=True) as status:
        try:
            # 1. Parse URL & Validate Video ID (15%)
            progress_bar.progress(15, text="🔍 Extracting YouTube Video ID (15%)...")
            st.write("🔍 **Parsing YouTube URL...**")
            video_id = parse_video_id(video_url.strip())
            st.session_state["video_id"] = video_id
            st.write(f"✓ Video ID extracted: `{video_id}`")
            
            # Fetch Video Title (30%)
            progress_bar.progress(30, text="🎬 Fetching metadata and video details (30%)...")
            st.write("🎬 **Fetching video metadata...**")
            title = get_video_title(video_id)
            st.session_state["video_title"] = title
            st.write(f"✓ Title: **{title}**")
            
            # 2. Extract Transcript (50%)
            progress_bar.progress(50, text="📥 Extracting transcript captions (50%)...")
            transcript_text = ""
            metadata = {}
            langs = available_languages if available_languages else ["es", "en"]
            
            if not no_save_option and transcript_exists(video_id):
                st.write("⚡ **Found cached transcript.** Loading...")
                transcript_text = load_transcript(video_id)
                metadata = {"source": "local-cache"}
            else:
                st.write(f"📥 **Extracting captions** (preferred languages: `{', '.join(langs)}`)...")
                result = get_transcript(video_id, langs)
                
                if result:
                    transcript_text = result["text"]
                    metadata = {
                        "language": result["language"],
                        "is_generated": result["is_generated"],
                        "source": "youtube-transcript-api"
                    }
                    st.write(f"✓ Captions extracted ({result['language']})")
                elif enable_whisper:
                    progress_bar.progress(60, text="🎙️ Running local Whisper audio transcription (60%)...")
                    st.write("🎙️ **No captions found.** Falling back to local audio transcription (Whisper)...")
                    result = transcribe_audio_fallback(video_url.strip())
                    transcript_text = result["text"]
                    metadata = {
                        "language": result.get("language", "auto"),
                        "is_generated": True,
                        "source": "faster-whisper"
                    }
                    st.write("✓ Whisper transcription completed.")
                else:
                    raise ValueError("No YouTube captions found and Whisper fallback is disabled.")
                
                # Sanitize Transcript (70%)
                progress_bar.progress(70, text="🧹 Sanitizing and formatting transcript (70%)...")
                st.write("🧹 **Sanitizing transcript text...**")
                transcript_text = sanitize_transcript(transcript_text)
                
                # Save Transcript
                if not no_save_option:
                    save_transcript(video_id, transcript_text, metadata, save_to_disk=True)
                    st.write("✓ Saved transcript to cache.")
            
            st.session_state["transcript_result"] = transcript_text
            
            # 3. Summarize with Gemini (85%)
            progress_bar.progress(85, text=f"🤖 Synthesizing AI executive summary via {selected_model} (85%)...")
            summary_lang = langs[0] if langs else "es"
            st.write(f"🤖 **Generating AI summary in `{summary_lang}` using `{selected_model}`...**")
            summarizer = GeminiSummarizer(model_name=selected_model)
            summary = summarizer.generate_summary(transcript_text, target_language=summary_lang)
            
            if not no_save_option:
                summary_file = save_summary(video_id, summary, title=title, save_to_disk=True)
                st.write(f"✓ Saved summary to `{summary_file}`")
            
            # Complete (100%)
            progress_bar.progress(100, text="🎉 Summary generation complete! (100%)")
            elapsed = time.time() - start_time
            st.session_state["summary_result"] = summary
            st.session_state["pipeline_metadata"] = {
                "elapsed_seconds": round(elapsed, 2),
                "model": selected_model,
                "source": metadata.get("source", "unknown"),
                "char_count": len(transcript_text),
                "word_count": len(transcript_text.split()),
                "language": metadata.get("language", "unknown")
            }
            
            status.update(label=f"Pipeline completed in {elapsed:.1f}s!", state="complete", expanded=False)
            st.toast("Summary generated successfully!", icon=":material/check_circle:")
            
        except Exception as e:
            progress_bar.empty()
            status.update(label="Pipeline failed", state="error", expanded=True)
            st.error(f"Error: {str(e)}", icon=":material/error:")
            if "FFmpeg" in str(e):
                st.info("Tip: Install FFmpeg to enable audio downloading and Whisper transcription.", icon=":material/lightbulb:")
            elif "API_KEY" in str(e) or "400" in str(e) or "403" in str(e):
                st.info("Tip: Check your GEMINI_API_KEY setting in the environment/.env file.", icon=":material/lightbulb:")



# Key Highlights Metric Header (when summary is loaded)
if st.session_state["summary_result"]:
    meta = st.session_state.get("pipeline_metadata", {})
    with st.container(horizontal=True):
        st.metric("Processing Time", f"{meta.get('elapsed_seconds', 0)}s", delta="Fast Pipeline", border=True)
        st.metric("Word Count", f"{meta.get('word_count', 0):,}", border=True)
        st.metric("Model Used", meta.get('model', selected_model), border=True)
    st.space("small")

# Results Display Section
with st.container(border=True):
    st.subheader("Results Overview")
    tab_summary, tab_transcript, tab_export = st.tabs([
        "AI Summary",
        "Transcript Search & Viewer",
        "Downloads & Export"
    ])

    with tab_summary:
        if st.session_state["summary_result"]:
            st.markdown(st.session_state["summary_result"])
        else:
            st.caption("No summary generated yet. Enter a YouTube URL and click 'Generate Summary' to begin.")

    with tab_transcript:
        if st.session_state["transcript_result"]:
            transcript = st.session_state["transcript_result"]
            
            search_query = st.text_input(
                "Search transcript",
                placeholder="Type a keyword to filter lines...",
                icon=":material/search:"
            )
            
            if search_query.strip():
                lines = transcript.splitlines()
                matching_lines = [line for line in lines if search_query.lower() in line.lower()]
                st.caption(f"Found {len(matching_lines)} matching lines out of {len(lines)} total lines.")
                filtered_text = "\n".join(matching_lines)
                st.text_area("Filtered transcript lines", filtered_text, height=350)
            else:
                st.text_area("Full sanitized transcript", transcript, height=350)
        else:
            st.caption("No transcript loaded yet.")

    with tab_export:
        if st.session_state["summary_result"] and st.session_state["transcript_result"]:
            vid_id = st.session_state.get("video_id", "summary")
            title = st.session_state.get("video_title", "Summary")
            meta = st.session_state.get("pipeline_metadata", {})
            
            st.subheader("Download Files")
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            
            with col_dl1:
                st.download_button(
                    label="Download Summary (.md)",
                    data=st.session_state["summary_result"],
                    file_name=f"{vid_id}_summary.md",
                    mime="text/markdown",
                    icon=":material/description:",
                    width="stretch"
                )
                
            with col_dl2:
                st.download_button(
                    label="Download Transcript (.txt)",
                    data=st.session_state["transcript_result"],
                    file_name=f"{vid_id}_transcript.txt",
                    mime="text/plain",
                    icon=":material/article:",
                    width="stretch"
                )
                
            json_export_data = {
                "video_id": vid_id,
                "title": title,
                "metadata": meta,
                "summary": st.session_state["summary_result"],
                "transcript": st.session_state["transcript_result"]
            }
            json_str = json.dumps(json_export_data, indent=2, ensure_ascii=False)
            
            with col_dl3:
                st.download_button(
                    label="Download Full Package (.json)",
                    data=json_str,
                    file_name=f"{vid_id}_bundle.json",
                    mime="application/json",
                    icon=":material/folder_zip:",
                    width="stretch"
                )
        else:
            st.caption("Export options will be available after generating a summary.")
