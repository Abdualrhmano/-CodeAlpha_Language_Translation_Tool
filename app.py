
"""
Language Translation Tool - CodeAlpha AI Internship
--------------------------------------------------
Streamlit app that translates text between languages using googletrans
for translation/detection and gTTS for text-to-speech playback.
Features:
- Auto-detect source language
- Select source and target languages
- Translate button with styled UI
- Output container with translated text
- Copy-to-clipboard button (client-side)
- Text-to-Speech playback and audio download
"""

from typing import Dict, Tuple
import tempfile
import os
import logging

import streamlit as st
import streamlit.components.v1 as components
from googletrans import Translator, LANGUAGES
from gtts import gTTS
from requests.exceptions import RequestException

# Configure basic logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def build_language_map() -> Dict[str, str]:
    """
    Build a curated language map for the UI.

    Returns:
        Dict[str, str]: Mapping of display name -> language code.
    """
    # Start with a curated set of common languages
    curated = {
        "Auto-detect": "auto",
        "English": "en",
        "Arabic": "ar",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Chinese (Simplified)": "zh-cn",
        "Chinese (Traditional)": "zh-tw",
        "Japanese": "ja",
        "Korean": "ko",
        "Russian": "ru",
        "Portuguese": "pt",
        "Italian": "it",
        "Dutch": "nl",
        "Turkish": "tr",
        "Hindi": "hi",
        "Bengali": "bn",
        "Urdu": "ur",
        "Vietnamese": "vi",
        "Polish": "pl",
    }

    # Ensure codes are valid according to googletrans LANGUAGES
    # googletrans uses two-letter codes like 'zh-cn' is not in LANGUAGES keys,
    # so we keep curated mapping but validate common two-letter codes.
    valid_map = {}
    for name, code in curated.items():
        # Normalize some codes for googletrans compatibility
        normalized = code.lower()
        if normalized == "zh-cn":
            normalized = "zh-cn"  # googletrans accepts 'zh-cn' in translate but LANGUAGES uses 'zh-cn' not present; keep as-is
        if normalized == "zh-tw":
            normalized = "zh-tw"
        valid_map[name] = normalized
    return valid_map


def detect_language(translator: Translator, text: str) -> Tuple[str, float]:
    """
    Detect the language of the provided text.

    Args:
        translator (Translator): googletrans Translator instance.
        text (str): Text to detect.

    Returns:
        Tuple[str, float]: Detected language code and confidence (0-1).
    """
    try:
        detection = translator.detect(text)
        # detection.lang is language code, detection.confidence is float
        lang_code = detection.lang if hasattr(detection, "lang") else str(detection)
        confidence = getattr(detection, "confidence", 0.0)
        return lang_code, float(confidence)
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Language detection failed: %s", exc)
        return "unknown", 0.0


def translate_text(
    translator: Translator, text: str, src: str, dest: str
) -> Tuple[str, str]:
    """
    Translate text using googletrans.

    Args:
        translator (Translator): googletrans Translator instance.
        text (str): Text to translate.
        src (str): Source language code or 'auto'.
        dest (str): Destination language code.

    Returns:
        Tuple[str, str]: (translated_text, detected_source_code)
    """
    if not text or not text.strip():
        raise ValueError("Input text is empty.")

    try:
        # If src is 'auto', let googletrans detect automatically by passing src='auto'
        result = translator.translate(text, src=src if src != "auto" else "auto", dest=dest)
        translated = result.text
        detected = getattr(result, "src", src)
        return translated, detected
    except RequestException as req_exc:
        LOGGER.exception("Network error during translation: %s", req_exc)
        raise
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Translation failed: %s", exc)
        raise


def generate_tts_audio(text: str, lang: str) -> bytes:
    """
    Generate TTS audio bytes using gTTS.

    Args:
        text (str): Text to convert to speech.
        lang (str): Language code for TTS.

    Returns:
        bytes: MP3 audio bytes.
    """
    if not text or not text.strip():
        raise ValueError("No text provided for TTS.")

    try:
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            temp_path = tmp.name
        tts.save(temp_path)
        with open(temp_path, "rb") as f:
            audio_bytes = f.read()
        # Clean up temp file
        try:
            os.remove(temp_path)
        except OSError:
            LOGGER.warning("Could not remove temporary TTS file: %s", temp_path)
        return audio_bytes
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("TTS generation failed: %s", exc)
        raise


