import secrets
import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import AuthToken, User
from backend.utils.auth import (
    create_session_token,
    get_current_user,
    hash_password,
    verify_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# =========================================================
# REQUEST SCHEMAS
# =========================================================
# Define request data for signup and login.


class SignUpRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# =========================================================
# RESPONSE HELPER
# =========================================================
# Prepare user data for API responses.


def user_response(
    user: User,
    access_token: str | None = None,
) -> dict:
    """
    Return only account/authentication information.

    Learning setup information is NOT stored as a
    separate profile anymore.
    """

    response = {
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
    }

    if access_token:
        response["access_token"] = access_token
        response["token_type"] = "bearer"

    return response


# =========================================================
# SIGNUP
# =========================================================
# Create a new user account and login session.


@router.post("/signup")
def signup(
    request: SignUpRequest,
    db: Session = Depends(get_db),
):
    email = request.email.strip().lower()

    # -----------------------------------------------------
    # Check existing account
    # -----------------------------------------------------

    existing = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "An account with this "
                "email already exists."
            ),
        )

    # -----------------------------------------------------
    # Validate password
    # -----------------------------------------------------

    password = request.password.strip()

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail=(
                "Password must be at least "
                "8 characters long."
            ),
        )

    # -----------------------------------------------------
    # Validate name
    # -----------------------------------------------------

    full_name = request.full_name.strip()

    if not full_name:
        raise HTTPException(
            status_code=400,
            detail="Full name is required.",
        )

    # -----------------------------------------------------
    # Create user
    # -----------------------------------------------------

    user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(
            password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # -----------------------------------------------------
    # Create login session
    # -----------------------------------------------------

    access_token = create_session_token(
        db=db,
        user_id=user.id,
    )

    return user_response(
        user,
        access_token=access_token,
    )


# =========================================================
# LOGIN
# =========================================================
# Authenticate an existing user and create a session.


@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    email = request.email.strip().lower()

    user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # -----------------------------------------------------
    # Create new session
    # -----------------------------------------------------

    access_token = create_session_token(
        db=db,
        user_id=user.id,
    )

    return user_response(
        user,
        access_token=access_token,
    )


# =========================================================
# LOGOUT
# =========================================================
# Remove the current authentication session.


@router.post("/logout")
def logout(
    authorization: str | None = Header(
        default=None
    ),
    db: Session = Depends(get_db),
):
    if not authorization:
        return {
            "message": "Logged out successfully."
        }

    if not authorization.lower().startswith(
        "bearer "
    ):
        return {
            "message": "Logged out successfully."
        }

    token = authorization.split(
        " ",
        1,
    )[1].strip()

    if token:
        auth_token = (
            db.query(AuthToken)
            .filter(
                AuthToken.token == token
            )
            .first()
        )

        if auth_token:
            db.delete(auth_token)
            db.commit()

    return {
        "message": "Logged out successfully."
    }


# =========================================================
# CURRENT USER
# =========================================================
# Get details of the currently logged-in user.


@router.get("/me")
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):
    return user_response(
        current_user
    )