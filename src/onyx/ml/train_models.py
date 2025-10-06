"""
Training script for Onyx ML models.

Trains trust scoring and risk assessment models using synthetic data.
"""

import os
import sys
from pathlib import Path
import logging
import numpy as np
import pandas as pd

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from onyx.ml.trust_scoring import TrustScoringModel
from onyx.ml.risk_assessment import RiskAssessmentModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_synthetic_trust_data(n_samples: int = 5000) -> tuple[pd.DataFrame, pd.Series]:
    """Generate synthetic data for trust scoring training."""
    np.random.seed(42)
    
    data = {
        "device_reputation": np.random.uniform(0.1, 1.0, n_samples),
        "velocity": np.random.exponential(2.0, n_samples),
        "ip_risk": np.random.uniform(0.0, 1.0, n_samples),
        "history_len": np.random.poisson(50, n_samples),
        "user_age_days": np.random.exponential(365, n_samples),
        "session_duration_min": np.random.exponential(30, n_samples),
        "device_consistency": np.random.uniform(0.5, 1.0, n_samples),
        "location_consistency": np.random.uniform(0.5, 1.0, n_samples),
        "payment_method_age_days": np.random.exponential(180, n_samples),
        "transaction_amount": np.random.exponential(100, n_samples),
        "merchant_trust_score": np.random.uniform(0.3, 1.0, n_samples),
        "time_since_last_login_hours": np.random.exponential(2, n_samples),
        "failed_attempts_24h": np.random.poisson(0.5, n_samples),
        "account_verification_level": np.random.choice([0, 1, 2, 3], n_samples, p=[0.1, 0.2, 0.5, 0.2]),
        "is_mobile_device": np.random.choice([True, False], n_samples, p=[0.4, 0.6]),
        "is_vpn_connection": np.random.choice([True, False], n_samples, p=[0.05, 0.95]),
        "transaction_hour": np.random.randint(0, 24, n_samples),
        "transaction_day_of_week": np.random.randint(0, 7, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Generate synthetic trust scores based on features
    # Higher device reputation, lower velocity, lower IP risk, longer history = higher trust
    trust_score = (
        df['device_reputation'] * 0.3 +
        (1.0 - np.minimum(df['velocity'] / 10.0, 1.0)) * 0.2 +
        (1.0 - df['ip_risk']) * 0.2 +
        np.minimum(df['history_len'] / 100.0, 1.0) * 0.15 +
        np.minimum(df['user_age_days'] / 1000.0, 1.0) * 0.05 +
        df['device_consistency'] * 0.05 +
        df['location_consistency'] * 0.05
    )
    
    # Add some noise
    noise = np.random.normal(0, 0.1, n_samples)
    trust_score = np.clip(trust_score + noise, 0.0, 1.0)
    
    return df, pd.Series(trust_score)


def generate_synthetic_risk_data(n_samples: int = 5000) -> tuple[pd.DataFrame, pd.Series]:
    """Generate synthetic data for risk assessment training."""
    np.random.seed(42)
    
    data = {
        "transaction_amount": np.random.exponential(150, n_samples),
        "merchant_risk_score": np.random.uniform(0.1, 1.0, n_samples),
        "user_trust_score": np.random.uniform(0.2, 1.0, n_samples),
        "device_risk_score": np.random.uniform(0.0, 1.0, n_samples),
        "ip_risk_score": np.random.uniform(0.0, 1.0, n_samples),
        "velocity_24h": np.random.exponential(3.0, n_samples),
        "velocity_7d": np.random.exponential(20.0, n_samples),
        "avg_transaction_amount": np.random.exponential(120, n_samples),
        "time_since_last_transaction_hours": np.random.exponential(8, n_samples),
        "payment_method_age_days": np.random.exponential(200, n_samples),
        "user_age_days": np.random.exponential(400, n_samples),
        "is_high_value": np.random.choice([True, False], n_samples, p=[0.1, 0.9]),
        "is_international": np.random.choice([True, False], n_samples, p=[0.05, 0.95]),
        "is_new_merchant": np.random.choice([True, False], n_samples, p=[0.15, 0.85]),
        "is_weekend": np.random.choice([True, False], n_samples, p=[0.3, 0.7]),
        "is_off_hours": np.random.choice([True, False], n_samples, p=[0.2, 0.8]),
        "failed_attempts_24h": np.random.poisson(0.3, n_samples),
        "account_verification_level": np.random.choice([0, 1, 2, 3], n_samples, p=[0.05, 0.15, 0.6, 0.2]),
    }
    
    df = pd.DataFrame(data)
    
    # Generate synthetic risk labels
    # Higher amounts, velocity, failed attempts, new merchants, off-hours = higher risk
    risk_score = (
        np.minimum(df['transaction_amount'] / 1000.0, 1.0) * 0.2 +
        df['merchant_risk_score'] * 0.2 +
        (1.0 - df['user_trust_score']) * 0.15 +
        df['device_risk_score'] * 0.15 +
        df['ip_risk_score'] * 0.15 +
        np.minimum(df['velocity_24h'] / 20.0, 1.0) * 0.05 +
        df['is_high_value'] * 0.05 +
        df['is_new_merchant'] * 0.03 +
        df['is_off_hours'] * 0.02
    )
    
    # Add some noise
    noise = np.random.normal(0, 0.05, n_samples)
    risk_score = np.clip(risk_score + noise, 0.0, 1.0)
    
    # Convert to binary labels (high risk = 1, low risk = 0)
    risk_labels = (risk_score > 0.5).astype(int)
    
    return df, pd.Series(risk_labels)


def train_all_models():
    """Train all ML models."""
    logger.info("🚀 Starting Onyx ML model training...")

    # Train Trust Scoring Model
    logger.info("🔧 Training trust scoring model...")
    trust_model = TrustScoringModel()
    trust_X, trust_y = generate_synthetic_trust_data(5000)
    trust_model.train_model(trust_X, trust_y)
    logger.info("✅ Trust scoring model trained and saved")

    # Train Risk Assessment Model
    logger.info("🔧 Training risk assessment model...")
    risk_model = RiskAssessmentModel()
    risk_X, risk_y = generate_synthetic_risk_data(5000)
    risk_model.train_model(risk_X, risk_y)
    logger.info("✅ Risk assessment model trained and saved")

    logger.info("🎉 All ML models trained successfully!")


if __name__ == "__main__":
    train_all_models()
