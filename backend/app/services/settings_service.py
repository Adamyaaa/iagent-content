import logging
from pydantic import BaseModel
from ..config import settings as env_settings
from ..database.supabase_client import supabase_db

logger = logging.getLogger(__name__)

class AppSettings(BaseModel):
    groq_api_key: str = ""
    gemini_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""

class SettingsService:
    def _get_db_value(self, key: str, default: str) -> str:
        client = supabase_db.get_client()
        if not client:
            return default
        try:
            res = client.table("system_settings").select("value").eq("key", key).execute()
            if res.data and len(res.data) > 0:
                val = res.data[0]["value"]
                # Reject masked values like gsk_******
                if val and "*" not in val:
                    return val
        except Exception as e:
            logger.warning(f"Could not fetch {key} from DB: {e}")
        return default

    def _set_db_value(self, key: str, value: str):
        client = supabase_db.get_client()
        if not client or not value or "*" in value:
            return
        try:
            client.table("system_settings").upsert({"key": key, "value": value}).execute()
        except Exception as e:
            logger.warning(f"Could not save {key} to DB: {e}")

    def load_settings(self) -> AppSettings:
        groq_val = self._get_db_value("groq_api_key", env_settings.groq_api_key)
        gemini_val = self._get_db_value("gemini_api_key", env_settings.gemini_api_key)
        return AppSettings(
            groq_api_key=groq_val if groq_val and "*" not in groq_val else "",
            gemini_api_key=gemini_val if gemini_val and "*" not in gemini_val else "",
            supabase_url=env_settings.supabase_url,
            supabase_service_key=env_settings.supabase_service_key,
        )

    def save_settings(self, new_settings: AppSettings):
        if new_settings.groq_api_key and "*" not in new_settings.groq_api_key:
            self._set_db_value("groq_api_key", new_settings.groq_api_key)
        if new_settings.gemini_api_key and "*" not in new_settings.gemini_api_key:
            self._set_db_value("gemini_api_key", new_settings.gemini_api_key)

    def get_groq_key(self):
        val = self.load_settings().groq_api_key
        if val and "*" not in val:
            return val.strip()
        if env_settings.groq_api_key and "*" not in env_settings.groq_api_key:
            return env_settings.groq_api_key.strip()
        return None

    def get_gemini_key(self):
        val = self.load_settings().gemini_api_key
        if val and "*" not in val:
            return val.strip()
        if env_settings.gemini_api_key and "*" not in env_settings.gemini_api_key:
            return env_settings.gemini_api_key.strip()
        return None

settings_service = SettingsService()
