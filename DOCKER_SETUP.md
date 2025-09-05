# Docker Setup Guide for SIM Project

This guide will help you run the entire SIM project using Docker containers.

## Prerequisites

- Docker and Docker Compose installed on your system
- At least 8GB of available RAM
- API keys for your preferred LLM provider (OpenAI, Anthropic, Google, etc.)

## Quick Start

### 1. Environment Setup

First, create a `.env` file in the project root with your configuration:

```bash
# Copy the example environment file
cp apps/sim-agent-local/.env.example .env
```

Edit the `.env` file and set your API keys:

```bash
# Required: Set at least one LLM provider API key
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Customize other settings
COPILOT_PROVIDER=openai
NEXT_PUBLIC_APP_URL=http://localhost:3000
BETTER_AUTH_SECRET=your_auth_secret_here
ENCRYPTION_KEY=your_encryption_key_here

# Database settings (optional, defaults provided)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=simstudio
POSTGRES_PORT=5432
```

### 2. Run the Project

```bash
# Start all services
docker-compose -f docker-compose.local.yml up -d

# Or start with logs visible
docker-compose -f docker-compose.local.yml up
```

### 3. Access the Services

Once all containers are running, you can access:

- **SIM Studio Web App**: http://localhost:3000
- **Local SIM Agent API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Realtime Socket Server**: http://localhost:3002
- **PostgreSQL Database**: localhost:5432

## Services Overview

The Docker setup includes the following services:

### 1. **simstudio** (Port 3000)
- Main web application built with Next.js
- Provides the user interface for SIM Studio
- Depends on database and realtime services

### 2. **sim-agent-local** (Port 8001)
- Local API service replacing external SIM-managed API
- FastAPI-based Python service
- Handles LLM interactions and tool processing

### 3. **realtime** (Port 3002)
- WebSocket server for real-time communication
- Handles live updates and notifications

### 4. **db** (Port 5432)
- PostgreSQL database with pgvector extension
- Stores application data and vector embeddings

### 5. **migrations**
- One-time service that runs database migrations
- Automatically sets up the database schema

## Common Commands

### Start Services
```bash
# Start all services in background
docker-compose -f docker-compose.local.yml up -d

# Start specific service
docker-compose -f docker-compose.local.yml up simstudio
```

### Stop Services
```bash
# Stop all services
docker-compose -f docker-compose.local.yml down

# Stop and remove volumes (WARNING: This will delete your data)
docker-compose -f docker-compose.local.yml down -v
```

### View Logs
```bash
# View logs for all services
docker-compose -f docker-compose.local.yml logs

# View logs for specific service
docker-compose -f docker-compose.local.yml logs simstudio

# Follow logs in real-time
docker-compose -f docker-compose.local.yml logs -f
```

### Rebuild Services
```bash
# Rebuild all services
docker-compose -f docker-compose.local.yml build

# Rebuild specific service
docker-compose -f docker-compose.local.yml build sim-agent-local

# Rebuild and restart
docker-compose -f docker-compose.local.yml up --build
```

## Health Checks

All services include health checks. You can monitor service health:

```bash
# Check service status
docker-compose -f docker-compose.local.yml ps

# View detailed health status
docker inspect <container_name> | grep Health -A 10
```

## Troubleshooting

### Service Won't Start
1. Check logs: `docker-compose -f docker-compose.local.yml logs <service_name>`
2. Verify environment variables are set correctly
3. Ensure required ports are not in use by other applications

### Database Connection Issues
1. Wait for database to be fully ready (health check passes)
2. Check database credentials in `.env` file
3. Verify migrations completed successfully

### Memory Issues
1. Ensure you have at least 8GB RAM available
2. Adjust memory limits in docker-compose.local.yml if needed
3. Close other resource-intensive applications

### API Key Issues
1. Verify API keys are correctly set in `.env` file
2. Check that the COPILOT_PROVIDER matches your available API key
3. Test API keys independently before using in Docker

## Development Mode

For development with hot reloading:

1. Set `DEBUG=true` in your `.env` file
2. The sim-agent-local service will automatically reload on code changes
3. The main app supports hot reloading through Next.js

## Production Considerations

For production deployment:

1. Use `docker-compose.prod.yml` instead of `docker-compose.local.yml`
2. Set strong, unique values for all secrets
3. Configure proper CORS origins
4. Set up proper SSL/TLS termination
5. Configure backup strategies for the database
6. Monitor resource usage and scale accordingly

## Alternative Docker Compose Files

- `docker-compose.local.yml` - Local development (this guide)
- `docker-compose.prod.yml` - Production deployment
- `docker-compose.ollama.yml` - Local setup with Ollama for offline LLM usage

## Support

If you encounter issues:

1. Check the logs for error messages
2. Verify your environment configuration
3. Ensure all prerequisites are met
4. Refer to the main project README for additional information