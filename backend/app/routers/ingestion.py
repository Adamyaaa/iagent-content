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
    try:
        import shutil
        import traceback
        
        queue_id = str(uuid.uuid4())
        temp_dir = os.path.join(os.getcwd(), 'app', 'temp', queue_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Guard against None filename
        filename = file.filename or "uploaded_video.mp4"
        video_path = os.path.join(temp_dir, filename)
        
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        if supabase_db.get_client():
            supabase_db.get_client().table("trend_queue").insert({
                "id": queue_id,
                "source_url": f"Local Upload: {filename}",
                "status": "queued"
            }).execute()

        background_tasks.add_task(
            run_upload_pipeline,
            queue_id=queue_id,
            video_path=video_path,
            filename=filename,
            platform=source_platform
        )
        return {"queue_id": queue_id, "status": "pending"}
    except Exception as e:
        import traceback
        error_msg = f"{str(e)} - {traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
