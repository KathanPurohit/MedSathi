import base64
import io
import logging
from gtts import gTTS

# Neural natural caregiver & doctor voices via Microsoft Edge Neural TTS
EDGE_VOICE_MAP = {
    "English": {
        "female": "en-IN-NeerjaExpressiveNeural",
        "male": "en-IN-PrabhatNeural",
    },
    "Hindi": {
        "female": "hi-IN-SwaraNeural",
        "male": "hi-IN-MadhurNeural",
    },
    "Gujarati": {
        "female": "gu-IN-DhwaniNeural",
        "male": "gu-IN-NiranjanNeural",
    },
}

GTTS_LANG_MAP = {
    "English": "en",
    "Hindi": "hi",
    "Gujarati": "gu",
}


async def generate_voice_note_base64(voice_script: str, language: str = "English", gender: str = "female") -> str:
    """Converts translated voice script into a human-sounding Base64 MP3 voice note with selectable doctor persona."""
    normalized_gender = "male" if gender and gender.lower() == "male" else "female"
    lang_voices = EDGE_VOICE_MAP.get(language, EDGE_VOICE_MAP["English"])
    voice_name = lang_voices.get(normalized_gender, "en-IN-NeerjaExpressiveNeural")

    try:
        import edge_tts

        communicate = edge_tts.Communicate(voice_script, voice_name)
        mp3_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_buffer.write(chunk["data"])

        mp3_buffer.seek(0)
        encoded_mp3 = base64.b64encode(mp3_buffer.read()).decode("utf-8")
        return f"data:audio/mp3;base64,{encoded_mp3}"
    except Exception as exc:
        logging.warning(f"[Edge TTS Error] Fallback to gTTS due to: {exc}")
        lang_code = GTTS_LANG_MAP.get(language, "en")
        fallback_buf = io.BytesIO()
        tts = gTTS(text=voice_script, lang=lang_code, slow=False)
        tts.write_to_fp(fallback_buf)
        fallback_buf.seek(0)
        encoded_mp3 = base64.b64encode(fallback_buf.read()).decode("utf-8")
        return f"data:audio/mp3;base64,{encoded_mp3}"
