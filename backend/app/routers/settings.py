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
    current = settings_service.load_settings()
    
    if new_settings.groq_api_key and "*" not in new_settings.groq_api_key:
        current.groq_api_key = new_settings.groq_api_key.strip()
    if new_settings.gemini_api_key and "*" not in new_settings.gemini_api_key:
        current.gemini_api_key = new_settings.gemini_api_key.strip()
    if new_settings.supabase_url:
        current.supabase_url = new_settings.supabase_url.strip()
    if new_settings.supabase_service_key and "*" not in new_settings.supabase_service_key:
        current.supabase_service_key = new_settings.supabase_service_key.strip()
        
    settings_service.save_settings(current)
    return {"status": "success", "message": "Settings updated"}

@router.post("/test/{provider}")
async def test_provider(provider: str):
    from fastapi import HTTPException
    
    if provider == "groq_api_key":
        from groq import Groq
        key = settings_service.get_groq_key()
        if not key:
            raise HTTPException(status_code=400, detail="Key not set")
        try:
            client = Groq(api_key=key)
            client.models.list()
            return {"status": "success", "message": "Groq connection successful"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Groq test failed: {str(e)}")
            
    elif provider == "gemini_api_key":
        import google.generativeai as genai
        key = settings_service.get_gemini_key()
        if not key:
            raise HTTPException(status_code=400, detail="Key not set")
        try:
            genai.configure(api_key=key)
            list(genai.list_models())
            return {"status": "success", "message": "Gemini connection successful"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Gemini test failed: {str(e)}")
            
    raise HTTPException(status_code=400, detail="Unknown provider")
