"""
Health check utilities for the Pakistani Bank Fraud Detection System.
Provides comprehensive system health monitoring.
"""

import time
import psutil
import platform
from typing import Dict, Any
from app.config import settings
from app.core.logging import get_logger

logger = get_logger("health")


class HealthCheck:
    """System health check utilities."""
    
    @staticmethod
    def check_system_resources() -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            return {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory_percent,
                "memory_available_gb": round(memory_available_gb, 2),
                "disk_usage_percent": disk_percent,
                "disk_free_gb": round(disk_free_gb, 2),
                "status": "healthy" if cpu_percent < 80 and memory_percent < 80 and disk_percent < 90 else "warning"
            }
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    def check_application_config() -> Dict[str, Any]:
        """Check application configuration."""
        try:
            config_status = {
                "app_name": settings.app_name,
                "app_version": settings.app_version,
                "environment": settings.environment,
                "debug_mode": settings.debug,
                "fraud_threshold": settings.fraud_threshold,
                "max_transaction_amount": settings.max_transaction_amount,
                "status": "healthy"
            }
            
            # Validate critical settings
            if settings.is_production and settings.secret_key == "your-secret-key-change-in-production":
                config_status["status"] = "warning"
                config_status["warning"] = "Default secret key in production"
            
            return config_status
        except Exception as e:
            logger.error(f"Error checking application config: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    def check_dependencies() -> Dict[str, Any]:
        """Check if all required dependencies are available."""
        required_packages = [
            'nicegui',
            'uvicorn',
            'pydantic',
            'httpx',
            'python_dotenv'
        ]
        
        dependency_status = {
            "required_packages": required_packages,
            "available_packages": [],
            "missing_packages": [],
            "status": "healthy"
        }
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                dependency_status["available_packages"].append(package)
            except ImportError:
                dependency_status["missing_packages"].append(package)
        
        if dependency_status["missing_packages"]:
            dependency_status["status"] = "error"
            dependency_status["error"] = f"Missing packages: {', '.join(dependency_status['missing_packages'])}"
        
        return dependency_status
    
    @staticmethod
    def check_platform_info() -> Dict[str, Any]:
        """Get platform and Python version information."""
        try:
            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor() or "Unknown",
                "hostname": platform.node(),
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"Error getting platform info: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    def check_all() -> Dict[str, Any]:
        """Perform comprehensive health check."""
        timestamp = time.time()
        
        health_report = {
            "timestamp": timestamp,
            "status": "healthy",
            "checks": {
                "system_resources": HealthCheck.check_system_resources(),
                "application_config": HealthCheck.check_application_config(),
                "dependencies": HealthCheck.check_dependencies(),
                "platform_info": HealthCheck.check_platform_info()
            }
        }
        
        # Determine overall status
        check_statuses = [check["status"] for check in health_report["checks"].values()]
        
        if "error" in check_statuses:
            health_report["status"] = "error"
        elif "warning" in check_statuses:
            health_report["status"] = "warning"
        else:
            health_report["status"] = "healthy"
        
        # Log health check result
        logger.info(f"Health check completed with status: {health_report['status']}")
        
        return health_report


# Perform initial health check on import
if __name__ == "__main__":
    import json
    health_result = HealthCheck.check_all()
    print(json.dumps(health_result, indent=2))