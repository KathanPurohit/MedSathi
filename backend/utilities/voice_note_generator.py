import base64
import io
from gtts import gTTS


LANGUAGE_CODE_MAP = {
    "English": "en",
    "Hindi": "hi",
    "Gujarati": "gu",
}


def generate_voice_note_base64(voice_script: str, language: str) -> str:
    """Converts the translated voice script into an in-memory Base64 MP3 data URL."""
    lang_code = LANGUAGE_CODE_MAP.get(language, "en")
    mp3_buffer = io.BytesIO()

    tts = gTTS(text=voice_script, lang=lang_code, slow=False)
    tts.write_to_fp(mp3_buffer)
    mp3_buffer.seek(0)

    encoded_mp3 = base64.b64encode(mp3_buffer.read()).decode("utf-8")
    return f"data:audio/mp3;base64,{encoded_mp3}"
