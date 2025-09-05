# Local SIM Agent API Implementation Plan

## Overview

This document outlines the implementation of a local SIM Agent API service to replace the external `https://agent.sim.ai` dependency, making the Copilot feature fully self-contained and independent.

## Current External API Dependencies

The Copilot system currently depends on these external endpoints:

### Core Chat & AI
- `POST /api/chat-completion-streaming` - Main conversational AI interface
- `POST /api/stats` - Usage analytics and feedback tracking

### Workflow Processing
- `POST /api/yaml/to-workflow` - Convert YAML/natural language to workflow structure
- `POST /api/yaml/parse` - Parse and validate YAML workflow definitions
- `POST /api/workflow/to-yaml` - Convert workflow state to YAML format
- `POST /api/yaml/diff/create` - Create workflow diffs for intelligent editing
- `POST /api/yaml/diff/merge` - Apply workflow diffs
- `POST /api/yaml/autolayout` - Auto-arrange workflow blocks

### Tool Management
- `POST /api/tools/mark-complete` - Handle tool completion states

### API Key Management
- `POST /api/validate-key/generate` - Generate API keys
- `GET /api/validate-key/get-api-keys` - List API keys
- `DELETE /api/validate-key/delete` - Delete API keys

## Architecture Design

### System Overview
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Sim App       │    │  Local SIM Agent │    │   LLM Provider  │
│   (Frontend)    │◄──►│     API          │◄──►│  (OpenAI/etc)   │
│                 │    │   (FastAPI)      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Technology Stack
- **Framework**: FastAPI (Python) for high-performance async API
- **LLM Integration**: Support for OpenAI, Anthropic, Google, Azure OpenAI
- **YAML Processing**: PyYAML with custom validation
- **Auto-layout**: NetworkX for graph algorithms
- **Streaming**: Server-Sent Events (SSE) for chat streaming
- **Containerization**: Docker for easy deployment

### Project Structure
```
apps/sim-agent-local/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Local development setup
├── config/
│   ├── __init__.py
│   ├── settings.py        # Environment configuration
│   └── llm_config.py      # LLM provider settings
├── api/
│   ├── __init__.py
│   ├── chat.py            # Chat completion endpoints
│   ├── yaml_processing.py # YAML conversion endpoints
│   ├── workflow.py        # Workflow management endpoints
│   ├── tools.py           # Tool management endpoints
│   └── auth.py            # API key validation endpoints
├── services/
│   ├── __init__.py
│   ├── llm_service.py     # LLM provider abstraction
│   ├── yaml_service.py    # YAML processing logic
│   ├── workflow_service.py # Workflow state management
│   ├── layout_service.py  # Auto-layout algorithms
│   └── diff_service.py    # Workflow diffing logic
├── prompts/
│   ├── __init__.py
│   ├── chat_prompts.py    # Conversational AI prompts
│   ├── workflow_prompts.py # Workflow building prompts
│   ├── yaml_prompts.py    # YAML processing prompts
│   └── editing_prompts.py # Workflow editing prompts
├── models/
│   ├── __init__.py
│   ├── requests.py        # Request/response models
│   ├── workflow.py        # Workflow data structures
│   └── chat.py            # Chat message models
├── utils/
│   ├── __init__.py
│   ├── validation.py      # YAML/workflow validation
│   ├── streaming.py       # SSE streaming utilities
│   └── logging.py         # Logging configuration
└── tests/
    ├── __init__.py
    ├── test_chat.py
    ├── test_yaml.py
    ├── test_workflow.py
    └── test_integration.py
```

## Implementation Phases

### Phase 1: Core Infrastructure
1. **FastAPI Setup**
   - Basic FastAPI application with proper error handling
   - Environment configuration management
   - Logging and monitoring setup
   - Health check endpoints

2. **LLM Integration**
   - Abstract LLM service supporting multiple providers
   - Configuration matching existing Copilot settings
   - Proper error handling and retry logic
   - Token usage tracking

### Phase 2: Chat Functionality
1. **Chat Completion Streaming**
   - Server-Sent Events implementation
   - Tool calling support (build_workflow, edit_workflow)
   - Context management and conversation history
   - Streaming response formatting

