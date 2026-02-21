"""
Basic tests for the agent system.
Run with: pytest tests/
"""

import pytest
from app.agents.state import (
    create_initial_state,
    calculate_confidence_score,
    should_proceed_to_diagnosis,
    AgentPhase
)


def test_create_initial_state():
    """Test that initial state is created correctly"""
    state = create_initial_state("test-session-123")
    
    assert state["session_id"] == "test-session-123"
    assert state["messages"] == []
    assert state["symptoms"] == []
    assert state["images"] == []
    assert state["current_phase"] == AgentPhase.INITIAL
    assert state["confidence_score"] == 0.0
    assert state["ready_for_diagnosis"] == False
    assert state["turn_count"] == 0


def test_calculate_confidence_score():
    """Test confidence score calculation"""
    state = create_initial_state("test-123")
    
    # Empty state should have 0 confidence
    score = calculate_confidence_score(state)
    assert score == 0.0
    
    # Add some data
    state["symptoms"] = ["dolor de cabeza", "fiebre"]
    state["patient_info"] = {"age": 35, "sex": "F"}
    state["info_categories_covered"]["chief_complaint"] = True
    state["info_categories_covered"]["symptom_onset"] = True
    
    score = calculate_confidence_score(state)
    assert score > 0.2  # Should have some confidence now


def test_should_proceed_to_diagnosis():
    """Test diagnosis readiness logic"""
    state = create_initial_state("test-123")
    
    # Empty state should not be ready
    assert should_proceed_to_diagnosis(state) == False
    
    # Set required minimums
    state["symptoms"] = ["dolor torácico"]
    state["info_categories_covered"]["chief_complaint"] = True
    state["info_categories_covered"]["symptom_onset"] = True
    state["info_categories_covered"]["severity"] = True
    state["confidence_score"] = 0.75
    state["turn_count"] = 5
    
    # Now should be ready
    assert should_proceed_to_diagnosis(state) == True


def test_max_turns_forces_diagnosis():
    """Test that max turns forces diagnosis"""
    from app.core.config import settings
    
    state = create_initial_state("test-123")
    state["symptoms"] = ["test symptom"]
    state["turn_count"] = settings.MAX_INTERVIEW_TURNS
    
    # Should proceed even with low confidence
    assert should_proceed_to_diagnosis(state) == True


@pytest.mark.asyncio
async def test_interviewer_agent_basic():
    """Basic test that interviewer agent can be instantiated"""
    from app.agents.interviewer import interviewer_agent
    
    assert interviewer_agent is not None
    assert interviewer_agent.llm is not None


@pytest.mark.asyncio
async def test_image_analyzer_agent_basic():
    """Basic test that image analyzer agent can be instantiated"""
    from app.agents.image_analyzer import image_analyzer_agent
    
    assert image_analyzer_agent is not None
    assert image_analyzer_agent.llm is not None


@pytest.mark.asyncio
async def test_diagnostic_agent_basic():
    """Basic test that diagnostic agent can be instantiated"""
    from app.agents.diagnostic import diagnostic_agent
    
    assert diagnostic_agent is not None
    assert diagnostic_agent.llm is not None


def test_orchestrator_routing():
    """Test orchestrator routing logic"""
    from app.agents.orchestrator import orchestrator
    
    state = create_initial_state("test-123")
    
    # Initial state should route to interviewer
    next_node = orchestrator.decide_next_node(state)
    assert next_node == "interviewer"
    
    # With final assessment should end
    state["final_assessment"] = {"test": "data"}
    next_node = orchestrator.decide_next_node(state)
    assert next_node == "end"
    
    # Ready for diagnosis should route to diagnostic
    state["final_assessment"] = {}
    state["ready_for_diagnosis"] = True
    next_node = orchestrator.decide_next_node(state)
    assert next_node == "diagnostic"


def test_minimum_turns_requirement():
    """Test that diagnosis requires minimum number of turns"""
    state = create_initial_state("test-123")
    
    # Even with good data, should not proceed with < 4 turns
    state["symptoms"] = ["dolor torácico"]
    state["info_categories_covered"]["chief_complaint"] = True
    state["info_categories_covered"]["symptom_onset"] = True
    state["info_categories_covered"]["severity"] = True
    state["confidence_score"] = 0.85
    state["turn_count"] = 2  # Less than minimum
    
    assert should_proceed_to_diagnosis(state) == False
    
    # With 4+ turns, should proceed
    state["turn_count"] = 4
    assert should_proceed_to_diagnosis(state) == True


