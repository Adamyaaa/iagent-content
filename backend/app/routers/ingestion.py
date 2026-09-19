import os
import uuid
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from ..models.api import IngestUrlRequest, IngestUrlResponse
from ..services.ingestion_service import ingestion_service
from ..database.supabase_client import supabase_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/ingest",
    tags=["Ingestion"]
)

def run_ingestion_pipeline(url: str, queue_id: str, platform: str):
    try:
        ingestion_service.process_url(url, queue_id, platform)
    except Exception as e:
        logger.error(f"Background task failed for queue_id {queue_id}: {str(e)}")

def run_upload_pipeline(queue_id: str, video_path: str, filename: str, platform: str):
    try:
        ingestion_service.process_local_file(queue_id, video_path, filename, platform)
    except Exception as e:
        logger.error(f"Background task failed for queue_id {queue_id}: {str(e)}")

@router.post("/", response_model=IngestUrlResponse)
async def ingest_url(request: IngestUrlRequest, background_tasks: BackgroundTasks):
    queue_id = str(uuid.uuid4())
    background_tasks.add_task(run_ingestion_pipeline, url=str(request.url), queue_id=queue_id, platform=request.source_platform)
    return IngestUrlResponse(message="Ingestion pipeline started.", queue_id=queue_id, status="pending")

@router.post("/upload")
async def ingest_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_platform: str = Form("youtube")
):
    import shutil
    
    queue_id = str(uuid.uuid4())
    temp_dir = os.path.join(os.getcwd(), 'app', 'temp', queue_id)
    os.makedirs(temp_dir, exist_ok=True)
    video_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
        
    if supabase_db.client:
        supabase_db.client.table("trend_queue").insert({
            "id": queue_id,
            "source_url": f"Local Upload: {file.filename}",
            "status": "queued"
        }).execute()

    background_tasks.add_task(
        run_upload_pipeline,
        queue_id=queue_id,
        video_path=video_path,
        filename=file.filename,
        platform=source_platform
    )
    return {"queue_id": queue_id, "status": "pending"}
