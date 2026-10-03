import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.agents.assessment_agent import create_assessment
from backend.agents.adaptive_agent import choose_adaptive_action
from backend.agents.evaluator_agent import evaluate_answers
from backend.agents.task_agent import generate_daily_activity

from backend.database.database import get_db
from backend.database.models import (
    LearningActivity,
    LearningSession,
    User,
    UserLearningSession,
)

from backend.utils.auth import get_current_user
from backend.graph.workflow import learning_graph

from backend.schemas.learning import (
    ActivityCompletionRequest,
    LearningStartRequest,
    QuizSubmissionRequest,
    RoadmapApprovalRequest,
)


router = APIRouter(
    prefix="/learning",
    tags=["Learning"],
)


# ============================================================
# HELPERS
# ============================================================
# Helper functions for session, state, activity, and response handling.


# Get the learning session belonging to the current user.
def get_session(
    learning_id: str,
    db: Session,
    user: User,
):
    session = (
        db.query(LearningSession)
        .join(
            UserLearningSession,
            UserLearningSession.learning_id == LearningSession.id,
        )
        .filter(
            LearningSession.id == learning_id,
            UserLearningSession.user_id == user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Learning session not found",
        )

    return session


# Load saved learning state from the database.
def load_state(session: LearningSession):
    if not session.state_json:
        return {}

    try:
        return json.loads(session.state_json)
    except Exception:
        return {}


# Save the current learning state to the database.
def save_state(
    session: LearningSession,
    state: dict,
    db: Session,
):
    session.state_json = json.dumps(
        state,
        default=str,
    )

    session.status = state.get(
        "status",
        session.status,
    )

    session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(session)


# Clean assessment data before sending it in the API response.
def sanitize_assessment(assessment):
    if not assessment:
        return {}

    return {
        "topic": assessment.get("topic"),
        "questions": assessment.get("questions", []),
        "options": assessment.get("options", []),
        "question_topics": assessment.get(
            "question_topics",
            [],
        ),
        "total_questions": assessment.get(
            "total_questions",
            len(assessment.get("questions", [])),
        ),
        "status": assessment.get(
            "status",
            "ACTIVE",
        ),
    }


# Get the current week from the learning roadmap.
def get_current_week(state):
    roadmap = state.get("roadmap", {})

    weeks = roadmap.get("weeks", [])

    current_week = state.get(
        "current_week",
        1,
    )

    if not weeks:
        return None

    if current_week < 1:
        current_week = 1

    if current_week > len(weeks):
        current_week = len(weeks)

    return weeks[current_week - 1]


# Get the learning focus for a specific day.
def get_day_focus(
    topic,
    day,
):
    if not topic:
        return ""

    days = topic.get("days", [])

    if days:
        index = day - 1

        if 0 <= index < len(days):
            selected_day = days[index]

            if isinstance(
                selected_day,
                dict,
            ):
                return (
                    selected_day.get("focus")
                    or selected_day.get("description")
                    or selected_day.get("topic")
                    or selected_day.get("title")
                    or ""
                )

            return str(selected_day)

    return (
        topic.get("description")
        or topic.get("topic")
        or topic.get("title")
        or ""
    )


# Get the total number of learning days for a topic.
def get_total_learning_days(topic):
    if not topic:
        return 1

    days = topic.get("days", [])

    if days:
        return len(days)

    daily_focus = topic.get(
        "daily_focus",
        [],
    )

    if daily_focus:
        return len(daily_focus)

    return 1


# Limit the number of resources returned to the user.
def limit_resources(resources):
    if not resources:
        return []

    if isinstance(resources, list):
        return resources[:2]

    return []


# Build information about the previous or missed activity.
def build_previous_activity(
    activity,
    current_activity_state=None,
):
    if not activity:
        return None

    result = {
        "activity_id": activity.id,
        "week": activity.week,
        "day": activity.day,
        "topic": activity.topic,
        "title": activity.title,
        "description": activity.description,
        "status": "NOT_DONE",
    }

    # Include rich content from the in-memory state if available
    if (
        current_activity_state
        and isinstance(
            current_activity_state,
            dict,
        )
    ):
        result["learning_content"] = (
            current_activity_state.get(
                "learning_content",
                "",
            )
        )

        result["key_takeaways"] = (
            current_activity_state.get(
                "key_takeaways",
                [],
            )
        )

        result["base_focus"] = (
            current_activity_state.get(
                "base_focus",
                "",
            )
        )

        result["focus"] = (
            current_activity_state.get(
                "base_focus",
                "",
            )
        )

        result["objectives"] = (
            current_activity_state.get(
                "objectives",
                [],
            )
        )

    return result


# ============================================================
# ROADMAP HELPERS
# ============================================================
# Helper functions for accessing and managing roadmap weeks.


# Get all weeks from the roadmap.
def get_weeks(state):
    roadmap = state.get(
        "roadmap",
        {},
    )

    if not isinstance(roadmap, dict):
        return []

    weeks = roadmap.get(
        "weeks",
        [],
    )

    if not isinstance(weeks, list):
        return []

    return weeks


# Get a specific week from the roadmap.
def get_week_topic(
    state,
    week_number,
):
    weeks = get_weeks(state)

    if week_number < 1:
        return None

    if week_number > len(weeks):
        return None

    return weeks[week_number - 1]


# Get the name of a roadmap topic.
def get_topic_name(topic):
    if not topic:
        return None

    if isinstance(topic, str):
        return topic

    return (
        topic.get("topic")
        or topic.get("title")
        or topic.get("name")
    )


# Calculate dashboard progress for the learning session.
def calculate_dashboard(
    session,
    state,
    db,
):
    weeks = get_weeks(state)

    total_weeks = len(weeks)

    current_week = state.get(
        "current_week",
        1,
    )

    current_day = state.get(
        "current_day",
        1,
    )

    current_topic = get_week_topic(
        state,
        current_week,
    )

    total_days_current_week = get_total_learning_days(
        current_topic
    )

    # --------------------------------------------------------
    # Count completed activities
    # --------------------------------------------------------

    completed_activities = (
        db.query(LearningActivity)
        .filter(
            LearningActivity.learning_id == session.id,
            LearningActivity.status == "COMPLETED",
        )
        .count()
    )

    total_activities = (
        db.query(LearningActivity)
        .filter(
            LearningActivity.learning_id == session.id,
        )
        .count()
    )

    # --------------------------------------------------------
    # Calculate overall progress
    # --------------------------------------------------------

    total_planned_days = 0

    for week in weeks:
        total_planned_days += get_total_learning_days(
            week
        )

    if total_planned_days <= 0:
        total_planned_days = 1

    completed_days = completed_activities

    progress_percentage = int(
        min(
            100,
            (
                completed_days
                / total_planned_days
            )
            * 100,
        )
    )

    # --------------------------------------------------------
    # Current week
    # --------------------------------------------------------

    current_week_details = {
        "week": current_week,
        "topic": get_topic_name(
            current_topic
        ),
        "current_day": current_day,
        "total_days": total_days_current_week,
        "progress_percentage": int(
            min(
                100,
                (
                    max(
                        0,
                        current_day - 1,
                    )
                    / max(
                        1,
                        total_days_current_week,
                    )
                )
                * 100,
            )
        ),
    }

    # --------------------------------------------------------
    # Next week
    # --------------------------------------------------------

    next_week_number = current_week + 1

    next_topic = get_week_topic(
        state,
        next_week_number,
    )

    next_week = None

    if next_topic:
        next_week = {
            "week": next_week_number,
            "topic": get_topic_name(
                next_topic
            ),
            "total_days": get_total_learning_days(
                next_topic
            ),
            "description": (
                next_topic.get("description")
                if isinstance(
                    next_topic,
                    dict,
                )
                else None
            ),
        }

    return {
        "current_week": current_week,
        "total_weeks": total_weeks,
        "current_day": current_day,
        "total_days_current_week": total_days_current_week,
        "completed_activities": completed_activities,
        "total_activities": total_activities,
        "completed_days": completed_days,
        "total_planned_days": total_planned_days,
        "progress_percentage": progress_percentage,
        "current_week_details": current_week_details,
        "next_week": next_week,
    }


# ============================================================
# RESPONSE BUILDER
# ============================================================
# Build the complete response returned by learning APIs.


def build_response(
    session,
    state,
    db=None,
):
    current_week = state.get(
        "current_week",
        1,
    )

    current_day = state.get(
        "current_day",
        1,
    )

    current_topic = get_current_week(
        state
    )

    response = {
        "learning_id": session.id,

        "status": state.get(
            "status",
            session.status,
        ),

        "mode": state.get(
            "mode",
            "general",
        ),

        "goal": state.get(
            "goal"
        ),

        "current_level": state.get(
            "current_level"
        ),

        "project": state.get(
            "project"
        ),

        "role": state.get(
            "role"
        ),

        "current_skills": state.get(
            "current_skills",
            [],
        ),

        "required_skills": state.get(
            "required_skills",
            [],
        ),

        "required_technologies": state.get(
            "required_technologies",
            [],
        ),

        "context": state.get(
            "context",
            {},
        ),

        "skill_gap": state.get(
            "skill_gap",
            [],
        ),

        "acquired_skills": state.get(
            "acquired_skills",
            [],
        ),

        "roadmap": state.get(
            "roadmap",
            {},
        ),

        "roadmap_approved": state.get(
            "roadmap_approved",
            False,
        ),

        "current_week": current_week,

        "day": current_day,

        "topic": current_topic,

        "current_activity": state.get(
            "current_activity"
        ),

        "previous_activity": state.get(
            "previous_activity"
        ),

        "activity_completed": state.get(
            "activity_completed",
            False,
        ),

        "assessment": sanitize_assessment(
            state.get("assessment")
        ),

        "evaluation": state.get(
            "evaluation",
            {},
        ),

        "adaptive_action": state.get(
            "adaptive_action",
            {},
        ),

        "remedial": state.get(
            "remedial",
            False,
        ),
    }

    # --------------------------------------------------------
    # Dashboard
    # --------------------------------------------------------

    if db is not None:
        response["dashboard"] = calculate_dashboard(
            session,
            state,
            db,
        )
    else:
        response["dashboard"] = {}

    return response


# ============================================================
# ACTIVITY CREATION
# ============================================================
# Generate and save a daily learning activity.


def create_activity(
    session,
    state,
    db,
    remedial=False,
):
    current_week = state.get(
        "current_week",
        1,
    )

    current_day = state.get(
        "current_day",
        1,
    )

    topic = get_week_topic(
        state,
        current_week,
    )

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="Current roadmap week not found",
        )

    topic_name = get_topic_name(
        topic
    )

    base_focus = get_day_focus(
        topic,
        current_day,
    )

    activity = generate_daily_activity(
        topic=topic_name,
        day=current_day,
        daily_focus=base_focus,
        mode=state.get(
            "mode",
            "general",
        ),
        project=state.get(
            "project"
        ),
        remedial=remedial,
        include_resources=True,
    )

    if not activity:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate learning activity",
        )

    learning_activity = LearningActivity(
        learning_id=session.id,
        week=current_week,
        day=current_day,
        topic=topic_name,
        title=activity.get(
            "title",
            f"Day {current_day} Activity",
        ),
        description=activity.get(
            "description",
            "",
        ),
        activity_type=(
            "REMEDIAL"
            if remedial
            else activity.get(
                "activity_type",
                "LEARNING",
            )
        ),
        status="PENDING",
    )

    db.add(
        learning_activity
    )

    db.flush()

    current_activity = {
        "activity_id": learning_activity.id,
        "week": current_week,
        "day": current_day,
        "topic": topic_name,
        "title": activity.get(
            "title"
        ),
        "description": activity.get(
            "description",
            "",
        ),
        "learning_content": activity.get(
            "learning_content",
            "",
        ),
        "objectives": activity.get(
            "objectives",
            [],
        ),
        "concepts": activity.get(
            "concepts",
            [],
        ),
        "examples": activity.get(
            "examples",
            [],
        ),
        "steps": activity.get(
            "steps",
            [],
        ),
        "practical_task": activity.get(
            "practical_task",
            "",
        ),
        "common_mistakes": activity.get(
            "common_mistakes",
            [],
        ),
        "key_takeaways": activity.get(
            "key_takeaways",
            [],
        ),
        "activity_type": (
            "REMEDIAL"
            if remedial
            else activity.get(
                "activity_type",
                "LEARNING",
            )
        ),
        "status": "PENDING",
        "remedial": remedial,
        "base_focus": base_focus,
        "resources": limit_resources(
            activity.get(
                "resources",
                [],
            )
        ),
    }

    state["current_activity"] = current_activity
    state["activity_completed"] = False
    state["status"] = (
        "REMEDIAL_ACTIVITY"
        if remedial
        else "DAILY_ACTIVITY"
    )

    # NOTE: previous_activity is intentionally NOT cleared here.
    # The caller sets it before calling create_activity so that
    # the missed day's info is preserved and shown alongside
    # the newly generated activity.

    save_state(
        session,
        state,
        db,
    )

    return current_activity


