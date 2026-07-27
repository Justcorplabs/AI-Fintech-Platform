from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class FraudStatus(str, enum.Enum):
    pending = "pending"
    flagged = "flagged"
    cleared = "cleared"
    investigating = "investigating"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_ref = Column(String, unique=True, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    merchant_name = Column(String)
    merchant_category = Column(String)
    card_type = Column(String)
    transaction_hour = Column(Integer)
    distance_from_home = Column(Float)
    is_foreign = Column(Boolean, default=False)

    fraud_score = Column(Float, nullable=True)
    is_fraud = Column(Boolean, nullable=True)
    status = Column(Enum(FraudStatus), default=FraudStatus.pending)
    shap_values = Column(JSONB, nullable=True)
    model_version = Column(String, default="v1.0")

    analyst_notes = Column(Text, nullable=True)
    reviewed_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    audit_events = relationship(
        "TransactionAuditEvent",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )


class TransactionAuditEvent(Base):
    __tablename__ = "transaction_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, index=True)

    action = Column(String, nullable=False)
    status = Column(String, nullable=True)
    actor = Column(String, default="System")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transaction = relationship("Transaction", back_populates="audit_events")