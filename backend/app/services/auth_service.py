from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import jwt
from app.config import settings
from app.models.models import User
from app.models.models import User, RefreshToken
import hashlib
import secrets

password_hash = PasswordHash.recommended()

def register_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user is not None:
        raise ValueError("User with this email already exists")

    user = User(
        email=email,
        password_hash=hash_password(password),
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user




def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, password_hash_value: str) -> bool:
    return password_hash.verify(password, password_hash_value)


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None or not verify_password(
        password,
        user.password_hash,
    ):
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("User account is inactive")

    return user

def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    

def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_refresh_token(db: Session, user_id: int) -> str:
    raw_token = secrets.token_urlsafe(48)

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=expires_at,
        revoked=False,
    )

    db.add(refresh_token)
    db.commit()

    return raw_token

def refresh_access_token(db: Session, raw_token: str) -> str:
    token_hash = hash_refresh_token(raw_token)

    refresh_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
        )
        .first()
    )

    if refresh_token is None:
        raise ValueError("Invalid refresh token")

    now = datetime.now()

    if refresh_token.expires_at <= now:
        raise ValueError("Refresh token has expired")

    user = db.query(User).filter(User.id == refresh_token.user_id).first()

    if user is None or not user.is_active:
        raise ValueError("User is not authorized")

    return create_access_token(user.id)


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    token_hash = hash_refresh_token(raw_token)

    refresh_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if refresh_token is None:
        raise ValueError("Invalid refresh token")

    refresh_token.revoked = True
    db.commit()