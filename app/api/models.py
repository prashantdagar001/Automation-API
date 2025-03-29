from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class ExecuteRequest(BaseModel):
    prompt: str = Field(..., description="User prompt requesting a function")
    session_id: Optional[str] = Field(None, description="Session ID for context continuation")

class ExecuteResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    function: Optional[str] = Field(None, description="The function ID that was executed")
    function_name: Optional[str] = Field(None, description="The name of the function that was executed")
    relevance_score: Optional[float] = Field(None, description="Relevance score of the function match")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters used in function execution")
    code: Optional[str] = Field(None, description="Generated executable code")
    execution_result: Optional[Dict[str, Any]] = Field(None, description="Result of function execution")
    error: Optional[str] = Field(None, description="Error message if the request failed")
    prompt: str = Field(..., description="Original user prompt")
    session_id: str = Field(..., description="Session ID for context continuation")

class SessionRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Session ID to retrieve history for")

class SessionHistoryResponse(BaseModel):
    session_id: str = Field(..., description="Session ID")
    history: List[Dict[str, Any]] = Field(..., description="Session interaction history")
    context: Dict[str, Any] = Field(..., description="Session context data")

class RegistryInitRequest(BaseModel):
    module_paths: List[str] = Field(..., description="List of module paths to register functions from")

class RegistryInitResponse(BaseModel):
    results: Dict[str, Any] = Field(..., description="Results of function registration by module") 