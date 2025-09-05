#!/usr/bin/env python3
"""
Workflow API endpoints for Local SIM Agent API

Handles workflow to YAML conversion and workflow management operations.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.requests import (
    WorkflowToYAMLRequest, SuccessResponse, ErrorResponse
)
from models.responses import (
    WorkflowToYAMLResponse
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

@router.post("/workflow/to-yaml", response_model=WorkflowToYAMLResponse)
async def workflow_to_yaml(
    request_data: WorkflowToYAMLRequest,
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service),
    llm_service: LLMService = Depends(get_llm_service),
    authorized: bool = Depends(verify_api_key)
):
    """Convert workflow structure to YAML format
    
    This endpoint matches the external SIM Agent API interface:
    POST /api/workflow/to-yaml
    """
    try:
        logger.info(f"Converting workflow to YAML: {len(request_data.workflow.get('blocks', []))} blocks")
        
        # Convert workflow structure to YAML
        yaml_result = await yaml_service.workflow_to_yaml(
            workflow=request_data.workflow,
            options=request_data.options,
            llm_service=llm_service
        )
        
        if not yaml_result.success:
            return WorkflowToYAMLResponse(
                success=False,
                errors=yaml_result.errors,
                warnings=yaml_result.warnings
            )
        
        # Validate the generated YAML
        validation_result = yaml_service.validate_workflow_yaml(yaml_result.yaml)
        
        # Generate metadata
        metadata = {
            "total_blocks": len(request_data.workflow.get('blocks', [])),
            "yaml_lines": len(yaml_result.yaml.split('\n')),
            "has_layout": yaml_service.has_layout_data(yaml_result.yaml),
            "complexity_score": yaml_service.calculate_complexity(yaml_result.yaml)
        }
        
        return WorkflowToYAMLResponse(
            success=True,
            yaml=yaml_result.yaml,
            validation=validation_result.dict(),
            metadata=metadata,
            warnings=yaml_result.warnings
        )
    
    except Exception as e:
        logger.error(f"Workflow to YAML conversion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflow/validate")
async def validate_workflow(
    workflow_data: Dict[str, Any],
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service),
    authorized: bool = Depends(verify_api_key)
):
    """Validate workflow structure
    
    Additional endpoint for workflow validation
    """
    try:
        logger.info("Validating workflow structure")
        
        # Validate workflow structure
        validation_result = yaml_service.validate_workflow_structure(workflow_data)
        
        return {
            "valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "metadata": {
                "total_blocks": len(workflow_data.get('blocks', [])),
                "has_triggers": any(
                    block.get('type') == 'trigger' 
                    for block in workflow_data.get('blocks', [])
                ),
                "has_actions": any(
                    block.get('type') in ['action', 'condition', 'loop']
                    for block in workflow_data.get('blocks', [])
                )
            }
        }
    
    except Exception as e:
        logger.error(f"Workflow validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflow/optimize")
async def optimize_workflow(
    workflow_data: Dict[str, Any],
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service),
    llm_service: LLMService = Depends(get_llm_service),
    authorized: bool = Depends(verify_api_key)
):
    """Optimize workflow structure for better performance
    
    Additional endpoint for workflow optimization
    """
    try:
        logger.info("Optimizing workflow structure")
        
        # Analyze workflow for optimization opportunities
        optimization_result = await yaml_service.optimize_workflow(
            workflow=workflow_data,
            llm_service=llm_service
        )
        
        return {
            "optimized": optimization_result.success,
            "optimized_workflow": optimization_result.workflow,
            "optimizations_applied": optimization_result.optimizations,
            "performance_improvement": optimization_result.performance_metrics,
            "recommendations": optimization_result.recommendations
        }
    
    except Exception as e:
        logger.error(f"Workflow optimization error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflow/analyze")
async def analyze_workflow(
    workflow_data: Dict[str, Any],
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service),
    llm_service: LLMService = Depends(get_llm_service),
    authorized: bool = Depends(verify_api_key)
):
    """Analyze workflow for insights and recommendations
    
    Additional endpoint for workflow analysis
    """
    try:
        logger.info("Analyzing workflow")
        
        # Perform comprehensive workflow analysis
        analysis_result = await yaml_service.analyze_workflow(
            workflow=workflow_data,
            llm_service=llm_service
        )
        
        return {
            "analysis": analysis_result.analysis,
            "complexity_score": analysis_result.complexity_score,
            "performance_metrics": analysis_result.performance_metrics,
            "security_assessment": analysis_result.security_assessment,
            "recommendations": analysis_result.recommendations,
            "potential_issues": analysis_result.potential_issues,
            "best_practices": analysis_result.best_practices
        }
    
    except Exception as e:
        logger.error(f"Workflow analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow/templates")
async def get_workflow_templates(
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service),
    authorized: bool = Depends(verify_api_key)
):
    """Get available workflow templates
    
    Additional endpoint for workflow templates
    """
    try:
        logger.info("Fetching workflow templates")
        
        templates = yaml_service.get_workflow_templates()
        
        return {
            "templates": templates,
            "categories": yaml_service.get_template_categories(),
            "total_templates": len(templates)
        }
    
    except Exception as e:
        logger.error(f"Template fetching error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflow/from-template")
async def create_workflow_from_template(
    template_id: str,
    parameters: Dict[str, Any],
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service),
    llm_service: LLMService = Depends(get_llm_service),
    authorized: bool = Depends(verify_api_key)
):
    """Create workflow from template
    
    Additional endpoint for template-based workflow creation
    """
    try:
        logger.info(f"Creating workflow from template: {template_id}")
        
        # Create workflow from template
        creation_result = await yaml_service.create_from_template(
            template_id=template_id,
            parameters=parameters,
            llm_service=llm_service
        )
        
        if not creation_result.success:
            return {
                "success": False,
                "errors": creation_result.errors
            }
        
        # Validate created workflow
        validation_result = yaml_service.validate_workflow_structure(creation_result.workflow)
        
        return {
            "success": True,
            "workflow": creation_result.workflow,
            "yaml": creation_result.yaml,
            "validation": validation_result.dict(),
            "template_info": creation_result.template_info
        }
    
    except Exception as e:
        logger.error(f"Template workflow creation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow/health")
async def workflow_health_check(
    request: Request,
    yaml_service: YamlService = Depends(get_yaml_service)
):
    """Health check for workflow functionality"""
    try:
        # Test basic workflow operations
        test_workflow = {
            "name": "test_workflow",
            "blocks": [
                {
                    "id": "trigger_1",
                    "type": "trigger",
                    "name": "Test Trigger"
                },
                {
                    "id": "action_1",
                    "type": "action",
                    "name": "Test Action"
                }
            ]
        }
        
        # Test workflow validation
        validation_result = yaml_service.validate_workflow_structure(test_workflow)
        
        # Test workflow to YAML conversion
        yaml_result = await yaml_service.workflow_to_yaml(
            workflow=test_workflow,
            options={}
        )
        
        return {
            "status": "healthy",
            "workflow_validation": "functional" if validation_result.is_valid else "error",
            "workflow_to_yaml": "functional" if yaml_result.success else "error",
            "supported_features": [
                "workflow_validation",
                "workflow_to_yaml",
                "workflow_optimization",
                "workflow_analysis",
                "template_support"
            ]
        }
    
    except Exception as e:
        logger.error(f"Workflow health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Workflow service unhealthy: {str(e)}"
        )