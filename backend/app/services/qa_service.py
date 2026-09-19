import google.generativeai as genai
import logging
import json
from ..services.settings_service import settings_service
from ..models.domain import ContentConcept, QAScore

logger = logging.getLogger(__name__)

class QAService:
    def __init__(self):
        self.model_name = 'gemini-1.5-pro'

    def _configure_genai(self):
        key = settings_service.get_gemini_key()
        if key:
            genai.configure(api_key=key)
            return True
        return False

    def evaluate_concept(self, concept: ContentConcept) -> QAScore:
        """
        Acts as a harsh Brand QA Critic to evaluate the generated concept.
        """
        if not self._configure_genai():
            logger.warning("GEMINI_API_KEY not set. Returning a mock QA Score.")
            return QAScore(
                approved=True,
                overall_score=85,
                brand_alignment=85,
                audience_relevance=85,
                business_value=85,
                hook_strength=85,
                originality=85,
                clarity=85,
                cta_quality=85,
                ai_accuracy=85,
                issues=[],
                improvements=[]
            )

        logger.info(f"Evaluating concept: '{concept.title}'")
        model = genai.GenerativeModel(self.model_name)
        
        prompt = f"""
        You are the Chief Brand Critic for iAgent Labs (Hyderabad, India).
        Evaluate the following content concept based on our strict brand guidelines.
        
        Brand Guidelines:
        - We build AI systems and agents, we don't just advise. Focus on execution and ROI.
        - Audience: Indian business owners, CXOs, founders.
        - Tone: Intelligent, confident, direct, practical, slightly provocative.
        - No generic AI buzzwords (e.g., "AI will change everything", "Unlock the power").
        - CTA should be natural ("Want to automate this? Talk to us."), not forced.
        
        Concept to evaluate:
        {concept.model_dump_json(indent=2)}
        
        Return your evaluation as a STRICT JSON object matching this exact schema:
        {{
            "overall_score": 0,
            "brand_alignment": 0,
            "audience_relevance": 0,
            "business_value": 0,
            "hook_strength": 0,
            "originality": 0,
            "clarity": 0,
            "cta_quality": 0,
            "ai_accuracy": 0,
            "issues": ["list", "of", "specific", "flaws"],
            "improvements": ["list", "of", "actionable", "improvements"]
        }}
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith('```json'): 
            text = text[7:-3].strip()
        elif text.startswith('```'): 
            text = text[3:-3].strip()
        
        try:
            data = json.loads(text)
            data["approved"] = data.get("overall_score", 0) >= 80
            return QAScore(**data)
        except Exception as e:
            logger.error(f"Failed to parse QA response: {e}")
            raise e

qa_service = QAService()
