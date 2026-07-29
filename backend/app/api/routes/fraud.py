import json
import os
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.dependencies import require_permission
from app.core.permissions import Permission
from app.core.rate_limit import (
    FRAUD_PREDICTION_LIMIT,
    authenticated_user_key,
    limiter,
)
from app.core.rbac import ROLE_PERMISSIONS
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.fraud import (
    FraudStatus,
    Transaction,
    TransactionAuditEvent,
)
from app.models.user import User
from app.schemas.fraud import (
    FraudPredictionOut,
    TransactionCreate,
    TransactionDetailOut,
    TransactionOut,
    TransactionReviewUpdate,
)
from app.services.fraud.connection_manager import (
    fraud_ws_manager,
)
from app.services.fraud.predictor import fraud_predictor


router = APIRouter(
    prefix="/fraud",
    tags=["Fraud Detection"],
)


fraud_read_access = require_permission(
    Permission.FRAUD_READ
)

fraud_analyze_access = require_permission(
    Permission.FRAUD_ANALYZE
)


def user_display_name(user: User) -> str:
    return user.full_name or user.email


def create_audit_event(
    db: Session,
    transaction_id,
    action: str,
    status: str | None = None,
    actor: str = "System",
    notes: str | None = None,
):
    event = TransactionAuditEvent(
        transaction_id=transaction_id,
        action=action,
        status=status,
        actor=actor,
        notes=notes,
    )

    db.add(event)


def validate_websocket_token(
    token: str | None,
) -> dict:
    """
    Validate a WebSocket JWT and confirm that the user's
    role has permission to read fraud information.
    """

    if not token:
        raise InvalidTokenError(
            "Authentication token is missing."
        )

    payload = decode_access_token(token)

    role = str(payload.get("role", ""))

    permissions = ROLE_PERMISSIONS.get(
        role,
        set(),
    )

    if Permission.FRAUD_READ not in permissions:
        raise InvalidTokenError(
            "User does not have fraud read permission."
        )

    return payload


@router.websocket("/ws/alerts")
async def fraud_alert_socket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    try:
        validate_websocket_token(token)

    except InvalidTokenError:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=(
                "Authentication credentials could "
                "not be validated."
            ),
        )
        return

    await fraud_ws_manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        fraud_ws_manager.disconnect(websocket)

    except Exception:
        fraud_ws_manager.disconnect(websocket)

        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR,
        )


@router.post(
    "/predict",
    response_model=FraudPredictionOut,
)
@limiter.limit(
    FRAUD_PREDICTION_LIMIT,
    key_func=authenticated_user_key,
)
async def predict_fraud(
    request: Request,
    response: Response,
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        fraud_analyze_access
    ),
):
    result = fraud_predictor.predict(
        payload.model_dump()
    )

    tx = Transaction(
        transaction_ref=payload.transaction_ref,
        amount=payload.amount,
        currency=payload.currency,
        merchant_name=payload.merchant_name,
        merchant_category=(
            payload.merchant_category
        ),
        card_type=payload.card_type,
        transaction_hour=(
            payload.transaction_hour
        ),
        distance_from_home=(
            payload.distance_from_home
        ),
        is_foreign=payload.is_foreign,
        fraud_score=result["fraud_score"],
        is_fraud=result["is_fraud"],
        shap_values=result["top_risk_factors"],
        model_version=result["model_version"],
        status=(
            FraudStatus.flagged
            if result["is_fraud"]
            else FraudStatus.pending
        ),
    )

    db.add(tx)
    db.flush()

    create_audit_event(
        db=db,
        transaction_id=tx.id,
        action="Transaction created",
        status=tx.status.value,
        actor=user_display_name(
            current_user
        ),
        notes=(
            "Transaction submitted for "
            "fraud scoring."
        ),
    )

    create_audit_event(
        db=db,
        transaction_id=tx.id,
        action="AI prediction completed",
        status=tx.status.value,
        actor="SentinelAI",
        notes=(
            f"Fraud score: "
            f"{round(result['fraud_score'] * 100, 2)}%. "
            f"Model: {result['model_version']}."
        ),
    )

    db.commit()
    db.refresh(tx)

    await fraud_ws_manager.broadcast(
        {
            "type": "fraud_prediction",
            "transaction_id": str(tx.id),
            "transaction_ref": (
                tx.transaction_ref
            ),
            "amount": tx.amount,
            "currency": tx.currency,
            "fraud_score": tx.fraud_score,
            "is_fraud": tx.is_fraud,
            "status": tx.status.value,
            "model_version": (
                tx.model_version
            ),
        }
    )

    return {
        "transaction_ref": (
            payload.transaction_ref
        ),
        **result,
    }


