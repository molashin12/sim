#!/usr/bin/env python3
"""
Tools API endpoints for Local SIM Agent API

Handles tool completion tracking and tool management operations.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.requests import (
    ToolCompleteRequest, SuccessResponse, ErrorResponse
)
from models.responses import (
    ToolCompleteResponse
)
from services.tool_service import ToolService
from config.settings import get_settings
from utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)

def get_tool_service(request: Request) -> ToolService:
    """Get tool service from app state"""
    return request.app.state.tool_service

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key (optional for local service)"""
    return True

@router.post("/tools/mark-complete", response_model=ToolCompleteResponse)
async def mark_tool_complete(
    request_data: ToolCompleteRequest,
    request: Request,
    tool_service: ToolService = Depends(get_tool_service),
    authorized: bool = Depends(verify_api_key)
):
    """Mark a tool as completed with results
    
    This endpoint matches the external SIM Agent API interface:
    POST /api/tools/mark-complete
    """
    try:
        logger.info(f"Marking tool complete: {request_data.tool_id}")
        
        # Mark tool as complete
        completion_result = await tool_service.mark_complete(
            tool_id=request_data.tool_id,
            result=request_data.result,
            metadata=request_data.metadata,
            session_id=request_data.session_id
        )
        
        if not completion_result.success:
            return ToolCompleteResponse(
                success=False,
                errors=completion_result.errors,
                warnings=completion_result.warnings
            )
        
        return ToolCompleteResponse(
            success=True,
            tool_id=request_data.tool_id,
            completion_time=completion_result.completion_time,
            next_actions=completion_result.next_actions,
            metadata=completion_result.metadata
        )
    
    except Exception as e:
        logger.error(f"Tool completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/status/{tool_id}")
