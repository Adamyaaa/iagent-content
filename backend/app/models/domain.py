from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class VideoMetadata(BaseModel):
    duration: float
    resolution: str
    frame_rate: float
    
class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str

class Transcript(BaseModel):
    transcript: str
    language: str
    duration: float
    segments: List[TranscriptSegment]

class SceneBreakdown(BaseModel):
    scene_number: int
    duration_seconds: float
    voiceover: str
    on_screen_text: str
    visual_description: str
    camera_direction: str
    b_roll_suggestion: str

class ContentConcept(BaseModel):
    title: str
    content_angle: str
    hook: str
    problem: str
    body: str
    insight: str
    cta: str
    target_audience: str
    platform: str
    estimated_duration: str
    scene_breakdown: List[SceneBreakdown]

class QAScore(BaseModel):
    approved: bool
    overall_score: int
    brand_alignment: int
    audience_relevance: int
    business_value: int
    hook_strength: int
    originality: int
    clarity: int
    cta_quality: int
    ai_accuracy: int
    issues: List[str]
    improvements: List[str]

class LinkedInIdeation(BaseModel):
    text_post: str = Field(description="A long-form professional text post using the viral hook")
    carousel_outline: List[str] = Field(description="A 5-slide outline for a PDF document post")

class InstagramIdeation(BaseModel):
    infographic_caption: str = Field(description="An emoji-rich caption with aggressive SEO hashtags")
    story_idea: str = Field(description="An interactive IG Story idea (e.g. poll or quiz)")

class WhatsAppIdeation(BaseModel):
    broadcast_message: str = Field(description="A short, punchy 2-sentence hook with *bolding* and emojis")
    community_poll: str = Field(description="A multiple-choice poll idea based on the core problem")

class GenerationResult(BaseModel):
    final_concept: Optional[ContentConcept] = None
    final_score: Optional[QAScore] = None
    linkedin: Optional[LinkedInIdeation] = None
    instagram: Optional[InstagramIdeation] = None
    whatsapp: Optional[WhatsAppIdeation] = None
    revisions_taken: int = 0
    history: List[Dict[str, Any]] = []
