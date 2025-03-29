from typing import Dict, List, Any, Optional
import time
import uuid

class ContextManager:
    def __init__(self, max_history_length: int = 10):
        """Initialize the context manager for session management."""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_history_length = max_history_length
    
    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": time.time(),
            "last_activity": time.time(),
            "history": [],
            "context": {}
        }
        return session_id
    
    def add_interaction(self, session_id: str, prompt: str, function_id: Optional[str] = None, 
                         result: Optional[Any] = None) -> None:
        """Add an interaction to the session history."""
        if session_id not in self.sessions:
            session_id = self.create_session()
        
        # Update last activity time
        self.sessions[session_id]["last_activity"] = time.time()
        
        # Create interaction record
        interaction = {
            "timestamp": time.time(),
            "prompt": prompt,
            "function_id": function_id,
            "result": result
        }
        
        # Add to history and maintain max length
        history = self.sessions[session_id]["history"]
        history.append(interaction)
        
        if len(history) > self.max_history_length:
            self.sessions[session_id]["history"] = history[-self.max_history_length:]
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the interaction history for a session."""
        if session_id not in self.sessions:
            return []
        
        return self.sessions[session_id]["history"]
    
    def update_context(self, session_id: str, key: str, value: Any) -> None:
        """Update a context value for the session."""
        if session_id not in self.sessions:
            session_id = self.create_session()
        
        self.sessions[session_id]["context"][key] = value
    
    def get_context(self, session_id: str, key: str) -> Any:
        """Get a context value from the session."""
        if session_id not in self.sessions:
            return None
        
        return self.sessions[session_id]["context"].get(key)
    
    def get_full_context(self, session_id: str) -> Dict[str, Any]:
        """Get the complete context for a session."""
        if session_id not in self.sessions:
            return {}
        
        return self.sessions[session_id]["context"]
    
    def enhance_prompt_with_history(self, session_id: str, prompt: str) -> str:
        """Enhance the user prompt with relevant history information."""
        if session_id not in self.sessions or not self.sessions[session_id]["history"]:
            return prompt
        
        # Get recent successful interactions
        history = self.sessions[session_id]["history"]
        recent_successful = [
            item for item in history 
            if item.get("function_id") and 
               isinstance(item.get("result"), dict) and 
               item.get("result", {}).get("success", False)
        ]
        
        if not recent_successful:
            return prompt
        
        # Create context from history
        context_info = []
        for item in recent_successful[-3:]:  # Use last 3 successful interactions
            function_name = item["function_id"].split(".")[-1] if item.get("function_id") else "unknown"
            original_prompt = item.get("prompt", "")
            result_summary = str(item.get("result", {}).get("result", ""))[:100]  # Truncate long results
            
            context_info.append(f"- You previously asked: '{original_prompt}', which executed '{function_name}' with result: '{result_summary}'")
        
        # Build enhanced prompt
        enhanced_prompt = f"""With this context from your previous interactions:
{chr(10).join(context_info)}

Current request: {prompt}"""
        
        return enhanced_prompt
    
    def clean_old_sessions(self, max_age_seconds: int = 3600) -> int:
        """Clean up sessions older than the specified age."""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time - session["last_activity"] > max_age_seconds
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        return len(expired_sessions) 