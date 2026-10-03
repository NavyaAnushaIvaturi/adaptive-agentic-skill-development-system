from pydantic import BaseModel, Field


# Validate the data required to create a new user account.
class SignUpRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: str = Field(
        min_length=5,
        max_length=255,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )


# Validate the data required for user login.
class LoginRequest(BaseModel):
    email: str = Field(
        min_length=5,
        max_length=255,
    )

    password: str = Field(
        min_length=1,
        max_length=128,
    )


# Validate profile information when a user updates their profile.
class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    years_experience: int | None = Field(
        default=None,
        ge=0,
        le=60,
    )

    education: str | None = None

    current_role: str | None = None

    learning_preference: str | None = None

    preferred_difficulty: str | None = None

    interests: list[str] = Field(
        default_factory=list,
    )

    career_goal: str | None = None

    github_url: str | None = None

    linkedin_url: str | None = None

    portfolio_url: str | None = None

    bio: str | None = None


# Validate the information needed to start a learning session.
class LearningStartRequest(BaseModel):
    user_id: str | None = None

    mode: str = "general"

    goal: str

    current_level: str

    time_per_day: int = Field(
        gt=0,
    )

    duration_days: int = Field(
        gt=0,
    )

    preference: str | None = None

    role: str | None = None

    project: str | None = None

    current_skills: list[str] = Field(
        default_factory=list,
    )

    required_skills: list[str] = Field(
        default_factory=list,
    )

    required_technologies: list[str] = Field(
        default_factory=list,
    )

    deadline: str | None = None

    profile: dict = Field(
        default_factory=dict,
    )


# Validate the user's decision to approve a roadmap.
class RoadmapApprovalRequest(BaseModel):
    approved: bool


# Validate whether a learning activity was completed.
class ActivityCompletionRequest(BaseModel):
    completed: bool = True


# Validate the answers submitted for a quiz.
class QuizSubmissionRequest(BaseModel):
    answers: list[str]