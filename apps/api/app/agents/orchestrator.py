"""
Orchestrator: Manages the flow between agents and decides next actions.
"""

from typing import Dict, Any, Literal
from app.agents.state import (
    ConversationState,
    AgentPhase,
    should_proceed_to_diagnosis,
    calculate_confidence_score
)

class Orchestrator:
    """Orchestrator that decides which agent should act next"""
    
    def decide_next_node(self, state: ConversationState) -> Literal[
        "interviewer",
        "image_analyzer", 
        "ready_check",
        "diagnostic",
        "end"
    ]:
        """
        Decide which node/agent should execute next based on current state.
        
        Returns:
            Name of the next node to execute
        """
        current_phase = state.get("current_phase", AgentPhase.INITIAL)
        
        # If we already have a final assessment, we're done
        if state.get("final_assessment"):
            return "end"
        
        # Priority 1: If ready for diagnosis flag is set (by interviewer or manually), go to diagnosis
        if state.get("ready_for_diagnosis", False):
            return "diagnostic"
        
        # Priority 2: Check if we should proceed to diagnosis based on info completeness (backup)
        if should_proceed_to_diagnosis(state):
            return "ready_check"
        
        # If there are new images to analyze (not yet analyzed)
        # This would be triggered by the image upload endpoint
        # For now, default behavior continues to interviewer
        
        # Default: continue interview
        return "interviewer"
    
    def should_analyze_image(self, state: ConversationState) -> bool:
        """Check if there are images pending analysis"""
        # This is a simplified check - in practice, we'd track which images
        # have been analyzed vs just uploaded
        return False  # Images are analyzed immediately on upload
    
    def transition_phase(
        self,
        state: ConversationState,
        new_phase: AgentPhase
    ) -> Dict[str, Any]:
        """
        Transition to a new phase.
        
        Returns:
            State updates
        """
        return {
            "current_phase": new_phase
        }


# Singleton
orchestrator = Orchestrator()


def route_after_user_message(state: ConversationState) -> str:
    """
    Routing function called after processing a user message.
    Decides whether to continue interview or move to diagnosis.
    """
    return orchestrator.decide_next_node(state)


def route_after_ready_check(state: ConversationState) -> str:
    """
    Routing after checking if ready for diagnosis.
    """
    if state.get("ready_for_diagnosis", False):
        return "diagnostic"
    else:
        return "interviewer"


def route_after_image_analysis(state: ConversationState) -> str:
    """
    Routing after image analysis.
    Always returns to interviewer to ask follow-up questions about the image.
    """
    return "interviewer"
