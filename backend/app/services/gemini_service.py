import google.generativeai as genai
import logging
import json
import os
from typing import List, Dict, Any
from ..services.settings_service import settings_service
from ..models.domain import Transcript

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.multimodal_model_name = 'gemini-1.5-pro'

    def _configure_genai(self):
        key = settings_service.get_gemini_key()
        if key:
            genai.configure(api_key=key)
            return True
        return False

    def analyze_content(self, frame_paths: List[str], transcript: Transcript, metadata: Dict[str, Any], platform: str = "youtube") -> Dict[str, Any]:
        """
        Takes 7 representative frames + transcript and reverse-engineers the video structure.
        """
        if not self._configure_genai():
            logger.warning("GEMINI_API_KEY is not set. Returning a mock analysis.")
            return {"hook": "mock", "narrative_structure": {}, "emotional_trigger": "mock"}

        logger.info("Uploading frames and analyzing content with Gemini Multimodal.")
        model = genai.GenerativeModel(self.multimodal_model_name)
        
        uploaded_frames = []
        try:
            for path in frame_paths:
                # Upload files to Gemini API
                img = genai.upload_file(path=path)
                uploaded_frames.append(img)
                
            prompt = f"""
            You are an expert AI Product Architect and Content Strategist.
            Reverse-engineer this video content.
            
            Video Metadata:
            - Source Platform: {platform}
            - Duration: {metadata.get('duration')}s
            
            Transcript:
            {transcript.transcript}
            
            Analyze the provided frames and transcript. Return the analysis as a STRICT JSON object with exactly these keys:
            {{
                "hook": "Describe the first 1-5 seconds, curiosity mechanism, problem introduced, etc.",
                "narrative_structure": {{
                    "context": "...",
                    "problem": "...",
                    "escalation": "...",
                    "insight": "...",
                    "payoff": "...",
                    "cta": "..."
                }},
                "emotional_trigger": "Curiosity, fear of missing out, surprise, humor, contrarian thinking, authority, aspirational, pain points, relatability, discovery",
                "pacing": {{
                    "information_density": "...",
                    "visual_changes": "..."
                }},
                "visual_storytelling": {{
                    "camera_style": "...",
                    "text_overlays": "..."
                }},
                "cta_analysis": {{
                    "action_requested": "...",
                    "explicit_or_implicit": "..."
                }}
            }}
            """
            
            # Request generation passing prompt + list of File objects
            response = model.generate_content([prompt] + uploaded_frames)
            
            text = response.text.strip()
            # Clean up markdown JSON wrapper if present
            if text.startswith('```json'):
                text = text[7:-3].strip()
            elif text.startswith('```'):
                text = text[3:-3].strip()
                
            return json.loads(text)
            
        except Exception as e:
            logger.error(f"Error during Gemini analysis: {e}")
            raise e
            
        finally:
            # Cleanup uploaded files from Google servers
            for img in uploaded_frames:
                try:
                    genai.delete_file(img.name)
                except Exception as e:
                    logger.warning(f"Failed to delete uploaded frame {img.name}: {e}")

    def extract_pattern(self, analysis: Dict[str, Any]) -> str:
        """
        Abstracts the underlying viral/retention pattern from the detailed analysis.
        This ensures we don't plagiarize original content during generation.
        """
        if not self._configure_genai():
            return "Mock pattern -> mock outcome -> mock CTA"

        logger.info("Extracting underlying content pattern.")
        model = genai.GenerativeModel(self.multimodal_model_name)
        
        prompt = f"""
        You are an expert Content Automation Systems Designer.
        Review this content analysis and extract the underlying psychological and structural pattern.
        DO NOT copy the source content. Provide ONLY the abstracted formula.
        
        Analysis:
        {json.dumps(analysis, indent=2)}
        
        Example output format:
        Problem -> quantify hidden cost -> reveal automation opportunity -> demonstrate solution -> show outcome -> CTA
        
        Return ONLY the extracted pattern string.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()

gemini_service = GeminiService()
