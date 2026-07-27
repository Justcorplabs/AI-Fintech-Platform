from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class TransactionCreate(BaseModel):
    transaction_ref: str
    amount: float
    currency: str = "USD"
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    card_type: Optional[str] = None
    transaction_hour: Optional[int] = None
    distance_from_home: Optional[float] = None
    is_foreign: bool = False
    demo_profile: Optional[str] = None


class FraudPredictionOut(BaseModel):
    transaction_ref: str
    fraud_score: float
    is_fraud: bool
    risk_level: str
    top_risk_factors: list[Dict[str, Any]]
    model_version: str

    model_config = ConfigDict(from_attributes=True)


class TransactionOut(BaseModel):
    id: UUID
    transaction_ref: str
    amount: float
    currency: str
    fraud_score: Optional[float]
    is_fraud: Optional[bool]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class TransactionAuditEventOut(BaseModel):
    id: UUID
    action: str
    status: Optional[str]
    actor: Optional[str]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionDetailOut(BaseModel):
    id: UUID
    transaction_ref: str
    amount: float
    currency: str
    merchant_name: Optional[str]
    merchant_category: Optional[str]
    card_type: Optional[str]
    transaction_hour: Optional[int]
    distance_from_home: Optional[float]
    is_foreign: bool
    fraud_score: Optional[float]
    is_fraud: Optional[bool]
    status: str
    shap_values: Optional[list[Dict[str, Any]]]
    model_version: Optional[str]
    analyst_notes: Optional[str]
    reviewed_by: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]
    audit_events: list[TransactionAuditEventOut] = []

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class TransactionReviewUpdate(BaseModel):
    status: str
    analyst_notes: Optional[str] = None
    reviewed_by: Optional[str] = "Joseph"