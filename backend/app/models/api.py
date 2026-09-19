from pydantic import BaseModel, HttpUrl
from typing import Optional

class IngestUrlRequest(BaseModel):
    url: HttpUrl
    priority: int = 0
    source: str = "manual"
    source_platform: str = "youtube"

class IngestUrlResponse(BaseModel):
    message: str
    queue_id: str
    status: str

class GenerateConceptRequest(BaseModel):
    queue_id: str

class GenerateConceptResponse(BaseModel):
    message: str
    concept_id: str
    status: str
