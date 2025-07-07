"""
Utility functions for the fraud detection system.
"""

from datetime import datetime, time
from typing import List, Dict, Any
import json
from app.config import settings


def format_currency(amount: float, currency: str = "PKR") -> str:
    """Format currency amount for Pakistani Rupees."""
    if currency == "PKR":
        return f"Rs. {amount:,.2f}"
    return f"{amount:,.2f} {currency}"


def is_business_hours(timestamp: datetime = None) -> bool:
    """Check if transaction is during business hours."""
    if timestamp is None:
        timestamp = datetime.now()
    
    current_time = timestamp.time()
    start_time = time(settings.business_hours_start, 0)
    end_time = time(settings.business_hours_end, 0)
    
    return start_time <= current_time <= end_time


def is_weekend(timestamp: datetime = None) -> bool:
    """Check if transaction is on weekend."""
    if timestamp is None:
        timestamp = datetime.now()
    
    # Friday is weekend in Pakistan (weekday 4)
    return timestamp.weekday() in [4, 5]  # Friday, Saturday


def calculate_time_risk(timestamp: datetime) -> float:
    """Calculate risk based on transaction time."""
    risk_score = 0.0
    
    # Higher risk for non-business hours
    if not is_business_hours(timestamp):
        risk_score += 0.3
    
    # Higher risk for weekends
    if is_weekend(timestamp):
        risk_score += 0.2
    
    # Very high risk for late night (11 PM - 5 AM)
    hour = timestamp.hour
    if hour >= 23 or hour <= 5:
        risk_score += 0.4
    
    return min(risk_score, 1.0)


def calculate_amount_risk(amount: float, account_balance: float, avg_transaction: float) -> float:
    """Calculate risk based on transaction amount."""
    risk_score = 0.0
    
    # Risk based on amount relative to balance
    if account_balance > 0:
        balance_ratio = amount / account_balance
        if balance_ratio > 0.8:  # More than 80% of balance
            risk_score += 0.5
        elif balance_ratio > 0.5:  # More than 50% of balance
            risk_score += 0.3
    
    # Risk based on amount relative to average
    if avg_transaction > 0:
        avg_ratio = amount / avg_transaction
        if avg_ratio > 10:  # 10x average
            risk_score += 0.4
        elif avg_ratio > 5:  # 5x average
            risk_score += 0.2
    
    # High amount threshold (1 million PKR)
    if amount > 1000000:
        risk_score += 0.3
    
    return min(risk_score, 1.0)


def parse_risk_factors(risk_factors: str) -> List[str]:
    """Parse risk factors from JSON string."""
    try:
        return json.loads(risk_factors) if risk_factors else []
    except json.JSONDecodeError:
        return []


def serialize_risk_factors(risk_factors: List[str]) -> str:
    """Serialize risk factors to JSON string."""
    return json.dumps(risk_factors)


def get_location_risk(location: str) -> float:
    """Calculate risk based on transaction location."""
    if not location:
        return 0.1  # Unknown location has some risk
    
    # High-risk locations (simplified)
    high_risk_locations = [
        "unknown", "foreign", "international", "offshore"
    ]
    
    location_lower = location.lower()
    if any(risk_loc in location_lower for risk_loc in high_risk_locations):
        return 0.6
    
    return 0.0


def generate_transaction_id() -> str:
    """Generate unique transaction ID."""
    import uuid
    return f"TXN{uuid.uuid4().hex[:12].upper()}"


def mask_account_number(account_number: str) -> str:
    """Mask account number for display."""
    if len(account_number) <= 4:
        return account_number
    return f"****{account_number[-4:]}"


def mask_cnic(cnic: str) -> str:
    """Mask CNIC for display."""
    if len(cnic) < 8:
        return cnic
    return f"{cnic[:5]}-****{cnic[-3:]}"