# ============================================================
# START LEARNING
# ============================================================
# Start a new learning session and generate its roadmap.


@router.post("/start")
def start_learning(
    request: LearningStartRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # --------------------------------------------------------
    # Project mode validation
    # --------------------------------------------------------

    if request.mode in {"project", "project-oriented"}:
        if not request.project:
            raise HTTPException(
                status_code=400,
                detail="Project is required in project mode",
            )

        if (
            not request.required_skills
            and not request.required_technologies
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Required skills or technologies "
                    "are required in project mode"
                ),
            )

    # --------------------------------------------------------
    # Initial graph state
    # --------------------------------------------------------

    initial_state = {
        "mode": (
            "project"
            if request.mode == "project-oriented"
            else request.mode
        ),
        "goal": request.goal,
        "current_level": request.current_level,
        "time_per_day": request.time_per_day,
        "duration_days": request.duration_days,
        "preference": request.preference,
        "role": request.role,
        "project": request.project,
        "deadline": request.deadline,
        "current_skills": request.current_skills,
        "acquired_skills": request.current_skills.copy(),
        "required_skills": request.required_skills,
        "required_technologies": request.required_technologies,
        "pending_focuses": [],
        "previous_activity": None,
    }

    # --------------------------------------------------------
    # Generate roadmap
    # --------------------------------------------------------

    result = learning_graph.invoke(
        initial_state
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate learning roadmap",
        )

    # --------------------------------------------------------
    # Create session
    # --------------------------------------------------------

    session = LearningSession(
        mode=request.mode
        if request.mode != "project-oriented"
        else "project",
        goal=request.goal,
        current_level=request.current_level,
        time_per_day=request.time_per_day,
        duration_days=request.duration_days,
        preference=request.preference,
        role=request.role,
        project=request.project,
        deadline=request.deadline,
        status=result.get(
            "status",
            "ROADMAP_GENERATED",
        ),
        state_json=json.dumps(
            result,
            default=str,
        ),
    )

    db.add(session)

    db.flush()

    user_session = UserLearningSession(
        user_id=user.id,
        learning_id=session.id,
    )

    db.add(
        user_session
    )

    db.commit()
    db.refresh(session)

    return build_response(
        session,
        result,
        db,
    )


