#!/usr/bin/env python3
"""
YAML Processing API endpoints for Local SIM Agent API

Handles YAML to workflow conversion, parsing, validation,
and other YAML-related operations.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.requests import (
    YAMLToWorkflowRequest, WorkflowToYAMLRequest,
    YAMLParseRequest, YAMLDiffCreateRequest, YAMLDiffMergeRequest,
    AutoLayoutRequest, SuccessResponse, ErrorResponse
)
from models.responses import (
    YAMLToWorkflowResponse, WorkflowToYAMLResponse,
    YAMLParseResponse, YAMLDiffCreateResponse, YAMLDiffMergeResponse,
    AutoLayoutResponse
)
from services.llm_service import LLMService
from services.yaml_service import YamlService
from config.settings import get_settings
from utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)

def get_llm_service(request: Request) -> LLMService:
    """Get LLM service from app state"""
    return request.app.state.llm_service

def get_yaml_service(request: Request) -> YamlService:
    """Get YAML service from app state"""
    return request.app.state.yaml_service

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key (optional for local service)"""
    return True

@router.post("/yaml/to-workflow", response_model=YAMLToWorkflowResponse)
async def yaml_to_workflow(
    request_data: YAMLToWorkflowRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    yaml_service: YamlService = Depends(get_yaml_service),
    authorized: bool = Depends(verify_api_key)
):
    """Convert natural language description to workflow YAML
    
    This endpoint matches the external SIM Agent API interface:
    POST /api/yaml/to-workflow
    """
    try:
        logger.info(f"Converting description to workflow: {request_data.description[:100]}...")
        
        # Use LLM to convert description to workflow
        workflow_yaml = await yaml_service.description_to_workflow(
            description=request_data.description,
            context=request_data.context,
            llm_service=llm_service
        )
        
        # Validate the generated YAML
        validation_result = yaml_service.validate_workflow_yaml(workflow_yaml)
        
        if not validation_result.is_valid:
            logger.warning(f"Generated YAML validation failed: {validation_result.errors}")
            # Try to fix common issues
            workflow_yaml = yaml_service.fix_common_yaml_issues(workflow_yaml)
            validation_result = yaml_service.validate_workflow_yaml(workflow_yaml)
        
        return YAMLToWorkflowResponse(
            workflow_state=parse_result.data if parse_result.success else {},
            validation=validation_result,
            metadata={
                "generated_blocks": yaml_service.count_blocks(workflow_yaml),
                "has_triggers": yaml_service.has_triggers(workflow_yaml),
                "complexity_score": yaml_service.calculate_complexity(workflow_yaml)
            }
        )
    
    except Exception as e:
        logger.error(f"YAML to workflow conversion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/yaml/parse", response_model=YAMLParseResponse)
async def yaml_parse(
    request_data: YAMLParseRequest,
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service),
    authorized: bool = Depends(verify_api_key)
):
    """Parse and validate YAML workflow
    
    This endpoint matches the external SIM Agent API interface:
    POST /api/yaml/parse
    """
    try:
        logger.info("Parsing YAML workflow")
        
        # Parse the YAML
        parse_result = yaml_service.parse_yaml(request_data.yaml)
        
        if not parse_result.success:
            return YAMLParseResponse(
                parsed_data={},
                validation=None,
                metadata={"errors": parse_result.errors, "warnings": parse_result.warnings}
            )
        
        # Validate workflow structure
        validation_result = yaml_service.validate_workflow_yaml(request_data.yaml)
        
        # Extract workflow metadata
        metadata = yaml_service.extract_metadata(request_data.yaml)
        
        return YAMLParseResponse(
            parsed_data=parse_result.data,
            validation=validation_result,
            metadata=metadata
        )
    
    except Exception as e:
        logger.error(f"YAML parsing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/yaml/diff/create", response_model=YAMLDiffCreateResponse)
