from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    groq_api_key: str = ""
    gemini_api_key: str = ""
    elevenlabs_api_key: str = ""
    
    supabase_url: str = ""
    supabase_service_key: str = ""
    
    telegram_bot_token: str = ""
    gemini_model: str = "gemini-flash-lite-latest"
    
    environment: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
