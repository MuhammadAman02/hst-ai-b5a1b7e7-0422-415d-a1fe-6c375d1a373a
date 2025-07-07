"""
Security utilities for the fraud detection system.
"""

import hashlib
import secrets
from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def generate_session_token() -> str:
    """Generate secure session token."""
    return secrets.token_urlsafe(32)


def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging/storage."""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def validate_cnic(cnic: str) -> bool:
    """Validate Pakistani CNIC format."""
    import re
    pattern = r'^\d{5}-\d{7}-\d{1}$'
    return bool(re.match(pattern, cnic))


def validate_phone(phone: str) -> bool:
    """Validate Pakistani mobile phone format."""
    import re
    pattern = r'^(\+92|0)?3\d{9}$'
    return bool(re.match(pattern, phone))


def is_suspicious_ip(ip_address: str) -> bool:
    """Check if IP address is from suspicious location."""
    # Simplified check - in production, use IP geolocation services
    suspicious_ranges = [
        "192.168.",  # Local network (suspicious for online banking)
        "10.0.",     # Private network
        "172.16."    # Private network
    ]
    return any(ip_address.startswith(range_) for range_ in suspicious_ranges)


def calculate_velocity_risk(transactions: list, time_window: int = 60) -> float:
    """Calculate transaction velocity risk score."""
    if not transactions:
        return 0.0
    
    # Count transactions in the last time_window minutes
    now = datetime.utcnow()
    recent_transactions = [
        t for t in transactions 
        if (now - t.timestamp).total_seconds() <= time_window * 60
    ]
    
    # Risk increases with transaction frequency
    velocity_score = min(len(recent_transactions) / 10.0, 1.0)
    return velocity_score