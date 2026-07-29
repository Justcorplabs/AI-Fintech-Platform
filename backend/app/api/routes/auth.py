import secrets
from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select, update
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.rate_limit import (
    AUTH_FORGOT_PASSWORD_LIMIT,
    AUTH_LOGIN_LIMIT,
    AUTH_REFRESH_LIMIT,
    AUTH_REGISTER_LIMIT,
    AUTH_RESET_PASSWORD_LIMIT,
    limiter,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.db.database import get_db
from app.models.password_reset_token import (
    PasswordResetToken,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LogoutAllResponse,
    LogoutRequest,
    PasswordResetResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.services.auth_audit import (
    create_auth_audit_log,
    create_user_auth_audit_log,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


INVALID_LOGIN_MESSAGE = (
    "Invalid email or password."
)


def get_role_value(user: User) -> str:
    """
    Return the user's role as a plain string.
    """
    return (
        user.role.value
        if hasattr(user.role, "value")
        else str(user.role)
    )


def ensure_timezone_aware(
    value: datetime | None,
) -> datetime | None:
    """
    Ensure a database datetime can safely be compared
    with timezone-aware UTC datetimes.
    """
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def create_token_pair(
    user: User,
) -> tuple[str, str]:
    """
    Generate a new access-token and refresh-token pair.
    """
    role = get_role_value(user)

    token_payload = {
        "sub": str(user.id),
        "role": role,
    }

    access_token = create_access_token(
        token_payload
    )

    refresh_token = create_refresh_token(
        token_payload
    )

    return access_token, refresh_token


def save_refresh_token(
    db: Session,
    user: User,
    refresh_token: str,
) -> RefreshToken:
    """
    Store the hashed refresh token in the database.
    """
    payload = decode_refresh_token(
        refresh_token
    )

    expires_at = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc,
    )

    token_record = RefreshToken(
        user_id=user.id,
        jti=payload["jti"],
        token_hash=hash_token(
            refresh_token
        ),
        expires_at=expires_at,
    )

    db.add(token_record)

    return token_record


def build_token_response(
    access_token: str,
    refresh_token: str,
) -> Token:
    """
    Build the standard authentication response.
    """
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=(
            settings.ACCESS_TOKEN_EXPIRE_MINUTES
            * 60
        ),
        refresh_expires_in=(
            settings.REFRESH_TOKEN_EXPIRE_DAYS
            * 24
            * 60
            * 60
        ),
    )


def revoke_user_refresh_tokens(
    db: Session,
    user_id,
    revoked_at: datetime,
) -> int:
    """
    Revoke every active refresh token belonging to a user.
    """
    result = db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(
            revoked_at=revoked_at
        )
    )

    return result.rowcount or 0


def reset_login_security_state(
    user: User,
) -> None:
    """
    Clear failed-attempt and account-lock information.
    """
    user.failed_login_attempts = 0
    user.locked_until = None


def register_failed_login(
    user: User,
    current_time: datetime,
) -> bool:
    """
    Record a failed login attempt.

    Returns True when the attempt causes the account
    to become temporarily locked.
    """
    current_attempts = (
        user.failed_login_attempts or 0
    )

    user.failed_login_attempts = (
        current_attempts + 1
    )

    if (
        user.failed_login_attempts
        >= settings.FAILED_LOGIN_MAX_ATTEMPTS
    ):
        user.locked_until = (
            current_time
            + timedelta(
                minutes=(
                    settings
                    .ACCOUNT_LOCKOUT_MINUTES
                )
            )
        )

        return True

    return False


