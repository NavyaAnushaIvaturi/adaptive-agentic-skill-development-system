import json
from typing import Any

from backend.utils.llm import get_llm


# Clean markdown formatting from LLM JSON output.
def clean_json(
    content: str,
) -> str:

    content = content.strip()

    if content.startswith("```json"):
        content = content[
            len("```json"):
        ]

    elif content.startswith("```"):
        content = content[
            len("```"):
        ]

    if content.endswith("```"):
        content = content[
            :-len("```")
        ]

    return content.strip()


# Normalize text for reliable comparison.
def normalize_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return " ".join(
        str(value)
        .strip()
        .casefold()
        .split()
    )


# Validate a generated assessment question.
def validate_question(
    question: Any,
    topic: str,
) -> dict[str, Any] | None:

    if not isinstance(
        question,
        dict,
    ):
        return None

    text = question.get(
        "question"
    )

    options = question.get(
        "options"
    )

    correct = question.get(
        "correct_answer"
    )

    # -------------------------------------------------
    # Basic validation
    # -------------------------------------------------

    if not isinstance(
        text,
        str,
    ):
        return None

    if not text.strip():
        return None

    if not isinstance(
        options,
        list,
    ):
        return None

    if len(options) != 4:
        return None

    if not all(
        isinstance(
            option,
            str,
        )
        and option.strip()
        for option in options
    ):
        return None

    if not isinstance(
        correct,
        str,
    ):
        return None

    if not correct.strip():
        return None

    # -------------------------------------------------
    # Correct answer must match one option
    # -------------------------------------------------

    normalized_correct = normalize_text(
        correct
    )

    normalized_options = [
        normalize_text(option)
        for option in options
    ]

    if normalized_correct not in normalized_options:
        return None

    # -------------------------------------------------
    # Prevent duplicate options
    # -------------------------------------------------

    if len(
        set(normalized_options)
    ) != 4:
        return None

    return {
        "question": text.strip(),

        "options": [
            option.strip()
            for option in options
        ],

        "correct_answer": correct.strip(),

        "topic": topic,
    }


# Create backup questions when the LLM does not generate enough valid questions.
def fallback_questions(
    topic: str,
) -> list[dict[str, Any]]:

    questions = [

        {
            "question": (
                f"What is the main purpose "
                f"of learning {topic}?"
            ),

            "options": [
                f"To understand and use {topic}",
                "To avoid the technology",
                "To remove all testing",
                "To ignore practical work",
            ],

            "correct_answer":
                f"To understand and use {topic}",
        },

        {
            "question": (
                f"Which approach best supports "
                f"learning {topic}?"
            ),

            "options": [
                "Combining explanation with practice",
                "Only memorizing terms",
                "Never running examples",
                "Avoiding documentation",
            ],

            "correct_answer":
                "Combining explanation with practice",
        },

        {
            "question": (
                f"How can a learner check "
                f"understanding of {topic}?"
            ),

            "options": [
                "Apply the concept to an example",
                "Skip all examples",
                "Avoid using the concept",
                "Delete the practice work",
            ],

            "correct_answer":
                "Apply the concept to an example",
        },

        {
            "question": (
                f"What should a learner do "
                f"when confused about {topic}?"
            ),

            "options": [
                "Review the concept and practice again",
                "Ignore the problem",
                "Move to an unrelated topic",
                "Stop checking the result",
            ],

            "correct_answer":
                "Review the concept and practice again",
        },

        {
            "question": (
                f"What indicates practical "
                f"understanding of {topic}?"
            ),

            "options": [
                "Being able to use the concept correctly",
                "Only recognizing its name",
                "Avoiding implementation",
                "Skipping evaluation",
            ],

            "correct_answer":
                "Being able to use the concept correctly",
        },
    ]

    return [
        {
            **question,
            "topic": topic,
        }
        for question in questions
    ]


# Generate and validate a five-question topic assessment.
def create_assessment(
    topic: str,
    mode: str = "general",
    project: str | None = None,
) -> dict[str, Any]:

    prompt = f"""
Create a topic-ending assessment for:

{topic}

Requirements:

- Exactly 5 multiple-choice questions.
- Exactly 4 options per question.
- Exactly one correct answer.
- Correct answer must exactly match one option.
- Test understanding and practical knowledge.
- Cover different parts of the topic.
- Questions must be relevant to the topic.
- Questions should be appropriate for a software learner.
- Avoid generic questions when topic-specific questions are possible.
- Do not repeat questions.
- Do not mention the correct answer separately.
- Return ONLY valid JSON.
- No markdown.
- No explanation outside JSON.

Format:

{{
  "questions": [
    {{
      "question": "question",
      "options": [
        "option A",
        "option B",
        "option C",
        "option D"
      ],
      "correct_answer": "exact option"
    }}
  ]
}}
"""

    valid_questions: list[
        dict[str, Any]
    ] = []

    # =================================================
    # Generate assessment
    # =================================================

    try:

        # Get the configured language model.
        llm = get_llm()

        response = llm.invoke(
            prompt
        )

        content = response.content

        if not isinstance(
            content,
            str,
        ):
            content = str(
                content
            )

        content = clean_json(
            content
        )

        result = json.loads(
            content
        )

        questions = result.get(
            "questions",
            [],
        )

        if isinstance(
            questions,
            list,
        ):

            for question in questions:

                validated = (
                    validate_question(
                        question,
                        topic,
                    )
                )

                if validated is None:
                    continue

                # -----------------------------------------
                # Prevent duplicate questions
                # -----------------------------------------

                normalized_question = (
                    normalize_text(
                        validated[
                            "question"
                        ]
                    )
                )

                already_exists = any(
                    normalize_text(
                        existing[
                            "question"
                        ]
                    )
                    == normalized_question
                    for existing
                    in valid_questions
                )

                if already_exists:
                    continue

                valid_questions.append(
                    validated
                )

                if len(
                    valid_questions
                ) == 5:
                    break

    except Exception as exc:

        print(
            "Assessment generation failed:",
            exc,
        )

    # =================================================
    # If LLM produced fewer than 5 valid questions,
    # use fallback questions.
    # =================================================

    if len(
        valid_questions
    ) < 5:

        fallback = fallback_questions(
            topic
        )

        for question in fallback:

            if len(
                valid_questions
            ) >= 5:
                break

            normalized_question = (
                normalize_text(
                    question[
                        "question"
                    ]
                )
            )

            already_exists = any(
                normalize_text(
                    existing[
                        "question"
                    ]
                )
                == normalized_question
                for existing
                in valid_questions
            )

            if already_exists:
                continue

            valid_questions.append(
                question
            )

    # =================================================
    # Final safety check
    # =================================================

    valid_questions = [
        question
        for question
        in valid_questions
        if validate_question(
            question,
            topic,
        )
        is not None
    ]

    # There must ALWAYS be exactly 5.
    # The fallback list itself contains 5 valid
    # questions, so this should never be zero.

    if len(
        valid_questions
    ) < 5:

        valid_questions = (
            fallback_questions(
                topic
            )
        )

    valid_questions = (
        valid_questions[:5]
    )

    return {

        "topic": topic,

        "questions": valid_questions,

        "total_questions": len(
            valid_questions
        ),

        "status": (
            "WAITING_FOR_LEARNER"
        ),
    }