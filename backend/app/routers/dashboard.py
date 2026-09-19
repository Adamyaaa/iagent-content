from fastapi import APIRouter, HTTPException
from ..database.supabase_client import supabase_db

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)

@router.get("/stats")
async def get_stats():
    client = supabase_db.get_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Simple stats
        queue_count = client.table("trend_queue").select("id", count="exact").execute().count
        concept_count = client.table("content_concepts").select("id", count="exact").execute().count
        approved_count = client.table("content_concepts").select("id", count="exact").eq("approval_status", True).execute().count
        
        return {
            "total_urls_processed": queue_count,
            "concepts_generated": concept_count,
            "approved_concepts": approved_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queue")
async def get_queue():
    client = supabase_db.get_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not configured")
        
    try:
        res = client.table("trend_queue").select("*").order("created_at", desc=True).limit(20).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/queue/{queue_id}")
async def delete_queue_item(queue_id: str):
    client = supabase_db.get_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not configured")
        
    try:
        res = client.table("trend_queue").delete().eq("id", queue_id).execute()
        return {"status": "success", "message": "Item deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/concepts")
async def get_concepts():
    client = supabase_db.get_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not configured")
        
    try:
        # Fetch concepts joined with queue data (for original url/pattern context if needed)
        res = client.table("content_concepts").select("*").order("created_at", desc=True).limit(20).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/concepts/{concept_id}")
async def delete_concept(concept_id: str):
    client = supabase_db.get_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not configured")
        
    try:
        res = client.table("content_concepts").delete().eq("id", concept_id).execute()
        return {"status": "success", "message": "Concept deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
