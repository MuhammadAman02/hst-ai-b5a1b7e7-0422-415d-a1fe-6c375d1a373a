"""
Transaction processing and management service.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models.schemas import Transaction, TransactionCreate, Customer
from core.database import TransactionDB, CustomerDB, get_db
from core.utils import generate_transaction_id
from services.fraud_detection import fraud_detector


class TransactionService:
    """Service for managing transactions and customer data."""
    
    def __init__(self):
        self.db_session = None
    
    def get_db_session(self) -> Session:
        """Get database session."""
        if not self.db_session:
            self.db_session = next(get_db())
        return self.db_session
    
    def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        """Create a new transaction with fraud detection."""
        db = self.get_db_session()
        
        try:
            # Get customer data for fraud detection
            customer_data = self.get_customer_data(transaction_data.account_number)
            
            # Create transaction object
            transaction = Transaction(
                transaction_id=transaction_data.transaction_id or generate_transaction_id(),
                account_number=transaction_data.account_number,
                transaction_type=transaction_data.transaction_type,
                amount=transaction_data.amount,
                timestamp=datetime.utcnow(),
                location=transaction_data.location,
                device_info=transaction_data.device_info,
                ip_address=transaction_data.ip_address,
                merchant_name=transaction_data.merchant_name,
                description=transaction_data.description
            )
            
            # Calculate fraud score
            fraud_score = fraud_detector.calculate_fraud_score(transaction, customer_data)
            transaction.fraud_score = fraud_score.fraud_score
            transaction.risk_level = fraud_score.risk_level
            transaction.is_flagged = fraud_score.fraud_score >= 0.7
            
            # Save to database
            db_transaction = TransactionDB(
                transaction_id=transaction.transaction_id,
                account_number=transaction.account_number,
                transaction_type=transaction.transaction_type.value,
                amount=transaction.amount,
                timestamp=transaction.timestamp,
                location=transaction.location,
                device_info=transaction.device_info,
                ip_address=transaction.ip_address,
                merchant_name=transaction.merchant_name,
                description=transaction.description,
                fraud_score=transaction.fraud_score,
                risk_level=transaction.risk_level.value,
                is_flagged=transaction.is_flagged
            )
            
            db.add(db_transaction)
            db.commit()
            db.refresh(db_transaction)
            
            return transaction
            
        except Exception as e:
            db.rollback()
            raise e
    
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID."""
        db = self.get_db_session()
        
        db_transaction = db.query(TransactionDB).filter(
            TransactionDB.transaction_id == transaction_id
        ).first()
        
        if not db_transaction:
            return None
        
        return Transaction(
            id=db_transaction.id,
            transaction_id=db_transaction.transaction_id,
            account_number=db_transaction.account_number,
            transaction_type=db_transaction.transaction_type,
            amount=db_transaction.amount,
            timestamp=db_transaction.timestamp,
            location=db_transaction.location,
            device_info=db_transaction.device_info,
            ip_address=db_transaction.ip_address,
            merchant_name=db_transaction.merchant_name,
            description=db_transaction.description,
            fraud_score=db_transaction.fraud_score,
            risk_level=db_transaction.risk_level,
            is_flagged=db_transaction.is_flagged
        )
    
    def get_transactions_by_account(self, account_number: str, limit: int = 100) -> List[Transaction]:
        """Get transactions for an account."""
        db = self.get_db_session()
        
        db_transactions = db.query(TransactionDB).filter(
            TransactionDB.account_number == account_number
        ).order_by(desc(TransactionDB.timestamp)).limit(limit).all()
        
        transactions = []
        for db_transaction in db_transactions:
            transaction = Transaction(
                id=db_transaction.id,
                transaction_id=db_transaction.transaction_id,
                account_number=db_transaction.account_number,
                transaction_type=db_transaction.transaction_type,
                amount=db_transaction.amount,
                timestamp=db_transaction.timestamp,
                location=db_transaction.location,
                device_info=db_transaction.device_info,
                ip_address=db_transaction.ip_address,
                merchant_name=db_transaction.merchant_name,
                description=db_transaction.description,
                fraud_score=db_transaction.fraud_score,
                risk_level=db_transaction.risk_level,
                is_flagged=db_transaction.is_flagged
            )
            transactions.append(transaction)
        
        return transactions
    
    def get_flagged_transactions(self, limit: int = 50) -> List[Transaction]:
        """Get flagged transactions for review."""
        db = self.get_db_session()
        
        db_transactions = db.query(TransactionDB).filter(
            TransactionDB.is_flagged == True
        ).order_by(desc(TransactionDB.timestamp)).limit(limit).all()
        
        transactions = []
        for db_transaction in db_transactions:
            transaction = Transaction(
                id=db_transaction.id,
                transaction_id=db_transaction.transaction_id,
                account_number=db_transaction.account_number,
                transaction_type=db_transaction.transaction_type,
                amount=db_transaction.amount,
                timestamp=db_transaction.timestamp,
                location=db_transaction.location,
                device_info=db_transaction.device_info,
                ip_address=db_transaction.ip_address,
                merchant_name=db_transaction.merchant_name,
                description=db_transaction.description,
                fraud_score=db_transaction.fraud_score,
                risk_level=db_transaction.risk_level,
                is_flagged=db_transaction.is_flagged
            )
            transactions.append(transaction)
        
        return transactions
    
    def get_customer_data(self, account_number: str) -> Dict:
        """Get customer data for fraud detection."""
        db = self.get_db_session()
        
        # Get customer info
        customer = db.query(CustomerDB).filter(
            CustomerDB.account_number == account_number
        ).first()
        
        if not customer:
            return {}
        
        # Get recent transactions
        recent_transactions = db.query(TransactionDB).filter(
            TransactionDB.account_number == account_number,
            TransactionDB.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        # Calculate average transaction amount
        if recent_transactions:
            avg_amount = sum(t.amount for t in recent_transactions) / len(recent_transactions)
        else:
            avg_amount = 0
        
        return {
            'account_balance': customer.account_balance,
            'avg_transaction_amount': avg_amount,
            'recent_transactions': recent_transactions,
            'customer_risk_score': customer.risk_score,
            'account_age_days': (datetime.utcnow() - customer.account_created).days
        }
    
    def get_transaction_stats(self) -> Dict:
        """Get transaction statistics."""
        db = self.get_db_session()
        
        # Total transactions
        total_transactions = db.query(TransactionDB).count()
        
        # Flagged transactions
        flagged_transactions = db.query(TransactionDB).filter(
            TransactionDB.is_flagged == True
        ).count()
        
        # Today's transactions
        today = datetime.utcnow().date()
        today_transactions = db.query(TransactionDB).filter(
            func.date(TransactionDB.timestamp) == today
        ).count()
        
        # High-risk transactions
        high_risk_transactions = db.query(TransactionDB).filter(
            TransactionDB.fraud_score >= 0.7
        ).count()
        
        # Total transaction volume
        total_volume = db.query(func.sum(TransactionDB.amount)).scalar() or 0
        
        return {
            'total_transactions': total_transactions,
            'flagged_transactions': flagged_transactions,
            'today_transactions': today_transactions,
            'high_risk_transactions': high_risk_transactions,
            'total_volume': total_volume,
            'fraud_rate': (flagged_transactions / total_transactions * 100) if total_transactions > 0 else 0
        }


# Global transaction service instance
transaction_service = TransactionService()