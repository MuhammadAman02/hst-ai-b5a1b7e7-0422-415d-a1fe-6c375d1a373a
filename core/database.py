"""
Database configuration and connection management.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from app.config import settings

# Database setup
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CustomerDB(Base):
    """Customer database model."""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String, unique=True, index=True)
    name = Column(String)
    cnic = Column(String, unique=True)
    phone = Column(String)
    email = Column(String)
    city = Column(String)
    province = Column(String)
    account_balance = Column(Float)
    account_created = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    risk_score = Column(Float, default=0.0)


class TransactionDB(Base):
    """Transaction database model."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    account_number = Column(String, index=True)
    transaction_type = Column(String)
    amount = Column(Float)
    currency = Column(String, default="PKR")
    timestamp = Column(DateTime, default=datetime.utcnow)
    location = Column(String)
    device_info = Column(String)
    ip_address = Column(String)
    merchant_name = Column(String)
    description = Column(Text)
    is_successful = Column(Boolean, default=True)
    fraud_score = Column(Float, default=0.0)
    risk_level = Column(String, default="low")
    is_flagged = Column(Boolean, default=False)


class FraudAlertDB(Base):
    """Fraud alert database model."""
    __tablename__ = "fraud_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True)
    account_number = Column(String, index=True)
    alert_type = Column(String)
    severity = Column(String)
    message = Column(Text)
    fraud_score = Column(Float)
    risk_factors = Column(Text)  # JSON string
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String)
    resolution_notes = Column(Text)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)