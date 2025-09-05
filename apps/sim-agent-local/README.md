# Local SIM Agent API

A comprehensive local replacement for the external SIM Agent API service that provides all the functionality needed to make the copilot fully functional and independent.

## Overview

The Local SIM Agent API is a FastAPI-based service that provides:

- **Chat Completion Streaming**: Real-time streaming chat completions with tool calling support
- **YAML Processing**: Convert natural language to workflow YAML, parse, validate, and auto-layout
- **Workflow Management**: Validate, optimize, and analyze workflows with AI-powered insights
- **Tool Management**: Track and manage tool executions with comprehensive analytics
- **Authentication**: Multi-provider API key validation and local key management

## Features

### 🚀 Core Capabilities

- **Multi-Provider LLM Support**: OpenAI, Anthropic, Google Gemini, Azure OpenAI
- **Streaming Responses**: Server-Sent Events (SSE) for real-time chat completions
- **Tool Calling**: Full support for function calling and tool execution
- **YAML Intelligence**: AI-powered YAML generation, validation, and optimization
- **Auto-Layout Algorithms**: Hierarchical, force-directed, and grid layout algorithms
- **Workflow Analytics**: Performance analysis and optimization recommendations
- **Health Monitoring**: Comprehensive health checks and service monitoring

### 🔧 Technical Features

- **Asynchronous Architecture**: Built with FastAPI and async/await patterns
- **Type Safety**: Full Pydantic model validation and type hints
- **Error Handling**: Robust error handling with graceful degradation
- **Security**: CORS, trusted hosts, API key validation, and secure configurations
- **Logging**: Structured logging with Rich console output for development
- **Configuration**: Environment-based configuration with sensible defaults

## Quick Start

### Prerequisites

- Python 3.8+
- pip or conda
- API keys for your preferred LLM providers

### Installation

1. **Clone and navigate to the project**:
   ```bash
   cd d:\CODING\sim\apps\sim-agent-local
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your configuration
   # At minimum, set your LLM provider API keys
   ```

4. **Run the server**:
   ```bash
   python main.py
   ```

5. **Access the API**:
   - API: `http://localhost:8000`
   - Documentation: `http://localhost:8000/docs` (development mode)
   - Health Check: `http://localhost:8000/health`

## Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Server Configuration
SERVER_HOST=localhost
SERVER_PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# LLM Provider Configuration
COPILOT_PROVIDER=openai
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Security Configuration
CORS_ENABLED=true
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["*"]

# Performance Configuration
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=300
CLEANUP_INTERVAL=3600
API_KEY_CACHE_TTL=3600
```

### Provider Configuration

The service supports multiple LLM providers. Set `COPILOT_PROVIDER` to your preferred default:

- `openai` - OpenAI GPT models
- `anthropic` - Anthropic Claude models
- `google` - Google Gemini models
- `azure` - Azure OpenAI models

## API Endpoints

### Chat Completion

**POST** `/api/chat-completion-streaming`

Stream chat completions with tool calling support.

```json
{
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "model": "gpt-4",
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### YAML Processing

- **POST** `/yaml/to-workflow` - Convert natural language to workflow YAML
- **POST** `/yaml/parse` - Parse and validate YAML
- **POST** `/yaml/diff/create` - Create intelligent diffs between YAML files
- **POST** `/yaml/diff/merge` - Merge diffs into original YAML
- **POST** `/yaml/autolayout` - Auto-layout workflow blocks

### Workflow Management

- **POST** `/workflow/to-yaml` - Convert workflow structure to YAML
- **POST** `/workflow/validate` - Validate workflow structure
- **POST** `/workflow/optimize` - Optimize workflow performance
- **POST** `/workflow/analyze` - Analyze workflow for insights
- **GET** `/workflow/templates` - Get available templates
- **POST** `/workflow/from-template` - Create workflow from template

### Tool Management

- **POST** `/tools/mark-complete` - Mark tool as completed
- **GET** `/tools/status/{tool_id}` - Get tool status
- **GET** `/tools/session/{session_id}` - Get session tools
- **POST** `/tools/create` - Create new tool
- **GET** `/tools/analytics` - Get usage analytics

### Authentication

- **POST** `/validate-key/{key_type}` - Validate API key
- **POST** `/validate-key/batch` - Batch validate keys
- **GET** `/providers` - List supported providers
- **GET** `/provider/{provider}/models` - Get provider models
- **POST** `/test-connection` - Test provider connection

## Usage Examples

### Chat Completion with Streaming

```python
import httpx
import json

async def stream_chat():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/chat-completion-streaming",
            json={
                "messages": [{"role": "user", "content": "Hello!"}],
                "model": "gpt-4",
                "stream": True
            },
            headers={"Accept": "text/event-stream"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data != "[DONE]":
                        chunk = json.loads(data)
                        print(chunk)
```

### Convert Natural Language to YAML

```python
import httpx

async def create_workflow():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/yaml/to-workflow",
            json={
                "description": "Create a workflow that processes user input, validates it, and sends an email notification",
                "workflow_type": "automation"
            }
        )
        result = response.json()
        print(result["yaml_content"])
```

### Validate API Key

```python
import httpx

async def validate_key():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/validate-key/openai",
            json={"api_key": "sk-..."}
        )
        result = response.json()
        print(f"Valid: {result['is_valid']}")
```

## Architecture

### Service Layer

- **LLMService**: Manages multiple LLM providers with unified interface
- **YamlService**: Handles YAML processing, validation, and auto-layout
- **ToolService**: Manages tool execution tracking and analytics
- **AuthService**: Handles API key validation and management

### API Layer

- **FastAPI Application**: Main application with middleware and routing
- **Router Modules**: Organized endpoints by functionality
- **Pydantic Models**: Type-safe request/response validation
- **Exception Handlers**: Centralized error handling

### Configuration

- **Settings Management**: Environment-based configuration
- **Provider Abstraction**: Unified interface for different LLM providers
- **Logging System**: Structured logging with Rich console output

## Development

### Running in Development Mode

```bash
# Set DEBUG=true in .env
DEBUG=true

# Run with auto-reload
python main.py
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### Production Configuration

```bash
# Production environment variables
DEBUG=false
LOG_LEVEL=WARNING
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Security settings
CORS_ORIGINS=["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=false
```

## Monitoring

### Health Checks

- **Basic Health**: `GET /health`
- **Detailed Health**: `GET /health/detailed`
- **Service-Specific Health**: Each API module includes health endpoints

### Logging

The service provides structured logging with different levels:

- **DEBUG**: Detailed debugging information
- **INFO**: General operational information
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical error conditions

### Metrics

- Request/response metrics
- Tool execution statistics
- Provider usage tracking
- Performance benchmarks

## Troubleshooting

### Common Issues

1. **API Key Validation Fails**
   - Verify API keys are correctly set in `.env`
   - Check provider-specific key formats
   - Ensure network connectivity to provider APIs

2. **YAML Processing Errors**
   - Verify LLM provider is configured and accessible
   - Check input format and content
   - Review error logs for specific validation issues

3. **Streaming Connection Issues**
   - Verify client supports Server-Sent Events
   - Check CORS configuration for cross-origin requests
   - Ensure proper headers are set

### Debug Mode

Enable debug mode for detailed logging and API documentation:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is part of the SIM ecosystem. See the main repository for license information.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Check the health endpoints for service status
4. Review logs for detailed error information

---

**Note**: This local API service is designed to be a complete replacement for the external SIM Agent API, providing all necessary functionality for the copilot to operate independently.