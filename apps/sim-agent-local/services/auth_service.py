#!/usr/bin/env python3
"""
Authentication Service for Local SIM Agent API

Handles API key validation, provider management,
and local key generation for the service.
"""

import uuid
import hashlib
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import json

from config.settings import get_settings
from utils.logging import get_logger

logger = get_logger(__name__)

class ProviderType(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    LOCAL = "local"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"

class KeyStatus(Enum):
    """API key validation status"""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    QUOTA_EXCEEDED = "quota_exceeded"
    RATE_LIMITED = "rate_limited"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"

@dataclass
class ValidationResult:
    """API key validation result"""
    is_valid: bool
    status: KeyStatus
    provider: ProviderType
    message: str
    details: Optional[Dict[str, Any]] = None
    quota_info: Optional[Dict[str, Any]] = None
    rate_limit_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['provider'] = self.provider.value
        return data

@dataclass
class LocalApiKey:
    """Local API key record"""
    key_id: str
    key_hash: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    permissions: List[str]
    usage_count: int
    last_used: Optional[datetime]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without sensitive data)"""
        return {
            'key_id': self.key_id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'permissions': self.permissions,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'metadata': self.metadata or {}
        }

class AuthService:
    """Service for handling authentication and API key management"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        self.local_keys: Dict[str, LocalApiKey] = {}
        self.validation_cache: Dict[str, Tuple[ValidationResult, datetime]] = {}
        self.cache_ttl = timedelta(minutes=15)  # Cache validation results for 15 minutes
        
        # Provider configurations
        self.provider_configs = {
            ProviderType.OPENAI: {
                'name': 'OpenAI',
                'base_url': 'https://api.openai.com/v1',
                'test_endpoint': '/models',
                'auth_header': 'Authorization',
                'auth_format': 'Bearer {key}',
                'models': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 'gpt-4o', 'gpt-4o-mini']
            },
            ProviderType.ANTHROPIC: {
                'name': 'Anthropic',
                'base_url': 'https://api.anthropic.com',
                'test_endpoint': '/v1/messages',
                'auth_header': 'x-api-key',
                'auth_format': '{key}',
                'models': ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307']
            },
            ProviderType.GOOGLE: {
                'name': 'Google AI',
                'base_url': 'https://generativelanguage.googleapis.com',
                'test_endpoint': '/v1/models',
                'auth_header': None,  # Uses query parameter
                'auth_format': None,
                'models': ['gemini-pro', 'gemini-pro-vision', 'gemini-1.5-pro', 'gemini-1.5-flash']
            },
            ProviderType.AZURE: {
                'name': 'Azure OpenAI',
                'base_url': None,  # Dynamic based on endpoint
                'test_endpoint': '/openai/deployments',
                'auth_header': 'api-key',
                'auth_format': '{key}',
                'models': []  # Dynamic based on deployments
            },
            ProviderType.LOCAL: {
                'name': 'Local SIM Agent',
                'base_url': f"http://{self.settings.host}:{self.settings.port}",
                'test_endpoint': '/health',
                'auth_header': 'Authorization',
                'auth_format': 'Bearer {key}',
                'models': ['local-agent']
            }
        }
    
    async def validate_api_key(self, provider: str, api_key: str, 
                              use_cache: bool = True) -> ValidationResult:
        """Validate API key for a specific provider"""
        try:
            provider_enum = ProviderType(provider.lower())
        except ValueError:
            return ValidationResult(
                is_valid=False,
                status=KeyStatus.INVALID,
                provider=ProviderType.LOCAL,
                message=f"Unsupported provider: {provider}"
            )
        
        # Check cache first
        cache_key = f"{provider}:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        if use_cache and cache_key in self.validation_cache:
            cached_result, cached_time = self.validation_cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                self.logger.debug(f"Using cached validation result for {provider}")
                return cached_result
        
        # Validate based on provider
        if provider_enum == ProviderType.LOCAL:
            result = await self._validate_local_key(api_key)
        else:
            result = await self._validate_external_key(provider_enum, api_key)
        
        # Cache result
        if use_cache:
            self.validation_cache[cache_key] = (result, datetime.now())
        
        return result
    
    async def _validate_local_key(self, api_key: str) -> ValidationResult:
        """Validate local API key"""
        try:
            # Hash the provided key
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Find matching key
            for local_key in self.local_keys.values():
                if local_key.key_hash == key_hash and local_key.is_active:
                    # Check expiration
                    if local_key.expires_at and datetime.now() > local_key.expires_at:
                        return ValidationResult(
                            is_valid=False,
                            status=KeyStatus.EXPIRED,
                            provider=ProviderType.LOCAL,
                            message="Local API key has expired"
                        )
                    
                    # Update usage
                    local_key.usage_count += 1
                    local_key.last_used = datetime.now()
                    
                    return ValidationResult(
                        is_valid=True,
                        status=KeyStatus.VALID,
                        provider=ProviderType.LOCAL,
                        message="Local API key is valid",
                        details={
                            'key_id': local_key.key_id,
                            'name': local_key.name,
                            'permissions': local_key.permissions
                        }
                    )
            
            return ValidationResult(
                is_valid=False,
                status=KeyStatus.INVALID,
                provider=ProviderType.LOCAL,
                message="Local API key not found or inactive"
            )
            
        except Exception as e:
            self.logger.error(f"Local key validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                status=KeyStatus.UNKNOWN,
                provider=ProviderType.LOCAL,
                message=f"Validation error: {str(e)}"
            )
    
    async def _validate_external_key(self, provider: ProviderType, api_key: str) -> ValidationResult:
        """Validate external provider API key"""
        config = self.provider_configs.get(provider)
        if not config:
            return ValidationResult(
                is_valid=False,
                status=KeyStatus.INVALID,
                provider=provider,
                message=f"No configuration for provider: {provider.value}"
            )
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Prepare request
                url = f"{config['base_url']}{config['test_endpoint']}"
                headers = {}
                params = {}
                
                # Set authentication
                if provider == ProviderType.GOOGLE:
                    params['key'] = api_key
                elif provider == ProviderType.AZURE:
                    # Azure requires special handling
                    return await self._validate_azure_key(api_key)
                else:
                    auth_format = config['auth_format']
                    headers[config['auth_header']] = auth_format.format(key=api_key)
                
                # Add common headers
                headers['User-Agent'] = 'SIM-Agent-Local/1.0'
                
                # Make request
                if provider == ProviderType.ANTHROPIC:
                    # Anthropic requires a different test approach
                    return await self._validate_anthropic_key(api_key)
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return ValidationResult(
                            is_valid=True,
                            status=KeyStatus.VALID,
                            provider=provider,
                            message=f"{config['name']} API key is valid",
                            details={'response_data': data}
                        )
                    elif response.status == 401:
                        return ValidationResult(
                            is_valid=False,
                            status=KeyStatus.INVALID,
                            provider=provider,
                            message=f"{config['name']} API key is invalid"
                        )
                    elif response.status == 429:
                        return ValidationResult(
                            is_valid=False,
                            status=KeyStatus.RATE_LIMITED,
                            provider=provider,
                            message=f"{config['name']} API key is rate limited"
                        )
                    else:
                        error_text = await response.text()
                        return ValidationResult(
                            is_valid=False,
                            status=KeyStatus.UNKNOWN,
                            provider=provider,
                            message=f"{config['name']} validation failed: {response.status} - {error_text}"
                        )
        
        except asyncio.TimeoutError:
            return ValidationResult(
                is_valid=False,
                status=KeyStatus.NETWORK_ERROR,
                provider=provider,
                message=f"{config['name']} validation timed out"
            )
        except Exception as e:
            self.logger.error(f"External key validation failed for {provider.value}: {e}")
            return ValidationResult(
                is_valid=False,
                status=KeyStatus.NETWORK_ERROR,
                provider=provider,
                message=f"{config['name']} validation error: {str(e)}"
            )
    
    async def _validate_anthropic_key(self, api_key: str) -> ValidationResult:
        """Special validation for Anthropic API"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                }
                
                # Minimal test request
                data = {
                    'model': 'claude-3-haiku-20240307',
                    'max_tokens': 1,
                    'messages': [{'role': 'user', 'content': 'Hi'}]
                }
                
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status in [200, 400]:  # 400 is OK for validation
                        return ValidationResult(
                            is_valid=True,
                            status=KeyStatus.VALID,
                            provider=ProviderType.ANTHROPIC,
                            message="Anthropic API key is valid"
                        )
                    elif response.status == 401:
                        return ValidationResult(
                            is_valid=False,
                            status=KeyStatus.INVALID,
                            provider=ProviderType.ANTHROPIC,
                            message="Anthropic API key is invalid"
                        )
                    else:
                        return ValidationResult(
                            is_valid=False,
                            status=KeyStatus.UNKNOWN,
                            provider=ProviderType.ANTHROPIC,
                            message=f"Anthropic validation failed: {response.status}"
                        )
        
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                status=KeyStatus.NETWORK_ERROR,
                provider=ProviderType.ANTHROPIC,
                message=f"Anthropic validation error: {str(e)}"
            )
    
    async def _validate_azure_key(self, api_key: str) -> ValidationResult:
        """Special validation for Azure OpenAI"""
        # Azure validation requires endpoint URL which we don't have in the key
        # For now, return a basic validation
        if api_key and len(api_key) > 10:
            return ValidationResult(
                is_valid=True,
                status=KeyStatus.VALID,
                provider=ProviderType.AZURE,
                message="Azure API key format appears valid (full validation requires endpoint)"
            )
        else:
            return ValidationResult(
                is_valid=False,
                status=KeyStatus.INVALID,
                provider=ProviderType.AZURE,
                message="Azure API key format is invalid"
            )
    
    async def batch_validate_keys(self, keys: Dict[str, str]) -> Dict[str, ValidationResult]:
        """Validate multiple API keys simultaneously"""
        tasks = []
        for provider, api_key in keys.items():
            task = asyncio.create_task(
                self.validate_api_key(provider, api_key),
                name=f"validate_{provider}"
            )
            tasks.append((provider, task))
        
        results = {}
        for provider, task in tasks:
            try:
                result = await task
                results[provider] = result
            except Exception as e:
                self.logger.error(f"Batch validation failed for {provider}: {e}")
                results[provider] = ValidationResult(
                    is_valid=False,
                    status=KeyStatus.UNKNOWN,
                    provider=ProviderType.LOCAL,
                    message=f"Validation error: {str(e)}"
                )
        
        return results
    
    def get_supported_providers(self) -> List[Dict[str, Any]]:
        """Get list of supported providers"""
        providers = []
        for provider_type, config in self.provider_configs.items():
            providers.append({
                'id': provider_type.value,
                'name': config['name'],
                'models': config['models'],
                'requires_endpoint': provider_type == ProviderType.AZURE
            })
        
        return providers
    
    def get_provider_models(self, provider: str) -> List[str]:
        """Get available models for a provider"""
        try:
            provider_enum = ProviderType(provider.lower())
            config = self.provider_configs.get(provider_enum, {})
            return config.get('models', [])
        except ValueError:
            return []
    
    async def test_connection(self, provider: str, api_key: str, 
                            endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Test connection to a provider"""
        validation_result = await self.validate_api_key(provider, api_key, use_cache=False)
        
        return {
            'provider': provider,
            'connection_status': 'connected' if validation_result.is_valid else 'failed',
            'validation_result': validation_result.to_dict(),
            'latency_ms': 0,  # Could measure actual latency
            'endpoint_used': endpoint or self.provider_configs.get(
                ProviderType(provider.lower()), {}
            ).get('base_url', 'unknown')
        }
    
    async def get_quota_info(self, provider: str, api_key: str) -> Dict[str, Any]:
        """Get quota information for a provider"""
        # This would require provider-specific implementations
        # For now, return basic info
        
        validation_result = await self.validate_api_key(provider, api_key)
        
        if not validation_result.is_valid:
            return {
                'provider': provider,
                'quota_available': False,
                'error': validation_result.message
            }
        
        return {
            'provider': provider,
            'quota_available': True,
            'usage': {
                'requests_made': 'unknown',
                'requests_remaining': 'unknown',
                'reset_time': 'unknown'
            },
            'limits': {
                'requests_per_minute': 'unknown',
                'tokens_per_minute': 'unknown'
            }
        }
    
    def generate_local_api_key(self, name: str, permissions: List[str] = None,
                              expires_in_days: Optional[int] = None) -> Tuple[str, str]:
        """Generate a new local API key"""
        # Generate secure random key
        key = f"sim_local_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_id = str(uuid.uuid4())
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        # Create key record
        local_key = LocalApiKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            created_at=datetime.now(),
            expires_at=expires_at,
            is_active=True,
            permissions=permissions or ['read', 'write'],
            usage_count=0,
            last_used=None
        )
        
        self.local_keys[key_id] = local_key
        
        self.logger.info(f"Generated local API key: {key_id} for {name}")
        return key, key_id
    
    def list_local_keys(self) -> List[Dict[str, Any]]:
        """List all local API keys (without sensitive data)"""
        return [key.to_dict() for key in self.local_keys.values()]
    
    def revoke_local_key(self, key_id: str) -> bool:
        """Revoke a local API key"""
        if key_id not in self.local_keys:
            return False
        
        self.local_keys[key_id].is_active = False
        self.logger.info(f"Revoked local API key: {key_id}")
        return True
    
    def delete_local_key(self, key_id: str) -> bool:
        """Delete a local API key"""
        if key_id not in self.local_keys:
            return False
        
        del self.local_keys[key_id]
        self.logger.info(f"Deleted local API key: {key_id}")
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get authentication service health status"""
        active_local_keys = len([k for k in self.local_keys.values() if k.is_active])
        cache_size = len(self.validation_cache)
        
        return {
            'status': 'healthy',
            'local_keys': {
                'total': len(self.local_keys),
                'active': active_local_keys,
                'inactive': len(self.local_keys) - active_local_keys
            },
            'validation_cache': {
                'size': cache_size,
                'ttl_minutes': self.cache_ttl.total_seconds() / 60
            },
            'supported_providers': len(self.provider_configs),
            'provider_list': [p.value for p in ProviderType]
        }
    
    def clear_validation_cache(self) -> int:
        """Clear validation cache"""
        cache_size = len(self.validation_cache)
        self.validation_cache.clear()
        self.logger.info(f"Cleared validation cache ({cache_size} entries)")
        return cache_size
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired entries from validation cache"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, cached_time) in self.validation_cache.items()
            if now - cached_time >= self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.validation_cache[key]
        
        if expired_keys:
            self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)