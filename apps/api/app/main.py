from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import asyncio
import json

from app.models.clinical import AnalyzeRequest, AnalyzeResponse
from app.models.session import (
    SessionCreate,
    SessionResponse,
    MessageCreate,
    MessageResponse,
    ImageUploadResponse
)
from app.services.analyzer import analyze_case
from app.services import session_service
from app.services.storage import storage_service
from app.db.base import get_db
from app.db.models import MessageRole
from app.agents.graph import process_user_message, process_image_upload, force_diagnosis
from app.core.config import settings

app = FastAPI(title="Medical Diagnostic Assistant", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod: restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for local storage
if not settings.use_s3:
    uploads_path = Path(settings.LOCAL_STORAGE_PATH)
    uploads_path.mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

@app.get("/health")
def health():
    return {"ok": True}

# ============= LEGACY ENDPOINT (backward compatibility) =============

@app.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """Legacy endpoint: One-shot analysis without conversation"""
    try:
        assessment = await analyze_case(req.case_text)
        return {"assessment": assessment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= NEW AGENT-BASED ENDPOINTS =============

@app.post("/v1/sessions", response_model=SessionResponse)
async def create_session(
    req: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation session"""
    try:
        session = await session_service.create_session(
            db=db,
            user_id=req.user_id,
            patient_info=req.patient_info
        )
        
        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            status=session.status,
            patient_info=session.patient_info,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get session details with message history"""
    try:
        session = await session_service.get_session(db, session_id, include_messages=True)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Convert messages
        messages = [
            MessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                images=msg.images,
                message_metadata=msg.message_metadata,
                timestamp=msg.timestamp
            )
            for msg in session.messages
        ]
        
        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            status=session.status,
            patient_info=session.patient_info,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=messages
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    req: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a user message and get agent response.
    This processes the message through the agent graph.
    """
    try:
        # Verify session exists
        session = await session_service.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Save user message
        await session_service.add_message(
            db=db,
            session_id=session_id,
            role=MessageRole.USER,
            content=req.content,
            images=req.images
        )
        
        # Load current state
        state = await session_service.load_state_from_db(db, session_id)
        
        # Process through agent graph
        updated_state = await process_user_message(state, req.content)
        
        # Sync state back to DB
        await session_service.sync_state_to_db(db, updated_state)
        
        # Get the last assistant message
        if updated_state["messages"] and updated_state["messages"][-1]["role"] == "assistant":
            assistant_msg_content = updated_state["messages"][-1]["content"]
            
            # Save assistant message
            assistant_msg = await session_service.add_message(
                db=db,
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=assistant_msg_content,
                message_metadata={
                    "confidence_score": updated_state.get("confidence_score", 0.0),
                    "phase": updated_state.get("current_phase", "interview")
                }
            )
            
            return MessageResponse(
                id=assistant_msg.id,
                session_id=assistant_msg.session_id,
                role=assistant_msg.role,
                content=assistant_msg.content,
                images=assistant_msg.images,
                message_metadata=assistant_msg.message_metadata,
                timestamp=assistant_msg.timestamp
            )
        else:
            raise HTTPException(status_code=500, detail="Agent did not generate response")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/sessions/{session_id}/images", response_model=ImageUploadResponse)
async def upload_image(
    session_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload and analyze a medical image"""
    try:
        # Verify session exists
        session = await session_service.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Save image
        file_url, metadata = await storage_service.save_image(file, session_id)
        
        # Load current state
        state = await session_service.load_state_from_db(db, session_id)
        
        # Process image through analyzer
        updated_state = await process_image_upload(state, file_url)
        
        # Sync state back to DB
        await session_service.sync_state_to_db(db, updated_state)
        
        # Save the analysis message if generated
        if updated_state["messages"] and updated_state["messages"][-1]["role"] == "assistant":
            assistant_msg_content = updated_state["messages"][-1]["content"]
            
            await session_service.add_message(
                db=db,
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=assistant_msg_content,
                images=[file_url],
                message_metadata={"image_analysis": True}
            )
        
        return ImageUploadResponse(
            url=file_url,
            filename=metadata["filename"],
            size=metadata["size"],
            content_type=metadata["content_type"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/sessions/{session_id}/finalize")
async def finalize_diagnosis(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Force finalization and generation of diagnosis with real-time progress updates.
    Returns a stream of Server-Sent Events (SSE) with progress updates.
    """
    async def generate_progress_stream():
        try:
            # Verify session exists
            session = await session_service.get_session(db, session_id)
            if not session:
                yield f"event: error\ndata: {json.dumps({'error': 'Session not found'})}\n\n"
                return
            
            # Load current state
            state = await session_service.load_state_from_db(db, session_id)
            
            # Send initial progress update
            yield f"event: progress\ndata: {json.dumps({'type': 'progress', 'message': 'Iniciando análisis diagnóstico...'})}\n\n"
            await asyncio.sleep(0.5)
            
            # Import diagnostic agent
            from app.agents.diagnostic import diagnostic_agent
            
            # Set ready flag
            state["ready_for_diagnosis"] = True
            
            # Phase 1
            yield f"event: progress\ndata: {json.dumps({'type': 'progress', 'message': 'Revisando información del caso y síntomas presentados...'})}\n\n"
            await asyncio.sleep(2.5)
            
            # Phase 2
            yield f"event: progress\ndata: {json.dumps({'type': 'progress', 'message': 'Consultando base de conocimiento médico y casos similares...'})}\n\n"
            await asyncio.sleep(2.0)
            
            # Phase 3
            yield f"event: progress\ndata: {json.dumps({'type': 'progress', 'message': 'Analizando diagnósticos diferenciales y evaluando probabilidades...'})}\n\n"
            await asyncio.sleep(2.5)
            
            # Phase 4
            yield f"event: progress\ndata: {json.dumps({'type': 'progress', 'message': 'Generando evaluación clínica estructurada y plan de acción...'})}\n\n"
            
            # Run the actual diagnostic agent (without the built-in delays since we're doing them here)
            updates = await diagnostic_agent.run(state, progress_callback=None)
            
            await asyncio.sleep(1.5)
            
            # Phase 5
            yield f"event: progress\ndata: {json.dumps({'type': 'progress', 'message': 'Finalizando evaluación y preparando recomendaciones...'})}\n\n"
            await asyncio.sleep(1.5)
            
            # Apply updates
            from app.agents.state import AgentPhase
            updated_state = {**state, **updates}
            updated_state["current_phase"] = AgentPhase.COMPLETED
            
            # Sync state back to DB
            await session_service.sync_state_to_db(db, updated_state)
            
            # Save the diagnosis message
            if updated_state["messages"] and updated_state["messages"][-1]["role"] == "assistant":
                assistant_msg_content = updated_state["messages"][-1]["content"]
                
                await session_service.add_message(
                    db=db,
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=assistant_msg_content,
                    message_metadata={"final_diagnosis": True}
                )
            
            # Send completion event
            completion_data = {
                "type": "complete",
                "status": "completed",
                "assessment": updated_state.get("final_assessment")
            }
            yield f"event: complete\ndata: {json.dumps(completion_data)}\n\n"
        
        except Exception as e:
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/v1/sessions/{session_id}/diagnosis")
async def get_diagnosis(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the diagnostic result for a session"""
    try:
        result = await session_service.get_diagnostic_result(db, session_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Diagnosis not yet available")
        
        return {
            "assessment": result.assessment_json,
            "confidence_score": result.confidence_score,
            "created_at": result.created_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
