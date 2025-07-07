"""
Configuration management for the fraud detection system.
"""

import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with Pakistani banking context."""
    
    # Application
    app_name: str = "Pakistani Bank Fraud Detection System"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./fraud_detection.db"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Fraud Detection
    fraud_threshold: float = 0.7
    high_risk_threshold: float = 0.8
    alert_email: str = "security@bank.com.pk"
    
    # Pakistani Banking Context
    currency: str = "PKR"
    timezone: str = "Asia/Karachi"
    business_hours_start: int = 9
    business_hours_end: int = 17
    
    # ML Model
    model_retrain_interval: int = 24
    feature_importance_threshold: float = 0.1
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()