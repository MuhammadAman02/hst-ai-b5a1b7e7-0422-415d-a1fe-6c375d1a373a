"""
Health check utilities for the fraud detection system.
"""

import time
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import text

from core.database import engine
from app.config import settings


class HealthCheck:
    """Health check utilities for monitoring system status."""
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Check database connectivity and status."""
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            
            return {
                "status": "healthy",
                "message": "Database connection successful",
                "response_time_ms": 0
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "message": f"Database connection failed: {str(e)}",
                "response_time_ms": 0
            }
    
    @staticmethod
    def check_ml_models() -> Dict[str, Any]:
        """Check ML model status."""
        try:
            from services.fraud_detection import fraud_detector
            model_stats = fraud_detector.get_model_stats()
            
            return {
                "status": "healthy",
                "message": "ML models loaded and ready",
                "model_version": model_stats.get("model_version", "unknown"),
                "features_count": model_stats.get("features_count", 0)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"ML models not available: {str(e)}",
                "model_version": "unknown"
            }
    
    @staticmethod
    def check_all() -> Dict[str, Any]:
        """Perform comprehensive health check."""
        start_time = time.time()
        
        # Check individual components
        db_health = HealthCheck.check_database()
        ml_health = HealthCheck.check_ml_models()
        
        # Overall status
        overall_status = "healthy" if (
            db_health["status"] == "healthy" and 
            ml_health["status"] == "healthy"
        ) else "unhealthy"
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": response_time,
            "version": settings.app_version,
            "components": {
                "database": db_health,
                "ml_models": ml_health
            },
            "system_info": {
                "app_name": settings.app_name,
                "environment": "development" if settings.debug else "production",
                "fraud_threshold": settings.fraud_threshold,
                "high_risk_threshold": settings.high_risk_threshold
            }
        }