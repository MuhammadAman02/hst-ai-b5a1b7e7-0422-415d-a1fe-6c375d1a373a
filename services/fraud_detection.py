"""
Machine Learning-based fraud detection service.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

from models.schemas import Transaction, FraudScore, RiskLevel
from core.utils import (
    calculate_time_risk, 
    calculate_amount_risk, 
    get_location_risk,
    is_business_hours,
    is_weekend
)
from core.security import is_suspicious_ip, calculate_velocity_risk
from app.config import settings


class FraudDetectionService:
    """Advanced fraud detection using machine learning."""
    
    def __init__(self):
        self.isolation_forest = None
        self.random_forest = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'amount', 'hour', 'day_of_week', 'is_weekend', 'is_business_hours',
            'amount_to_balance_ratio', 'velocity_score', 'location_risk',
            'time_risk', 'transaction_type_encoded'
        ]
        self.model_path = "models/fraud_model.joblib"
        self.scaler_path = "models/scaler.joblib"
        
        # Load or initialize models
        self._load_or_initialize_models()
    
    def _load_or_initialize_models(self):
        """Load existing models or initialize new ones."""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.isolation_forest = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                print("✅ Fraud detection models loaded successfully")
            else:
                self._initialize_models()
                print("🔄 Initialized new fraud detection models")
        except Exception as e:
            print(f"⚠️ Error loading models: {e}")
            self._initialize_models()
    
    def _initialize_models(self):
        """Initialize new ML models with default parameters."""
        self.isolation_forest = IsolationForest(
            contamination=0.1,  # Expect 10% fraud
            random_state=42,
            n_estimators=100
        )
        
        # Create sample data for initial training
        sample_data = self._generate_sample_data()
        if len(sample_data) > 0:
            self._train_models(sample_data)
    
    def _generate_sample_data(self) -> pd.DataFrame:
        """Generate sample transaction data for initial model training."""
        np.random.seed(42)
        n_samples = 1000
        
        # Generate normal transactions
        normal_transactions = []
        for i in range(int(n_samples * 0.9)):  # 90% normal
            transaction = {
                'amount': np.random.lognormal(8, 1),  # Log-normal distribution for amounts
                'hour': np.random.choice(range(9, 18), p=[0.1, 0.15, 0.15, 0.2, 0.2, 0.1, 0.05, 0.03, 0.02]),
                'day_of_week': np.random.choice(range(7), p=[0.2, 0.2, 0.2, 0.2, 0.1, 0.05, 0.05]),
                'is_weekend': 0,
                'is_business_hours': 1,
                'amount_to_balance_ratio': np.random.uniform(0.01, 0.3),
                'velocity_score': np.random.uniform(0, 0.2),
                'location_risk': np.random.uniform(0, 0.1),
                'time_risk': np.random.uniform(0, 0.2),
                'transaction_type_encoded': np.random.choice(range(8)),
                'is_fraud': 0
            }
            normal_transactions.append(transaction)
        
        # Generate fraudulent transactions
        fraud_transactions = []
        for i in range(int(n_samples * 0.1)):  # 10% fraud
            transaction = {
                'amount': np.random.lognormal(10, 1.5),  # Higher amounts
                'hour': np.random.choice(range(24), p=[0.1]*6 + [0.02]*12 + [0.1]*6),  # More at night
                'day_of_week': np.random.choice(range(7)),
                'is_weekend': np.random.choice([0, 1], p=[0.3, 0.7]),  # More on weekends
                'is_business_hours': np.random.choice([0, 1], p=[0.7, 0.3]),  # More outside business hours
                'amount_to_balance_ratio': np.random.uniform(0.5, 1.0),  # Higher ratios
                'velocity_score': np.random.uniform(0.3, 1.0),  # Higher velocity
                'location_risk': np.random.uniform(0.2, 0.8),  # Higher location risk
                'time_risk': np.random.uniform(0.3, 1.0),  # Higher time risk
                'transaction_type_encoded': np.random.choice(range(8)),
                'is_fraud': 1
            }
            fraud_transactions.append(transaction)
        
        all_transactions = normal_transactions + fraud_transactions
        return pd.DataFrame(all_transactions)
    
    def extract_features(self, transaction: Transaction, customer_data: Dict = None) -> Dict:
        """Extract features from transaction for ML model."""
        features = {}
        
        # Basic transaction features
        features['amount'] = transaction.amount
        features['hour'] = transaction.timestamp.hour
        features['day_of_week'] = transaction.timestamp.weekday()
        features['is_weekend'] = int(is_weekend(transaction.timestamp))
        features['is_business_hours'] = int(is_business_hours(transaction.timestamp))
        
        # Risk-based features
        features['time_risk'] = calculate_time_risk(transaction.timestamp)
        features['location_risk'] = get_location_risk(transaction.location or "")
        
        # Customer-specific features
        if customer_data:
            account_balance = customer_data.get('account_balance', 0)
            avg_transaction = customer_data.get('avg_transaction_amount', transaction.amount)
            recent_transactions = customer_data.get('recent_transactions', [])
            
            features['amount_to_balance_ratio'] = (
                transaction.amount / account_balance if account_balance > 0 else 1.0
            )
            features['velocity_score'] = calculate_velocity_risk(recent_transactions)
        else:
            features['amount_to_balance_ratio'] = 0.5  # Default
            features['velocity_score'] = 0.0
        
        # Encode transaction type
        type_mapping = {
            'deposit': 0, 'withdrawal': 1, 'transfer': 2, 'bill_payment': 3,
            'mobile_banking': 4, 'atm': 5, 'online': 6, 'cheque': 7
        }
        features['transaction_type_encoded'] = type_mapping.get(transaction.transaction_type, 0)
        
        return features
    
    def calculate_fraud_score(self, transaction: Transaction, customer_data: Dict = None) -> FraudScore:
        """Calculate fraud score for a transaction."""
        try:
            # Extract features
            features = self.extract_features(transaction, customer_data)
            
            # Prepare feature vector
            feature_vector = np.array([[features[col] for col in self.feature_columns]])
            
            # Scale features
            if hasattr(self.scaler, 'transform'):
                feature_vector_scaled = self.scaler.transform(feature_vector)
            else:
                feature_vector_scaled = feature_vector
            
            # Get anomaly score from Isolation Forest
            anomaly_score = self.isolation_forest.decision_function(feature_vector_scaled)[0]
            
            # Convert to probability (0-1 scale)
            fraud_probability = max(0, min(1, (1 - anomaly_score) / 2))
            
            # Rule-based adjustments
            rule_based_score = self._calculate_rule_based_score(features)
            
            # Combine ML and rule-based scores
            final_score = (fraud_probability * 0.7) + (rule_based_score * 0.3)
            final_score = max(0, min(1, final_score))
            
            # Determine risk level
            risk_level = self._determine_risk_level(final_score)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(features, final_score)
            
            return FraudScore(
                transaction_id=transaction.transaction_id,
                fraud_score=final_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                confidence=0.85,  # Model confidence
                model_version="1.0",
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            print(f"Error calculating fraud score: {e}")
            # Return conservative high-risk score on error
            return FraudScore(
                transaction_id=transaction.transaction_id,
                fraud_score=0.8,
                risk_level=RiskLevel.HIGH,
                risk_factors=["Model error - manual review required"],
                confidence=0.5,
                model_version="1.0",
                timestamp=datetime.utcnow()
            )
    
    def _calculate_rule_based_score(self, features: Dict) -> float:
        """Calculate rule-based fraud score."""
        score = 0.0
        
        # High amount transactions
        if features['amount'] > 500000:  # 5 lakh PKR
            score += 0.3
        elif features['amount'] > 100000:  # 1 lakh PKR
            score += 0.1
        
        # Time-based rules
        if not features['is_business_hours']:
            score += 0.2
        
        if features['is_weekend']:
            score += 0.1
        
        # Late night transactions (11 PM - 5 AM)
        if features['hour'] >= 23 or features['hour'] <= 5:
            score += 0.3
        
        # High velocity
        if features['velocity_score'] > 0.5:
            score += 0.4
        
        # High amount to balance ratio
        if features['amount_to_balance_ratio'] > 0.8:
            score += 0.4
        elif features['amount_to_balance_ratio'] > 0.5:
            score += 0.2
        
        # Location risk
        score += features['location_risk'] * 0.3
        
        return min(score, 1.0)
    
    def _determine_risk_level(self, fraud_score: float) -> RiskLevel:
        """Determine risk level based on fraud score."""
        if fraud_score >= settings.high_risk_threshold:
            return RiskLevel.CRITICAL
        elif fraud_score >= settings.fraud_threshold:
            return RiskLevel.HIGH
        elif fraud_score >= 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _identify_risk_factors(self, features: Dict, fraud_score: float) -> List[str]:
        """Identify specific risk factors contributing to the fraud score."""
        risk_factors = []
        
        if features['amount'] > 500000:
            risk_factors.append("High transaction amount (>5 Lakh PKR)")
        elif features['amount'] > 100000:
            risk_factors.append("Large transaction amount (>1 Lakh PKR)")
        
        if not features['is_business_hours']:
            risk_factors.append("Transaction outside business hours")
        
        if features['is_weekend']:
            risk_factors.append("Weekend transaction")
        
        if features['hour'] >= 23 or features['hour'] <= 5:
            risk_factors.append("Late night transaction")
        
        if features['velocity_score'] > 0.5:
            risk_factors.append("High transaction velocity")
        
        if features['amount_to_balance_ratio'] > 0.8:
            risk_factors.append("Transaction amount >80% of account balance")
        elif features['amount_to_balance_ratio'] > 0.5:
            risk_factors.append("Transaction amount >50% of account balance")
        
        if features['location_risk'] > 0.3:
            risk_factors.append("Suspicious transaction location")
        
        if fraud_score > 0.8:
            risk_factors.append("Multiple high-risk indicators detected")
        
        return risk_factors
    
    def _train_models(self, data: pd.DataFrame):
        """Train the fraud detection models."""
        try:
            # Prepare features
            X = data[self.feature_columns]
            
            # Fit scaler
            self.scaler.fit(X)
            X_scaled = self.scaler.transform(X)
            
            # Train Isolation Forest (unsupervised)
            self.isolation_forest.fit(X_scaled)
            
            # Save models
            os.makedirs("models", exist_ok=True)
            joblib.dump(self.isolation_forest, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            print("✅ Fraud detection models trained and saved")
            
        except Exception as e:
            print(f"❌ Error training models: {e}")
    
    def retrain_models(self, transactions: List[Transaction], labels: List[int] = None):
        """Retrain models with new transaction data."""
        if not transactions:
            return
        
        try:
            # Convert transactions to DataFrame
            data_rows = []
            for transaction in transactions:
                features = self.extract_features(transaction)
                features['is_fraud'] = 0  # Default to non-fraud
                data_rows.append(features)
            
            if labels:
                for i, label in enumerate(labels):
                    if i < len(data_rows):
                        data_rows[i]['is_fraud'] = label
            
            df = pd.DataFrame(data_rows)
            
            # Retrain models
            self._train_models(df)
            
        except Exception as e:
            print(f"❌ Error retraining models: {e}")
    
    def get_model_stats(self) -> Dict:
        """Get model statistics and performance metrics."""
        return {
            "model_version": "1.0",
            "algorithm": "Isolation Forest + Rule-based",
            "features_count": len(self.feature_columns),
            "fraud_threshold": settings.fraud_threshold,
            "high_risk_threshold": settings.high_risk_threshold,
            "last_trained": datetime.utcnow().isoformat(),
            "model_status": "Active"
        }


# Global fraud detection service instance
fraud_detector = FraudDetectionService()