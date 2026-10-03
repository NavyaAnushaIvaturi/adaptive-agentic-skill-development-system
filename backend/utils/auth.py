import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import AuthToken, User


PBKDF2_ITERATIONS = 310_000


# Create a secure password hash using a random salt.
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    return (
        f"pbkdf2_sha256$"
        f"{PBKDF2_ITERATIONS}$"
        f"{salt.hex()}$"
        f"{digest.hex()}"
    )


# Check whether a password matches its stored hash.
def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)

        if algorithm != "pbkdf2_sha256":
            return False

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )

        return hmac.compare_digest(
            digest.hex(),
            digest_hex,
        )

    except Exception:
        return False


def create_session_token(
    db: Session,
    user_id: str,
) -> str:
    """
    Create and persist a session token for the authenticated user.
    """

    # Generate and save a secure login session token.
    token = secrets.token_urlsafe(48)

    auth_token = AuthToken(
        token=token,
        user_id=user_id,
    )

    db.add(auth_token)
    db.commit()

    return token


# Backward-compatible alias.
# Some existing code may still call create_token().
def create_token(
    db: Session,
    user_id: str,
) -> str:
    return create_session_token(
        db=db,
        user_id=user_id,
    )


# Define Bearer token authentication for protected API endpoints.
security = HTTPBearer(
    auto_error=False,
)


# Find the user from an optional Bearer authentication token.
def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> User | None:

    if not credentials:
        return None

    token = credentials.credentials.strip()

    if not token:
        return None

    auth_token = (
        db.query(AuthToken)
        .filter(
            AuthToken.token == token,
        )
        .first()
    )

    if not auth_token:
        return None

    return (
        db.query(User)
        .filter(
            User.id == auth_token.user_id,
        )
        .first()
    )


# Require a valid authenticated user for protected API routes.
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
    db: Session = Depends(get_db),
) -> User:

    user = get_optional_user(
        credentials=credentials,
        db=db,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return user