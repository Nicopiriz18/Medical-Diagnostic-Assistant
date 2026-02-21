"""
Session Service: Manages conversation sessions with the database.
"""

import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.db.models import Session, Message, DiagnosticResult, SessionStatus, MessageRole
from app.agents.state import create_initial_state, ConversationState


async def create_session(
    db: AsyncSession,
    user_id: Optional[str] = None,
    patient_info: Optional[dict] = None
) -> Session:
    """Create a new conversation session"""
    session_id = str(uuid.uuid4())
    
    session = Session(
        id=session_id,
        user_id=user_id,
        status=SessionStatus.ACTIVE,
        patient_info=patient_info or {}
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session


async def get_session(
    db: AsyncSession,
    session_id: str,
    include_messages: bool = False
) -> Optional[Session]:
    """Get a session by ID"""
    query = select(Session).where(Session.id == session_id)
    
    if include_messages:
        query = query.options(selectinload(Session.messages))
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def add_message(
    db: AsyncSession,
    session_id: str,
    role: MessageRole,
    content: str,
    images: Optional[List[str]] = None,
    message_metadata: Optional[dict] = None
) -> Message:
    """Add a message to a session"""
    message = Message(
        session_id=session_id,
        role=role,
        content=content,
        images=images or [],
        message_metadata=message_metadata or {}
    )
    
    db.add(message)
    
    # Update session updated_at
    session = await get_session(db, session_id)
    if session:
        session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(message)
    
    return message


async def get_session_messages(
    db: AsyncSession,
    session_id: str,
    limit: Optional[int] = None
) -> List[Message]:
    """Get all messages for a session"""
    query = select(Message).where(Message.session_id == session_id).order_by(Message.timestamp)
    
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def save_diagnostic_result(
    db: AsyncSession,
    session_id: str,
    assessment: dict,
    confidence_score: float
) -> DiagnosticResult:
    """Save the diagnostic result for a session"""
    result = DiagnosticResult(
        session_id=session_id,
        assessment_json=assessment,
        confidence_score=confidence_score
    )
    
    db.add(result)
    
    # Update session status
    session = await get_session(db, session_id)
    if session:
        session.status = SessionStatus.COMPLETED
        session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(result)
    
    return result


async def get_diagnostic_result(
    db: AsyncSession,
    session_id: str
) -> Optional[DiagnosticResult]:
    """Get the diagnostic result for a session"""
    query = select(DiagnosticResult).where(
        DiagnosticResult.session_id == session_id
    ).order_by(DiagnosticResult.created_at.desc())
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def load_state_from_db(
    db: AsyncSession,
    session_id: str
) -> ConversationState:
    """
    Load conversation state from database.
    Reconstructs the ConversationState from stored messages and session data.
    """
    session = await get_session(db, session_id, include_messages=True)
    
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    # Create initial state
    state = create_initial_state(session_id)
    
    # Load patient info
    state["patient_info"] = session.patient_info or {}
    
    # Load messages
    messages = []
    for msg in session.messages:
        messages.append({
            "role": msg.role.value,
            "content": msg.content
        })
        
        # Extract images if any
        if msg.images:
            for img_data in msg.images:
                if isinstance(img_data, dict) and img_data not in state["images"]:
                    state["images"].append(img_data)
    
    state["messages"] = messages
    
    # Extract symptoms and other metadata from messages if stored
    # In practice, you might want to store these explicitly or extract them
    
    # Load diagnostic result if exists
    diag_result = await get_diagnostic_result(db, session_id)
    if diag_result:
        state["final_assessment"] = diag_result.assessment_json
        state["confidence_score"] = diag_result.confidence_score or 0.0
        state["ready_for_diagnosis"] = True
    
    # Update turn count
    state["turn_count"] = len([m for m in messages if m["role"] == "user"])
    
    return state


async def sync_state_to_db(
    db: AsyncSession,
    state: ConversationState
) -> None:
    """
    Sync state back to database.
    Updates session with current patient_info and other metadata.
    """
    session = await get_session(db, state["session_id"])
    
    if not session:
        return
    
    # Update patient info
    session.patient_info = state["patient_info"]
    session.updated_at = datetime.utcnow()
    
    # If diagnosis is complete, save it
    if state.get("final_assessment") and not await get_diagnostic_result(db, state["session_id"]):
        await save_diagnostic_result(
            db=db,
            session_id=state["session_id"],
            assessment=state["final_assessment"],
            confidence_score=state.get("confidence_score", 0.0)
        )
    
    await db.commit()