2. **Specialized Prompts**
   - Conversational AI prompts for Sim Studio context
   - Workflow explanation and guidance prompts
   - Error handling and fallback responses

### Phase 3: Workflow Processing
1. **YAML Processing**
   - YAML to workflow conversion with validation
   - Workflow to YAML generation
   - Schema validation against Sim's workflow structure
   - Error reporting and suggestions

2. **Workflow Intelligence**
   - Natural language to workflow conversion
   - Block type understanding and validation
   - Connection logic and data flow analysis
   - Best practice recommendations

### Phase 4: Advanced Features
1. **Workflow Editing**
   - Intelligent diff creation and merging
   - Operation validation and conflict resolution
   - Undo/redo support
   - Change impact analysis

2. **Auto-layout**
   - Graph-based layout algorithms
   - Block positioning optimization
   - Connection routing
   - Visual hierarchy management

### Phase 5: Tool & API Management
1. **Tool Management**
   - Tool completion state tracking
   - Progress monitoring
   - Error handling and recovery

2. **API Key Management**
   - Local API key generation and validation
   - Usage tracking and analytics
   - Security and access control

## Technical Specifications

### LLM Integration
```python
class LLMService:
    def __init__(self, provider: str, model: str, api_key: str):
        self.provider = provider
        self.model = model
        self.client = self._create_client(provider, api_key)
    
    async def chat_completion_stream(self, messages, tools=None):
        # Streaming chat completion with tool support
        pass
    
    async def structured_completion(self, prompt, schema):
        # Structured output for YAML/workflow generation
        pass
```

### YAML Processing
```python
class YAMLService:
    def __init__(self, llm_service: LLMService, block_registry: dict):
        self.llm = llm_service
        self.blocks = block_registry
    
    async def yaml_to_workflow(self, yaml_content: str, description: str = None):
        # Convert YAML + description to workflow state
        pass
    
    async def workflow_to_yaml(self, workflow_state: dict):
        # Convert workflow state to YAML
        pass
    
    def validate_yaml(self, yaml_content: str):
        # Validate YAML against Sim's schema
        pass
```

### Auto-layout Algorithm
```python
class LayoutService:
    def __init__(self):
        self.algorithms = {
            'smart': self._smart_layout,
            'hierarchical': self._hierarchical_layout,
            'force_directed': self._force_directed_layout
        }
    
    def auto_layout(self, workflow_state: dict, options: dict):
        # Apply layout algorithm to position blocks
        pass
```

### Streaming Chat Implementation
```python
@app.post("/api/chat-completion-streaming")
async def chat_completion_streaming(request: ChatRequest):
    async def generate():
        async for chunk in llm_service.chat_completion_stream(
            messages=request.messages,
            tools=request.tools
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )
```

## Specialized Prompts

### Chat System Prompt
```
You are a helpful AI assistant for Sim Studio, a powerful workflow automation platform.

You help users:
- Build and edit workflows using visual blocks
- Understand workflow concepts and best practices
- Debug and optimize automation processes
- Connect different services and APIs

Key capabilities:
- Explain workflow concepts clearly
- Suggest improvements and optimizations
- Help with block configuration and connections
- Provide troubleshooting guidance

Available blocks: {block_registry}
Current workflow: {workflow_context}
```

### Workflow Building Prompt
```
Convert the following description into a Sim Studio workflow.

Description: {description}
YAML Content: {yaml_content}

Generate a workflow with:
1. Appropriate blocks for the described functionality
2. Proper connections between blocks
3. Correct configuration for each block
4. Logical flow and error handling

Available blocks: {block_registry}

Return the workflow as a JSON object with blocks, edges, and metadata.
```

### YAML Processing Prompt
```
Parse and validate this YAML workflow definition:

{yaml_content}

Tasks:
1. Validate syntax and structure
2. Check block types against registry
3. Verify connections and data flow
4. Identify potential issues
5. Suggest improvements

Block registry: {block_registry}

Return validation results and processed workflow state.
```

## Environment Configuration