async def get_tool_status(
    tool_id: str,
    request: Request,
    tool_service: ToolService = Depends(get_tool_service),
    authorized: bool = Depends(verify_api_key)
):
    """Get the status of a specific tool
    
    Additional endpoint for tool status tracking
    """
    try:
        logger.info(f"Getting tool status: {tool_id}")
        
        status = await tool_service.get_tool_status(tool_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        return {
            "tool_id": tool_id,
            "status": status.status,
            "created_at": status.created_at,
            "updated_at": status.updated_at,
            "completion_time": status.completion_time,
            "result": status.result,
            "metadata": status.metadata,
            "session_id": status.session_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool status retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/session/{session_id}")
async def get_session_tools(
    session_id: str,
    request: Request,
    tool_service: ToolService = Depends(get_tool_service),
    authorized: bool = Depends(verify_api_key)
):
    """Get all tools for a specific session
    
    Additional endpoint for session-based tool tracking
    """
    try:
        logger.info(f"Getting tools for session: {session_id}")
        
        tools = await tool_service.get_session_tools(session_id)
        
        return {
            "session_id": session_id,
            "tools": [
                {
                    "tool_id": tool.tool_id,
                    "status": tool.status,
                    "created_at": tool.created_at,
                    "completion_time": tool.completion_time,
                    "result": tool.result
                }
                for tool in tools
            ],
            "total_tools": len(tools),
            "completed_tools": len([t for t in tools if t.status == "completed"]),
            "pending_tools": len([t for t in tools if t.status == "pending"]),
            "failed_tools": len([t for t in tools if t.status == "failed"])
        }
    
    except Exception as e:
        logger.error(f"Session tools retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/create")
async def create_tool(
    tool_data: Dict[str, Any],
    request: Request,
    tool_service: ToolService = Depends(get_tool_service),
    authorized: bool = Depends(verify_api_key)
):
    """Create a new tool instance
    
    Additional endpoint for tool creation
    """
    try:
        logger.info(f"Creating tool: {tool_data.get('name', 'unnamed')}")
        
        creation_result = await tool_service.create_tool(
            name=tool_data.get('name'),
            description=tool_data.get('description'),
            parameters=tool_data.get('parameters', {}),
            session_id=tool_data.get('session_id'),
            metadata=tool_data.get('metadata', {})
        )
        
        if not creation_result.success:
            return {
                "success": False,
                "errors": creation_result.errors
            }
        
        return {
            "success": True,
            "tool_id": creation_result.tool_id,
            "created_at": creation_result.created_at,
            "metadata": creation_result.metadata
        }
    
    except Exception as e:
        logger.error(f"Tool creation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tools/{tool_id}/update")
async def update_tool(
    tool_id: str,
    update_data: Dict[str, Any],
    request: Request,
    tool_service: ToolService = Depends(get_tool_service),
    authorized: bool = Depends(verify_api_key)
):
    """Update tool information
    
    Additional endpoint for tool updates
    """
    try:
        logger.info(f"Updating tool: {tool_id}")
        
        update_result = await tool_service.update_tool(
            tool_id=tool_id,
            updates=update_data
        )
        
        if not update_result.success:
            return {
                "success": False,
                "errors": update_result.errors
            }
        
        return {
            "success": True,
            "tool_id": tool_id,
            "updated_at": update_result.updated_at,
            "changes": update_result.changes
        }
    
    except Exception as e:
        logger.error(f"Tool update error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tools/{tool_id}")
async def delete_tool(
    tool_id: str,
    request: Request,
    tool_service: ToolService = Depends(get_tool_service),
    authorized: bool = Depends(verify_api_key)
):
    """Delete a tool
    
    Additional endpoint for tool deletion
    """
    try:
        logger.info(f"Deleting tool: {tool_id}")
        
        deletion_result = await tool_service.delete_tool(tool_id)
        
        if not deletion_result.success:
            return {
                "success": False,
                "errors": deletion_result.errors
            }
        
        return {
            "success": True,
            "tool_id": tool_id,
            "deleted_at": deletion_result.deleted_at
        }
    
    except Exception as e:
        logger.error(f"Tool deletion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/analytics")
async def get_tool_analytics(
    request: Request,
    session_id: str = None,
    start_date: str = None,
    end_date: str = None,
    tool_service: ToolService = Depends(get_tool_service),
    authorized: bool = Depends(verify_api_key)
):
    """Get tool usage analytics
    
    Additional endpoint for tool analytics
    """
    try:
        logger.info("Getting tool analytics")
        
        analytics = await tool_service.get_analytics(
            session_id=session_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "analytics": analytics.data,
            "summary": {
                "total_tools": analytics.total_tools,
                "completed_tools": analytics.completed_tools,
                "failed_tools": analytics.failed_tools,
                "average_completion_time": analytics.average_completion_time,
                "success_rate": analytics.success_rate
            },
            "trends": analytics.trends,
            "top_tools": analytics.top_tools,
            "performance_metrics": analytics.performance_metrics
        }
    
    except Exception as e:
        logger.error(f"Tool analytics error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/bulk-complete")
async def bulk_complete_tools(
    tools_data: List[Dict[str, Any]],
    request: Request,
    tool_service: ToolService = Depends(get_tool_service),
    authorized: bool = Depends(verify_api_key)
):
    """Mark multiple tools as completed
    
    Additional endpoint for bulk tool completion
    """
    try:
        logger.info(f"Bulk completing {len(tools_data)} tools")
        
        results = []
        for tool_data in tools_data:
            try:
                completion_result = await tool_service.mark_complete(
                    tool_id=tool_data.get('tool_id'),
                    result=tool_data.get('result'),
                    metadata=tool_data.get('metadata', {}),
                    session_id=tool_data.get('session_id')
                )
                results.append({
                    "tool_id": tool_data.get('tool_id'),
                    "success": completion_result.success,
                    "errors": completion_result.errors if not completion_result.success else None
                })
            except Exception as e:
                results.append({
                    "tool_id": tool_data.get('tool_id'),
                    "success": False,
                    "errors": [str(e)]
                })
        
        successful_completions = len([r for r in results if r['success']])
        
        return {
            "results": results,
            "summary": {
                "total_tools": len(tools_data),
                "successful_completions": successful_completions,
                "failed_completions": len(tools_data) - successful_completions,
                "success_rate": successful_completions / len(tools_data) if tools_data else 0
            }
        }
    
    except Exception as e:
        logger.error(f"Bulk tool completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/health")
async def tools_health_check(
    request: Request,
    tool_service: ToolService = Depends(get_tool_service)
):
    """Health check for tools functionality"""
    try:
        # Test basic tool operations
        health_status = await tool_service.health_check()
        
        return {
            "status": "healthy" if health_status.healthy else "unhealthy",
            "tool_storage": "functional" if health_status.storage_healthy else "error",
            "tool_tracking": "functional" if health_status.tracking_healthy else "error",
            "supported_features": [
                "tool_completion",
                "tool_tracking",
                "session_management",
                "bulk_operations",
                "analytics"
            ],
            "metrics": health_status.metrics
        }
    
    except Exception as e:
        logger.error(f"Tools health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Tools service unhealthy: {str(e)}"
        )