async def yaml_diff_create(
    request_data: YAMLDiffCreateRequest,
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service),
    llm_service: LLMService = Depends(get_llm_service),
    authorized: bool = Depends(verify_api_key)
):
    """Create intelligent diff between two YAML workflows
    
    This endpoint matches the external SIM Agent API interface:
    POST /api/yaml/diff/create
    """
    try:
        logger.info("Creating YAML diff")
        
        # Create semantic diff
        diff_result = await yaml_service.create_intelligent_diff(
            original_yaml=request_data.original_yaml,
            modified_yaml=request_data.modified_yaml,
            llm_service=llm_service
        )
        
        return YAMLDiffCreateResponse(
            diff=diff_result.diff,
            summary=diff_result.summary,
            impact_analysis={
                "total_changes": len(diff_result.changes) if hasattr(diff_result, 'changes') else 0,
                "change_types": getattr(diff_result, 'change_types', []),
                "complexity_delta": getattr(diff_result, 'complexity_delta', 0)
            },
            metadata={}
        )
    
    except Exception as e:
        logger.error(f"YAML diff creation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/yaml/diff/merge", response_model=YAMLDiffMergeResponse)
async def yaml_diff_merge(
    request_data: YAMLDiffMergeRequest,
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service),
    authorized: bool = Depends(verify_api_key)
):
    """Merge diff into YAML workflow
    
    This endpoint matches the external SIM Agent API interface:
    POST /api/yaml/diff/merge
    """
    try:
        logger.info("Merging YAML diff")
        
        # Apply diff to original YAML
        merge_result = yaml_service.merge_diff(
            original_yaml=request_data.original_yaml,
            diff=request_data.diff
        )
        
        if not merge_result.success:
            return YAMLDiffMergeResponse(
                merged_yaml="",
                conflicts=[{"error": error} for error in merge_result.errors],
                resolution_strategy="failed",
                metadata={"warnings": merge_result.warnings}
            )
        
        # Validate merged result
        validation_result = yaml_service.validate_workflow_yaml(merge_result.merged_yaml)
        
        return YAMLDiffMergeResponse(
            merged_yaml=merge_result.merged_yaml,
            conflicts=[],
            resolution_strategy="automatic",
            metadata={
                "validation": validation_result,
                "applied_changes": getattr(merge_result, 'applied_changes', []),
                "warnings": getattr(merge_result, 'warnings', [])
            }
        )
    
    except Exception as e:
        logger.error(f"YAML diff merge error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/yaml/autolayout", response_model=AutoLayoutResponse)
async def yaml_autolayout(
    request_data: AutoLayoutRequest,
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service),
    authorized: bool = Depends(verify_api_key)
):
    """Auto-layout workflow blocks with intelligent positioning
    
    This endpoint matches the external SIM Agent API interface:
    POST /api/yaml/autolayout
    """
    try:
        logger.info("Auto-layouting workflow")
        
        # Generate layout
        layout_result = yaml_service.auto_layout_workflow(
            yaml_content=request_data.yaml,
            layout_options=request_data.options
        )
        
        if not layout_result.success:
            return AutoLayoutResponse(
                layout_data={},
                algorithm_used="failed",
                suggestions=[f"Error: {error}" for error in layout_result.errors]
            )
        
        return AutoLayoutResponse(
            layout_data=layout_result.layout_data,
            algorithm_used=getattr(layout_result, 'algorithm_used', 'smart'),
            performance_metrics={
                "total_blocks": getattr(layout_result, 'total_blocks', 0),
                "execution_time_ms": getattr(layout_result, 'execution_time_ms', 0)
            },
            suggestions=[]
        )
    
    except Exception as e:
        logger.error(f"YAML autolayout error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/yaml/health")
async def yaml_health_check(
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service)
):
    """Health check for YAML processing functionality"""
    try:
        # Test basic YAML parsing
        test_yaml = """
name: test_workflow
blocks:
  - id: test_block
    type: trigger
    name: Test Block
"""
        
        parse_result = yaml_service.parse_yaml(test_yaml)
        validation_result = yaml_service.validate_workflow_yaml(test_yaml)
        
        return {
            "status": "healthy",
            "yaml_parser": "functional" if parse_result.success else "error",
            "yaml_validator": "functional" if validation_result.is_valid else "error",
            "supported_features": [
                "yaml_parsing",
                "workflow_validation",
                "intelligent_diff",
                "auto_layout",
                "description_to_workflow"
            ]
        }
    
    except Exception as e:
        logger.error(f"YAML health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"YAML service unhealthy: {str(e)}"
        )