def is_account_locked(
    user: User,
    current_time: datetime,
) -> bool:
    """
    Check whether the user is currently locked.

    Expired locks are cleared automatically.
    """
    locked_until = ensure_timezone_aware(
        user.locked_until
    )

    if locked_until is None:
        return False

    if locked_until > current_time:
        return True

    reset_login_security_state(user)

    return False


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(AUTH_REGISTER_LIMIT)
def register(
    request: Request,
    response: Response,
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    email = str(
        payload.email
    ).strip().lower()

    existing_user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_user is not None:
        create_user_auth_audit_log(
            db=db,
            event_type="register_duplicate",
            success=False,
            user=existing_user,
            request=request,
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration rejected because the email already exists.",
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An account with this email "
                "already exists."
            ),
        )

    user = User(
        email=email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(
            payload.password
        ),
        organisation=payload.organisation,
        failed_login_attempts=0,
        locked_until=None,
    )

    try:
        db.add(user)
        db.flush()

        create_user_auth_audit_log(
            db=db,
            event_type="register_success",
            success=True,
            user=user,
            request=request,
            status_code=status.HTTP_201_CREATED,
            detail="User account created successfully.",
        )

        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An account with this email "
                "already exists."
            ),
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The account could not be created."
            ),
        )

    return user


