from supabase import create_client, Client
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class SupabaseManager:
    def get_client(self) -> Client | None:
        url = settings.supabase_url
        key = settings.supabase_service_key
        if url and key:
            try:
                return create_client(url, key)
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                return None
        return None

supabase_db = SupabaseManager()
