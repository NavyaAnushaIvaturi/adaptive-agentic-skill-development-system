from typing import Any


# Analyze and organize the learner's background and learning requirements.
def analyze_context(
    goal: str,
    current_level: str,
    time_per_day: int,
    duration_days: int,
    preference: str | None = None,
    mode: str = "general",
    role: str | None = None,
    project: str | None = None,
    deadline: str | None = None,
    current_skills: list[str] | None = None,
    required_skills: list[str] | None = None,
    required_technologies: list[str] | None = None,
) -> dict[str, Any]:

    current_skills = (
        current_skills or []
    )

    required_skills = (
        required_skills or []
    )

    required_technologies = (
        required_technologies or []
    )

    is_project_mode = (
        mode == "project-oriented"
    )

    return {
        "mode": mode,

        "is_project_mode": (
            is_project_mode
        ),

        "goal": goal,

        "current_level": (
            current_level
        ),

        "time_per_day": (
            time_per_day
        ),

        "duration_days": (
            duration_days
        ),

        "preference": preference,

        "role": role,

        "project": project,

        "deadline": deadline,

        "current_skills": (
            current_skills
        ),

        "required_skills": (
            required_skills
        ),

        "required_technologies": (
            required_technologies
        ),
    }