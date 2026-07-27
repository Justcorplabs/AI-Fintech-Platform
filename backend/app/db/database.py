from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def build_engine() -> Engine:
    engine_options = {
        "pool_pre_ping": settings.DATABASE_POOL_PRE_PING,
    }

    if settings.DATABASE_URL.startswith("sqlite"):
        engine_options["connect_args"] = {
            "check_same_thread": False,
        }
    else:
        engine_options.update(
            {
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
                "pool_recycle": settings.DATABASE_POOL_RECYCLE_SECONDS,
            }
        )

    return create_engine(
        settings.DATABASE_URL,
        **engine_options,
    )


engine = build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()