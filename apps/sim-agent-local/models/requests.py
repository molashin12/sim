#!/usr/bin/env python3
"""
Request and response models for Local SIM Agent API

Defines Pydantic models for all API endpoints to ensure
type safety and validation.
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field

# Chat models
class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")

class ToolFunction(BaseModel):
    """Tool function definition"""
    name: str = Field(..., description="Function name")
    description: Optional[str] = Field(None, description="Function description")
    parameters: Dict[str, Any] = Field(..., description="Function parameters schema")

class Tool(BaseModel):
    """Tool definition"""
    type: str = Field(default="function", description="Tool type")
    function: ToolFunction = Field(..., description="Function definition")

class ChatRequest(BaseModel):
    """Chat completion request"""
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    tools: Optional[List[Tool]] = Field(None, description="Available tools")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    stream: bool = Field(default=True, description="Enable streaming")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=4000, gt=0, description="Maximum tokens to generate")

class ChatResponse(BaseModel):
    """Chat completion response"""
    content: Optional[str] = Field(None, description="Response content")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls")
    finish_reason: Optional[str] = Field(None, description="Completion finish reason")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage")

# YAML processing models
class YAMLToWorkflowRequest(BaseModel):
    """YAML to workflow conversion request"""
    yaml_content: str = Field(..., description="YAML workflow content")
    description: Optional[str] = Field(None, description="Natural language description")
    block_registry: Dict[str, Any] = Field(..., description="Available block types")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class WorkflowToYAMLRequest(BaseModel):
    """Workflow to YAML conversion request"""
    workflow_state: Dict[str, Any] = Field(..., description="Workflow state")
    format_options: Optional[Dict[str, Any]] = Field(None, description="Formatting options")

class YAMLParseRequest(BaseModel):
    """YAML parsing request"""
    yaml_content: str = Field(..., description="YAML content to parse")
    operations: List[Dict[str, Any]] = Field(..., description="Operations to apply")
    block_registry: Dict[str, Any] = Field(..., description="Available block types")

class YAMLDiffCreateRequest(BaseModel):
    """YAML diff creation request"""
    original_yaml: str = Field(..., description="Original YAML content")
    target_yaml: str = Field(..., description="Target YAML content")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class YAMLDiffMergeRequest(BaseModel):
    """YAML diff merge request"""
    original_yaml: str = Field(..., description="Original YAML content")
    diff: Dict[str, Any] = Field(..., description="Diff to apply")
    merge_strategy: str = Field(default="smart", description="Merge strategy")

class AutoLayoutRequest(BaseModel):
    """Auto-layout request"""
    workflow_state: Dict[str, Any] = Field(..., description="Workflow state")
    layout_options: Optional[Dict[str, Any]] = Field(None, description="Layout options")
    algorithm: str = Field(default="smart", description="Layout algorithm")

# Tool management models
class ToolCompleteRequest(BaseModel):
    """Tool completion request"""
    tool_id: str = Field(..., description="Tool identifier")
    status: str = Field(..., description="Completion status")
    result: Optional[Dict[str, Any]] = Field(None, description="Tool result")
    error: Optional[str] = Field(None, description="Error message if failed")

# API key management models
class APIKeyGenerateRequest(BaseModel):
    """API key generation request"""
    name: str = Field(..., description="Key name")
    permissions: List[str] = Field(default=["read", "write"], description="Key permissions")
    expires_at: Optional[str] = Field(None, description="Expiration date (ISO format)")

class APIKeyResponse(BaseModel):
    """API key response"""
    id: str = Field(..., description="Key ID")
    name: str = Field(..., description="Key name")
    key: Optional[str] = Field(None, description="API key (only on creation)")
    permissions: List[str] = Field(..., description="Key permissions")
    created_at: str = Field(..., description="Creation date")
    expires_at: Optional[str] = Field(None, description="Expiration date")
    last_used: Optional[str] = Field(None, description="Last used date")

class APIKeyDeleteRequest(BaseModel):
    """API key deletion request"""
    key_id: str = Field(..., description="Key ID to delete")

class ValidateKeyRequest(BaseModel):
    """API key validation request"""
    api_key: str = Field(..., description="API key to validate")
    permissions: Optional[List[str]] = Field(None, description="Required permissions")
    context: Optional[Dict[str, Any]] = Field(None, description="Validation context")

# Stats and analytics models
class StatsRequest(BaseModel):
    """Stats reporting request"""
    event_type: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: Optional[str] = Field(None, description="Event timestamp")
    user_id: Optional[str] = Field(None, description="User identifier")

# Generic response models
class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = Field(default=True, description="Success status")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = Field(default=False, description="Success status")
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")

# Validation response models
class ValidationResult(BaseModel):
    """Validation result"""
    valid: bool = Field(..., description="Validation status")
    errors: List[str] = Field(default=[], description="Validation errors")
    warnings: List[str] = Field(default=[], description="Validation warnings")
    suggestions: List[str] = Field(default=[], description="Improvement suggestions")

class WorkflowValidationResponse(BaseModel):
    """Workflow validation response"""
    validation: ValidationResult = Field(..., description="Validation result")
    processed_workflow: Optional[Dict[str, Any]] = Field(None, description="Processed workflow")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")