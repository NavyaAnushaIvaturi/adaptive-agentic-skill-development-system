import json
import math
from typing import Any

from backend.utils.llm import get_llm


# Check whether a daily focus is related to an assessment.
def _is_assessment_focus(focus: str) -> bool:
    text = focus.lower()

    assessment_words = [
        "assessment",
        "quiz",
        "test",
        "exam",
        "final evaluation",
        "knowledge check",
    ]

    return any(
        word in text
        for word in assessment_words
    )


# Create a fallback daily focus when the LLM does not provide one.
def _fallback_focus(
    topic: str,
    day_number: int,
) -> str:
    """
    Return a distinct daily focus for a given week topic.
    Each of the 7 days targets a different aspect of the topic
    so fallback schedules are genuinely varied.
    """
    day_focuses = [
        f"Introduction to {topic}: overview, purpose, and core terminology.",
        f"Core concepts of {topic}: key ideas explained with worked examples.",
        f"Hands-on practice: apply {topic} concepts to simple coding exercises.",
        f"Intermediate {topic}: explore common patterns and real-world usage.",
        f"Practical project: build a small working example using {topic}.",
        f"Troubleshooting and edge cases in {topic} — common mistakes to avoid.",
        f"Review and consolidate {topic}: end-to-end summary exercise and recap.",
    ]

    index = min(day_number - 1, len(day_focuses) - 1)
    return day_focuses[index]


# Clean and remove invalid or duplicate learning items.
def _clean_learning_items(
    values: list[str] | None,
) -> list[str]:

    if not values:
        return []

    cleaned = []

    for value in values:

        if not isinstance(
            value,
            str,
        ):
            continue

        value = value.strip()

        if not value:
            continue

        if value not in cleaned:
            cleaned.append(value)

    return cleaned