@router.post(
    "/login",
    response_model=Token,
)
@limiter.limit(AUTH_LOGIN_LIMIT)
def login(
    request: Request,
    response: Response,
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    email = str(
        payload.email
    ).strip().lower()

    current_time = datetime.now(
        timezone.utc
    )

    try:
        user = db.scalar(
            select(User)
            .where(
                User.email == email
            )
            .with_for_update()
        )

        if user is None:
            create_auth_audit_log(
                db=db,
                event_type="login_failed",
                success=False,
                request=request,
                email=email,
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login failed because the email was not recognised.",
            )
            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail=INVALID_LOGIN_MESSAGE,
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )

        if is_account_locked(
            user=user,
            current_time=current_time,
        ):
            create_user_auth_audit_log(
                db=db,
                event_type="login_blocked_locked",
                success=False,
                user=user,
                request=request,
                status_code=status.HTTP_423_LOCKED,
                detail="Login blocked because the account is temporarily locked.",
            )
            db.commit()

            locked_until = ensure_timezone_aware(
                user.locked_until
            )

            retry_after = (
                max(
                    1,
                    int(
                        (
                            locked_until
                            - current_time
                        ).total_seconds()
                    ),
                )
                if locked_until is not None
                else 1
            )

            raise HTTPException(
                status_code=(
                    status.HTTP_423_LOCKED
                ),
                detail=(
                    "The account is temporarily "
                    "locked because of repeated "
                    "failed login attempts. "
                    "Please try again later."
                ),
                headers={
                    "Retry-After": str(
                        retry_after
                    )
                },
            )

        password_is_valid = verify_password(
            payload.password,
            user.hashed_password,
        )

        if not password_is_valid:
            account_was_locked = (
                register_failed_login(
                    user=user,
                    current_time=current_time,
                )
            )

            create_user_auth_audit_log(
                db=db,
                event_type=(
                    "account_locked"
                    if account_was_locked
                    else "login_failed"
                ),
                success=False,
                user=user,
                request=request,
                status_code=(
                    status.HTTP_423_LOCKED
                    if account_was_locked
                    else status.HTTP_401_UNAUTHORIZED
                ),
                detail=(
                    "Account locked after repeated failed login attempts."
                    if account_was_locked
                    else "Login failed because the password was invalid."
                ),
            )

            db.commit()

            if account_was_locked:
                raise HTTPException(
                    status_code=(
                        status.HTTP_423_LOCKED
                    ),
                    detail=(
                        "The account is temporarily "
                        "locked because of repeated "
                        "failed login attempts. "
                        "Please try again later."
                    ),
                    headers={
                        "Retry-After": str(
                            settings
                            .ACCOUNT_LOCKOUT_MINUTES
                            * 60
                        )
                    },
                )

            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail=INVALID_LOGIN_MESSAGE,
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )

        if not user.is_active:
            create_user_auth_audit_log(
                db=db,
                event_type="login_blocked_disabled",
                success=False,
                user=user,
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Login blocked because the account is disabled.",
            )
            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "This account has been disabled."
                ),
            )

        reset_login_security_state(user)

        access_token, refresh_token = (
            create_token_pair(user)
        )

        save_refresh_token(
            db=db,
            user=user,
            refresh_token=refresh_token,
        )

        create_user_auth_audit_log(
            db=db,
            event_type="login_success",
            success=True,
            user=user,
            request=request,
            status_code=status.HTTP_200_OK,
            detail="Login completed and a new session was created.",
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The login session could not "
                "be created."
            ),
        )

    return build_token_response(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=Token,
)
@limiter.limit(AUTH_REFRESH_LIMIT)
def refresh_access_token(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    try:
        token_payload = decode_refresh_token(
            payload.refresh_token
        )

    except InvalidTokenError:
        create_auth_audit_log(
            db=db,
            event_type="refresh_failed",
            success=False,
            request=request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh failed because the token was invalid or expired.",
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "The refresh token is invalid "
                "or has expired."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    refresh_token_hash = hash_token(
        payload.refresh_token
    )

    current_time = datetime.now(
        timezone.utc
    )

    try:
        stored_token = db.scalar(
            select(RefreshToken)
            .where(
                RefreshToken.token_hash
                == refresh_token_hash,
                RefreshToken.jti
                == token_payload["jti"],
                RefreshToken.user_id
                == token_payload["sub"],
            )
            .with_for_update()
        )

        if stored_token is None:
            create_auth_audit_log(
                db=db,
                event_type="refresh_failed",
                success=False,
                request=request,
                user_id=token_payload.get("sub"),
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token was not recognised.",
            )
            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail=(
                    "The refresh token is "
                    "not recognised."
                ),
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )

        if stored_token.revoked_at is not None:
            create_auth_audit_log(
                db=db,
                event_type="refresh_failed",
                success=False,
                request=request,
                user_id=stored_token.user_id,
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token had already been revoked.",
            )
            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail=(
                    "The refresh token has "
                    "already been revoked."
                ),
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )

        stored_expiry = ensure_timezone_aware(
            stored_token.expires_at
        )

        if (
            stored_expiry is None
            or stored_expiry <= current_time
        ):
            stored_token.revoked_at = (
                current_time
            )

            create_auth_audit_log(
                db=db,
                event_type="refresh_failed",
                success=False,
                request=request,
                user_id=stored_token.user_id,
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired and was revoked.",
            )

            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail=(
                    "The refresh token has expired."
                ),
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )

        user = db.scalar(
            select(User)
            .where(
                User.id == token_payload["sub"]
            )
            .with_for_update()
        )

        if user is None:
            stored_token.revoked_at = (
                current_time
            )

            create_auth_audit_log(
                db=db,
                event_type="refresh_failed",
                success=False,
                request=request,
                user_id=stored_token.user_id,
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh failed because the linked account no longer exists.",
            )

            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail=(
                    "The account linked to this "
                    "session no longer exists."
                ),
            )

        if not user.is_active:
            stored_token.revoked_at = (
                current_time
            )

            create_user_auth_audit_log(
                db=db,
                event_type="refresh_blocked_disabled",
                success=False,
                user=user,
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Refresh blocked because the account is disabled.",
            )

            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "This account has been disabled."
                ),
            )

        if is_account_locked(
            user=user,
            current_time=current_time,
        ):
            stored_token.revoked_at = (
                current_time
            )

            create_user_auth_audit_log(
                db=db,
                event_type="refresh_blocked_locked",
                success=False,
                user=user,
                request=request,
                status_code=status.HTTP_423_LOCKED,
                detail="Refresh blocked because the account is temporarily locked.",
            )

            db.commit()

            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=(
                    "The account is temporarily "
                    "locked."
                ),
            )

        new_access_token, new_refresh_token = (
            create_token_pair(user)
        )

        new_refresh_payload = (
            decode_refresh_token(
                new_refresh_token
            )
        )

        stored_token.revoked_at = (
            current_time
        )

        stored_token.replaced_by_jti = (
            new_refresh_payload["jti"]
        )

        save_refresh_token(
            db=db,
            user=user,
            refresh_token=new_refresh_token,
        )

        create_user_auth_audit_log(
            db=db,
            event_type="refresh_success",
            success=True,
            user=user,
            request=request,
            status_code=status.HTTP_200_OK,
            detail="Session refreshed and refresh token rotated successfully.",
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The session could not "
                "be refreshed."
            ),
        )

    return build_token_response(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: Request,
    payload: LogoutRequest,
    db: Session = Depends(get_db),
):
    refresh_token_hash = hash_token(
        payload.refresh_token
    )

    current_time = datetime.now(
        timezone.utc
    )

    try:
        stored_token = db.scalar(
            select(RefreshToken)
            .where(
                RefreshToken.token_hash
                == refresh_token_hash
            )
            .with_for_update()
        )

        if (
            stored_token is not None
            and stored_token.revoked_at is None
        ):
            stored_token.revoked_at = (
                current_time
            )

        create_auth_audit_log(
            db=db,
            event_type="logout",
            success=True,
            request=request,
            user_id=(
                stored_token.user_id
                if stored_token is not None
                else None
            ),
            status_code=status.HTTP_204_NO_CONTENT,
            detail=(
                "Refresh-token session revoked."
                if stored_token is not None
                else "Logout request completed without a matching session."
            ),
        )

        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The session could not "
                "be logged out."
            ),
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/logout-all",
    response_model=LogoutAllResponse,
)
def logout_all_sessions(
    request: Request,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    current_time = datetime.now(
        timezone.utc
    )

    try:
        revoked_sessions = (
            revoke_user_refresh_tokens(
                db=db,
                user_id=current_user.id,
                revoked_at=current_time,
            )
        )

        create_user_auth_audit_log(
            db=db,
            event_type="logout_all",
            success=True,
            user=current_user,
            request=request,
            status_code=status.HTTP_200_OK,
            detail=f"Revoked {revoked_sessions} active refresh-token session(s).",
        )

        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The account sessions could not "
                "be revoked."
            ),
        )

    return LogoutAllResponse(
        message=(
            "All refresh-token sessions "
            "have been revoked."
        ),
        revoked_sessions=revoked_sessions,
    )


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
@limiter.limit(AUTH_FORGOT_PASSWORD_LIMIT)
def forgot_password(
    request: Request,
    response: Response,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    generic_message = (
        "If an active account exists for this email, "
        "password-reset instructions have been created."
    )

    email = str(
        payload.email
    ).strip().lower()

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if user is None or not user.is_active:
        create_auth_audit_log(
            db=db,
            event_type="forgot_password_requested",
            success=True,
            request=request,
            user_id=(user.id if user is not None else None),
            email=email,
            status_code=status.HTTP_200_OK,
            detail=(
                "Generic password-reset response returned. "
                "No active account was confirmed."
            ),
        )
        db.commit()

        return ForgotPasswordResponse(
            message=generic_message
        )

    current_time = datetime.now(
        timezone.utc
    )

    expires_at = (
        current_time
        + timedelta(
            minutes=(
                settings
                .PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
            )
        )
    )

    raw_reset_token = secrets.token_urlsafe(
        48
    )

    reset_token_hash = hash_token(
        raw_reset_token
    )

    try:
        db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id
                == user.id,
                PasswordResetToken.used_at.is_(
                    None
                ),
            )
            .values(
                used_at=current_time
            )
        )

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=reset_token_hash,
            expires_at=expires_at,
        )

        db.add(reset_record)

        create_user_auth_audit_log(
            db=db,
            event_type="forgot_password_requested",
            success=True,
            user=user,
            request=request,
            status_code=status.HTTP_200_OK,
            detail="A new password-reset token was created.",
        )

        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The password-reset request "
                "could not be processed."
            ),
        )

    if settings.is_production:
        return ForgotPasswordResponse(
            message=generic_message
        )

    reset_url = (
        f"{settings.FRONTEND_URL}/reset-password"
        f"?token={raw_reset_token}"
    )

    return ForgotPasswordResponse(
        message=generic_message,
        reset_token=raw_reset_token,
        reset_url=reset_url,
        expires_in=(
            settings
            .PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
            * 60
        ),
    )


