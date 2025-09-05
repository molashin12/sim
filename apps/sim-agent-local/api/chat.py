#!/usr/bin/env python3
"""
Chat API endpoints for Local SIM Agent API

Handles chat completion streaming with tool support,
matching the external SIM Agent API interface.
"""

import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.requests import ChatRequest, StatsRequest, SuccessResponse
from services.llm_service import LLMService
from config.settings import get_settings
from prompts.chat_prompts import get_chat_system_prompt
from utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)

def get_llm_service(request: Request) -> LLMService:
    """Get LLM service from app state"""
    return request.app.state.llm_service

def get_app_settings(request: Request):
    """Get app settings from app state"""
    return request.app.state.settings

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key (optional for local service)"""
    # For local service, we can be more permissive
    # In production, implement proper key validation
    return True

@router.post("/chat-completion-streaming")
async def chat_completion_streaming(
    chat_request: ChatRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    settings = Depends(get_app_settings),
    authorized: bool = Depends(verify_api_key)
):
    """Stream chat completion with tool support
    
    This endpoint matches the external SIM Agent API interface:
    POST /api/chat-completion-streaming
    """
    try:
        logger.info(f"Chat completion request: {len(chat_request.messages)} messages, tools: {len(chat_request.tools or [])}")
        
        # Prepare messages with system prompt
        messages = []
        
        # Add system prompt if not present
        has_system = any(msg.role == "system" for msg in chat_request.messages)
        if not has_system:
            system_prompt = get_chat_system_prompt(
                context=chat_request.context,
                tools=chat_request.tools
            )
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add user messages
        for msg in chat_request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Convert tools to the format expected by LLM service
        tools = None
        if chat_request.tools:
            tools = []
            for tool in chat_request.tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.function.name,
                        "description": tool.function.description or "",
                        "parameters": tool.function.parameters
                    }
                })
        
        async def generate_stream():
            """Generate streaming response"""
            try:
                async for chunk in llm_service.chat_completion_stream(
                    messages=messages,
                    tools=tools,
                    temperature=chat_request.temperature,
                    max_tokens=chat_request.max_tokens
                ):
                    # Format chunk for SSE
                    chunk_data = json.dumps(chunk)
                    yield f"data: {chunk_data}\n\n"
                
                # Send final done event
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}", exc_info=True)
                error_chunk = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    
    except Exception as e:
        logger.error(f"Chat completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stats", response_model=SuccessResponse)
async def report_stats(
    stats_request: StatsRequest,
    request: Request,
    authorized: bool = Depends(verify_api_key)
):
    """Report usage statistics and feedback
    
    This endpoint matches the external SIM Agent API interface:
    POST /api/stats
    """
    try:
        logger.info(f"Stats report: {stats_request.event_type}")
        
        # For local service, we can log stats or store them locally
        # In a production setup, you might want to store these in a database
        
        stats_data = {
            "event_type": stats_request.event_type,
            "data": stats_request.data,
            "timestamp": stats_request.timestamp,
            "user_id": stats_request.user_id
        }
        
        # Log the stats (could be enhanced to store in database)
        logger.info(f"Usage stats: {json.dumps(stats_data)}")
        
        return SuccessResponse(
            message="Stats reported successfully",
            data={"recorded": True}
        )
    
    except Exception as e:
        logger.error(f"Stats reporting error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/health")
async def chat_health_check(
    request: Request,
    llm_service: LLMService = Depends(get_llm_service)
):
    """Health check for chat functionality"""
    try:
        # Test basic LLM connectivity
        test_response = await llm_service.structured_completion(
            prompt="Respond with just 'OK' to confirm connectivity.",
            temperature=0.1,
            max_tokens=10
        )
        
        return {
            "status": "healthy",
            "llm_provider": llm_service.provider_name,
            "model": llm_service.model,
            "test_response": test_response.get("content", "No response")
        }
    
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Chat service unhealthy: {str(e)}"
        )