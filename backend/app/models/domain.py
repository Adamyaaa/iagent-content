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
