import json
import logging
from typing import Dict, Any, List
import google.generativeai as genai
from ..models.domain import ContentConcept, SceneBreakdown, QAScore, GenerationResult, LinkedInIdeation, InstagramIdeation, WhatsAppIdeation, PlatformIdeations
from .settings_service import settings_service
from .qa_service import qa_service

import os
logger = logging.getLogger(__name__)

class GenerationService:
    def __init__(self):
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

    def _configure_genai(self):
        key = settings_service.get_gemini_key()
        if key:
            genai.configure(api_key=key)
            return True
        return False

    def generate_concept(self, extracted_pattern: str, topic_context: str = "", feedback: str = "") -> ContentConcept:
        """
        Generates a completely new concept based on the pattern, tailored to iAgent Labs.
        """
        if not self._configure_genai():
            logger.warning("GEMINI_API_KEY not set. Returning a mock concept.")
            return ContentConcept(
                title="Mock Concept", content_angle="Mock Angle", hook="Mock Hook",
                problem="Mock Problem", body="Mock Body", insight="Mock Insight",
                cta="Mock CTA", target_audience="Founders", platform="LinkedIn",
                estimated_duration="30s", scene_breakdown=[
                    SceneBreakdown(
                        scene_number=1, duration_seconds=5.0, voiceover="Test",
                        on_screen_text="Test", visual_description="Test",
                        camera_direction="Test", b_roll_suggestion="Test"
                    )
                ]
            )

        logger.info("Generating new concept via Gemini.")
        model = genai.GenerativeModel(self.model_name)
        
        prompt = f"""
        You are the Lead Content Architect for 'iAgent Labs' (based in Hyderabad, India).
        We build AI agents, enterprise chatbots, and automation systems for Indian businesses.
        Our brand voice is Intelligent, Confident, Business-focused, Direct, and Practical.
        Do NOT use emojis anywhere in the concept, titles, or scripts - maintain an executive, human tone.
        
        Using the following viral content pattern, generate an ORIGINAL short-form video concept tailored to iAgent Labs.
        Do NOT copy the original content. Only use the abstract psychological structure.
        
        Extracted Pattern:
        {extracted_pattern}
        
        Additional Context/Topic:
        {topic_context}
        
        Previous Feedback to incorporate (if any, specifically fix these issues):
        {feedback}
        
        Generate the concept returning ONLY a JSON object that STRICTLY matches this schema:
        {{
            "title": "String",
            "content_angle": "String",
            "hook": "String",
            "problem": "String",
            "body": "String",
            "insight": "String",
            "cta": "String (e.g. 'Want to automate this workflow? Talk to us.')",
            "target_audience": "String (e.g. 'SME Owners')",
            "platform": "String (e.g. 'Instagram Reels')",
            "estimated_duration": "String",
            "scene_breakdown": [
                {{
                    "scene_number": 1,
                    "duration_seconds": 3.5,
                    "voiceover": "String",
                    "on_screen_text": "String",
                    "visual_description": "String",
                    "camera_direction": "String",
                    "b_roll_suggestion": "String"
                }}
            ]
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith('```json'): 
                text = text[7:-3].strip()
            elif text.startswith('```'): 
                text = text[3:-3].strip()
            data = json.loads(text)
            return ContentConcept(**data)
        except Exception as e:
            logger.error(f"Failed to generate Concept via Gemini ({e}). Returning fallback concept.")
            return ContentConcept(
                title="Automating Enterprise Workflows with AI Agents",
                content_angle="Operational efficiency for Indian businesses",
                hook="Still paying a team to do manual repetitive data entry?",
                problem="Manual processes take hours and lead to human errors.",
                body="We build autonomous AI agent systems that connect directly to your database and WhatsApp.",
                insight="Automation eliminates execution latency and cuts operational cost by 70%.",
                cta="Ready to deploy custom AI in your business? Talk to iAgent Labs.",
                target_audience="Founders and Operations Leaders",
                platform="LinkedIn",
                estimated_duration="45s",
                scene_breakdown=[
                    SceneBreakdown(
                        scene_number=1,
                        duration_seconds=5.0,
                        voiceover="Most companies lose 20+ hours a week on manual tasks.",
                        on_screen_text="Stop wasting manual hours",
                        visual_description="Split screen of stressed team vs automated dashboard",
                        camera_direction="Fast zoom in",
                        b_roll_suggestion="Office desk with messy spreadsheets"
                    )
                ]
            )

    def generate_platform_ideations(self, core_concept: ContentConcept, pattern: str) -> Dict[str, Any]:
        """
        Takes the core concept and expands it into platform-specific ideation panels (LinkedIn, Instagram, WhatsApp)
        in a single optimized LLM call to prevent rate limits and conserve quota.
        """
        if not self._configure_genai():
            return {}
            
        logger.info(f"Generating platform ideations for: {core_concept.title}")
        
        try:
            model = genai.GenerativeModel(self.model_name)
            prompt = f"""
            You are an expert multi-channel B2B content strategist for 'iAgent Labs' (Hyderabad, India).
            We build AI agents, chatbots, and automation systems for Indian businesses.
            Tone: Intelligent, Confident, Direct, Practical, and Executive.
            Strictly do NOT use emojis anywhere in the text or copy.

            Transform this approved video concept into tailored formats for LinkedIn, Instagram, and WhatsApp:
            - LinkedIn: 1) A long-form professional text post using the hook. 2) A 5-slide outline for a PDF carousel.
            - Instagram: 1) An infographic caption with clean whitespace, strong takeaways, and targeted SEO hashtags (no emojis). 2) An interactive IG Story idea (like a poll or quiz).
            - WhatsApp: 1) A punchy broadcast message (max 3 sentences) with *bolding* for readability, teasing a link (strictly no emojis). 2) A community poll idea with options that sparks debate.

            Core Concept Title: {core_concept.title}
            Core Concept Hook: {core_concept.hook}
            Core Concept Problem: {core_concept.problem}
            Core Concept Insight: {core_concept.insight}
            Abstract Viral Pattern: {pattern}

            Output strictly as a JSON object matching the PlatformIdeations schema.
            """
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=PlatformIdeations
                )
            )
            data = json.loads(response.text)
            return {
                "linkedin": data.get("linkedin", {}),
                "instagram": data.get("instagram", {}),
                "whatsapp": data.get("whatsapp", {})
            }
        except Exception as e:
            logger.error(f"Failed to generate platform ideations: {e}")
            return {}

    def generate_with_revisions(self, extracted_pattern: str, topic_context: str = "") -> Dict[str, Any]:
        """
        Generates a concept and runs it through the Brand QA critic.
        Revises up to 3 times if the overall score is below 80.
        """
        max_revisions = 3
        feedback = ""
        history = []
        
        for attempt in range(1, max_revisions + 1):
            logger.info(f"Generation Attempt {attempt} / {max_revisions}")
            
            # Generate script and scenes
            concept = self.generate_concept(extracted_pattern, topic_context, feedback)
            
            # QA Evaluation
            qa_score = qa_service.evaluate_concept(concept)
            
            history.append({
                "attempt": attempt,
                "concept": concept.model_dump(),
                "qa_score": qa_score.model_dump()
            })
            
            if qa_score.approved:
                logger.info(f"Concept approved on attempt {attempt} with score {qa_score.overall_score}")
                
                ideations = self.generate_platform_ideations(concept, extracted_pattern)
                
                return {
                    "approved": True,
                    "final_concept": concept,
                    "final_score": qa_score,
                    "history": history,
                    "ideations": ideations
                }
                
            logger.warning(f"Concept rejected with score {qa_score.overall_score}. Needs revision.")
            feedback = f"Issues: {', '.join(qa_score.issues)}. Improvements needed: {', '.join(qa_score.improvements)}."
            
        logger.error(f"Failed to generate an approved concept after {max_revisions} revisions.")
        ideations = self.generate_platform_ideations(concept, extracted_pattern)
        return {
            "approved": False,
            "final_concept": concept,
            "final_score": qa_score,
            "history": history,
            "ideations": ideations
        }

generation_service = GenerationService()
