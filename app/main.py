from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router, service_processor
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Automation Function API",
    description="API service for retrieving and executing automation functions using LLM + RAG",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Create startup event to initialize function registry
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the application")
    
    # Register default modules at startup
    try:
        # Make sure to register all functions from the module
        from app.functions import automation_functions
        import inspect
        
        # Explicitly register each function
        functions_registered = 0
        for name, obj in inspect.getmembers(automation_functions):
            if inspect.isfunction(obj):
                service_processor.vector_db.add_function(obj)
                functions_registered += 1
                logger.info(f"Registered function: {obj.__name__}")
        
        logger.info(f"Explicitly registered {functions_registered} functions")
    except Exception as e:
        logger.error(f"Error initializing function registry: {str(e)}", exc_info=True)

@app.get("/")
async def root():
    """Root endpoint providing basic API information."""
    return {
        "name": "Automation Function API",
        "version": "1.0.0",
        "description": "API service for retrieving and executing automation functions using LLM + RAG",
        "endpoints": {
            "execute": "/api/execute",
            "session": {
                "create": "/api/session/create",
                "history": "/api/session/history"
            },
            "registry": {
                "initialize": "/api/registry/initialize",
                "status": "/api/registry/status"
            },
            "cleanup": "/api/cleanup"
        }
    }

# For direct execution (development)
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Start uvicorn server
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True) 