# Generate and normalize a personalized learning roadmap.
def create_roadmap(
    goal: str,
    current_level: str,
    time_per_day: int,
    duration_days: int,
    preference: str | None = None,
    mode: str = "general",
    project: str | None = None,
    skill_gaps: list[str] | None = None,
    current_skills: list[str] | None = None,
    role: str | None = None,
    deadline: str | None = None,
    required_technologies: list[str] | None = None,
) -> dict[str, Any]:

    skill_gaps = _clean_learning_items(
        skill_gaps
    )

    current_skills = _clean_learning_items(
        current_skills
    )

    required_technologies = _clean_learning_items(
        required_technologies
    )

    week_count = max(
        1,
        math.ceil(
            duration_days / 7
        ),
    )

    is_project_mode = (
        mode == "project-oriented"
    )

    # =====================================================
    # PROJECT ORIENTED MODE
    # =====================================================

    if is_project_mode:

        learning_requirements = []

        for skill in skill_gaps:

            if skill not in learning_requirements:
                learning_requirements.append(
                    skill
                )

        for technology in required_technologies:

            if technology not in learning_requirements:
                learning_requirements.append(
                    technology
                )

        prompt = f"""
You are an adaptive learning roadmap planner.

Create a skill-based learning roadmap for a learner
who selected PROJECT ORIENTED learning mode.

The learner has a project they want to understand or
eventually build, but the roadmap must teach the
KNOWLEDGE AND SKILLS required for that project.

PROJECT:
{project}

LEARNER'S CURRENT SKILLS:
{current_skills}

SKILLS THE LEARNER WANTS OR NEEDS TO LEARN:
{skill_gaps}

REQUIRED TECHNOLOGIES:
{required_technologies}

General goal:
{goal}

Current level:
{current_level}

Time available per day:
{time_per_day} minutes

Total duration:
{duration_days} days

Learning preference:
{preference}

Role:
{role}

Deadline:
{deadline}

IMPORTANT PROJECT MODE RULES:

1. The PROJECT is the learning context.

2. Do NOT make the roadmap a list of project-building
   tasks.

3. Do NOT create weeks such as:
   - Build the website
   - Build the dataset
   - Create the project
   - Implement the homepage
   - Finish the application
   - Deploy the project

4. Instead, identify and teach the SKILLS and
   TECHNOLOGIES required to understand and work on
   the project.

5. The learner's CURRENT SKILLS must NOT receive a
   complete week of beginner teaching.

6. Prioritize missing skills over skills already known.

7. Use the project only to determine why a skill is
   relevant and what practical examples should be used.

8. Each week must have exactly ONE MAIN LEARNING TOPIC.

9. A main topic should normally be a skill, technology,
   or closely related learning area.

10. Progress logically from foundational missing skills
    toward advanced missing skills.

11. Do not waste a week repeating a skill that already
    appears in the learner's current skills.

12. Daily focuses must teach or practice the week's
    learning topic.

13. Daily focuses must NOT be project-completion tasks.

14. Do NOT create assessment, quiz, test, exam, or
    knowledge-check activities.

15. Assessment is handled separately by the system.

16. If the learner already knows Python, do not create
    a full beginner Python week.

17. Example:

    Project:
    Disease Prediction Website

    Current skills:
    Python, HTML, CSS

    Missing skills:
    Machine Learning, Computer Vision,
    FastAPI, React

    A suitable roadmap structure would be similar to:

    Week 1 - Machine Learning Fundamentals
    Week 2 - Data Preprocessing and Model Training
    Week 3 - Computer Vision and Model Evaluation
    Week 4 - FastAPI and Model Serving
    Week 5 - React and API Integration
    Week 6 - Deployment Fundamentals

18. The exact topics must be determined from the actual
    learner's missing skills and required technologies.

STRUCTURE REQUIREMENT — EXACTLY 7 DAYS PER WEEK:

Every week must have EXACTLY 7 days.
Each day must have a DIFFERENT subtopic related to that week's main topic.
The 7 days should progress through the topic from introduction to mastery.

EXAMPLE — Week 1 topic: "Machine Learning Fundamentals"
  Day 1: What is Machine Learning — types, use cases, and key terminology
  Day 2: Supervised Learning — how it works, labelled datasets, examples
  Day 3: Linear Regression — training a model, cost function, gradient descent
  Day 4: Classification algorithms — Logistic Regression, Decision Trees
  Day 5: Model evaluation — accuracy, precision, recall, confusion matrix
  Day 6: Overfitting and regularization — L1, L2, cross-validation
  Day 7: Practical ML pipeline — data loading, training, predicting end-to-end

Do NOT repeat the same subtopic across multiple days in the same week.
Do NOT repeat any daily focus across different weeks.

Create exactly {week_count} weeks.

Return ONLY valid JSON.

{{
  "weeks": [
    {{
      "week": 1,
      "topic": "Main Learning Topic",
      "description": "What the learner will learn and achieve this week",
      "days": [
        {{"day": 1, "focus": "Day 1 specific subtopic and activity"}},
        {{"day": 2, "focus": "Day 2 specific subtopic and activity"}},
        {{"day": 3, "focus": "Day 3 specific subtopic and activity"}},
        {{"day": 4, "focus": "Day 4 specific subtopic and activity"}},
        {{"day": 5, "focus": "Day 5 specific subtopic and activity"}},
        {{"day": 6, "focus": "Day 6 specific subtopic and activity"}},
        {{"day": 7, "focus": "Day 7 specific subtopic and activity"}}
      ]
    }}
  ]
}}

Rules:
- Exactly {week_count} weeks.
- Exactly 7 days per week.
- Each day must have a UNIQUE focus different from all other days in that week.
- Focus on missing skills.
- Do not teach already-known skills from scratch.
- Use the project as context, not as a task list.
- Daily focuses must be learning or practice activities.
- Every daily focus must directly support the week's topic.
- No assessment. No quiz. No test. No exam.
- No project-completion task.
- No markdown.
"""


    # =====================================================
    # GENERAL LEARNING MODE
    # =====================================================

    else:

        prompt = f"""
You are an adaptive learning roadmap planner.

Create a structured, week-by-week learning roadmap.

Learner profile:
Goal: {goal}
Current level: {current_level}
Time per day: {time_per_day} minutes
Total duration: {duration_days} days ({week_count} weeks)
Learning preference: {preference}
Role: {role}
Current skills: {current_skills}
Skill gaps: {skill_gaps}
Required technologies: {required_technologies}
Project context: {project}
Deadline: {deadline}

═══════════════════════════════════════════════════
WEEK STRUCTURE — MANDATORY
═══════════════════════════════════════════════════

Every week must follow this exact structure:
  • ONE main topic (a specific area of the goal)
  • EXACTLY 7 days
  • Each day has a DIFFERENT subtopic related to THAT week's main topic
  • Days progress from introduction → practice → consolidation

NEVER reuse the same subtopic in two different days.
NEVER reuse the same main topic in two different weeks.
NEVER use the goal statement as the topic name.

═══════════════════════════════════════════════════
EXAMPLES
═══════════════════════════════════════════════════

EXAMPLE A — Goal: "Get good at Java"

  Week 1 — Topic: Java Fundamentals & Syntax
    Day 1: Java setup, JVM basics, first Hello World program
    Day 2: Variables, primitive data types, and type casting
    Day 3: Operators, expressions, and control flow (if/else, switch)
    Day 4: Loops — for, while, do-while with practical exercises
    Day 5: Methods — declaration, parameters, return types, overloading
    Day 6: Arrays — single and multi-dimensional, common operations
    Day 7: Mini project — write a Java program using all Week 1 concepts

  Week 2 — Topic: Object-Oriented Programming in Java
    Day 1: Classes and objects — what they are and why they matter
    Day 2: Constructors, instance vs. class members, this keyword
    Day 3: Encapsulation — access modifiers, getters, setters
    Day 4: Inheritance — extends, method overriding, super keyword
    Day 5: Polymorphism — compile-time vs. runtime, instanceof
    Day 6: Abstract classes vs. interfaces — when to use which
    Day 7: OOP mini project — design a class hierarchy for a real scenario

  Week 3 — Topic: Java Collections & Generics
    Day 1: Introduction to the Java Collections Framework
    Day 2: List — ArrayList vs. LinkedList, iteration, sorting
    Day 3: Set — HashSet, TreeSet, deduplication use cases
    Day 4: Map — HashMap, TreeMap, key-value patterns
    Day 5: Generics — why they exist, bounded wildcards, generic methods
    Day 6: Collections utility class — sort, shuffle, min, max
    Day 7: Practice — solve 3 data-manipulation problems using Collections

EXAMPLE B — Goal: "Learn Python for Data Science"

  Week 1 — Topic: Python Basics & Data Types
    Day 1: Python setup, interpreter, first script, print and input
    Day 2: Variables, int, float, string, bool — operations and conversions
    Day 3: Lists — creation, indexing, slicing, list methods
    Day 4: Tuples and Sets — differences, immutability, use cases
    Day 5: Dictionaries — creation, access, iteration, nested dicts
    Day 6: Control flow — if/elif/else, for loops, while, comprehensions
    Day 7: Functions — def, parameters, return, default args, *args/**kwargs

  Week 2 — Topic: NumPy & Array Operations
    Day 1: NumPy arrays vs. Python lists — why NumPy is faster
    Day 2: Array creation — zeros, ones, arange, linspace, random
    Day 3: Indexing and slicing — 1D, 2D, Boolean masks
    Day 4: Array operations — arithmetic, broadcasting rules
    Day 5: Linear algebra with NumPy — dot product, transpose, inverse
    Day 6: Statistical functions — mean, std, var, percentile
    Day 7: Practice — solve 5 NumPy data-manipulation challenges

═══════════════════════════════════════════════════
RULES
═══════════════════════════════════════════════════

1. Produce exactly {week_count} weeks.
2. Each week has exactly 7 days.
3. Each week must have a unique main topic — a specific subtopic of the goal.
4. Topic field: short descriptive name (3–6 words), NOT a sentence.
5. Each day's focus must be a DIFFERENT subtopic within that week's topic.
6. Days must progress logically: intro → core concepts → practice → project.
7. No assessment, quiz, test, or exam activities (handled separately).
8. No markdown — return ONLY valid JSON.

═══════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════

Return ONLY this JSON (no text before or after):

{{
  "weeks": [
    {{
      "week": 1,
      "topic": "Specific Topic Name",
      "description": "What the learner will learn and achieve this week",
      "days": [
        {{"day": 1, "focus": "Specific subtopic for day 1"}},
        {{"day": 2, "focus": "Specific subtopic for day 2"}},
        {{"day": 3, "focus": "Specific subtopic for day 3"}},
        {{"day": 4, "focus": "Specific subtopic for day 4"}},
        {{"day": 5, "focus": "Specific subtopic for day 5"}},
        {{"day": 6, "focus": "Specific subtopic for day 6"}},
        {{"day": 7, "focus": "Specific subtopic for day 7"}}
      ]
    }}
  ]
}}
"""

    # Get the configured language model.
    llm = get_llm()

    try:

        response = llm.invoke(
            prompt
        )

        content = response.content.strip()

        if content.startswith("```"):

            content = content.replace(
                "```json",
                "",
            )

            content = content.replace(
                "```",
                "",
            )

            content = content.strip()

        result = json.loads(
            content
        )

        weeks = result.get(
            "weeks",
            [],
        )

        if not isinstance(
            weeks,
            list,
        ):
            weeks = []

    except Exception:

        weeks = []

    # =====================================================
    # FALLBACK TOPICS
    # =====================================================

    fallback_topics = []

    if is_project_mode:

        fallback_topics.extend(
            skill_gaps
        )

        for technology in required_technologies:

            if technology not in fallback_topics:
                fallback_topics.append(
                    technology
                )

    else:

        fallback_topics.extend(
            skill_gaps
        )

        for technology in required_technologies:

            if technology not in fallback_topics:
                fallback_topics.append(
                    technology
                )

    # =====================================================
    # SMART FALLBACK TOPICS for general mode
    # Build meaningful subtopics from the goal string
    # instead of using the goal itself for all weeks.
    # =====================================================

    # Generate progressive fallback topics for general learning mode.
    def _generate_general_fallback_topics(
        goal: str,
        count: int,
    ) -> list[str]:
        """
        Produce distinct, progressive subtopics when the
        LLM fails to generate a proper roadmap.
        """
        stages = [
            "Fundamentals & Core Concepts",
            "Syntax & Basic Patterns",
            "Intermediate Techniques",
            "Practical Application",
            "Advanced Concepts",
            "Best Practices & Design Patterns",
            "Performance & Optimization",
            "Testing & Debugging",
        ]

        # Extract a short subject from goal
        # (first 3-4 meaningful words, strip "learn", "get good at", etc.)
        stop_words = {
            "learn", "get", "good", "at", "in", "to", "be",
            "become", "understand", "master", "study", "i", "want",
        }

        words = [
            w for w in goal.split()
            if w.lower() not in stop_words
        ]

        subject = " ".join(words[:4]).strip() if words else goal[:30]

        topics = []
        for i in range(count):
            stage = stages[i % len(stages)]
            topics.append(f"{subject} — {stage}")

        return topics

    # =====================================================
    # BUILD NORMALIZED WEEKS
    # =====================================================

    normalized = []

    # Precompute general fallback in case LLM failed
    if not is_project_mode and not fallback_topics:
        fallback_topics = _generate_general_fallback_topics(
            goal, week_count
        )

    for index in range(
        week_count
    ):

        week_number = index + 1

        if (
            index < len(weeks)
            and isinstance(
                weeks[index],
                dict,
            )
        ):

            week = weeks[index]

        else:

            week = {}

        topic = week.get(
            "topic"
        )

        # Reject topic if it is blank or too similar to
        # the raw goal string (LLM just repeated the goal).
        _topic_is_bad = (
            not isinstance(topic, str)
            or not topic.strip()
            or topic.strip().lower() == goal.strip().lower()
        )

        if _topic_is_bad:

            if index < len(
                fallback_topics
            ):

                topic = fallback_topics[
                    index
                ]

            elif is_project_mode:

                if fallback_topics:

                    topic = fallback_topics[
                        -1
                    ]

                else:

                    topic = (
                        "Core skills "
                        "for the project"
                    )

            else:
                # Use smart general fallback
                smart = _generate_general_fallback_topics(
                    goal, week_count
                )
                topic = smart[index % len(smart)]

        topic = topic.strip()

        description = week.get(
            "description"
        )

        if (
            not isinstance(
                description,
                str,
            )
            or not description.strip()
        ):

            if is_project_mode:

                description = (
                    f"Learn the skills and "
                    f"concepts of {topic} "
                    f"that are relevant to "
                    f"the learner's project."
                )

            else:

                description = (
                    f"Learn the fundamentals "
                    f"and practical concepts "
                    f"of {topic}."
                )

        # Every week always has exactly 7 days.
        days_in_week = 7

        raw_days = week.get(
            "days",
            [],
        )

        days = []
        seen_focuses = set()

        for day_number in range(
            1,
            days_in_week + 1,
        ):

            focus = None

            if (
                isinstance(
                    raw_days,
                    list,
                )
                and day_number <= len(
                    raw_days
                )
                and isinstance(
                    raw_days[
                        day_number - 1
                    ],
                    dict,
                )
            ):

                focus = raw_days[
                    day_number - 1
                ].get(
                    "focus"
                )

            # Reject focus if blank, looks like an assessment,
            # or is a duplicate within this week.
            _focus_key = (focus or "").strip().lower()
            if (
                not isinstance(
                    focus,
                    str,
                )
                or not focus.strip()
                or _is_assessment_focus(focus)
                or _focus_key in seen_focuses
            ):

                focus = _fallback_focus(
                    topic,
                    day_number,
                )

            seen_focuses.add(focus.strip().lower())

            days.append(
                {
                    "day": day_number,
                    "focus": focus.strip(),
                }
            )

        normalized.append(
            {
                "week": week_number,
                "topic": topic,
                "description": description.strip(),
                "days": days,
            }
        )

    return {
        "goal": goal,
        "mode": mode,
        "project": project,
        "current_level": current_level,
        "duration_days": duration_days,
        "time_per_day": time_per_day,
        "weeks": normalized,
        "status": "PENDING_APPROVAL",
    }