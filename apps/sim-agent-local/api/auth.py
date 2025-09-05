#!/usr/bin/env python3
"""
Authentication API endpoints for Local SIM Agent API

Handles API key validation and authentication operations.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.requests import (
    ValidateKeyRequest, SuccessResponse, ErrorResponse
)
from models.responses import (
    ValidateKeyResponse
)
from services.auth_service import AuthService
from config.settings import get_settings
from utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)

def get_auth_service(request: Request) -> AuthService:
    """Get auth service from app state"""
    return request.app.state.auth_service

@router.post("/validate-key/{key_type}", response_model=ValidateKeyResponse)
async def validate_key(
    key_type: str,
    request_data: ValidateKeyRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Validate API key for specific provider
    
    This endpoint matches the external SIM Agent API interface:
    POST /api/validate-key/{key_type}
    
    Supported key types: openai, anthropic, google, azure, local
    """
    try:
        logger.info(f"Validating {key_type} API key")
        
        # Validate the API key
        validation_result = await auth_service.validate_api_key(
            key_type=key_type,
            api_key=request_data.api_key,
            additional_params=request_data.additional_params
        )
        
        return ValidateKeyResponse(
            valid=validation_result.valid,
            provider=validation_result.provider,
            model_access=validation_result.model_access,
            rate_limits=validation_result.rate_limits,
            features=validation_result.features,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            metadata=validation_result.metadata
        )
    
    except Exception as e:
        logger.error(f"API key validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-key/batch")