def test_recommended_categories_influence():
    """Test that recommended categories help readiness decision"""
    state = create_initial_state("test-123")
    
    # Setup critical categories
    state["symptoms"] = ["dolor de cabeza"]
    state["info_categories_covered"]["chief_complaint"] = True
    state["info_categories_covered"]["symptom_onset"] = True
    state["info_categories_covered"]["severity"] = True
    state["confidence_score"] = 0.65
    state["turn_count"] = 5
    
    # Without recommended categories, might not be ready (depends on confidence)
    # But adding a recommended category should help
    state["info_categories_covered"]["symptom_duration"] = True
    
    # Recalculate confidence with more categories
    state["confidence_score"] = calculate_confidence_score(state)
    
    # Should be ready now
    assert should_proceed_to_diagnosis(state) == True


def test_high_confidence_bypasses_recommended():
    """Test that very high confidence can bypass recommended categories"""
    state = create_initial_state("test-123")
    
    # Setup minimal but critical data with high confidence
    state["symptoms"] = ["dolor torácico agudo"]
    state["patient_info"] = {"age": 45, "sex": "M"}
    state["info_categories_covered"]["chief_complaint"] = True
    state["info_categories_covered"]["symptom_onset"] = True
    state["info_categories_covered"]["severity"] = True
    state["confidence_score"] = 0.85  # High confidence
    state["turn_count"] = 5
    
    # Should proceed even without recommended categories
    assert should_proceed_to_diagnosis(state) == True


@pytest.mark.asyncio
async def test_interviewer_json_parsing():
    """Test that interviewer can parse JSON responses correctly"""
    from app.agents.interviewer import interviewer_agent
    
    # Test direct JSON
    response1 = '{"ready_for_diagnosis": true, "message": "Test message"}'
    parsed1 = interviewer_agent._parse_json_response(response1)
    assert parsed1["ready_for_diagnosis"] == True
    assert parsed1["message"] == "Test message"
    
    # Test JSON with markdown code blocks
    response2 = '```json\n{"ready_for_diagnosis": false, "message": "Next question?"}\n```'
    parsed2 = interviewer_agent._parse_json_response(response2)
    assert parsed2["ready_for_diagnosis"] == False
    assert parsed2["message"] == "Next question?"
    
    # Test JSON without language tag
    response3 = '```\n{"ready_for_diagnosis": true, "message": "Done"}\n```'
    parsed3 = interviewer_agent._parse_json_response(response3)
    assert parsed3["ready_for_diagnosis"] == True


def test_graph_route_from_interviewer_with_ready_flag():
    """Test that graph routes to diagnostic when interviewer sets ready flag"""
    from app.agents.graph import route_from_interviewer
    
    state = create_initial_state("test-123")
    state["turn_count"] = 2
    state["ready_for_diagnosis"] = True
    
    # Should route directly to diagnostic, not to ready_check
    route = route_from_interviewer(state)
    assert route == "diagnostic"


def test_graph_route_from_interviewer_periodic_check():
    """Test that graph does periodic ready checks every 3 turns"""
    from app.agents.graph import route_from_interviewer
    
    state = create_initial_state("test-123")
    
    # Turn 3 should check readiness
    state["turn_count"] = 3
    state["ready_for_diagnosis"] = False
    route = route_from_interviewer(state)
    assert route == "ready_check"
    
    # Turn 6 should also check
    state["turn_count"] = 6
    route = route_from_interviewer(state)
    assert route == "ready_check"
    
    # Turn 4 should just end (wait for user)
    state["turn_count"] = 4
    route = route_from_interviewer(state)
    assert route == "END"


def test_graph_route_priority():
    """Test that interviewer decision takes priority over periodic check"""
    from app.agents.graph import route_from_interviewer
    
    state = create_initial_state("test-123")
    state["turn_count"] = 3  # Would normally trigger ready_check
    state["ready_for_diagnosis"] = True  # But interviewer says ready
    
    # Should go directly to diagnostic, not to ready_check
    route = route_from_interviewer(state)
    assert route == "diagnostic"