@router.get(
    "/transactions",
    response_model=List[TransactionOut],
)
def get_transactions(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    flagged_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        fraud_read_access
    ),
):
    query = db.query(Transaction)

    if flagged_only:
        query = query.filter(
            Transaction.status
            == FraudStatus.flagged
        )

    return (
        query.order_by(
            Transaction.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/model/metadata")
def get_model_metadata(
    current_user: User = Depends(
        fraud_read_access
    ),
):
    root = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../../../",
        )
    )

    metadata_path = os.path.join(
        root,
        "ml",
        "registry",
        "champion_model_card.json",
    )

    registry_path = os.path.join(
        root,
        "ml",
        "registry",
        "model_registry.csv",
    )

    if not os.path.exists(
        metadata_path
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Model metadata not found.",
        )

    try:
        with open(
            metadata_path,
            "r",
            encoding="utf-8",
        ) as file:
            metadata = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Model metadata could not "
                "be loaded."
            ),
        )

    metadata["registry_available"] = (
        os.path.exists(registry_path)
    )

    return metadata


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionDetailOut,
)
def get_transaction_detail(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        fraud_read_access
    ),
):
    tx = (
        db.query(Transaction)
        .filter(
            Transaction.id
            == transaction_id
        )
        .first()
    )

    if not tx:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Transaction not found.",
        )

    return tx


@router.patch(
    "/transactions/{transaction_id}/review",
    response_model=TransactionDetailOut,
)
async def review_transaction(
    transaction_id: str,
    payload: TransactionReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        fraud_analyze_access
    ),
):
    tx = (
        db.query(Transaction)
        .filter(
            Transaction.id
            == transaction_id
        )
        .first()
    )

    if not tx:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Transaction not found.",
        )

    allowed_statuses = {
        "pending": FraudStatus.pending,
        "flagged": FraudStatus.flagged,
        "cleared": FraudStatus.cleared,
        "investigating": (
            FraudStatus.investigating
        ),
    }

    requested_status = (
        payload.status.strip().lower()
    )

    if requested_status not in allowed_statuses:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Invalid status. Use pending, "
                "flagged, cleared, or "
                "investigating."
            ),
        )

    previous_status = (
        tx.status.value
        if tx.status
        else None
    )

    reviewer_name = user_display_name(
        current_user
    )

    tx.status = allowed_statuses[
        requested_status
    ]

    tx.analyst_notes = (
        payload.analyst_notes
    )

    tx.reviewed_by = reviewer_name
    tx.reviewed_at = func.now()

    create_audit_event(
        db=db,
        transaction_id=tx.id,
        action="Analyst review updated",
        status=requested_status,
        actor=reviewer_name,
        notes=(
            f"Status changed from "
            f"{previous_status} "
            f"to {requested_status}. "
            f"{payload.analyst_notes or ''}"
        ).strip(),
    )

    db.commit()
    db.refresh(tx)

    await fraud_ws_manager.broadcast(
        {
            "type": "transaction_review",
            "transaction_id": str(tx.id),
            "transaction_ref": (
                tx.transaction_ref
            ),
            "fraud_score": tx.fraud_score,
            "status": tx.status.value,
            "reviewed_by": tx.reviewed_by,
        }
    )

    return tx


@router.get("/stats")
def get_fraud_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        fraud_read_access
    ),
):
    total = db.query(
        Transaction
    ).count()

    flagged = (
        db.query(Transaction)
        .filter(
            Transaction.is_fraud.is_(True)
        )
        .count()
    )

    cleared = (
        db.query(Transaction)
        .filter(
            Transaction.status
            == FraudStatus.cleared
        )
        .count()
    )

    investigating = (
        db.query(Transaction)
        .filter(
            Transaction.status
            == FraudStatus.investigating
        )
        .count()
    )

    return {
        "total_transactions": total,
        "flagged_count": flagged,
        "fraud_rate": (
            round(
                flagged / total * 100,
                2,
            )
            if total
            else 0
        ),
        "cleared_count": cleared,
        "investigating_count": (
            investigating
        ),
    }