# ============================================================
# APPROVE ROADMAP
# ============================================================
# Approve the generated roadmap and start the first activity.


@router.post("/{learning_id}/approve")
def approve_roadmap(
    learning_id: str,
    request: RoadmapApprovalRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = get_session(
        learning_id,
        db,
        user,
    )

    state = load_state(
        session
    )

    # --------------------------------------------------------
    # Reject roadmap
    # --------------------------------------------------------

    if not request.approved:
        state["roadmap_approved"] = False
        state["status"] = "ROADMAP_REJECTED"

        save_state(
            session,
            state,
            db,
        )

        return build_response(
            session,
            state,
            db,
        )

    # --------------------------------------------------------
    # Validate roadmap
    # --------------------------------------------------------

    weeks = get_weeks(
        state
    )

    if not weeks:
        raise HTTPException(
            status_code=400,
            detail="No roadmap weeks available",
        )

    # --------------------------------------------------------
    # Start first week
    # --------------------------------------------------------

    state["roadmap_approved"] = True
    state["current_week"] = 1
    state["current_day"] = 1

    state["current_topic"] = weeks[0]

    state["assessment"] = {}
    state["answers"] = []
    state["evaluation"] = {}
    state["adaptive_action"] = {}
    state["remedial"] = False
    state["pending_focuses"] = []
    state["previous_activity"] = None

    save_state(
        session,
        state,
        db,
    )

    create_activity(
        session,
        state,
        db,
        remedial=False,
    )

    return build_response(
        session,
        state,
        db,
    )


# ============================================================
# COMPLETE ACTIVITY
# ============================================================
# Mark an activity as completed or missed and move learning forward.


@router.post(
    "/{learning_id}/activities/{activity_id}/complete"
)
def complete_activity(
    learning_id: str,
    activity_id: str,
    request: ActivityCompletionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = get_session(
        learning_id,
        db,
        user,
    )

    state = load_state(
        session
    )

    activity = (
        db.query(LearningActivity)
        .filter(
            LearningActivity.id == activity_id,
            LearningActivity.learning_id == session.id,
        )
        .first()
    )

    if not activity:
        raise HTTPException(
            status_code=404,
            detail="Activity not found",
        )

    # --------------------------------------------------------
    # Activity NOT completed (missed)
    # --------------------------------------------------------

    if not request.completed:
        activity.status = "NOT_DONE"

        # Save full content of the missed activity so
        # the frontend can show it alongside the next day.
        state["previous_activity"] = build_previous_activity(
            activity,
            state.get("current_activity"),
        )

        current_day = state.get("current_day", 1)
        current_week = state.get("current_week", 1)

        current_topic = get_week_topic(
            state,
            current_week,
        )

        total_days = get_total_learning_days(
            current_topic
        )

        db.commit()

        if current_day < total_days:
            # ------------------------------------------------
            # Move to the next day; previous_activity stays
            # in state so next day's activity screen shows it.
            # ------------------------------------------------
            state["current_day"] = current_day + 1
            state["activity_completed"] = False

            save_state(
                session,
                state,
                db,
            )

            create_activity(
                session,
                state,
                db,
                remedial=False,
            )

        else:
            # ------------------------------------------------
            # Last day of the week was missed.
            # The week is still over — trigger the quiz so
            # the learner must demonstrate understanding
            # before advancing (or getting remedial work).
            # ------------------------------------------------
            topic_name = get_topic_name(
                current_topic
            )

            assessment = create_assessment(
                topic=topic_name,
                mode=state.get(
                    "mode",
                    "general",
                ),
                project=state.get(
                    "project"
                ),
            )

            state["assessment"] = assessment
            state["answers"] = []
            state["status"] = "TOPIC_ASSESSMENT"

            save_state(
                session,
                state,
                db,
            )

        return build_response(
            session,
            state,
            db,
        )

    # --------------------------------------------------------
    # Activity completed
    # --------------------------------------------------------

    activity.status = "COMPLETED"
    activity.completed_at = datetime.utcnow()

    state["activity_completed"] = True
    state["previous_activity"] = None

    current_week = state.get(
        "current_week",
        1,
    )

    current_day = state.get(
        "current_day",
        1,
    )

    current_topic = get_week_topic(
        state,
        current_week,
    )

    total_days = get_total_learning_days(
        current_topic
    )

    # --------------------------------------------------------
    # Remedial activity
    # --------------------------------------------------------

    if state.get("remedial"):
        topic_name = get_topic_name(
            current_topic
        )

        assessment = create_assessment(
            topic=topic_name,
            mode=state.get(
                "mode",
                "general",
            ),
            project=state.get(
                "project"
            ),
        )

        state["assessment"] = assessment
        state["answers"] = []
        state["status"] = "TOPIC_ASSESSMENT"

        save_state(
            session,
            state,
            db,
        )

        return build_response(
            session,
            state,
            db,
        )

    # --------------------------------------------------------
    # End of current week
    # --------------------------------------------------------

    if current_day >= total_days:
        topic_name = get_topic_name(
            current_topic
        )

        assessment = create_assessment(
            topic=topic_name,
            mode=state.get(
                "mode",
                "general",
            ),
            project=state.get(
                "project"
            ),
        )

        state["assessment"] = assessment
        state["answers"] = []
        state["status"] = "TOPIC_ASSESSMENT"

        save_state(
            session,
            state,
            db,
        )

        return build_response(
            session,
            state,
            db,
        )

    # --------------------------------------------------------
    # Move to next day
    # --------------------------------------------------------

    state["current_day"] = (
        current_day + 1
    )

    state["activity_completed"] = False

    save_state(
        session,
        state,
        db,
    )

    create_activity(
        session,
        state,
        db,
        remedial=False,
    )

    return build_response(
        session,
        state,
        db,
    )


# ============================================================
# QUIZ SUBMISSION
# ============================================================
# Submit quiz answers, evaluate them, and choose the next action.


@router.post(
    "/{learning_id}/quiz"
)
def submit_quiz(
    learning_id: str,
    request: QuizSubmissionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = get_session(
        learning_id,
        db,
        user,
    )

    state = load_state(
        session
    )

    assessment = state.get(
        "assessment"
    )

    if not assessment:
        raise HTTPException(
            status_code=400,
            detail="No active assessment",
        )

    questions = assessment.get(
        "questions",
        [],
    )

    if not questions:
        raise HTTPException(
            status_code=400,
            detail="Assessment contains no questions",
        )

    if len(request.answers) != len(
        questions
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Expected {len(questions)} answers, "
                f"received {len(request.answers)}"
            ),
        )

    # --------------------------------------------------------
    # Evaluate answers
    # --------------------------------------------------------

    evaluation = evaluate_answers(
        questions,
        request.answers,
    )

    total_questions = len(
        questions
    )

    score = evaluation.get(
        "score",
        0,
    )

    try:
        score = int(score)
    except Exception:
        score = 0

    score = max(
        0,
        min(
            score,
            total_questions,
        ),
    )

    percentage = (
        score
        / total_questions
        * 100
        if total_questions
        else 0
    )

    # --------------------------------------------------------
    # Strict pass:
    # 100% required
    # --------------------------------------------------------

    evaluation["score"] = score
    evaluation["total_questions"] = (
        total_questions
    )
    evaluation["percentage"] = percentage

    evaluation["passed"] = (
        total_questions > 0
        and score == total_questions
        and percentage == 100
    )

    quiz_history = state.setdefault(
        "quiz_history",
        []
    )

    quiz_history.append(
        {
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "passed": evaluation["passed"],
            "submitted_at": datetime.utcnow().isoformat(),
        }
    )

    # --------------------------------------------------------
    # Adaptive action
    # --------------------------------------------------------

    adaptive_action = choose_adaptive_action(
        percentage,
        evaluation.get(
            "weak_topics",
            [],
        ),
    )

    # --------------------------------------------------------
    # Acquired skills
    # --------------------------------------------------------

    acquired_skills = set(
        state.get(
            "acquired_skills",
            [],
        )
    )

    for topic in evaluation.get(
        "acquired_topics",
        [],
    ):
        acquired_skills.add(
            topic
        )

    state["acquired_skills"] = list(
        acquired_skills
    )

    state["answers"] = request.answers
    state["evaluation"] = evaluation
    state["adaptive_action"] = adaptive_action

    # ========================================================
    # PASSED
    # ========================================================
    # Move to the next week when the assessment is passed.

    if evaluation["passed"]:
        state["remedial"] = False
        state["assessment"] = {}
        state["answers"] = []

        # IMPORTANT:
        # Do NOT clear adaptive_action here.
        # The Adaptive Agent result is preserved so that
        # the API response shows ADVANCE and its analysis.

        state["current_activity"] = None
        state["activity_completed"] = False
        state["previous_activity"] = None

        current_week = state.get(
            "current_week",
            1,
        )

        next_week = current_week + 1

        weeks = get_weeks(
            state
        )

        # ----------------------------------------------------
        # NEXT WEEK EXISTS
        # ----------------------------------------------------

        if next_week <= len(weeks):
            state["current_week"] = (
                next_week
            )

            state["current_day"] = 1

            state["current_topic"] = (
                weeks[next_week - 1]
            )

            state["status"] = (
                "DAILY_ACTIVITY"
            )

            save_state(
                session,
                state,
                db,
            )

            create_activity(
                session,
                state,
                db,
                remedial=False,
            )

            return build_response(
                session,
                state,
                db,
            )

        # ----------------------------------------------------
        # ENTIRE ROADMAP COMPLETED
        # ----------------------------------------------------

        state["current_activity"] = None
        state["status"] = "COMPLETED"
        state["activity_completed"] = True

        save_state(
            session,
            state,
            db,
        )

        return build_response(
            session,
            state,
            db,
        )

    # ========================================================
    # FAILED / BELOW 100%
    # ========================================================
    # Generate a remedial activity when the learner does not pass.

    state["remedial"] = True
    state["current_activity"] = None
    state["activity_completed"] = False

    save_state(
        session,
        state,
        db,
    )

    create_activity(
        session,
        state,
        db,
        remedial=True,
    )

    return build_response(
        session,
        state,
        db,
    )


# ============================================================
# GET CURRENT USER'S ACTIVE SESSION
# (Must be before /{learning_id}/... routes)
# ============================================================
# Get the most recent learning session of the logged-in user.


@router.get("/my-session")
def get_my_session(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Return the most recent active learning session for the
    authenticated user, or null if none exists.
    """

    user_session = (
        db.query(UserLearningSession)
        .filter(
            UserLearningSession.user_id == user.id
        )
        .order_by(
            UserLearningSession.created_at.desc()
        )
        .first()
    )

    if not user_session:
        return {"session": None}

    session = (
        db.query(LearningSession)
        .filter(
            LearningSession.id
            == user_session.learning_id
        )
        .first()
    )

    if not session:
        return {"session": None}

    state = load_state(session)

    return {
        "session": build_response(
            session,
            state,
            db,
        )
    }


# ============================================================
# PROGRESS AND QUIZ HISTORY
# ============================================================
# Provide learning progress and previous quiz attempts.


@router.get("/{learning_id}/progress")
def get_progress(
    learning_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = get_session(
        learning_id,
        db,
        user,
    )

    state = load_state(
        session
    )

    dashboard = calculate_dashboard(
        session,
        state,
        db,
    )

    current_week_num = dashboard[
        "current_week"
    ]

    current_topic_obj = get_week_topic(
        state,
        current_week_num,
    )

    not_done_count = (
        db.query(LearningActivity)
        .filter(
            LearningActivity.learning_id == session.id,
            LearningActivity.status == "NOT_DONE",
        )
        .count()
    )

    return {
        **dashboard,
        "goal": state.get("goal"),
        "current_topic": current_topic_obj,
        "not_done_activities": not_done_count,
        "completed_percentage": dashboard.get(
            "progress_percentage",
            0,
        ),
        "completion_percentage": dashboard.get(
            "progress_percentage",
            0,
        ),
        "current_activity": state.get(
            "current_activity"
        ),
        "status": state.get(
            "status",
            session.status,
        ),
    }


# Get the quiz history for the learning session.
@router.get("/{learning_id}/quiz-history")
def get_quiz_history(
    learning_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = get_session(
        learning_id,
        db,
        user,
    )

    state = load_state(
        session
    )

    return {
        "attempts": state.get(
            "quiz_history",
            [],
        ),
    }