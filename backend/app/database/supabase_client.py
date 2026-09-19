from supabase import create_client, Client
import logging
from ..services.settings_service import settings_service

logger = logging.getLogger(__name__)

class SupabaseManager:
    def get_client(self) -> Client | None:
        url, key = settings_service.get_supabase_credentials()
        if url and key:
            try:
                return create_client(url, key)
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                return None
        return None

supabase_db = SupabaseManager()
