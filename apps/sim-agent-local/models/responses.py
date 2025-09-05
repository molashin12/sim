#!/usr/bin/env python3
"""
Response models for Local SIM Agent API

Defines Pydantic models for API responses to ensure
type safety and validation.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .requests import ValidationResult

# YAML processing response models
class YAMLToWorkflowResponse(BaseModel):
    """YAML to workflow conversion response"""
    workflow_state: Dict[str, Any] = Field(..., description="Generated workflow state")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Conversion metadata")
    validation: Optional[ValidationResult] = Field(None, description="Validation result")
    suggestions: List[str] = Field(default=[], description="Optimization suggestions")

class WorkflowToYAMLResponse(BaseModel):
    """Workflow to YAML conversion response"""
    yaml_content: str = Field(..., description="Generated YAML content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Conversion metadata")
    validation: Optional[ValidationResult] = Field(None, description="Validation result")
    formatting_info: Optional[Dict[str, Any]] = Field(None, description="Formatting information")

class YAMLParseResponse(BaseModel):
    """YAML parsing response"""
    parsed_data: Dict[str, Any] = Field(..., description="Parsed YAML data")
    operations_applied: List[Dict[str, Any]] = Field(default=[], description="Applied operations")
    validation: Optional[ValidationResult] = Field(None, description="Validation result")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Parsing metadata")

class YAMLDiffCreateResponse(BaseModel):
    """YAML diff creation response"""
    diff: Dict[str, Any] = Field(..., description="Generated diff")
    summary: str = Field(..., description="Human-readable diff summary")
    impact_analysis: Optional[Dict[str, Any]] = Field(None, description="Impact analysis")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Diff metadata")

class YAMLDiffMergeResponse(BaseModel):
    """YAML diff merge response"""
    merged_yaml: str = Field(..., description="Merged YAML content")
    conflicts: List[Dict[str, Any]] = Field(default=[], description="Merge conflicts")
    resolution_strategy: str = Field(..., description="Applied resolution strategy")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Merge metadata")

class AutoLayoutResponse(BaseModel):
    """Auto layout response"""
    layout_data: Dict[str, Any] = Field(..., description="Generated layout data")
    algorithm_used: str = Field(..., description="Layout algorithm used")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Layout performance metrics")
    suggestions: List[str] = Field(default=[], description="Layout optimization suggestions")

# Tool response models
class ToolExecutionResponse(BaseModel):
    """Tool execution response"""
    tool_id: str = Field(..., description="Tool identifier")
    status: str = Field(..., description="Execution status")
    result: Optional[Dict[str, Any]] = Field(None, description="Tool execution result")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Execution metadata")

class ToolCompleteResponse(BaseModel):
    """Tool completion response"""
    success: bool = Field(..., description="Completion success status")
    tool_id: str = Field(..., description="Tool identifier")
    completion_time: Optional[str] = Field(None, description="Completion timestamp")
    next_actions: List[str] = Field(default=[], description="Suggested next actions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Completion metadata")
    errors: List[str] = Field(default=[], description="Error messages")
    warnings: List[str] = Field(default=[], description="Warning messages")

class ToolListResponse(BaseModel):
    """Tool list response"""
    tools: List[Dict[str, Any]] = Field(..., description="Available tools")
    categories: List[str] = Field(default=[], description="Tool categories")
    total_count: int = Field(..., description="Total number of tools")
    metadata: Optional[Dict[str, Any]] = Field(None, description="List metadata")

# Health and monitoring response models
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    uptime: float = Field(..., description="Service uptime in seconds")
    dependencies: Dict[str, str] = Field(default={}, description="Dependency status")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Health metrics")

class MetricsResponse(BaseModel):
    """Metrics response"""
    metrics: Dict[str, Any] = Field(..., description="Service metrics")
    timestamp: str = Field(..., description="Metrics timestamp")
    period: Optional[str] = Field(None, description="Metrics collection period")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metrics metadata")

# Workflow response models
class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response"""
    execution_id: str = Field(..., description="Execution identifier")
    status: str = Field(..., description="Execution status")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Execution progress")
    current_step: Optional[str] = Field(None, description="Current execution step")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Execution metadata")

class WorkflowValidationResponse(BaseModel):
    """Workflow validation response"""
    validation: ValidationResult = Field(..., description="Validation result")
    processed_workflow: Optional[Dict[str, Any]] = Field(None, description="Processed workflow")
    optimization_suggestions: List[str] = Field(default=[], description="Optimization suggestions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Validation metadata")

# Authentication response models
class ValidateKeyResponse(BaseModel):
    """API key validation response"""
    valid: bool = Field(..., description="Validation status")
    key_info: Optional[Dict[str, Any]] = Field(None, description="Key information")
    permissions: List[str] = Field(default=[], description="Key permissions")
    expires_at: Optional[str] = Field(None, description="Key expiration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Validation metadata")