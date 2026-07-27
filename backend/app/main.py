import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from slowapi import (
    _rate_limit_exceeded_handler,
)
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import (
    admin,
    auth,
    fraud,
    recruitment,
)
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security_headers import (
    SecurityHeadersMiddleware,
)
from app.db.database import Base, engine
from app.models.auth_audit_log import (
    AuthAuditLog,
)
from app.models.fraud import (
    Transaction,
    TransactionAuditEvent,
)
from app.models.password_reset_token import (
    PasswordResetToken,
)
from app.models.recruitment import (
    CVApplication,
    JobPost,
)
from app.models.refresh_token import (
    RefreshToken,
)
from app.models.user import User


logging.basicConfig(
    level=(
        logging.DEBUG
        if settings.DEBUG
        else logging.INFO
    ),
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger(
    __name__
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    logger.info(
        "Starting %s version %s in %s mode.",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )

    if settings.CREATE_DATABASE_TABLES:
        Base.metadata.create_all(
            bind=engine
        )

        logger.info(
            "Database tables verified."
        )

    yield

    engine.dispose()

    logger.info(
        "Database engine disposed."
    )


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered financial fraud "
        "detection and recruitment "
        "intelligence platform."
    ),
    docs_url=(
        "/docs"
        if settings.docs_enabled
        else None
    ),
    redoc_url=(
        "/redoc"
        if settings.docs_enabled
        else None
    ),
    openapi_url=(
        "/openapi.json"
        if settings.docs_enabled
        else None
    ),
    lifespan=lifespan,
)


app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


app.add_middleware(
    SecurityHeadersMiddleware,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.ALLOWED_ORIGINS
    ),
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
    ],
    expose_headers=[
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Retry-After",
    ],
)


app.include_router(
    auth.router,
    prefix="/api/v1",
)

app.include_router(
    fraud.router,
    prefix="/api/v1",
)

app.include_router(
    recruitment.router,
    prefix="/api/v1",
)

app.include_router(
    admin.router,
    prefix="/api/v1",
)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": (
            settings.ENVIRONMENT
        ),
        "status": "running",
        "docs": (
            "/docs"
            if settings.docs_enabled
            else None
        ),
    }


@app.get("/health")
def health():
    database_status = "healthy"

    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

    except SQLAlchemyError:
        logger.exception(
            "Database health check failed."
        )

        database_status = "unhealthy"

    overall_status = (
        "healthy"
        if database_status == "healthy"
        else "degraded"
    )

    return {
        "status": overall_status,
        "database": database_status,
        "environment": (
            settings.ENVIRONMENT
        ),
        "version": settings.APP_VERSION,
    }