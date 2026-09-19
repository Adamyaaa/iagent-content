import os
import uuid
import logging
import shutil
import traceback
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from ..models.api import IngestUrlRequest, IngestUrlResponse
from ..services.ingestion_service import ingestion_service
from ..database.supabase_client import supabase_db
from ..services.media_service import media_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/ingest",
    tags=["Ingestion"]
)

# Anchor temp dir to backend/app/temp regardless of current working directory
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_ROOT = os.path.join(APP_DIR, 'temp')

def download_and_process_url(url: str, queue_id: str, platform: str):
    try:
        temp_dir = os.path.join(TEMP_ROOT, queue_id)
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"Downloading URL {url} for queue_id {queue_id}")
        
        # The 3-Layer Waterfall Downloader
        video_path = media_service.download_social_video(url, temp_dir)
        
        # Trigger the unified processing pipeline
        ingestion_service.process_video_pipeline(queue_id, video_path, "url_download.mp4", platform)
    except Exception as e:
        logger.error(f"Background task failed for queue_id {queue_id}: {str(e)}")
        client = supabase_db.get_client()
        if client:
            try:
                error_msg = f"FAILED: ERROR: {str(e)}"[:200]
                client.table("trend_queue").update({"status": "rejected", "source_url": error_msg}).eq("id", queue_id).execute()
            except Exception:
                pass

def run_upload_pipeline(queue_id: str, video_path: str, filename: str, platform: str):
    try:
        ingestion_service.process_video_pipeline(queue_id, video_path, filename, platform)
    except Exception as e:
        logger.error(f"Background task failed for queue_id {queue_id}: {str(e)}")

@router.post("/", response_model=IngestUrlResponse)
async def ingest_url(request: IngestUrlRequest, background_tasks: BackgroundTasks):
    queue_id = str(uuid.uuid4())
    
    client = supabase_db.get_client()
    if client:
        try:
            client.table("trend_queue").insert({
                "id": queue_id,
                "source_url": str(request.url),
                "source_platform": request.source_platform,
                "status": "pending"
            }).execute()
        except Exception as e:
            logger.warning(f"Could not insert initial queue item into Supabase: {e}")

    background_tasks.add_task(download_and_process_url, url=str(request.url), queue_id=queue_id, platform=request.source_platform)
    return IngestUrlResponse(message="Ingestion pipeline started.", queue_id=queue_id, status="pending")

@router.post("/upload")
async def ingest_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_platform: str = Form("youtube")
):
    try:
        queue_id = str(uuid.uuid4())
        temp_dir = os.path.join(TEMP_ROOT, queue_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Guard against None filename and sanitize
        raw_name = file.filename or "uploaded_video.mp4"
        filename = os.path.basename(raw_name)
        video_path = os.path.join(temp_dir, filename)
        
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        client = supabase_db.get_client()
        if client:
            try:
                client.table("trend_queue").insert({
                    "id": queue_id,
                    "source_url": f"Local Upload: {filename}",
                    "source_platform": source_platform,
                    "status": "pending"
                }).execute()
            except Exception as e:
                logger.warning(f"Could not insert initial upload into Supabase: {e}")

        background_tasks.add_task(
            run_upload_pipeline,
            queue_id=queue_id,
            video_path=video_path,
            filename=filename,
            platform=source_platform
        )
        return {"queue_id": queue_id, "status": "pending"}
    except Exception as e:
        error_msg = f"{str(e)} - {traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