@router.post(
    "/reset-password",
    response_model=PasswordResetResponse,
)
@limiter.limit(AUTH_RESET_PASSWORD_LIMIT)
def reset_password(
    request: Request,
    response: Response,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    current_time = datetime.now(
        timezone.utc
    )

    reset_token_hash = hash_token(
        payload.token
    )

    try:
        reset_record = db.scalar(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash
                == reset_token_hash
            )
            .with_for_update()
        )

        if reset_record is None:
            create_auth_audit_log(
                db=db,
                event_type="password_reset_failed",
                success=False,
                request=request,
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password-reset token was invalid or not recognised.",
            )
            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "The password-reset token is "
                    "invalid or has expired."
                ),
            )

        if reset_record.used_at is not None:
            create_auth_audit_log(
                db=db,
                event_type="password_reset_failed",
                success=False,
                request=request,
                user_id=reset_record.user_id,
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password-reset token had already been used.",
            )
            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "The password-reset token has "
                    "already been used."
                ),
            )

        reset_expiry = ensure_timezone_aware(
            reset_record.expires_at
        )

        if (
            reset_expiry is None
            or reset_expiry <= current_time
        ):
            reset_record.used_at = (
                current_time
            )

            create_auth_audit_log(
                db=db,
                event_type="password_reset_failed",
                success=False,
                request=request,
                user_id=reset_record.user_id,
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password-reset token expired.",
            )

            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "The password-reset token "
                    "has expired."
                ),
            )

        user = db.scalar(
            select(User)
            .where(
                User.id == reset_record.user_id
            )
            .with_for_update()
        )

        if user is None or not user.is_active:
            reset_record.used_at = (
                current_time
            )

            create_auth_audit_log(
                db=db,
                event_type="password_reset_failed",
                success=False,
                request=request,
                user_id=reset_record.user_id,
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset failed because the linked account was unavailable.",
            )

            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "The password-reset token is "
                    "invalid or has expired."
                ),
            )

        if verify_password(
            payload.new_password,
            user.hashed_password,
        ):
            create_user_auth_audit_log(
                db=db,
                event_type="password_reset_failed",
                success=False,
                user=user,
                request=request,
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password matched the current password.",
            )
            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "The new password must be "
                    "different from the current "
                    "password."
                ),
            )

        user.hashed_password = (
            get_password_hash(
                payload.new_password
            )
        )

        reset_login_security_state(user)

        reset_record.used_at = (
            current_time
        )

        db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id
                == user.id,
                PasswordResetToken.used_at.is_(
                    None
                ),
            )
            .values(
                used_at=current_time
            )
        )

        revoked_sessions = (
            revoke_user_refresh_tokens(
                db=db,
                user_id=user.id,
                revoked_at=current_time,
            )
        )

        create_user_auth_audit_log(
            db=db,
            event_type="password_reset_success",
            success=True,
            user=user,
            request=request,
            status_code=status.HTTP_200_OK,
            detail=(
                f"Password reset completed and {revoked_sessions} "
                "refresh-token session(s) were revoked."
            ),
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The password could not be reset."
            ),
        )

    return PasswordResetResponse(
        message=(
            "Password reset successful. "
            "Please sign in using the new password."
        ),
        revoked_sessions=revoked_sessions,
    )


@router.get(
    "/me",
    response_model=UserOut,
)
def get_authenticated_user(
    current_user: User = Depends(
        get_current_user
    ),
):
    return current_user