### Required Environment Variables
```bash
# LLM Provider Configuration (matches main app)
COPILOT_PROVIDER=anthropic
COPILOT_MODEL=claude-3-5-sonnet-latest
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Service Configuration
SIM_AGENT_LOCAL_PORT=8001
SIM_AGENT_LOCAL_HOST=0.0.0.0
LOG_LEVEL=INFO

# Security
API_KEY_SECRET=your-secret-for-key-generation
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Docker Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## Integration with Main App

### Environment Variable Update
```bash
# In main Sim app .env
SIM_AGENT_API_URL=http://localhost:8001
# or for production
SIM_AGENT_API_URL=http://sim-agent-local:8001
```

### Docker Compose Integration
```yaml
services:
  sim-app:
    # ... existing config
    environment:
      - SIM_AGENT_API_URL=http://sim-agent-local:8001
    depends_on:
      - sim-agent-local
  
  sim-agent-local:
    build: ./apps/sim-agent-local
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - COPILOT_PROVIDER=${COPILOT_PROVIDER:-anthropic}
      - COPILOT_MODEL=${COPILOT_MODEL:-claude-3-5-sonnet-latest}
```

## Testing Strategy

### Unit Tests
- LLM service integration tests
- YAML processing validation
- Workflow state management
- Auto-layout algorithms

### Integration Tests
- End-to-end API endpoint testing
- Streaming response validation
- Error handling scenarios
- Performance benchmarks

### Compatibility Tests
- Verify exact API compatibility with external service
- Test all existing Copilot features
- Validate response formats and timing

## Deployment Options

### Development
```bash
cd apps/sim-agent-local
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Production
```bash
docker-compose up -d sim-agent-local
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sim-agent-local
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sim-agent-local
  template:
    metadata:
      labels:
        app: sim-agent-local
    spec:
      containers:
      - name: sim-agent-local
        image: sim-agent-local:latest
        ports:
        - containerPort: 8001
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-api-key
```

## Performance Considerations

### Optimization Strategies
- **Caching**: Cache frequently used prompts and responses
- **Connection Pooling**: Reuse LLM API connections
- **Async Processing**: Handle multiple requests concurrently
- **Response Streaming**: Stream large responses for better UX

### Monitoring
- Request/response times
- LLM token usage
- Error rates and types
- Memory and CPU usage

## Security Considerations

### API Security
- API key validation and rotation
- Rate limiting per client
- Input validation and sanitization
- CORS configuration

### LLM Security
- Prompt injection prevention
- Output filtering and validation
- API key protection
- Usage monitoring

## Migration Plan

### Phase 1: Parallel Deployment
1. Deploy local service alongside external API
2. Add feature flag to switch between services
3. Test compatibility with subset of users

### Phase 2: Gradual Migration
1. Route percentage of traffic to local service
2. Monitor performance and error rates
3. Gradually increase local service usage

### Phase 3: Full Migration
1. Switch all traffic to local service
2. Remove external API dependency
3. Update documentation and deployment guides

## Success Metrics

### Functionality
- ✅ All Copilot features work identically
- ✅ Response times within 10% of external service
- ✅ Error rates below 1%
- ✅ 100% API compatibility

### Independence
- ✅ No external API dependencies
- ✅ Full local deployment capability
- ✅ Configurable LLM providers
- ✅ Self-contained operation

### Quality
- ✅ Comprehensive test coverage (>90%)
- ✅ Production-ready error handling
- ✅ Monitoring and observability
- ✅ Documentation and setup guides

## Next Steps

1. **Create Project Structure**: Set up the FastAPI project with proper organization
2. **Implement Core Infrastructure**: Basic FastAPI app with LLM integration
3. **Build Chat Functionality**: Streaming chat completion with tool support
4. **Add YAML Processing**: Workflow conversion and validation
5. **Implement Advanced Features**: Auto-layout, diffing, and tool management
6. **Testing and Validation**: Comprehensive testing against external API
7. **Documentation and Deployment**: Setup guides and production deployment

This plan provides a comprehensive roadmap for creating a professional, self-contained Copilot service that eliminates external dependencies while maintaining full functionality and compatibility.