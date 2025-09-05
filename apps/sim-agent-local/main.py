#!/usr/bin/env python3
"""
Main FastAPI Application for Local SIM Agent API

This is the entry point for the local SIM Agent API service that provides
all the functionality needed to replace the external SIM-managed API service.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

from config.settings import get_settings
from utils.logging import setup_logging, get_logger
from services.llm_service import LLMService
from services.yaml_service import YamlService
from services.tool_service import ToolService
from services.auth_service import AuthService

# Import API routers
from api.chat import router as chat_router
from api.yaml_processing import router as yaml_router
from api.workflow import router as workflow_router
from api.tools import router as tools_router
from api.auth import router as auth_router

# Global service instances
services: Dict[str, Any] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger = get_logger(__name__)
    settings = get_settings()
    
    # Startup
    logger.info("Starting Local SIM Agent API...")
    
    try:
        # Initialize services
        logger.info("Initializing services...")
        
        # Initialize LLM Service
        llm_service = LLMService(
            provider=settings.copilot_provider,
            model=settings.copilot_model,
            api_key=settings.get_llm_api_key()
        )
        services['llm'] = llm_service
        logger.info("LLM Service initialized")
        
        # Initialize YAML Service
        yaml_service = YamlService()
        services['yaml'] = yaml_service
        logger.info("YAML Service initialized")
        
        # Initialize Tool Service
        tool_service = ToolService()
        services['tool'] = tool_service
        logger.info("Tool Service initialized")
        
        # Initialize Auth Service
        auth_service = AuthService()
        services['auth'] = auth_service
        logger.info("Auth Service initialized")
        
        # Start background tasks
        logger.info("Starting background tasks...")
        
        # Tool service cleanup task
        cleanup_task = asyncio.create_task(
            tool_service._periodic_cleanup(),
            name="tool_cleanup"
        )
        services['cleanup_task'] = cleanup_task
        
        logger.info(f"Local SIM Agent API started successfully on {settings.host}:{settings.port}")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down Local SIM Agent API...")
    
    try:
        # Cancel background tasks
        if 'cleanup_task' in services:
            cleanup_task = services['cleanup_task']
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup services
        if 'llm' in services:
            await services['llm'].cleanup()
            logger.info("LLM Service cleaned up")
        
        if 'tool' in services:
            await services['tool'].cleanup()
            logger.info("Tool Service cleaned up")
        
        logger.info("Local SIM Agent API shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    # Setup logging
    setup_logging(
        level=settings.log_level,
        format_type="rich" if settings.debug else "json"
    )
    
    logger = get_logger(__name__)
    
    # Create FastAPI app
    app = FastAPI(
        title="Local SIM Agent API",
        description="Local API service that provides all SIM Agent functionality without external dependencies",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Add middleware
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS enabled for origins: {settings.allowed_origins}")
    
    # Trusted host middleware (security)
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[settings.host, "localhost", "127.0.0.1"]
        )
    
    # Exception handlers
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.warning(f"Validation error for {request.url}: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "Validation Error",
                "details": exc.errors(),
                "message": "Request validation failed"
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP error {exc.status_code} for {request.url}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": f"HTTP {exc.status_code}",
                "message": exc.detail
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        logger.error(f"Unhandled error for {request.url}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal Server Error",
                "message": "An unexpected error occurred" if not settings.debug else str(exc)
            }
        )
    
    # Health check endpoints
    
    @app.get("/health")
    async def health_check():
        """Basic health check"""
        return {
            "status": "healthy",
            "service": "Local SIM Agent API",
            "version": "1.0.0",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check including all services"""
        health_status = {
            "status": "healthy",
            "service": "Local SIM Agent API",
            "version": "1.0.0",
            "timestamp": asyncio.get_event_loop().time(),
            "services": {}
        }
        
        try:
            # Check LLM service
            if 'llm' in services:
                llm_health = await services['llm'].get_health_status()
                health_status['services']['llm'] = llm_health
            
            # Check Tool service
            if 'tool' in services:
                tool_health = services['tool'].get_health_status()
                health_status['services']['tool'] = tool_health
            
            # Check Auth service
            if 'auth' in services:
                auth_health = services['auth'].get_health_status()
                health_status['services']['auth'] = auth_health
            
            # Check YAML service
            if 'yaml' in services:
                health_status['services']['yaml'] = {"status": "healthy"}
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status['status'] = 'degraded'
            health_status['error'] = str(e)
        
        return health_status
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "Local SIM Agent API",
            "version": "1.0.0",
            "description": "Local API service providing SIM Agent functionality",
            "endpoints": {
                "health": "/health",
                "docs": "/docs" if settings.debug else "disabled",
                "chat": "/api/chat-completion-streaming",
                "yaml": "/yaml/*",
                "workflow": "/workflow/*",
                "tools": "/tools/*",
                "auth": "/validate-key/*"
            }
        }
    
    # Include API routers
    app.include_router(chat_router, tags=["Chat"])
    app.include_router(yaml_router, tags=["YAML Processing"])
    app.include_router(workflow_router, tags=["Workflow Management"])
    app.include_router(tools_router, tags=["Tool Management"])
    app.include_router(auth_router, tags=["Authentication"])
    
    return app

def get_service(service_name: str):
    """Dependency to get service instances"""
    if service_name not in services:
        raise HTTPException(
            status_code=503,
            detail=f"Service {service_name} not available"
        )
    return services[service_name]

# Create app instance
app = create_app()

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger = get_logger(__name__)
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    settings = get_settings()
    
    # Configure uvicorn
    uvicorn_config = {
        "host": settings.host,
        "port": settings.port,
        "log_level": settings.log_level.lower(),
        "access_log": settings.debug,
        "reload": settings.debug,
        "workers": 1,  # Single worker for now to maintain state
    }
    
    if settings.debug:
        uvicorn_config["reload_dirs"] = ["."]  # Watch current directory for changes
    
    print(f"Starting Local SIM Agent API on {settings.host}:{settings.port}")
    print(f"Debug mode: {settings.debug}")
    print(f"Log level: {settings.log_level}")
    
    if settings.debug:
        print(f"API Documentation: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run("main:app", **uvicorn_config)