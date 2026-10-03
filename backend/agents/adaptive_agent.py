import json
from typing import Any

from backend.utils.llm import get_llm


# Decide whether the learner should advance or repeat practice.
def choose_adaptive_action(
    percentage: int,
    weak_topics: list[str],
) -> dict[str, Any]:

    # 100% is required to advance.
    if percentage == 100:
        action = "ADVANCE"
    else:
        action = "REMEDIAL"

    analysis = generate_analysis(
        percentage,
        weak_topics,
    )

    return {
        "action": action,
        "percentage": percentage,
        "weak_topics": weak_topics,
        "analysis": analysis,
    }


# Generate an explanation and recommendation for the assessment result.
def generate_analysis(
    percentage: int,
    weak_topics: list[str],
) -> dict[str, Any]:

    # A perfect score does not require remedial analysis.
    if percentage == 100:

        return {
            "summary": (
                "The learner achieved 100% "
                "and demonstrated sufficient "
                "understanding."
            ),
            "recommendation": (
                "Continue to the next weekly topic."
            ),
        }

    # If there are no identified weak topics,
    # still keep the learner in remedial mode
    # because the score was below 100%.
    if not weak_topics:

        return {
            "summary": (
                "The learner scored below 100% "
                "and needs additional practice "
                "before advancing."
            ),
            "recommendation": (
                "Review the assessment material "
                "and take the assessment again."
            ),
        }

    prompt = f"""
Analyze this learning assessment result.

Score: {percentage}%

Weak topics:
{weak_topics}

Return ONLY valid JSON:

{{
  "summary": "brief explanation of the learner's result",
  "recommendation": "what the learner should review"
}}

Rules:

- Do not calculate the score.
- Do not change the score.
- Do not decide whether the learner advances.
- Do not say that the learner passed unless the score is 100%.
- Focus only on the weak topics.
- Keep the recommendation practical.
"""

    try:

        # Get the configured language model.
        llm = get_llm()

        response = llm.invoke(
            prompt
        )

        content = response.content.strip()

        if content.startswith("```"):

            content = content.replace(
                "```json",
                "",
                1,
            )

            content = content.replace(
                "```",
                "",
            )

            content = content.strip()

        result = json.loads(
            content
        )

        return {
            "summary": result.get(
                "summary",
                "Additional practice is needed.",
            ),
            "recommendation": result.get(
                "recommendation",
                (
                    "Review the weak areas "
                    "and try the assessment again."
                ),
            ),
        }

    except Exception:

        # Return a fallback response if the LLM or JSON parsing fails.
        return {
            "summary": (
                "The learner scored below 100% "
                "and needs additional practice "
                "with "
                + ", ".join(weak_topics)
                + "."
            ),
            "recommendation": (
                "Review the weak areas and "
                "take the assessment again."
            ),
        }