async def validate_keys_batch(
    keys_data: Dict[str, str],
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Validate multiple API keys at once
    
    Additional endpoint for batch key validation
    """
    try:
        logger.info(f"Batch validating {len(keys_data)} API keys")
        
        results = {}
        for key_type, api_key in keys_data.items():
            try:
                validation_result = await auth_service.validate_api_key(
                    key_type=key_type,
                    api_key=api_key
                )
                results[key_type] = {
                    "valid": validation_result.valid,
                    "provider": validation_result.provider,
                    "model_access": validation_result.model_access,
                    "errors": validation_result.errors
                }
            except Exception as e:
                results[key_type] = {
                    "valid": False,
                    "errors": [str(e)]
                }
        
        valid_keys = len([r for r in results.values() if r['valid']])
        
        return {
            "results": results,
            "summary": {
                "total_keys": len(keys_data),
                "valid_keys": valid_keys,
                "invalid_keys": len(keys_data) - valid_keys,
                "validation_rate": valid_keys / len(keys_data) if keys_data else 0
            }
        }
    
    except Exception as e:
        logger.error(f"Batch key validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers")
async def get_supported_providers(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get list of supported LLM providers
    
    Additional endpoint for provider information
    """
    try:
        logger.info("Getting supported providers")
        
        providers = auth_service.get_supported_providers()
        
        return {
            "providers": providers,
            "total_providers": len(providers),
            "default_provider": auth_service.get_default_provider(),
            "provider_features": auth_service.get_provider_features()
        }
    
    except Exception as e:
        logger.error(f"Provider listing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/provider/{provider_name}/models")
async def get_provider_models(
    provider_name: str,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get available models for a specific provider
    
    Additional endpoint for model information
    """
    try:
        logger.info(f"Getting models for provider: {provider_name}")
        
        models = await auth_service.get_provider_models(provider_name)
        
        if not models:
            raise HTTPException(status_code=404, detail="Provider not found or no models available")
        
        return {
            "provider": provider_name,
            "models": models,
            "total_models": len(models),
            "recommended_models": auth_service.get_recommended_models(provider_name),
            "model_capabilities": auth_service.get_model_capabilities(provider_name)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Provider models error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-connection")
async def test_provider_connection(
    connection_data: Dict[str, Any],
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Test connection to LLM provider
    
    Additional endpoint for connection testing
    """
    try:
        provider = connection_data.get('provider')
        api_key = connection_data.get('api_key')
        model = connection_data.get('model')
        
        logger.info(f"Testing connection to {provider}")
        
        connection_result = await auth_service.test_connection(
            provider=provider,
            api_key=api_key,
            model=model,
            additional_params=connection_data.get('additional_params', {})
        )
        
        return {
            "connected": connection_result.connected,
            "provider": provider,
            "model": model,
            "response_time_ms": connection_result.response_time_ms,
            "test_response": connection_result.test_response,
            "capabilities": connection_result.capabilities,
            "errors": connection_result.errors,
            "warnings": connection_result.warnings
        }
    
    except Exception as e:
        logger.error(f"Connection test error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quota/{provider_name}")
async def get_provider_quota(
    provider_name: str,
    api_key: str,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get quota information for a provider
    
    Additional endpoint for quota checking
    """
    try:
        logger.info(f"Getting quota for provider: {provider_name}")
        
        quota_info = await auth_service.get_quota_info(
            provider=provider_name,
            api_key=api_key
        )
        
        if not quota_info:
            raise HTTPException(status_code=404, detail="Quota information not available")
        
        return {
            "provider": provider_name,
            "quota": quota_info.quota,
            "usage": quota_info.usage,
            "remaining": quota_info.remaining,
            "reset_date": quota_info.reset_date,
            "rate_limits": quota_info.rate_limits,
            "billing_info": quota_info.billing_info
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quota check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-local-key")
async def generate_local_key(
    key_data: Dict[str, Any],
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Generate a local API key for the service
    
    Additional endpoint for local key generation
    """
    try:
        logger.info("Generating local API key")
        
        key_result = await auth_service.generate_local_key(
            name=key_data.get('name', 'default'),
            permissions=key_data.get('permissions', []),
            expires_in_days=key_data.get('expires_in_days', 365),
            metadata=key_data.get('metadata', {})
        )
        
        return {
            "success": True,
            "api_key": key_result.api_key,
            "key_id": key_result.key_id,
            "name": key_result.name,
            "permissions": key_result.permissions,
            "expires_at": key_result.expires_at,
            "created_at": key_result.created_at
        }
    
    except Exception as e:
        logger.error(f"Local key generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/local-keys")
async def list_local_keys(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """List all local API keys
    
    Additional endpoint for local key management
    """
    try:
        logger.info("Listing local API keys")
        
        keys = await auth_service.list_local_keys()
        
        return {
            "keys": [
                {
                    "key_id": key.key_id,
                    "name": key.name,
                    "permissions": key.permissions,
                    "created_at": key.created_at,
                    "expires_at": key.expires_at,
                    "last_used": key.last_used,
                    "is_active": key.is_active
                }
                for key in keys
            ],
            "total_keys": len(keys),
            "active_keys": len([k for k in keys if k.is_active]),
            "expired_keys": len([k for k in keys if not k.is_active])
        }
    
    except Exception as e:
        logger.error(f"Local keys listing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/local-keys/{key_id}")
async def revoke_local_key(
    key_id: str,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Revoke a local API key
    
    Additional endpoint for local key revocation
    """
    try:
        logger.info(f"Revoking local API key: {key_id}")
        
        revocation_result = await auth_service.revoke_local_key(key_id)
        
        if not revocation_result.success:
            return {
                "success": False,
                "errors": revocation_result.errors
            }
        
        return {
            "success": True,
            "key_id": key_id,
            "revoked_at": revocation_result.revoked_at
        }
    
    except Exception as e:
        logger.error(f"Local key revocation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auth/health")
async def auth_health_check(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Health check for authentication functionality"""
    try:
        # Test basic auth operations
        health_status = await auth_service.health_check()
        
        return {
            "status": "healthy" if health_status.healthy else "unhealthy",
            "key_validation": "functional" if health_status.validation_healthy else "error",
            "provider_connectivity": "functional" if health_status.connectivity_healthy else "error",
            "supported_providers": health_status.supported_providers,
            "supported_features": [
                "api_key_validation",
                "batch_validation",
                "provider_testing",
                "quota_checking",
                "local_key_management"
            ],
            "metrics": health_status.metrics
        }
    
    except Exception as e:
        logger.error(f"Auth health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Auth service unhealthy: {str(e)}"
        )