"""
Alert management service for fraud detection.
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json

from models.schemas import FraudAlert, Transaction, RiskLevel
from core.database import FraudAlertDB, get_db
from core.utils import serialize_risk_factors, parse_risk_factors


class AlertService:
    """Service for managing fraud alerts and notifications."""
    
    def __init__(self):
        self.db_session = None
    
    def get_db_session(self) -> Session:
        """Get database session."""
        if not self.db_session:
            self.db_session = next(get_db())
        return self.db_session
    
    def create_alert(self, transaction: Transaction, fraud_score: float, risk_factors: List[str]) -> FraudAlert:
        """Create a new fraud alert."""
        db = self.get_db_session()
        
        try:
            # Determine alert type and message
            alert_type = self._determine_alert_type(fraud_score)
            message = self._generate_alert_message(transaction, fraud_score, risk_factors)
            severity = self._determine_severity(fraud_score)
            
            # Create alert
            alert = FraudAlert(
                transaction_id=transaction.transaction_id,
                account_number=transaction.account_number,
                alert_type=alert_type,
                severity=severity,
                message=message,
                fraud_score=fraud_score,
                risk_factors=risk_factors,
                timestamp=datetime.utcnow(),
                is_resolved=False
            )
            
            # Save to database
            db_alert = FraudAlertDB(
                transaction_id=alert.transaction_id,
                account_number=alert.account_number,
                alert_type=alert.alert_type,
                severity=alert.severity.value,
                message=alert.message,
                fraud_score=alert.fraud_score,
                risk_factors=serialize_risk_factors(alert.risk_factors),
                timestamp=alert.timestamp,
                is_resolved=alert.is_resolved
            )
            
            db.add(db_alert)
            db.commit()
            db.refresh(db_alert)
            
            alert.id = db_alert.id
            return alert
            
        except Exception as e:
            db.rollback()
            raise e
    
    def get_active_alerts(self, limit: int = 50) -> List[FraudAlert]:
        """Get active (unresolved) fraud alerts."""
        db = self.get_db_session()
        
        db_alerts = db.query(FraudAlertDB).filter(
            FraudAlertDB.is_resolved == False
        ).order_by(desc(FraudAlertDB.timestamp)).limit(limit).all()
        
        alerts = []
        for db_alert in db_alerts:
            alert = FraudAlert(
                id=db_alert.id,
                transaction_id=db_alert.transaction_id,
                account_number=db_alert.account_number,
                alert_type=db_alert.alert_type,
                severity=db_alert.severity,
                message=db_alert.message,
                fraud_score=db_alert.fraud_score,
                risk_factors=parse_risk_factors(db_alert.risk_factors),
                timestamp=db_alert.timestamp,
                is_resolved=db_alert.is_resolved,
                resolved_by=db_alert.resolved_by,
                resolution_notes=db_alert.resolution_notes
            )
            alerts.append(alert)
        
        return alerts
    
    def get_alerts_by_severity(self, severity: RiskLevel, limit: int = 50) -> List[FraudAlert]:
        """Get alerts by severity level."""
        db = self.get_db_session()
        
        db_alerts = db.query(FraudAlertDB).filter(
            FraudAlertDB.severity == severity.value,
            FraudAlertDB.is_resolved == False
        ).order_by(desc(FraudAlertDB.timestamp)).limit(limit).all()
        
        alerts = []
        for db_alert in db_alerts:
            alert = FraudAlert(
                id=db_alert.id,
                transaction_id=db_alert.transaction_id,
                account_number=db_alert.account_number,
                alert_type=db_alert.alert_type,
                severity=db_alert.severity,
                message=db_alert.message,
                fraud_score=db_alert.fraud_score,
                risk_factors=parse_risk_factors(db_alert.risk_factors),
                timestamp=db_alert.timestamp,
                is_resolved=db_alert.is_resolved,
                resolved_by=db_alert.resolved_by,
                resolution_notes=db_alert.resolution_notes
            )
            alerts.append(alert)
        
        return alerts
    
    def resolve_alert(self, alert_id: int, resolved_by: str, resolution_notes: str = "") -> bool:
        """Resolve a fraud alert."""
        db = self.get_db_session()
        
        try:
            db_alert = db.query(FraudAlertDB).filter(FraudAlertDB.id == alert_id).first()
            
            if not db_alert:
                return False
            
            db_alert.is_resolved = True
            db_alert.resolved_by = resolved_by
            db_alert.resolution_notes = resolution_notes
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            return False
    
    def get_alert_stats(self) -> Dict:
        """Get alert statistics."""
        db = self.get_db_session()
        
        # Total alerts
        total_alerts = db.query(FraudAlertDB).count()
        
        # Active alerts
        active_alerts = db.query(FraudAlertDB).filter(
            FraudAlertDB.is_resolved == False
        ).count()
        
        # Critical alerts
        critical_alerts = db.query(FraudAlertDB).filter(
            FraudAlertDB.severity == RiskLevel.CRITICAL.value,
            FraudAlertDB.is_resolved == False
        ).count()
        
        # High-risk alerts
        high_risk_alerts = db.query(FraudAlertDB).filter(
            FraudAlertDB.severity == RiskLevel.HIGH.value,
            FraudAlertDB.is_resolved == False
        ).count()
        
        # Today's alerts
        today = datetime.utcnow().date()
        today_alerts = db.query(FraudAlertDB).filter(
            FraudAlertDB.timestamp >= today
        ).count()
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'critical_alerts': critical_alerts,
            'high_risk_alerts': high_risk_alerts,
            'today_alerts': today_alerts,
            'resolution_rate': ((total_alerts - active_alerts) / total_alerts * 100) if total_alerts > 0 else 0
        }
    
    def _determine_alert_type(self, fraud_score: float) -> str:
        """Determine alert type based on fraud score."""
        if fraud_score >= 0.9:
            return "CRITICAL_FRAUD"
        elif fraud_score >= 0.7:
            return "HIGH_RISK_TRANSACTION"
        elif fraud_score >= 0.5:
            return "SUSPICIOUS_ACTIVITY"
        else:
            return "ANOMALY_DETECTED"
    
    def _determine_severity(self, fraud_score: float) -> RiskLevel:
        """Determine severity based on fraud score."""
        if fraud_score >= 0.9:
            return RiskLevel.CRITICAL
        elif fraud_score >= 0.7:
            return RiskLevel.HIGH
        elif fraud_score >= 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_alert_message(self, transaction: Transaction, fraud_score: float, risk_factors: List[str]) -> str:
        """Generate alert message."""
        from core.utils import format_currency, mask_account_number
        
        masked_account = mask_account_number(transaction.account_number)
        formatted_amount = format_currency(transaction.amount)
        
        if fraud_score >= 0.9:
            message = f"🚨 CRITICAL FRAUD ALERT: {formatted_amount} transaction on account {masked_account}"
        elif fraud_score >= 0.7:
            message = f"⚠️ HIGH RISK: {formatted_amount} transaction on account {masked_account}"
        elif fraud_score >= 0.5:
            message = f"🔍 SUSPICIOUS: {formatted_amount} transaction on account {masked_account}"
        else:
            message = f"📊 ANOMALY: {formatted_amount} transaction on account {masked_account}"
        
        if risk_factors:
            message += f" | Risk factors: {', '.join(risk_factors[:3])}"
        
        return message


# Global alert service instance
alert_service = AlertService()