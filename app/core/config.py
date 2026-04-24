from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "EntomológicaValleSol"
    DEBUG: bool = False
    
    # Esto permite que si DATABASE_URL existe en el .env, sobrescriba al default
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/entovallesol_db"

    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Nota: Pydantic a veces tiene problemas parseando listas desde strings de .env
    # Si te da error en ALLOWED_ORIGINS, cámbialo a str y luego haz .split(",")
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"] 
    
    UPLOAD_DIR: str = "./storage/uploads"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Configuración para leer el archivo .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()