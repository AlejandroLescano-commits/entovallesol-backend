from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import field_validator  # <--- IMPORTA ESTO

class Settings(BaseSettings):
    APP_NAME: str = "EntomológicaValleSol"
    DEBUG: bool = False
    
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/entovallesol_db"

    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Solo el string, sin validadores complicados
    ALLOWED_ORIGINS: str = "http://localhost:5173" 
    
    UPLOAD_DIR: str = "./storage/uploads"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
