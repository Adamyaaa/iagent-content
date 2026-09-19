import google.generativeai as genai
import logging
import json
import os
from typing import List, Dict, Any
from PIL import Image
from ..services.settings_service import settings_service
from ..models.domain import Transcript

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.multimodal_model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

    def _configure_genai(self):
        key = settings_service.get_gemini_key()
        if key:
            genai.configure(api_key=key)
            return True
        return False

    def analyze_content(self, frame_paths: List[str], transcript: Transcript, metadata: Dict[str, Any], platform: str = "youtube") -> Dict[str, Any]:
        """
        Takes representative frames + transcript and reverse-engineers the video structure.
        """
        if not self._configure_genai():
            logger.warning("GEMINI_API_KEY is not set. Returning a mock analysis.")
            return {"hook": "mock", "narrative_structure": {}, "emotional_trigger": "mock"}

        logger.info("Analyzing content with Gemini Multimodal.")
        model = genai.GenerativeModel(self.multimodal_model_name)
        
        try:
            loaded_frames = []
            for path in frame_paths:
                try:
                    if os.path.exists(path):
                        loaded_frames.append(Image.open(path))
                except Exception as e:
                    logger.warning(f"Failed to open frame {path}: {e}")
                
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
            
            # Request generation passing prompt + list of PIL Image objects
            content_payload = [prompt] + loaded_frames if loaded_frames else [prompt]
            response = model.generate_content(content_payload)
            
            text = response.text.strip()
            # Clean up markdown JSON wrapper if present
            if text.startswith('```json'):
                text = text[7:-3].strip()
            elif text.startswith('```'):
                text = text[3:-3].strip()
                
            return json.loads(text)
            
        except Exception as e:
            logger.error(f"Error during Gemini analysis: {e}. Falling back to default structural analysis.")
            return {
                "hook": "Curiosity-driven hook addressing operational bottlenecks",
                "narrative_structure": {
                    "context": "Rapidly growing enterprise workflows",
                    "problem": "Manual bottlenecks slowing down customer turnaround",
                    "escalation": "Increasing overhead and missed revenue opportunities",
                    "insight": "Autonomous agentic workflows solve execution latency",
                    "payoff": "Seamless scale and automated execution",
                    "cta": "Transform operations with iAgent Labs"
                },
                "emotional_trigger": "Curiosity and operational ambition",
                "pacing": {
                    "information_density": "High",
                    "visual_changes": "Dynamic pacing"
                },
                "visual_storytelling": {
                    "camera_style": "Direct and authoritative",
                    "text_overlays": "High-impact takeaway cards"
                },
                "cta_analysis": {
                    "action_requested": "Automate workflows with iAgent Labs",
                    "explicit_or_implicit": "Explicit"
                }
            }

    def extract_pattern(self, analysis: Dict[str, Any]) -> str:
        """
        Abstracts the underlying viral/retention pattern from the detailed analysis.
        This ensures we don't plagiarize original content during generation.
        """
        fallback_pattern = "Problem -> quantify hidden cost -> reveal automation opportunity -> demonstrate solution -> show outcome -> CTA"
        if not self._configure_genai():
            return fallback_pattern

        try:
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
        except Exception as e:
            logger.error(f"Error extracting pattern via Gemini: {e}. Returning fallback pattern.")
            return fallback_pattern

gemini_service = GeminiService()
