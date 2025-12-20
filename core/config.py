"""
Configuration settings for Bite Me Buddy
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator, PostgresDsn
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Bite Me Buddy"
    DEBUG: bool = False
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Database
    DATABASE_URL: PostgresDsn = "postgresql+asyncpg://user:password@localhost/bite_me_buddy"
    
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
