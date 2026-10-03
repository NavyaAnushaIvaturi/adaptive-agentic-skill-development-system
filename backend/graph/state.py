from typing import Any, TypedDict


# Define the data structure used to store the learning workflow state.
class LearningState(TypedDict, total=False):
    learning_id: str

    mode: str
    goal: str
    current_level: str
    time_per_day: int
    duration_days: int
    preference: str | None

    role: str | None
    project: str | None
    deadline: str | None

    current_skills: list[str]
    acquired_skills: list[str]
    required_skills: list[str]
    required_technologies: list[str]

    context: dict[str, Any]
    skill_gap: dict[str, Any]

    roadmap: dict[str, Any]
    roadmap_approved: bool

    current_week: int
    current_day: int
    current_topic: dict[str, Any]

    current_activity: dict[str, Any]
    activity_completed: bool

    assessment: dict[str, Any]
    answers: list[Any]

    evaluation: dict[str, Any]
    adaptive_action: dict[str, Any]

    remedial: bool
    status: str