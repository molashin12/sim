#!/usr/bin/env python3
"""
LLM Service Abstraction

Provides a unified interface for multiple LLM providers including:
- OpenAI
- Anthropic
- Google Gemini
- Azure OpenAI

Supports both streaming and structured completions with tool calling.
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Any, Union
from abc import ABC, abstractmethod

import openai
import anthropic
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, model: str, api_key: str, **kwargs):
        self.model = model
        self.api_key = api_key
        self.kwargs = kwargs
    
    @abstractmethod
    async def chat_completion_stream(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion responses"""
        pass
    
    @abstractmethod
    async def structured_completion(
        self, 
        prompt: str, 
        schema: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured completion with optional schema validation"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup resources"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation"""
    
    def __init__(self, model: str, api_key: str, **kwargs):
        super().__init__(model, api_key, **kwargs)
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def chat_completion_stream(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream OpenAI chat completion"""
        try:
            request_params = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4000),
            }
            
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"
            
            stream = await self.client.chat.completions.create(**request_params)
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    
                    # Handle content
                    if delta.content:
                        yield {
                            "type": "content",
                            "content": delta.content
                        }
                    
                    # Handle tool calls
                    if delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            yield {
                                "type": "tool_call",
                                "tool_call": {
                                    "id": tool_call.id,
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                    }
                                }
                            }
                    
                    # Handle completion
                    if chunk.choices[0].finish_reason:
                        yield {
                            "type": "done",
                            "finish_reason": chunk.choices[0].finish_reason
                        }
        
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    async def structured_completion(
        self, 
        prompt: str, 
        schema: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured OpenAI completion"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 4000),
            }
            
            if schema:
                request_params["response_format"] = {
                    "type": "json_object"
                }
                # Add schema instruction to prompt
                messages[0]["content"] += f"\n\nPlease respond with valid JSON matching this schema: {json.dumps(schema)}"
            
            response = await self.client.chat.completions.create(**request_params)
            
            content = response.choices[0].message.content
            
            if schema:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON response", "raw_content": content}
            
            return {"content": content}
        
        except Exception as e:
            logger.error(f"OpenAI structured completion error: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup OpenAI client"""
        if hasattr(self.client, 'close'):
            await self.client.close()

class AnthropicProvider(LLMProvider):
    """Anthropic provider implementation"""
    
    def __init__(self, model: str, api_key: str, **kwargs):
        super().__init__(model, api_key, **kwargs)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def chat_completion_stream(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream Anthropic chat completion"""
        try:
            # Convert messages format
            anthropic_messages = []
            system_message = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            request_params = {
                "model": self.model,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens", 4000),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": True
            }
            
            if system_message:
                request_params["system"] = system_message
            
            if tools:
                # Convert tools to Anthropic format
                anthropic_tools = []
                for tool in tools:
                    anthropic_tools.append({
                        "name": tool["function"]["name"],
                        "description": tool["function"].get("description", ""),
                        "input_schema": tool["function"]["parameters"]
                    })
                request_params["tools"] = anthropic_tools
            
            async with self.client.messages.stream(**request_params) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            yield {
                                "type": "content",
                                "content": event.delta.text
                            }
                    elif event.type == "tool_use":
                        yield {
                            "type": "tool_call",
                            "tool_call": {
                                "id": event.id,
                                "function": {
                                    "name": event.name,
                                    "arguments": json.dumps(event.input)
                                }
                            }
                        }
                    elif event.type == "message_stop":
                        yield {
                            "type": "done",
                            "finish_reason": "stop"
                        }
        
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    async def structured_completion(
        self, 
        prompt: str, 
        schema: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured Anthropic completion"""
        try:
            if schema:
                prompt += f"\n\nPlease respond with valid JSON matching this schema: {json.dumps(schema)}"
            
            response = await self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 4000),
                temperature=kwargs.get("temperature", 0.1)
            )
            
            content = response.content[0].text
            
            if schema:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON response", "raw_content": content}
            
            return {"content": content}
        
        except Exception as e:
            logger.error(f"Anthropic structured completion error: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup Anthropic client"""
        pass  # Anthropic client doesn't require explicit cleanup

class GoogleProvider(LLMProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self, model: str, api_key: str, **kwargs):
        super().__init__(model, api_key, **kwargs)
        genai.configure(api_key=api_key)
        self.model_instance = genai.GenerativeModel(model)
    
    async def chat_completion_stream(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream Google Gemini completion"""
        try:
            # Convert messages to Gemini format
            prompt_parts = []
            for msg in messages:
                role_prefix = "Human: " if msg["role"] == "user" else "Assistant: "
                prompt_parts.append(f"{role_prefix}{msg['content']}")
            
            prompt = "\n\n".join(prompt_parts) + "\n\nAssistant: "
            
            generation_config = {
                "temperature": kwargs.get("temperature", 0.7),
                "max_output_tokens": kwargs.get("max_tokens", 4000),
            }
            
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            response = await self.model_instance.generate_content_async(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
                stream=True
            )
            
            async for chunk in response:
                if chunk.text:
                    yield {
                        "type": "content",
                        "content": chunk.text
                    }
            
            yield {
                "type": "done",
                "finish_reason": "stop"
            }
        
        except Exception as e:
            logger.error(f"Google streaming error: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    async def structured_completion(
        self, 
        prompt: str, 
        schema: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured Google completion"""
        try:
            if schema:
                prompt += f"\n\nPlease respond with valid JSON matching this schema: {json.dumps(schema)}"
            
            generation_config = {
                "temperature": kwargs.get("temperature", 0.1),
                "max_output_tokens": kwargs.get("max_tokens", 4000),
            }
            
            response = await self.model_instance.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            content = response.text
            
            if schema:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON response", "raw_content": content}
            
            return {"content": content}
        
        except Exception as e:
            logger.error(f"Google structured completion error: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup Google client"""
        pass  # Google client doesn't require explicit cleanup

class LLMService:
    """Main LLM service that manages different providers"""
    
    def __init__(self, provider: str, model: str, api_key: str, **kwargs):
        self.provider_name = provider
        self.model = model
        self.api_key = api_key
        self.kwargs = kwargs
        
        # Initialize the appropriate provider
        self.provider = self._create_provider(provider, model, api_key, **kwargs)
        
        logger.info(f"Initialized LLM service with provider: {provider}, model: {model}")
    
    def _create_provider(self, provider: str, model: str, api_key: str, **kwargs) -> LLMProvider:
        """Create the appropriate provider instance"""
        provider_map = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "google": GoogleProvider,
            "azure-openai": OpenAIProvider,  # Uses OpenAI client with different endpoint
        }
        
        if provider not in provider_map:
            raise ValueError(f"Unsupported provider: {provider}")
        
        provider_class = provider_map[provider]
        
        # Handle Azure OpenAI special case
        if provider == "azure-openai":
            kwargs["azure_endpoint"] = kwargs.get("azure_endpoint")
        
        return provider_class(model, api_key, **kwargs)
    
    async def chat_completion_stream(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion from the configured provider"""
        async for chunk in self.provider.chat_completion_stream(messages, tools, **kwargs):
            yield chunk
    
    async def structured_completion(
        self, 
        prompt: str, 
        schema: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured completion from the configured provider"""
        return await self.provider.structured_completion(prompt, schema, **kwargs)
    
    async def cleanup(self):
        """Cleanup the provider"""
        if self.provider:
            await self.provider.cleanup()
    
    def get_info(self) -> Dict[str, str]:
        """Get service information"""
        return {
            "provider": self.provider_name,
            "model": self.model,
            "status": "ready"
        }