import logging
from google import genai
from google.genai import types
from google.genai.errors import APIError
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception
from .config import get_gemini_api_key

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are an expert YouTube video summarizer specializing in technical and regulatory webinars.\n"
    "You MUST generate the ENTIRE response (including headers, field titles, labels, bullets, and text) in the EXACT SAME language as the provided transcript. "
    "For example, if the transcript is in Spanish, ALL section titles like 'Título', 'Temas Clave', 'Resumen en Puntos', and 'Conclusiones Clave' MUST be written in Spanish.\n\n"
    "Your output MUST consist of two parts, formatted as follows:\n\n"
    "### **PARTE 1: RESUMEN CONCISO / PART 1: CONCISE SUMMARY** (Translate heading to transcript language)\n"
    "1. **Título / Title**: Catchy and descriptive title (in the transcript language)\n"
    "2. **Temas Clave / Key Topics**: Comma-separated list of main subjects\n"
    "3. **Resumen en Puntos / Bullet-point Summary**: 4-5 high-level bullet points covering core concepts\n"
    "4. **Conclusiones Clave / Key Takeaways**: 3 action-oriented or strategic lessons learned\n\n"
    "---\n\n"
    "### **PARTE 2: RESUMEN EXHAUSTIVO Y DETALLADO / PART 2: COMPREHENSIVE SUMMARY** (Translate heading to transcript language)\n"
    "Provide an exhaustive, long-form, and highly detailed summary of the transcript. "
    "Explain all the arguments, technical specifications, legal/regulatory frameworks, and business models discussed.\n"
    "- Start with a brief introductory paragraph stating the webinar title, moderator, context/event, and dates.\n"
    "- Organize the main content by speaker (stating their full name, job title, and company) or major chronological blocks.\n"
    "- Under each speaker, write detailed sections/bullet points containing all original numbers, percentages, costs, LER codes, specific laws/decrees, and technology names.\n"
    "- If a process flow or balance of mass/energy is described, include a simple ASCII text flowchart representing it.\n"
    "- End with a dedicated 'Sesión de Q&A / Q&A Highlights' section detailing the specific questions asked by the audience and the exact answers given by the speakers.\n\n"
    "Do not extrapolate or introduce external facts. Base your response strictly on the provided transcript."
)

USER_PROMPT_TEMPLATE = """
Here is the transcript of a YouTube video:
<transcript>
{transcript}
</transcript>

Please summarize the transcript above according to your system instructions.
"""

def should_retry_api_error(exception: Exception) -> bool:
    if isinstance(exception, APIError):
        # APIError in google-genai usually has a 'code' attribute for HTTP status
        status_code = getattr(exception, 'code', None)
        if status_code in (429, 500, 502, 503, 504):
            return True
    return False

class GeminiSummarizer:
    def __init__(self, model_name: str = "gemini-3.1-flash-lite"):
        api_key = get_gemini_api_key()
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=2, max=10, jitter=1),
        retry=retry_if_exception(should_retry_api_error),
        reraise=True
    )
    def generate_summary(self, transcript_text: str, target_language: str = "es") -> str:
        """
        Sends the transcript to Gemini for summarization.
        Uses exponential backoff with jitter for transient errors and rate limits.
        """
        lang_names = {
            "es": "Spanish",
            "en": "English",
            "fr": "French",
            "de": "German",
            "it": "Italian"
        }
        lang_full = lang_names.get(target_language.lower(), target_language)
        
        dynamic_instruction = (
            f"You are an expert YouTube video summarizer specializing in technical and regulatory webinars.\n"
            f"CRITICAL REQUIREMENT: You MUST generate the ENTIRE response (including headers, titles, bullet points, labels, and text) in **{lang_full}**.\n\n"
            f"Output Format (All in {lang_full}):\n"
            f"### **PART 1: CONCISE SUMMARY** (Translated to {lang_full})\n"
            f"1. **Title**: Catchy and descriptive title in {lang_full}\n"
            f"2. **Key Topics**: Comma-separated list of main subjects in {lang_full}\n"
            f"3. **Bullet-point Summary**: 4-5 high-level bullet points in {lang_full}\n"
            f"4. **Key Takeaways**: 3 action-oriented or strategic lessons learned in {lang_full}\n\n"
            f"---\n\n"
            f"### **PART 2: COMPREHENSIVE AND IN-DEPTH SUMMARY** (Translated to {lang_full})\n"
            f"Provide an exhaustive, long-form, and highly detailed summary of the transcript written entirely in {lang_full}.\n"
            f"- Start with a brief introductory paragraph stating the webinar title, moderator, context/event, and dates.\n"
            f"- Organize main content by speaker or major chronological blocks.\n"
            f"- Detailed bullet points containing all numbers, costs, laws/decrees, and technology names.\n"
            f"- End with a dedicated 'Q&A Highlights' section in {lang_full}.\n\n"
            f"Do not extrapolate or introduce external facts. Base your response strictly on the provided transcript."
        )
        
        prompt = USER_PROMPT_TEMPLATE.format(transcript=transcript_text)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=dynamic_instruction,
                )
            )
            return response.text
        except Exception as e:
            logger.warning(f"Error during Gemini API call: {e}")
            raise
