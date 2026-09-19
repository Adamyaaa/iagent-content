import os
import json
from pydantic import BaseModel
from ..config import settings as env_settings

SETTINGS_FILE = os.path.join(os.getcwd(), 'data', 'settings.json')

class AppSettings(BaseModel):
    groq_api_key: str = ""
    gemini_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""

class SettingsService:
    def __init__(self):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        if not os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'w') as f:
                json.dump({}, f)

    def load_settings(self) -> AppSettings:
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
            
        return AppSettings(
            groq_api_key=data.get('groq_api_key', env_settings.groq_api_key),
            gemini_api_key=data.get('gemini_api_key', env_settings.gemini_api_key),
            supabase_url=data.get('supabase_url', env_settings.supabase_url),
            supabase_service_key=data.get('supabase_service_key', env_settings.supabase_service_key),
        )

    def save_settings(self, new_settings: AppSettings):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(new_settings.model_dump(), f)

    def get_groq_key(self):
        return self.load_settings().groq_api_key

    def get_gemini_key(self):
        return self.load_settings().gemini_api_key

    def get_supabase_credentials(self):
        s = self.load_settings()
        return s.supabase_url, s.supabase_service_key

settings_service = SettingsService()
