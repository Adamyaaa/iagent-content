import os
import logging
from groq import Groq
from ..services.settings_service import settings_service
from ..models.domain import Transcript, TranscriptSegment

logger = logging.getLogger(__name__)

class TranscriptionService:
    def get_client(self):
        key = settings_service.get_groq_key()
        return Groq(api_key=key) if key else None

    def _transcribe_with_gemini(self, audio_path: str) -> Transcript:
        gemini_key = settings_service.get_gemini_key()
        if not gemini_key:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-flash-latest")
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            mime = "audio/mp3" if audio_path.endswith(".mp3") else "audio/wav"
            res = model.generate_content([
                "Listen to this audio recording and produce an accurate transcript of what is spoken. Return ONLY the transcribed text.",
                {"mime_type": mime, "data": audio_bytes}
            ])
            text = res.text.strip()
            if text:
                logger.info("Successfully transcribed audio using Gemini Multimodal fallback.")
                return Transcript(
                    transcript=text,
                    language="en",
                    duration=0.0,
                    segments=[]
                )
        except Exception as e:
            logger.warning(f"Gemini multimodal audio transcription fallback failed: {e}")
        return None

    def transcribe_audio(self, audio_path: str) -> Transcript:
        client = self.get_client()
        """
        Sends the extracted audio to Groq Whisper or Gemini for transcription.
        Returns a structured Transcript object.
        """
        if client:
            logger.info(f"Transcribing audio via Groq Whisper: {audio_path}")
            try:
                with open(audio_path, "rb") as file:
                    response = client.audio.transcriptions.create(
                        file=(os.path.basename(audio_path), file.read()),
                        model="whisper-large-v3",
                        response_format="verbose_json"
                    )
                
                # Parse segments for detailed timing data
                segments = []
                response_segments = getattr(response, "segments", [])
                for seg in response_segments:
                    if isinstance(seg, dict):
                        start = seg.get('start', 0.0)
                        end = seg.get('end', 0.0)
                        text = seg.get('text', '')
                    else:
                        start = getattr(seg, 'start', 0.0)
                        end = getattr(seg, 'end', 0.0)
                        text = getattr(seg, 'text', '')
                        
                    segments.append(TranscriptSegment(
                        start=start,
                        end=end,
                        text=text
                    ))

                return Transcript(
                    transcript=getattr(response, "text", ""),
                    language=getattr(response, "language", "en"),
                    duration=getattr(response, "duration", 0.0),
                    segments=segments
                )
            except Exception as e:
                logger.warning(f"Groq Whisper transcription failed ({e}). Attempting Gemini fallback...")

        # Fallback to Gemini Multimodal Audio Transcription
        gemini_transcript = self._transcribe_with_gemini(audio_path)
        if gemini_transcript:
            return gemini_transcript

        logger.warning("Both Groq and Gemini audio transcription were unavailable. Returning fallback.")
        return Transcript(
            transcript="Audio transcription was unavailable. Please ensure Groq or Gemini API keys are configured.",
            language="en",
            duration=0.0,
            segments=[]
        )

transcription_service = TranscriptionService()
