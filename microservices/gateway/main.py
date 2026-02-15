#!/usr/bin/env python3
"""
Gateway Service - Entry point for all external requests.
Handles API requests, authentication, and routing to other microservices.
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import redis
from shared.models.base import ServiceResponse, Command, Event

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sinik Gateway Service",
    description="Gateway service for handling external requests",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis client
redis_client = None
try:
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

# Service URLs from environment variables
SERVICE_URLS = {
    "entity": os.getenv("ENTITY_SERVICE_URL", "http://entity:8000"),
    "brain": os.getenv("BRAIN_SERVICE_URL", "http://brain:8000"),
    "ha-manager": os.getenv("HA_MANAGER_SERVICE_URL", "http://ha-manager:8000"),
    "infrastructure-manager": os.getenv("INFRASTRUCTURE_MANAGER_SERVICE_URL", "http://infrastructure-manager:8000"),
    "protocol": os.getenv("PROTOCOL_SERVICE_URL", "http://protocol:8000"),
    "reconciler": os.getenv("RECONCILER_SERVICE_URL", "http://reconciler:8000"),
    "sensor": os.getenv("SENSOR_SERVICE_URL", "http://sensor:8000"),
}


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    timestamp: str
    redis_connected: bool
    services_available: Dict[str, bool]


class CommandRequest(BaseModel):
    """Command request model."""
    entity_id: str
    command: str
    parameters: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    priority: int = 0


async def get_http_client() -> httpx.AsyncClient:
    """Dependency for HTTP client."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@app.get("/", response_model=ServiceResponse)
async def root():
    """Root endpoint."""
    return ServiceResponse(
        success=True,
        data={
            "service": "gateway",
            "version": "1.0.0",
            "description": "Gateway service for Sinik IoT platform"
        }
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    import datetime
    
    # Check Redis connection
    redis_connected = False
    if redis_client:
        try:
            redis_client.ping()
            redis_connected = True
        except:
            redis_connected = False
    
    # Check service availability
    services_available = {}
    for service_name, service_url in SERVICE_URLS.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                services_available[service_name] = response.status_code == 200
        except:
            services_available[service_name] = False
    
    return HealthResponse(
        status="healthy",
        service="gateway",
        timestamp=datetime.datetime.utcnow().isoformat(),
        redis_connected=redis_connected,
        services_available=services_available
    )


@app.post("/api/v1/command", response_model=ServiceResponse)
async def send_command(
    command_request: CommandRequest,
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Send a command to an entity."""
    try:
        # Create command object
        command = Command(
            entity_id=command_request.entity_id,
            command=command_request.command,
            parameters=command_request.parameters or {},
            source=command_request.source or request.client.host,
            priority=command_request.priority
        )
        
        # Store command in Redis for tracking
        if redis_client:
            import json
            command_key = f"command:{command.entity_id}:{command.timestamp.isoformat()}"
            redis_client.setex(
                command_key,
                3600,  # 1 hour TTL
                json.dumps(command.dict())
            )
        
        # Route command to appropriate service based on entity type
        # For now, route to entity service
        entity_service_url = SERVICE_URLS["entity"]
        response = await client.post(
            f"{entity_service_url}/api/v1/command",
            json=command.dict(),
            timeout=10.0
        )
        
        if response.status_code == 200:
            return ServiceResponse(
                success=True,
                data=response.json()
            )
        else:
            return ServiceResponse(
                success=False,
                error=f"Failed to execute command: {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/entities", response_model=ServiceResponse)
async def get_entities(
    entity_type: Optional[str] = None,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Get all entities or filter by type."""
    try:
        entity_service_url = SERVICE_URLS["entity"]
        params = {}
        if entity_type:
            params["entity_type"] = entity_type
            
        response = await client.get(
            f"{entity_service_url}/api/v1/entities",
            params=params,
            timeout=10.0
        )
        
        if response.status_code == 200:
            return ServiceResponse(
                success=True,
                data=response.json()
            )
        else:
            return ServiceResponse(
                success=False,
                error=f"Failed to get entities: {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Error getting entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/entities/{entity_id}", response_model=ServiceResponse)
async def get_entity(
    entity_id: str,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Get a specific entity by ID."""
    try:
        entity_service_url = SERVICE_URLS["entity"]
        response = await client.get(
            f"{entity_service_url}/api/v1/entities/{entity_id}",
            timeout=10.0
        )
        
        if response.status_code == 200:
            return ServiceResponse(
                success=True,
                data=response.json()
            )
        else:
            return ServiceResponse(
                success=False,
                error=f"Failed to get entity: {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Error getting entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/events", response_model=ServiceResponse)
async def create_event(
    event: Event,
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Create a new event."""
    try:
        # Store event in Redis
        if redis_client:
            import json
            event_key = f"event:{event.event_type}:{event.timestamp.isoformat()}"
            redis_client.setex(
                event_key,
                86400,  # 24 hour TTL
                json.dumps(event.dict())
            )
        
        # Publish event to all interested services
        # For now, just log it
        logger.info(f"Event received: {event.event_type} - {event.data}")
        
        return ServiceResponse(
            success=True,
            data={"event_id": event_key if redis_client else "no_redis"}
        )
            
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting Gateway Service on {host}:{port}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
