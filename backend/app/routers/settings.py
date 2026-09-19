from fastapi import APIRouter
from ..services.settings_service import settings_service, AppSettings

router = APIRouter(
    prefix="/api/v1/settings",
    tags=["Settings"]
)

@router.get("/")
async def get_settings():
    # Load settings but mask the sensitive parts for the UI
    s = settings_service.load_settings()
    
    def mask(val):
        if not val: return ""
        if len(val) <= 8: return "********"
        return val[:4] + "*" * (len(val)-8) + val[-4:]
        
    return {
        "groq_api_key": mask(s.groq_api_key) if s.groq_api_key else "",
        "gemini_api_key": mask(s.gemini_api_key) if s.gemini_api_key else "",
        "supabase_url": s.supabase_url, # URL is usually not sensitive
        "supabase_service_key": mask(s.supabase_service_key) if s.supabase_service_key else "",
    }

@router.post("/")
async def update_settings(new_settings: AppSettings):
    # Only update fields that are provided and not masked
    current = settings_service.load_settings()
    
    if new_settings.groq_api_key and not new_settings.groq_api_key.endswith("***"):
        current.groq_api_key = new_settings.groq_api_key
    if new_settings.gemini_api_key and not new_settings.gemini_api_key.endswith("***"):
        current.gemini_api_key = new_settings.gemini_api_key
    if new_settings.supabase_url:
        current.supabase_url = new_settings.supabase_url
    if new_settings.supabase_service_key and not new_settings.supabase_service_key.endswith("***"):
        current.supabase_service_key = new_settings.supabase_service_key
        
    settings_service.save_settings(current)
    return {"status": "success", "message": "Settings updated"}
