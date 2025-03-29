import os
import sys
import logging
import uvicorn
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("automation_api")

def main():
    """Run the Automation Function API service."""
    try:
        # Ensure we're in the correct directory
        current_dir = Path(__file__).parent.absolute()
        os.chdir(current_dir)
        
        # Add the current directory to the Python path if not already there
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        # Get port from environment or use default
        port = int(os.environ.get("PORT", 8000))
        
        logger.info(f"Starting Automation Function API on port {port}")
        logger.info(f"API will be available at http://localhost:{port}")
        logger.info("Press Ctrl+C to stop the server")
        
        # Start the uvicorn server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 