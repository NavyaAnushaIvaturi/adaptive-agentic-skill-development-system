from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.database import Base


# Store user account and learning profile information.
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    current_role: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    years_experience: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    education: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    learning_style: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    preferred_difficulty: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    interests: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    career_goal: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    github_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    linkedin_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    portfolio_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# Store authentication tokens for logged-in users.
class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    token: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


# Store the main learning session and its current state.
class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    goal: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    current_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    time_per_day: Mapped[int] = mapped_column(
        nullable=False,
    )

    duration_days: Mapped[int] = mapped_column(
        nullable=False,
    )

    preference: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    role: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    project: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    deadline: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="STARTED",
    )

    state_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    activities: Mapped[list["LearningActivity"]] = relationship(
        back_populates="learning_session",
        cascade="all, delete-orphan",
    )


# Connect users with their learning sessions.
class UserLearningSession(Base):
    __tablename__ = "user_learning_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    learning_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "learning_sessions.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


# Store daily learning activities for each session.
class LearningActivity(Base):
    __tablename__ = "learning_activities"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    learning_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "learning_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    week: Mapped[int] = mapped_column(
        nullable=False,
    )

    day: Mapped[int] = mapped_column(
        nullable=False,
    )

    topic: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="LEARNING",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    learning_session: Mapped["LearningSession"] = relationship(
        back_populates="activities",
    )