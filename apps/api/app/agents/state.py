from typing import TypedDict, List, Dict, Any, Literal
from enum import Enum

class AgentPhase(str, Enum):
    """Current phase of the conversation"""
    INITIAL = "initial"
    INTERVIEW = "interview"
    IMAGE_ANALYSIS = "image_analysis"
    READY_CHECK = "ready_check"
    DIAGNOSIS = "diagnosis"
    COMPLETED = "completed"

class ConversationState(TypedDict):
    """
    Shared state for the agent conversation system.
    This state is passed between all agents in the LangGraph.
    """
    
    # Session identification
    session_id: str
    
    # Conversation messages
    messages: List[Dict[str, str]]  # [{"role": "user/assistant", "content": "..."}]
    
    # Patient information collected
    patient_info: Dict[str, Any]  # {"age": 45, "sex": "M", "medical_history": [...]}
    
    # Symptoms mentioned
    symptoms: List[str]
    
    # Images uploaded with analysis
    images: List[Dict[str, Any]]  # [{"url": "...", "analysis": {...}, "timestamp": "..."}]
    
    # Current phase of conversation
    current_phase: str  # AgentPhase value
    
    # Questions already asked (to avoid repetition)
    questions_asked: List[str]
    
    # Categories of information collected
    info_categories_covered: Dict[str, bool]  # {"chief_complaint": True, "duration": True, ...}
    
    # Confidence that we have enough information
    confidence_score: float  # 0.0 to 1.0
    
    # Ready for diagnosis flag
    ready_for_diagnosis: bool
    
    # Final assessment (once diagnosis is generated)
    final_assessment: Dict[str, Any]  # ClinicalAssessment as dict
    
    # Internal agent metadata
    turn_count: int
    last_agent: str  # Which agent last acted


# Required information categories for a complete assessment
REQUIRED_INFO_CATEGORIES = {
    "chief_complaint": "Main reason for consultation",
    "symptom_onset": "When symptoms started",
    "symptom_duration": "How long symptoms have lasted",
    "symptom_progression": "How symptoms have changed over time",
    "severity": "How severe the symptoms are",
    "associated_symptoms": "Other symptoms accompanying the main complaint",
    "medical_history": "Past medical conditions",
    "medications": "Current medications",
    "allergies": "Known allergies",
    "social_history": "Relevant lifestyle factors (smoking, alcohol, etc.)",
}

def create_initial_state(session_id: str) -> ConversationState:
    """Create a new initial conversation state"""
    return ConversationState(
        session_id=session_id,
        messages=[],
        patient_info={},
        symptoms=[],
        images=[],
        current_phase=AgentPhase.INITIAL,
        questions_asked=[],
        info_categories_covered={cat: False for cat in REQUIRED_INFO_CATEGORIES.keys()},
        confidence_score=0.0,
        ready_for_diagnosis=False,
        final_assessment={},
        turn_count=0,
        last_agent="",
    )

def calculate_confidence_score(state: ConversationState) -> float:
    """
    Calculate confidence score based on information completeness.
    
    Returns a score from 0.0 to 1.0 indicating how complete the assessment is.
    """
    # Count covered categories
    categories_covered = sum(state["info_categories_covered"].values())
    total_categories = len(REQUIRED_INFO_CATEGORIES)
    
    # Base score from category coverage
    category_score = categories_covered / total_categories
    
    # Bonus for having symptoms
    symptom_bonus = 0.1 if len(state["symptoms"]) > 0 else 0
    
    # Bonus for having patient demographics
    demo_bonus = 0.1 if state["patient_info"].get("age") and state["patient_info"].get("sex") else 0
    
    # Bonus for having images (if relevant)
    image_bonus = 0.05 if len(state["images"]) > 0 else 0
    
    # Calculate final score (capped at 1.0)
    confidence = min(1.0, category_score + symptom_bonus + demo_bonus + image_bonus)
    
    return confidence

def should_proceed_to_diagnosis(state: ConversationState) -> bool:
    """
    Determine if we have enough information to proceed to diagnosis.
    This is a backup check in case the interviewer LLM doesn't decide automatically.
    
    Returns True if:
    - Max turns reached (forced completion), OR
    - All of the following conditions are met:
      * Minimum turns threshold (at least 4 substantial exchanges)
      * Confidence score is above threshold
      * Critical categories are covered
      * Has symptoms identified
    """
    from app.core.config import settings
    
    # Check if max turns reached (forced completion for safety)
    if state["turn_count"] >= settings.MAX_INTERVIEW_TURNS:
        return True
    
    # Minimum turns requirement (avoid premature diagnosis)
    MINIMUM_TURNS = 4
    if state["turn_count"] < MINIMUM_TURNS:
        return False
    
    # Check confidence threshold
    if state["confidence_score"] < settings.CONFIDENCE_THRESHOLD:
        return False
    
    # Check critical categories (these are must-haves)
    critical_categories = ["chief_complaint", "symptom_onset", "severity"]
    critical_covered = all(
        state["info_categories_covered"].get(cat, False)
        for cat in critical_categories
    )
    
    if not critical_covered:
        return False
    
    # Check we have at least some symptoms
    if len(state["symptoms"]) == 0:
        return False
    
    # Optional but recommended categories for better assessment
    recommended_categories = ["symptom_duration", "associated_symptoms"]
    recommended_count = sum(
        1 for cat in recommended_categories
        if state["info_categories_covered"].get(cat, False)
    )
    
    # If we have critical info + at least one recommended category, we're good
    if recommended_count >= 1:
        return True
    
    # If confidence is very high (>= 0.8), proceed even without recommended categories
    if state["confidence_score"] >= 0.8:
        return True
    
    return False
