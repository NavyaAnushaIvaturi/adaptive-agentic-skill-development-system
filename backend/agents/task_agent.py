import json
from typing import Any

from backend.agents.resources_agent import (
    search_learning_resources,
)
from backend.utils.llm import get_llm


# Clean markdown formatting from LLM JSON output.
def clean_json(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        text = text.replace(
            "```json",
            "",
            1,
        )

        text = text.replace(
            "```",
            "",
        )

    return text.strip()


# Clean a list and keep only valid non-empty values.
def clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [
        str(item).strip()
        for item in value
        if str(item).strip()
    ]


# Create backup learning content when LLM generation fails.
def fallback_content(
    topic: str,
    daily_focus: str,
    remedial: bool,
) -> dict[str, Any]:

    return {
        "title": (
            "Review "
            if remedial
            else "Learn "
        ) + topic,

        "learning_content": (
            f"Study {daily_focus}. "
            "Build a clear understanding "
            "of the concept, connect it to "
            "the main topic, and explain it "
            "in your own words."
        ),

        "objectives": [
            (
                "Understand the main ideas "
                f"behind {daily_focus}."
            ),
            (
                "Explain the concept with "
                "a simple example."
            ),
            (
                "Apply the concept in a "
                "small practical exercise."
            ),
        ],

        "concepts": [
            daily_focus
        ],

        "examples": [
            (
                "Create one small example "
                "that demonstrates "
                f"{daily_focus}."
            )
        ],

        "steps": [
            "Read the concept carefully.",
            "Work through the example.",
            "Complete the practical exercise.",
            "Write down the main takeaway.",
        ],

        "practical_task": (
            f"Complete a small hands-on "
            f"exercise related to {daily_focus} "
            "and verify the result."
        ),

        "common_mistakes": [
            (
                "Memorizing terminology "
                "without understanding "
                "how the concept is used."
            ),
            (
                "Skipping the practical example."
            ),
        ],

        "key_takeaways": [
            (
                f"The main focus is {daily_focus}."
            ),
            (
                "Practice the concept before "
                "moving to the assessment."
            ),
        ],
    }


# Generate a complete daily learning activity using the LLM.
def generate_daily_activity(
    topic: str,
    day: int,
    daily_focus: str,
    mode: str = "general",
    project: str | None = None,
    remedial: bool = False,
    include_resources: bool = True,
) -> dict[str, Any]:

    activity_type = (
        "REMEDIAL"
        if remedial
        else "LEARNING"
    )

    prompt = f"""
You are an expert technical instructor
inside an adaptive learning platform.

Create ONE daily learning lesson.

Weekly topic:
{topic}

Day:
{day}

Daily focus:
{daily_focus}

Learning mode:
{mode}

Project:
{project or "None"}

Activity type:
{activity_type}

The learner needs useful teaching material
for this specific day's topic.

Return ONLY valid JSON:

{{
  "title": "lesson title",
  "learning_content": "Clear explanation of the day's topic.",
  "objectives": ["objective 1", "objective 2"],
  "concepts": ["concept 1", "concept 2"],
  "examples": ["example 1", "example 2"],
  "steps": ["step 1", "step 2"],
  "practical_task": "hands-on task",
  "common_mistakes": ["mistake 1"],
  "key_takeaways": ["takeaway 1"]
}}

Requirements:

- Teach the specified daily focus.
- Keep the content directly related to the topic.
- Explain what the concept is.
- Explain why it matters.
- Explain how it is used.
- Include useful technical examples.
- Include code examples when relevant.
- Include a practical hands-on task.
- Keep the lesson achievable in one session.
- Do not create a quiz.
- Do not introduce unrelated topics.
- Do not repeat unnecessary information.
- For remedial activities, focus on the learner's weak area.
- Match the learner's learning mode and level.
"""

    result = None

    try:
        # Get the configured language model.
        llm = get_llm()

        response = llm.invoke(prompt)

        result = json.loads(
            clean_json(
                response.content
            )
        )

    except Exception as exc:
        print(
            f"Daily activity generation failed: {exc}"
        )
        result = None

    # Create fallback content in case the LLM response is invalid.
    fallback = fallback_content(
        topic,
        daily_focus,
        remedial,
    )

    if not isinstance(
        result,
        dict,
    ):
        result = fallback

    # Fill missing or invalid fields with fallback values.
    for key, fallback_value in fallback.items():

        value = result.get(key)

        if key in {
            "title",
            "learning_content",
            "practical_task",
        }:

            if (
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
            ):
                result[key] = fallback_value

        else:

            if (
                not isinstance(
                    value,
                    list,
                )
                or not value
            ):
                result[key] = fallback_value

    # =====================================================
    # RESOURCES
    # Exactly TWO resources maximum.
    # =====================================================

    resources = []

    if include_resources:

        try:

            resources = search_learning_resources(
                topic=topic,
                daily_focus=daily_focus,
                max_results=2,
            )

        except Exception as exc:

            print(
                f"Resource search failed: {exc}"
            )

            resources = []

    # Extra safety:
    # Never return more than two resources.

    if not isinstance(
        resources,
        list,
    ):
        resources = []

    resources = resources[:2]

    return {

        "topic": topic,

        "day": day,

        "focus": daily_focus,

        "title": str(
            result["title"]
        ).strip(),

        "description": str(
            result["learning_content"]
        ).strip(),

        "learning_content": str(
            result["learning_content"]
        ).strip(),

        "objectives": clean_list(
            result["objectives"]
        ),

        "concepts": clean_list(
            result["concepts"]
        ),

        "examples": clean_list(
            result["examples"]
        ),

        "steps": clean_list(
            result["steps"]
        ),

        "practical_task": str(
            result["practical_task"]
        ).strip(),

        "common_mistakes": clean_list(
            result["common_mistakes"]
        ),

        "key_takeaways": clean_list(
            result["key_takeaways"]
        ),

        "resources": resources,

        "activity_type": activity_type,

        "status": "PENDING",

        "remedial": remedial,
    }