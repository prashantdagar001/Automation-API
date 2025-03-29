from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.api.models import (
    ExecuteRequest, ExecuteResponse, 
    SessionRequest, SessionHistoryResponse,
    RegistryInitRequest, RegistryInitResponse
)
from app.core.service_processor import ServiceProcessor
from typing import Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Create service processor instance
service_processor = ServiceProcessor()

@router.post("/execute", response_model=ExecuteResponse)
async def execute_function(request: ExecuteRequest):
    """Execute a function based on the user prompt."""
    logger.info(f"Received execute request: {request.prompt[:50]}...")
    
    # Process the request
    result = service_processor.process_request(request.prompt, request.session_id)
    
    # Return the result
    return result

@router.post("/session/history", response_model=SessionHistoryResponse)
async def get_session_history(request: SessionRequest):
    """Get the history for a specific session."""
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")
    
    # Get session history
    history = service_processor.context_manager.get_session_history(request.session_id)
    context = service_processor.context_manager.get_full_context(request.session_id)
    
    if not history:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    return {
        "session_id": request.session_id,
        "history": history,
        "context": context
    }

@router.post("/session/create")
async def create_session():
    """Create a new session."""
    session_id = service_processor.context_manager.create_session()
    return {"session_id": session_id}

@router.post("/registry/initialize", response_model=RegistryInitResponse)
async def initialize_registry(request: RegistryInitRequest, background_tasks: BackgroundTasks):
    """Initialize the function registry with specified modules."""
    # Run initialization in background task to prevent blocking
    def init_registry(module_paths):
        return service_processor.initialize_function_registry(module_paths)
    
    # For immediate response, start processing but return quickly
    background_tasks.add_task(init_registry, request.module_paths)
    
    return {
        "results": {
            "status": "initialization_started",
            "modules": request.module_paths
        }
    }

@router.get("/registry/status")
async def registry_status():
    """Get the status of the function registry."""
    # This would be more complex in a real implementation with proper status tracking
    collection_info = service_processor.vector_db.count()
    
    return {
        "status": "active",
        "function_count": collection_info,
        "db_path": service_processor.vector_db.persist_directory
    }

@router.post("/cleanup")
async def cleanup_sessions(background_tasks: BackgroundTasks):
    """Clean up old sessions."""
    def cleanup():
        return service_processor.context_manager.clean_old_sessions()
    
    background_tasks.add_task(cleanup)
    
    return {"status": "cleanup_started"} 