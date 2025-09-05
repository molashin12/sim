#!/usr/bin/env python3
"""
Configuration settings for Local SIM Agent API

Handles environment variables, LLM provider configuration,
and application settings with proper validation.
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="SIM_AGENT_LOCAL_HOST")
    port: int = Field(default=8001, env="SIM_AGENT_LOCAL_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # CORS configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "https://localhost:3000"],
        env="ALLOWED_ORIGINS"
    )
    
    # LLM Provider configuration (matches main Sim app)
    copilot_provider: str = Field(default="anthropic", env="COPILOT_PROVIDER")
    copilot_model: str = Field(default="claude-3-5-sonnet-latest", env="COPILOT_MODEL")
    
    # LLM API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    azure_openai_api_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    
    # API Key management
    api_key_secret: str = Field(default="local-sim-agent-secret", env="API_KEY_SECRET")
    
    # Performance settings
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")  # 5 minutes
    
    # Cache settings
    enable_cache: bool = Field(default=True, env="ENABLE_CACHE")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in .env file
    
    def get_llm_api_key(self) -> str:
        """Get the appropriate API key for the configured provider"""
        provider_key_map = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "google": self.google_api_key,
            "azure-openai": self.azure_openai_api_key,
        }
        
        api_key = provider_key_map.get(self.copilot_provider)
        if not api_key:
            raise ValueError(
                f"No API key found for provider '{self.copilot_provider}'. "
                f"Please set the appropriate environment variable."
            )
        
        return api_key
    
    def get_provider_config(self) -> dict:
        """Get provider-specific configuration"""
        base_config = {
            "provider": self.copilot_provider,
            "model": self.copilot_model,
            "api_key": self.get_llm_api_key(),
            "timeout": self.request_timeout,
        }
        
        # Add provider-specific settings
        if self.copilot_provider == "azure-openai":
            base_config["azure_endpoint"] = self.azure_openai_endpoint
        
        return base_config
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.debug and self.log_level.upper() in ["WARNING", "ERROR"]
    
    def validate_configuration(self) -> List[str]:
        """Validate the current configuration and return any issues"""
        issues = []
        
        # Check required API key
        try:
            self.get_llm_api_key()
        except ValueError as e:
            issues.append(str(e))
        
        # Check Azure-specific requirements
        if self.copilot_provider == "azure-openai" and not self.azure_openai_endpoint:
            issues.append("Azure OpenAI endpoint is required when using azure-openai provider")
        
        # Check port availability (basic check)
        if not (1024 <= self.port <= 65535):
            issues.append(f"Port {self.port} is not in valid range (1024-65535)")
        
        return issues

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get the global settings instance (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
        
        # Validate configuration on first load
        issues = _settings.validate_configuration()
        if issues:
            raise ValueError(f"Configuration validation failed: {'; '.join(issues)}")
    
    return _settings

def reload_settings() -> Settings:
    """Reload settings from environment (useful for testing)"""
    global _settings
    _settings = None
    return get_settings()