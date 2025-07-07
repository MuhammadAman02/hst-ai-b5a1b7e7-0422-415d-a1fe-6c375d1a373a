"""
Pydantic models for data validation and serialization.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class TransactionType(str, Enum):
    """Transaction types common in Pakistani banking."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    BILL_PAYMENT = "bill_payment"
    MOBILE_BANKING = "mobile_banking"
    ATM = "atm"
    ONLINE = "online"
    CHEQUE = "cheque"


class RiskLevel(str, Enum):
    """Risk levels for fraud detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Customer(BaseModel):
    """Customer information model."""
    id: Optional[int] = None
    account_number: str = Field(..., min_length=10, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    cnic: str = Field(..., regex=r'^\d{5}-\d{7}-\d{1}$')  # Pakistani CNIC format
    phone: str = Field(..., regex=r'^(\+92|0)?3\d{9}$')  # Pakistani mobile format
    email: Optional[str] = None
    city: str
    province: str
    account_balance: float = Field(..., ge=0)
    account_created: datetime
    is_active: bool = True
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @validator('province')
    def validate_province(cls, v):
        """Validate Pakistani provinces."""
        valid_provinces = ['Punjab', 'Sindh', 'KPK', 'Balochistan', 'Gilgit-Baltistan', 'AJK']
        if v not in valid_provinces:
            raise ValueError(f'Province must be one of: {", ".join(valid_provinces)}')
        return v


class CustomerCreate(BaseModel):
    """Model for creating new customers."""
    account_number: str = Field(..., min_length=10, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    cnic: str = Field(..., regex=r'^\d{5}-\d{7}-\d{1}$')
    phone: str = Field(..., regex=r'^(\+92|0)?3\d{9}$')
    email: Optional[str] = None
    city: str
    province: str
    account_balance: float = Field(..., ge=0)


class Transaction(BaseModel):
    """Transaction model with Pakistani banking context."""
    id: Optional[int] = None
    transaction_id: str = Field(..., min_length=10, max_length=50)
    account_number: str = Field(..., min_length=10, max_length=20)
    transaction_type: TransactionType
    amount: float = Field(..., gt=0)
    currency: str = Field(default="PKR")
    timestamp: datetime
    location: Optional[str] = None
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    merchant_name: Optional[str] = None
    description: Optional[str] = None
    is_successful: bool = True
    fraud_score: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    is_flagged: bool = False
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate transaction amount limits."""
        if v > 10000000:  # 10 million PKR limit
            raise ValueError('Transaction amount exceeds maximum limit')
        return v


class TransactionCreate(BaseModel):
    """Model for creating new transactions."""
    transaction_id: str = Field(..., min_length=10, max_length=50)
    account_number: str = Field(..., min_length=10, max_length=20)
    transaction_type: TransactionType
    amount: float = Field(..., gt=0)
    location: Optional[str] = None
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    merchant_name: Optional[str] = None
    description: Optional[str] = None


class FraudScore(BaseModel):
    """Fraud scoring result."""
    transaction_id: str
    fraud_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    risk_factors: List[str] = []
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str = "1.0"
    timestamp: datetime


class FraudAlert(BaseModel):
    """Fraud alert model."""
    id: Optional[int] = None
    transaction_id: str
    account_number: str
    alert_type: str
    severity: RiskLevel
    message: str
    fraud_score: float
    risk_factors: List[str] = []
    timestamp: datetime
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None