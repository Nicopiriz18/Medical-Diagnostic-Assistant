"""
LangGraph: Main agent graph that orchestrates the medical interview and diagnosis flow.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.agents.state import (
    ConversationState,
    AgentPhase,
    should_proceed_to_diagnosis,
    calculate_confidence_score,
)
from app.agents.interviewer import interviewer_agent
from app.agents.image_analyzer import image_analyzer_agent
from app.agents.diagnostic import diagnostic_agent
from app.agents.orchestrator import (
    route_after_user_message,
    route_after_ready_check,
)


# Node functions that wrap agent execution

async def interviewer_node(state: ConversationState) -> Dict[str, Any]:
    """Node that runs the interviewer agent"""
    # First, process the last user response if exists
    if state["messages"] and state["messages"][-1]["role"] == "user":
        extraction_updates = await interviewer_agent.process_user_response(state)
        # Apply extraction updates to state
        state = {**state, **extraction_updates}
    
    # Then generate next question
    updates = await interviewer_agent.run(state)
    
    # Update phase
    updates["current_phase"] = AgentPhase.INTERVIEW
    
    return updates


async def ready_check_node(state: ConversationState) -> Dict[str, Any]:
    """
    Node that checks if we're ready for diagnosis.
    This is where we evaluate completeness and set the ready flag.
    """
    # Recalculate confidence
    confidence = calculate_confidence_score(state)
    
    # Check if ready
    ready = should_proceed_to_diagnosis(state)
    
    return {
        "confidence_score": confidence,
        "ready_for_diagnosis": ready,
        "current_phase": AgentPhase.READY_CHECK,
    }


async def diagnostic_node(state: ConversationState) -> Dict[str, Any]:
    """Node that runs the diagnostic agent"""
    updates = await diagnostic_agent.run(state)
    
    # Update phase to completed
    updates["current_phase"] = AgentPhase.COMPLETED
    
    return updates


# Conditional routing functions

def route_from_interviewer(state: ConversationState) -> str:
    """
    Route after interviewer completes.
    Check if the interviewer decided we're ready for diagnosis, or if we should continue.
    """
    # First priority: Check if interviewer decided we're ready for diagnosis
    if state.get("ready_for_diagnosis", False):
        return "diagnostic"
    
    # Second priority: Periodic check if we should evaluate readiness (every 3 turns as backup)
    if state["turn_count"] % 3 == 0 and state["turn_count"] > 0:
        return "ready_check"
    
    # Otherwise, wait for next user message (handled externally)
    return END


def route_from_ready_check(state: ConversationState) -> str:
    """Route after ready check"""
    if state.get("ready_for_diagnosis", False):
        return "diagnostic"
    else:
        # Not ready yet, but we've asked enough - continue interview
        return END  # Will resume on next user message


def route_from_diagnostic(state: ConversationState) -> str:
    """Route after diagnostic - always end"""
    return END


# Build the graph

def create_agent_graph() -> StateGraph:
    """
    Create and compile the LangGraph for the medical assistant.
    
    Returns:
        Compiled StateGraph
    """
    # Create the graph
    workflow = StateGraph(ConversationState)
    
    # Add nodes
    workflow.add_node("interviewer", interviewer_node)
    workflow.add_node("ready_check", ready_check_node)
    workflow.add_node("diagnostic", diagnostic_node)
    
    # Set entry point
    workflow.set_entry_point("interviewer")
    
    # Add edges
    # From interviewer: can go to diagnostic (if ready), ready_check (periodic), or end turn
    workflow.add_conditional_edges(
        "interviewer",
        route_from_interviewer,
        {
            "diagnostic": "diagnostic",
            "ready_check": "ready_check",
            END: END,
        }
    )
    
    # From ready_check: either diagnose or continue interview
    workflow.add_conditional_edges(
        "ready_check",
        route_from_ready_check,
        {
            "diagnostic": "diagnostic",
            END: END,
        }
    )
    
    # From diagnostic: always end
    workflow.add_edge("diagnostic", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


# Create the compiled graph
agent_graph = create_agent_graph()


# Convenience functions for external use

async def process_user_message(
    state: ConversationState,
    user_message: str
) -> ConversationState:
    """
    Process a user message through the agent graph.
    
    Args:
        state: Current conversation state
        user_message: User's message
    
    Returns:
        Updated state after agent processing
    """
    # Add user message to state
    new_messages = state["messages"].copy()
    new_messages.append({
        "role": "user",
        "content": user_message
    })
    
    state["messages"] = new_messages
    
    # Run the graph
    result = await agent_graph.ainvoke(state)
    
    return result


async def process_image_upload(
    state: ConversationState,
    image_url: str
) -> ConversationState:
    """
    Process an image upload.
    
    Args:
        state: Current conversation state
        image_url: URL of uploaded image
    
    Returns:
        Updated state after image analysis
    """
    # Analyze the image directly
    updates = await image_analyzer_agent.run(state, image_url)
    
    # Apply updates to state
    updated_state = {**state, **updates}
    
    return updated_state


async def force_diagnosis(state: ConversationState) -> ConversationState:
    """
    Force generation of diagnosis even if not ready.
    Used when user explicitly requests to finalize.
    
    Args:
        state: Current conversation state
    
    Returns:
        Updated state with diagnosis
    """
    # Set ready flag
    state["ready_for_diagnosis"] = True
    
    # Run diagnostic node directly
    updates = await diagnostic_node(state)
    
    # Apply updates
    updated_state = {**state, **updates}
    
    return updated_state
