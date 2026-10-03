from typing import Any


# Normalize a skill name for consistent comparison.
def normalize_skill(value: str) -> str:
    return " ".join(
        value.strip().lower().split()
    )


# Compare current skills with required skills and find the skill gaps.
def analyze_skill_gap(
    current_skills: list[str],
    required_skills: list[str],
    required_technologies: list[str] | None = None,
) -> dict[str, Any]:

    required_technologies = required_technologies or []

    # ---------------------------------------------------------
    # CLEAN CURRENT SKILLS
    # ---------------------------------------------------------
    current = [
        skill.strip()
        for skill in current_skills
        if isinstance(skill, str)
        and skill.strip()
    ]

    # ---------------------------------------------------------
    # CLEAN REQUIRED SKILLS
    # ---------------------------------------------------------
    required = [
        skill.strip()
        for skill in required_skills
        if isinstance(skill, str)
        and skill.strip()
    ]

    # ---------------------------------------------------------
    # CLEAN REQUIRED TECHNOLOGIES
    # ---------------------------------------------------------
    technologies = [
        technology.strip()
        for technology in required_technologies
        if isinstance(technology, str)
        and technology.strip()
    ]

    # ---------------------------------------------------------
    # COMBINE REQUIREMENTS
    # ---------------------------------------------------------
    # A skill/technology should appear only once.
    combined_required = []
    seen_required = set()

    for item in required + technologies:

        normalized = normalize_skill(item)

        if normalized not in seen_required:
            seen_required.add(normalized)
            combined_required.append(item)

    # ---------------------------------------------------------
    # NORMALIZE CURRENT SKILLS
    # ---------------------------------------------------------
    normalized_current = {
        normalize_skill(skill)
        for skill in current
    }

    # ---------------------------------------------------------
    # FIND MATCHED AND MISSING SKILLS
    # ---------------------------------------------------------
    matched_skills = []
    missing_skills = []
    priorities = []

    for skill in combined_required:

        normalized_skill = normalize_skill(skill)

        if normalized_skill in normalized_current:

            # Learner already knows this skill.
            matched_skills.append(skill)

        else:

            # Learner does not currently have this skill.
            missing_skills.append(skill)

            priorities.append(
                {
                    "skill": skill,
                    "priority": "HIGH",
                    "reason": (
                        "Required skill or technology is not "
                        "present in the learner's provided skills."
                    ),
                }
            )

    # ---------------------------------------------------------
    # GAP STATISTICS
    # ---------------------------------------------------------
    total_required = len(combined_required)
    total_missing = len(missing_skills)

    if total_required:
        gap_percentage = round(
            (total_missing / total_required) * 100
        )
    else:
        gap_percentage = 0

    # ---------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------
    return {
        "current_skills": current,
        "required_skills": combined_required,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "priorities": priorities,
        "total_required": total_required,
        "total_missing": total_missing,
        "gap_percentage": gap_percentage,
    }