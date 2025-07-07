"""
Configuration management for Pakistani Bank Fraud Detection System.
Simple, dependency-free configuration using environment variables.
"""

import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Server Configuration
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.reload: bool = os.getenv("RELOAD", "false").lower() == "true"
        
        # Application Configuration
        self.app_name: str = os.getenv("APP_NAME", "Pakistani Bank Fraud Detection System")
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        
        # Security Configuration
        self.secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.cors_origins: list = self._parse_cors_origins()
        
        # Database Configuration (if needed)
        self.database_url: Optional[str] = os.getenv("DATABASE_URL")
        
        # Fraud Detection Configuration
        self.fraud_threshold: float = float(os.getenv("FRAUD_THRESHOLD", "0.7"))
        self.max_transaction_amount: float = float(os.getenv("MAX_TRANSACTION_AMOUNT", "1000000.0"))
        
        # Logging Configuration
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_format: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    def _parse_cors_origins(self) -> list:
        """Parse CORS origins from environment variable."""
        origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def get_database_config(self) -> dict:
        """Get database configuration dictionary."""
        return {
            "url": self.database_url,
            "echo": self.debug and not self.is_production,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
    
    def get_uvicorn_config(self) -> dict:
        """Get uvicorn server configuration."""
        return {
            "host": self.host,
            "port": self.port,
            "reload": self.reload and self.is_development,
            "log_level": self.log_level.lower(),
            "access_log": self.debug,
        }
    
    def validate_config(self) -> bool:
        """Validate critical configuration values."""
        errors = []
        
        # Validate port range
        if not (1 <= self.port <= 65535):
            errors.append(f"Invalid port: {self.port}. Must be between 1 and 65535.")
        
        # Validate fraud threshold
        if not (0.0 <= self.fraud_threshold <= 1.0):
            errors.append(f"Invalid fraud threshold: {self.fraud_threshold}. Must be between 0.0 and 1.0.")
        
        # Validate secret key in production
        if self.is_production and self.secret_key == "your-secret-key-change-in-production":
            errors.append("SECRET_KEY must be changed in production environment.")
        
        if errors:
            print("❌ Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("✅ Configuration validation passed")
        return True
    
    def display_config(self) -> None:
        """Display current configuration (excluding sensitive data)."""
        print(f"🚀 {self.app_name} v{self.app_version}")
        print(f"📍 Environment: {self.environment}")
        print(f"🌐 Server: {self.host}:{self.port}")
        print(f"🔍 Debug Mode: {self.debug}")
        print(f"🎯 Fraud Threshold: {self.fraud_threshold}")
        print(f"💰 Max Transaction: PKR {self.max_transaction_amount:,.2f}")
        if self.database_url:
            # Mask sensitive parts of database URL
            masked_url = self.database_url.split('@')[-1] if '@' in self.database_url else "configured"
            print(f"🗄️  Database: {masked_url}")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


# Validate configuration on import
if __name__ == "__main__":
    settings.display_config()
    settings.validate_config()