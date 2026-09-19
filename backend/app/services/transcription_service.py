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

    def transcribe_audio(self, audio_path: str) -> Transcript:
        client = self.get_client()
        """
        Sends the extracted .wav file to Groq Whisper for fast transcription.
        Returns a structured Transcript object.
        """
        if not client:
            logger.warning("GROQ_API_KEY is not set. Returning a mock transcript.")
            return Transcript(
                transcript="This is a mock transcript.",
                language="en",
                duration=0.0,
                segments=[]
            )

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
            logger.error(f"Groq Whisper transcription failed: {e}. Falling back to default transcript.")
            return Transcript(
                transcript="Audio transcription was temporarily unavailable. Please verify your Groq API key in settings.",
                language="en",
                duration=0.0,
                segments=[]
            )

transcription_service = TranscriptionService()
