from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.agents.context_agent import analyze_context
from backend.agents.skill_gap_agent import analyze_skill_gap
from backend.agents.planner_agent import create_roadmap
from backend.graph.state import LearningState


# =========================================================
# CONTEXT NODE
# =========================================================

# Analyze the learner's context and learning requirements.
def context_node(
    state: LearningState,
) -> dict[str, Any]:

    context = analyze_context(
        goal=state["goal"],
        current_level=state["current_level"],
        time_per_day=state["time_per_day"],
        duration_days=state["duration_days"],
        preference=state.get(
            "preference"
        ),
        mode=state.get(
            "mode",
            "general",
        ),
        role=state.get(
            "role"
        ),
        project=state.get(
            "project"
        ),
        deadline=state.get(
            "deadline"
        ),
        current_skills=state.get(
            "current_skills",
            [],
        ),
        required_skills=state.get(
            "required_skills",
            [],
        ),
        required_technologies=state.get(
            "required_technologies",
            [],
        ),
    )

    return {
        "context": context,
        "status": "CONTEXT_ANALYZED",
    }


# =========================================================
# SKILL GAP NODE
# =========================================================

# Identify the skills missing between the learner and the goal.
def skill_gap_node(
    state: LearningState,
) -> dict[str, Any]:

    skill_gap = analyze_skill_gap(
        current_skills=state.get(
            "current_skills",
            [],
        ),
        required_skills=state.get(
            "required_skills",
            [],
        ),
        required_technologies=state.get(
            "required_technologies",
            [],
        ),
    )

    return {
        "skill_gap": skill_gap,
        "status": "SKILL_GAP_ANALYZED",
    }


# =========================================================
# PLANNER NODE
# =========================================================

# Create a personalized learning roadmap from the learner's information.
def planner_node(
    state: LearningState,
) -> dict[str, Any]:

    skill_gap = state.get(
        "skill_gap",
        {},
    )

    roadmap = create_roadmap(
        goal=state["goal"],

        current_level=state[
            "current_level"
        ],

        time_per_day=state[
            "time_per_day"
        ],

        duration_days=state[
            "duration_days"
        ],

        preference=state.get(
            "preference"
        ),

        mode=state.get(
            "mode",
            "general",
        ),

        project=state.get(
            "project"
        ),

        current_skills=state.get(
            "current_skills",
            [],
        ),

        skill_gaps=skill_gap.get(
            "missing_skills",
            [],
        ),

        role=state.get(
            "role"
        ),

        deadline=state.get(
            "deadline"
        ),

        required_technologies=state.get(
            "required_technologies",
            [],
        ),
    )

    return {
        "roadmap": roadmap,
        "status": "PENDING_APPROVAL",
    }


# =========================================================
# WORKFLOW
# =========================================================

# Create the LangGraph workflow using the learning state.
workflow = StateGraph(
    LearningState
)


workflow.add_node(
    "context",
    context_node,
)


workflow.add_node(
    "skill_gap",
    skill_gap_node,
)


workflow.add_node(
    "planner",
    planner_node,
)


# =========================================================
# FLOW
# =========================================================

# Start the workflow with context analysis.
workflow.add_edge(
    START,
    "context",
)


# Analyze skill gaps after context analysis.
workflow.add_edge(
    "context",
    "skill_gap",
)


# Create the roadmap after identifying skill gaps.
workflow.add_edge(
    "skill_gap",
    "planner",
)


# End the workflow after creating the roadmap.
workflow.add_edge(
    "planner",
    END,
)


# Compile the workflow into an executable graph.
learning_graph = workflow.compile()