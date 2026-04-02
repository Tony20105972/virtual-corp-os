from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"

    # LLM
    OPENAI_API_KEY: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_DB_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
