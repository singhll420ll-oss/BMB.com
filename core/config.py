# core/config.py
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator, PostgresDsn
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Bite Me Buddy"
    DEBUG: bool = False
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*.onrender.com"]
    
    # Database - YEH IMPORTANT CHANGE HAI
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/bite_me_buddy"
    
    @validator("DATABASE_URL", pre=True)
    def fix_database_url(cls, v):
        """Convert Render's postgresql:// to postgresql+asyncpg://"""
        if v and v.startswith("postgresql://"):
            # Render se aata hai: postgresql://user:pass@host/db
            # Convert karein: postgresql+asyncpg://user:pass@host/db
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Twilio
    TWILIO_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # File Uploads
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif"]
    UPLOAD_DIR: str = "static/uploads"
    
    # OTP
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    
    # Session
    SESSION_TIMEOUT_MINUTES: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()