import uuid
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..models.api import IngestUrlRequest, IngestUrlResponse
from ..services.ingestion_service import ingestion_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/ingest",
    tags=["Ingestion"]
)

def run_ingestion_pipeline(url: str, queue_id: str):
    try:
        # Runs synchronously in the background task
        # In a real production setup, we might use Celery or Temporal.
        # BackgroundTasks is fine for this phase.
        ingestion_service.process_url(url, queue_id)
    except Exception as e:
        logger.error(f"Background task failed for queue_id {queue_id}: {str(e)}")

@router.post("/", response_model=IngestUrlResponse)
async def ingest_url(request: IngestUrlRequest, background_tasks: BackgroundTasks):
    """
    Accepts a URL (Instagram, TikTok, YouTube, etc.) and starts the ingestion pipeline.
    """
    queue_id = str(uuid.uuid4())
    
    # Trigger background processing
    background_tasks.add_task(
        run_ingestion_pipeline, 
        url=str(request.url), 
        queue_id=queue_id
    )
    
    return IngestUrlResponse(
        message="Ingestion pipeline started.",
        queue_id=queue_id,
        status="pending"
    )
