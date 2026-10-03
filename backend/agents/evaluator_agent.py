from typing import Any


# Normalize an answer so different text formats can be compared.
def normalize_answer(
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


# Check whether the user's answer matches the correct answer.
def answer_matches(
    question: dict[str, Any],
    user_answer: Any,
) -> bool:

    correct_answer = question.get(
        "correct_answer"
    )

    options = question.get(
        "options"
    ) or []

    normalized_user = normalize_answer(
        user_answer
    )

    normalized_correct = normalize_answer(
        correct_answer
    )

    # =================================================
    # Empty answer cannot be correct
    # =================================================

    if not normalized_user:
        return False

    if not normalized_correct:
        return False

    # =================================================
    # Direct answer-text comparison
    # =================================================

    if normalized_user == normalized_correct:
        return True

    # =================================================
    # User submitted A/B/C/D
    # =================================================

    if (
        len(normalized_user) == 1
        and normalized_user in {
            "a",
            "b",
            "c",
            "d",
        }
    ):

        index = (
            ord(normalized_user)
            - ord("a")
        )

        if index < len(options):

            selected_option = (
                normalize_answer(
                    options[index]
                )
            )

            # Correct answer is the
            # actual option text.

            if (
                selected_option
                == normalized_correct
            ):
                return True

            # Correct answer itself is
            # A/B/C/D.

            if (
                len(normalized_correct) == 1
                and normalized_correct
                in {
                    "a",
                    "b",
                    "c",
                    "d",
                }
                and normalized_user
                == normalized_correct
            ):
                return True

    # =================================================
    # Correct answer is A/B/C/D
    # =================================================

    if (
        len(normalized_correct) == 1
        and normalized_correct in {
            "a",
            "b",
            "c",
            "d",
        }
    ):

        index = (
            ord(normalized_correct)
            - ord("a")
        )

        if index < len(options):

            correct_option = (
                normalize_answer(
                    options[index]
                )
            )

            if (
                normalized_user
                == correct_option
            ):
                return True

    return False


# Evaluate all quiz answers and calculate the learner's result.
def evaluate_answers(
    questions: list[dict[str, Any]],
    answers: list[Any],
) -> dict[str, Any]:

    score = 0

    weak_topics: list[str] = []

    acquired_topics: list[str] = []

    question_results: list[
        dict[str, Any]
    ] = []

    total = len(
        questions
    )

    # =================================================
    # Evaluate every question
    # =================================================

    for index, question in enumerate(
        questions
    ):

        correct_answer = question.get(
            "correct_answer"
        )

        user_answer = (
            answers[index]
            if index < len(answers)
            else None
        )

        topic = question.get(
            "topic",
            "Unknown",
        ) or "Unknown"

        correct = answer_matches(
            question,
            user_answer,
        )

        if correct:

            score += 1

            if (
                topic != "Unknown"
                and topic not in acquired_topics
            ):

                acquired_topics.append(
                    topic
                )

        else:

            if (
                topic != "Unknown"
                and topic not in weak_topics
            ):

                weak_topics.append(
                    topic
                )

        question_results.append(
            {
                "question_index": index,

                "question": question.get(
                    "question",
                    "",
                ),

                "user_answer": user_answer,

                "correct_answer": correct_answer,

                "correct": correct,

                "topic": topic,
            }
        )

    # =================================================
    # Calculate percentage
    # =================================================

    if total > 0:

        percentage = round(
            (
                score
                / total
            )
            * 100
        )

    else:

        percentage = 0

    # =================================================
    # ONLY 100% PASSES
    # =================================================

    passed = (
        total > 0
        and score == total
        and percentage == 100
    )

    return {

        "score": score,

        "total": total,

        "percentage": percentage,

        "passed": passed,

        "weak_topics": weak_topics,

        "acquired_topics": acquired_topics,

        "question_results": question_results,
    }