def render_copy_button(text: str, element_id: str = "translated_text") -> None:
    """
    Render a client-side copy-to-clipboard button using an HTML component.

    Args:
        text (str): Text to copy.
        element_id (str): DOM id for the hidden textarea.
    """
    # Use a small HTML + JS snippet to copy text to clipboard
    safe_text = text.replace("\\", "\\\\").replace("'", "\\'")
    html = f"""
    <div style="display:flex; gap:8px; align-items:center;">
      <textarea id="{element_id}" style="display:none;">{safe_text}</textarea>
      <button onclick="
        const t = document.getElementById('{element_id}');
        navigator.clipboard.writeText(t.value).then(() => {{
          const btn = document.getElementById('copy-btn');
          btn.innerText = 'Copied';
          setTimeout(()=> btn.innerText = 'Copy', 1500);
        }});
      " id="copy-btn" style="
        background-color:#4CAF50;
        color:white;
        border:none;
        padding:8px 12px;
        border-radius:6px;
        cursor:pointer;
        font-weight:600;
      ">Copy</button>
    </div>
    """
    components.html(html, height=50)


def main() -> None:
    """
    Main Streamlit application entrypoint.
    """
    st.set_page_config(
        page_title="Language Translation Tool",
        page_icon="🌐",
        layout="centered",
        initial_sidebar_state="auto",
    )

    st.title("🌐 Language Translation Tool")
    st.markdown(
        "Translate text between languages with auto-detection, copy-to-clipboard, "
        "and text-to-speech playback."
    )

    # Sidebar with small help and credits
    with st.sidebar:
        st.header("About")
        st.write(
            "This app uses **googletrans** for translation and detection, "
            "and **gTTS** for text-to-speech audio."
        )
        st.markdown("---")
        st.write("CodeAlpha AI Internship — Task 1")

    # Build language map and UI controls
    language_map = build_language_map()
    language_names = list(language_map.keys())

    st.subheader("Input")
    source_text = st.text_area(
        "Enter text to translate",
        placeholder="Type or paste text here...",
        height=180,
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        source_choice = st.selectbox("Source Language", language_names, index=0)
    with col2:
        # Default target language is English
        default_target_index = language_names.index("English") if "English" in language_names else 1
        target_choice = st.selectbox("Target Language", language_names, index=default_target_index)

    # Styled translate button
    translate_button = st.button(
        "Translate",
        key="translate_btn",
    )

    # Initialize translator instance
    translator = Translator()

    # Output container
    output_container = st.container()

    if translate_button:
        # Validate input
        if not source_text or not source_text.strip():
            st.warning("Please enter text to translate.")
        else:
            try:
                src_code = language_map.get(source_choice, "auto")
                dest_code = language_map.get(target_choice, "en")

                # If user selected Auto-detect, we will detect first for feedback
                detected_lang_code = src_code
                detected_confidence = 0.0
                if src_code == "auto":
                    detected_lang_code, detected_confidence = detect_language(translator, source_text)
                    # If detection failed, fallback to 'auto' for translation call
                    if detected_lang_code == "unknown":
                        detected_lang_code = "auto"

                # Perform translation
                translated_text, detected_from_translate = translate_text(
                    translator, source_text, src_code, dest_code
                )

                # If googletrans returned a detected source, prefer that for display
                if detected_from_translate and detected_from_translate != "auto":
                    detected_lang_code = detected_from_translate

                # Map detected code to human-readable name if possible
                detected_name = LANGUAGES.get(detected_lang_code, detected_lang_code)

                # Display results in a well-designed output container
                with output_container:
                    st.markdown("### Translated Text")
                    st.success(translated_text)

                    # Show detection feedback if auto-detect was used
                    if source_choice == "Auto-detect":
                        st.info(
                            f"Detected source language: **{detected_name}** "
                            f"(confidence: {detected_confidence:.2f})"
                        )

                    # Copy to clipboard button (client-side)
                    st.markdown("**Copy translated text**")
                    render_copy_button(translated_text, element_id="translated_text_area")

                    # Text-to-Speech controls
                    st.markdown("---")
                    st.markdown("**Text-to-Speech (TTS)**")
                    try:
                        # gTTS expects a language code like 'en', 'es', etc.
                        # For some codes like 'zh-cn' or 'zh-tw', gTTS may accept 'zh-cn' or 'zh-tw'.
                        tts_lang = dest_code
                        # Some normalization: gTTS uses 'zh-cn' as 'zh-CN' sometimes; keep lower-case
                        audio_bytes = generate_tts_audio(translated_text, tts_lang)
                        if audio_bytes:
                            st.audio(audio_bytes, format="audio/mp3")
                            st.download_button(
                                label="Download audio (MP3)",
                                data=audio_bytes,
                                file_name="translation.mp3",
                                mime="audio/mpeg",
                            )
                    except Exception as tts_exc:
                        LOGGER.exception("TTS error: %s", tts_exc)
                        st.error("Text-to-Speech failed. Please try again or choose a different language.")

            except ValueError as val_err:
                st.error(str(val_err))
            except RequestException:
                st.error("Network error: unable to reach translation service. Please check your connection.")
            except Exception as exc:  # pragma: no cover - final fallback
                LOGGER.exception("Unexpected error: %s", exc)
                st.error("An unexpected error occurred. Please try again later.")


if __name__ == "__main__":
    main()
