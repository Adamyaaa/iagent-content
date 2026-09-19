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
                return res.data[0]["value"]
        except Exception as e:
            logger.warning(f"Could not fetch {key} from DB: {e}")
        return default

    def _set_db_value(self, key: str, value: str):
        client = supabase_db.get_client()
        if not client or not value:
            return
        try:
            client.table("system_settings").upsert({"key": key, "value": value}).execute()
        except Exception as e:
            logger.warning(f"Could not save {key} to DB: {e}")

    def load_settings(self) -> AppSettings:
        return AppSettings(
            groq_api_key=self._get_db_value("groq_api_key", env_settings.groq_api_key),
            gemini_api_key=self._get_db_value("gemini_api_key", env_settings.gemini_api_key),
            supabase_url=env_settings.supabase_url,
            supabase_service_key=env_settings.supabase_service_key,
        )

    def save_settings(self, new_settings: AppSettings):
        self._set_db_value("groq_api_key", new_settings.groq_api_key)
        self._set_db_value("gemini_api_key", new_settings.gemini_api_key)
        # Supabase URL and Key are now strictly env variables, we don't save them in the DB.

    def get_groq_key(self):
        return self.load_settings().groq_api_key

    def get_gemini_key(self):
        return self.load_settings().gemini_api_key

settings_service = SettingsService()
