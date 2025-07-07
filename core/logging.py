"""
Logging configuration for the fraud detection system.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fraud_detection.log', mode='a')
    ]
)

# Create logger instance
app_logger = logging.getLogger('fraud_detection')


class FraudLogger:
    """Specialized logger for fraud detection events."""
    
    @staticmethod
    def log_transaction(transaction_id: str, fraud_score: float, risk_level: str, risk_factors: list):
        """Log fraud detection result."""
        app_logger.info(
            f"FRAUD_DETECTION - Transaction: {transaction_id}, "
            f"Score: {fraud_score:.3f}, Risk: {risk_level}, "
            f"Factors: {', '.join(risk_factors[:3])}"
        )
    
    @staticmethod
    def log_alert(alert_type: str, account_number: str, severity: str, fraud_score: float):
        """Log fraud alert creation."""
        masked_account = f"****{account_number[-4:]}" if len(account_number) > 4 else account_number
        app_logger.warning(
            f"FRAUD_ALERT - Type: {alert_type}, Account: {masked_account}, "
            f"Severity: {severity}, Score: {fraud_score:.3f}"
        )
    
    @staticmethod
    def log_error(component: str, error: Exception, context: Dict[str, Any] = None):
        """Log system errors with context."""
        context_str = f", Context: {context}" if context else ""
        app_logger.error(f"ERROR - Component: {component}, Error: {str(error)}{context_str}")
    
    @staticmethod
    def log_performance(operation: str, duration_ms: float, details: Dict[str, Any] = None):
        """Log performance metrics."""
        details_str = f", Details: {details}" if details else ""
        app_logger.info(f"PERFORMANCE - Operation: {operation}, Duration: {duration_ms:.2f}ms{details_str}")


# Global fraud logger instance
fraud_logger = FraudLogger()