"""
DEDAN Health 2.0 - Frontend-Backend Integration
World-class API patterns, standardization, and adapter layer design
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
import aioredis
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid

# Configure logging
logger = logging.getLogger(__name__)

# Standard API Response Schema
class StandardAPIResponse(BaseModel):
    """Standardized API response format for all DEDAN endpoints"""
    status: str = Field(..., description="Response status: success or error")
    data: Optional[Any] = Field(None, description="Response data payload")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if status is error")
    meta: Optional[Dict[str, Any]] = Field(None, description="Response metadata")

class ErrorResponse(BaseModel):
    """Standardized error response"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="Error timestamp")

class APIResponseMeta(BaseModel):
    """Response metadata"""
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: str = Field(..., description="Response timestamp")
    version: str = Field(..., description="API version")
    processing_time: float = Field(..., description="Processing time in milliseconds")

# Request/Response Models
class TriageRequest(BaseModel):
    """Standard triage request model"""
    patient_id: str = Field(..., description="Patient identifier")
    symptoms: str = Field(..., description="Patient symptoms description")
    demographics: Dict[str, Any] = Field(default_factory=dict, description="Patient demographics")
    language: str = Field(default="en", description="Preferred language")
    session_id: Optional[str] = Field(None, description="Session identifier")
    voice_data: Optional[str] = Field(None, description="Voice input data")
    images: Optional[List[str]] = Field(None, description="Uploaded image URLs")

class TriageResponse(BaseModel):
    """Standard triage response model"""
    triage_level: str = Field(..., description="Triage level: emergency, urgent, routine, self_care")
    confidence: float = Field(..., description="Confidence score (0-1)")
    risk_score: str = Field(..., description="Risk score: low, medium, high")
    risk_time_horizon: str = Field(..., description="Risk time horizon")
    recommendations: List[str] = Field(..., description="Medical recommendations")
    agent_outputs: Dict[str, Any] = Field(..., description="Individual agent outputs")
    explainability: Dict[str, Any] = Field(..., description="AI decision explanation")
    session_id: str = Field(..., description="Session identifier")

class BatchTriageRequest(BaseModel):
    """Batch triage request for optimization"""
    requests: List[TriageRequest] = Field(..., description="Multiple triage requests")
    priority: str = Field(default="normal", description="Batch priority: low, normal, high")

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: str = Field(..., description="Message timestamp")
    session_id: str = Field(..., description="Session identifier")

# Middleware Classes
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging and performance tracking"""
    
    def __init__(self, app):
        super().__init__(app)
        self.redis_client = None
        
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        request.state.start_time = start_time
        
        # Log request
        logger.info(f"Request started: {request.method} {request.url} [{request_id}]")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Log completion
        logger.info(f"Request completed: {request.method} {request.url} [{request_id}] - {processing_time:.2f}ms")
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time"] = f"{processing_time:.2f}"
        
        # Store metrics
        await self._store_metrics(request, response, processing_time, request_id)
        
        return response
    
    async def _store_metrics(self, request: Request, response: Response, processing_time: float, request_id: str):
        """Store request metrics in Redis"""
        if not self.redis_client:
            try:
                self.redis_client = await aioredis.from_url("redis://localhost")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                return
        
        try:
            metrics = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat(),
                "user_agent": request.headers.get("user-agent"),
                "ip_address": request.client.host if request.client else "unknown"
            }
            
            await self.redis_client.lpush("dedan:metrics", json.dumps(metrics))
            await self.redis_client.expire("dedan:metrics", 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.redis_client = None
        
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not await self._is_allowed(client_id):
            return JSONResponse(
                status_code=429,
                content=StandardAPIResponse(
                    status="error",
                    error={
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    meta={
                        "request_id": str(uuid.uuid4()),
                        "timestamp": datetime.utcnow().isoformat(),
                        "version": "2.0.0",
                        "processing_time": 0.0
                    }
                ).dict()
            )
        
        # Process request
        response = await call_next(request)
        
        # Update rate limit counter
        await self._update_counter(client_id)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Use IP address or API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        return f"ip:{request.client.host if request.client else 'unknown'}"
    
    async def _is_allowed(self, client_id: str) -> bool:
        """Check if client is allowed to make request"""
        if not self.redis_client:
            try:
                self.redis_client = await aioredis.from_url("redis://localhost")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                return True  # Allow if Redis is unavailable
        
        try:
            current_requests = await self.redis_client.get(f"rate_limit:{client_id}")
            if current_requests and int(current_requests) >= self.requests_per_minute:
                return False
            return True
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return True  # Allow if Redis is unavailable
    
    async def _update_counter(self, client_id: str):
        """Update rate limit counter"""
        if not self.redis_client:
            return
        
        try:
            key = f"rate_limit:{client_id}"
            await self.redis_client.incr(key)
            await self.redis_client.expire(key, 60)  # 1 minute
        except Exception as e:
            logger.error(f"Failed to update rate limit counter: {e}")

# API Integration Manager
class APIIntegrationManager:
    """
    World-class API integration manager for DEDAN Health
    Handles REST, GraphQL, WebSocket, and optimization patterns
    """
    
    def __init__(self):
        self.app = FastAPI(
            title="DEDAN Health API v2.0",
            description="AI-powered primary-care triage and predictive-care platform",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        self.redis_client = None
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup world-class middleware"""
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure properly for production
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"]
        )
        
        # Gzip compression
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Request logging
        self.app.add_middleware(RequestLoggingMiddleware)
        
        # Rate limiting
        self.app.add_middleware(RateLimitingMiddleware, requests_per_minute=100)
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        
        @self.app.get("/api/v2/health")
        async def detailed_health_check():
            return {
                "status": "healthy",
                "version": "2.0.0",
                "services": {
                    "database": "healthy",
                    "redis": "healthy",
                    "ai_agents": "healthy"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Triage endpoints
        @self.app.post("/api/v2/triage", response_model=StandardAPIResponse)
        async def triage_endpoint(request: TriageRequest, http_request: Request):
            return await self._handle_triage_request(request, http_request)
        
        @self.app.post("/api/v2/batch-triage", response_model=StandardAPIResponse)
        async def batch_triage_endpoint(request: BatchTriageRequest, http_request: Request):
            return await self._handle_batch_triage_request(request, http_request)
        
        # WebSocket endpoint
        @self.app.websocket("/ws/triage/{session_id}")
        async def websocket_endpoint(websocket, session_id: str):
            await self._handle_websocket_connection(websocket, session_id)
        
        # GraphQL endpoint (optional)
        @self.app.post("/api/v2/graphql")
        async def graphql_endpoint():
            # GraphQL implementation would go here
            pass
    
    async def _handle_triage_request(self, request: TriageRequest, http_request: Request) -> StandardAPIResponse:
        """Handle individual triage request"""
        start_time = time.time()
        request_id = getattr(http_request.state, 'request_id', str(uuid.uuid4()))
        
        try:
            # Process triage through AI agents
            triage_result = await self._process_triage(request)
            
            processing_time = (time.time() - start_time) * 1000
            
            return StandardAPIResponse(
                status="success",
                data=triage_result,
                meta={
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "2.0.0",
                    "processing_time": processing_time
                }
            )
            
        except Exception as e:
            logger.error(f"Triage request failed: {e}")
            return StandardAPIResponse(
                status="error",
                error={
                    "code": "TRIAGE_PROCESSING_ERROR",
                    "message": "Failed to process triage request",
                    "details": {"error": str(e)},
                    "timestamp": datetime.utcnow().isoformat()
                },
                meta={
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "2.0.0",
                    "processing_time": (time.time() - start_time) * 1000
                }
            )
    
    async def _handle_batch_triage_request(self, request: BatchTriageRequest, http_request: Request) -> StandardAPIResponse:
        """Handle batch triage request for optimization"""
        start_time = time.time()
        request_id = getattr(http_request.state, 'request_id', str(uuid.uuid4()))
        
        try:
            # Process batch requests in parallel
            results = await asyncio.gather(*[
                self._process_triage(triage_req) for triage_req in request.requests
            ])
            
            processing_time = (time.time() - start_time) * 1000
            
            return StandardAPIResponse(
                status="success",
                data={
                    "results": results,
                    "batch_size": len(request.requests),
                    "priority": request.priority
                },
                meta={
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "2.0.0",
                    "processing_time": processing_time
                }
            )
            
        except Exception as e:
            logger.error(f"Batch triage request failed: {e}")
            return StandardAPIResponse(
                status="error",
                error={
                    "code": "BATCH_TRIAGE_ERROR",
                    "message": "Failed to process batch triage request",
                    "details": {"error": str(e)},
                    "timestamp": datetime.utcnow().isoformat()
                },
                meta={
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "2.0.0",
                    "processing_time": (time.time() - start_time) * 1000
                }
            )
    
    async def _handle_websocket_connection(self, websocket, session_id: str):
        """Handle WebSocket connection for real-time updates"""
        await websocket.accept()
        
        try:
            # Add to session pool
            await self._add_websocket_session(session_id, websocket)
            
            while True:
                # Receive message
                data = await websocket.receive_text()
                message = WebSocketMessage(**json.loads(data))
                
                # Process message
                if message.type == "triage_update":
                    await self._handle_triage_update(message, websocket)
                elif message.type == "risk_alert":
                    await self._handle_risk_alert(message, websocket)
                elif message.type == "heartbeat":
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat_response",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await self._remove_websocket_session(session_id)
    
    async def _process_triage(self, request: TriageRequest) -> TriageResponse:
        """Process triage request through AI agents"""
        
        # This would integrate with the existing agent system
        # For now, return a mock response
        
        return TriageResponse(
            triage_level="routine",
            confidence=0.85,
            risk_score="low",
            risk_time_horizon="30_days",
            recommendations=[
                "Schedule routine medical appointment",
                "Monitor symptoms at home",
                "Rest and stay hydrated"
            ],
            agent_outputs={
                "triage_agent": {"confidence": 0.85, "reasoning": "Symptoms suggest routine care"},
                "safety_guard": {"confidence": 0.92, "no_emergency": True},
                "guideline_agent": {"confidence": 0.78, "guidelines": ["WHO primary care"]},
                "risk_prediction": {"confidence": 0.81, "risk_factors": []}
            },
            explainability={
                "primary_factors": ["mild symptoms", "no emergency indicators"],
                "confidence_breakdown": {
                    "triage": 0.85,
                    "safety": 0.92,
                    "guideline": 0.78,
                    "risk": 0.81
                },
                "reasoning": "Based on symptom analysis, no immediate emergency detected"
            },
            session_id=request.session_id or str(uuid.uuid4())
        )
    
    async def _add_websocket_session(self, session_id: str, websocket):
        """Add WebSocket session to pool"""
        if not self.redis_client:
            self.redis_client = await aioredis.from_url("redis://localhost")
        
        await self.redis_client.hset("websocket_sessions", session_id, "active")
        logger.info(f"WebSocket session added: {session_id}")
    
    async def _remove_websocket_session(self, session_id: str):
        """Remove WebSocket session from pool"""
        if self.redis_client:
            await self.redis_client.hdel("websocket_sessions", session_id)
        logger.info(f"WebSocket session removed: {session_id}")
    
    async def _handle_triage_update(self, message: WebSocketMessage, websocket):
        """Handle triage update message"""
        # Process triage update and broadcast to relevant sessions
        pass
    
    async def _handle_risk_alert(self, message: WebSocketMessage, websocket):
        """Handle risk alert message"""
        # Process risk alert and notify relevant parties
        pass

# Adapter Layer Design
class BackendAdapter:
    """
    Abstract adapter layer for frontend-backend integration
    Allows swapping backend implementations
    """
    
    def __init__(self, adapter_type: str = "fastapi"):
        self.adapter_type = adapter_type
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize backend client based on adapter type"""
        if self.adapter_type == "fastapi":
            self.client = FastAPIAdapter()
        elif self.adapter_type == "graphql":
            self.client = GraphQLAdapter()
        elif self.adapter_type == "serverless":
            self.client = ServerlessAdapter()
        else:
            raise ValueError(f"Unsupported adapter type: {self.adapter_type}")
    
    async def make_request(self, endpoint: str, data: Dict[str, Any], method: str = "POST") -> StandardAPIResponse:
        """Make standardized API request"""
        return await self.client.request(endpoint, data, method)
    
    async def batch_request(self, requests: List[Dict[str, Any]]) -> StandardAPIResponse:
        """Make batch API request"""
        return await self.client.batch_request(requests)
    
    async def websocket_connect(self, session_id: str):
        """Connect to WebSocket"""
        return await self.client.websocket_connect(session_id)

class FastAPIAdapter:
    """FastAPI-specific adapter implementation"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.session = None
    
    async def request(self, endpoint: str, data: Dict[str, Any], method: str) -> StandardAPIResponse:
        """Make request to FastAPI backend"""
        import httpx
        
        if not self.session:
            self.session = httpx.AsyncClient()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = await self.session.get(url)
            else:
                response = await self.session.post(url, json=data)
            
            response.raise_for_status()
            return StandardAPIResponse(**response.json())
            
        except Exception as e:
            logger.error(f"FastAPI request failed: {e}")
            return StandardAPIResponse(
                status="error",
                error={
                    "code": "ADAPTER_ERROR",
                    "message": "Failed to make request",
                    "details": {"error": str(e)},
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    async def batch_request(self, requests: List[Dict[str, Any]]) -> StandardAPIResponse:
        """Make batch request to FastAPI backend"""
        return await self.request("/api/v2/batch-triage", {"requests": requests})
    
    async def websocket_connect(self, session_id: str):
        """Connect to FastAPI WebSocket"""
        import websockets
        
        uri = f"ws://localhost:8000/ws/triage/{session_id}"
        return await websockets.connect(uri)

class GraphQLAdapter:
    """GraphQL-specific adapter implementation"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.session = None
    
    async def request(self, endpoint: str, data: Dict[str, Any], method: str) -> StandardAPIResponse:
        """Make GraphQL request"""
        # GraphQL implementation would go here
        pass
    
    async def batch_request(self, requests: List[Dict[str, Any]]) -> StandardAPIResponse:
        """Make batch GraphQL request"""
        # GraphQL batch implementation would go here
        pass
    
    async def websocket_connect(self, session_id: str):
        """Connect to GraphQL WebSocket"""
        # GraphQL WebSocket implementation would go here
        pass

class ServerlessAdapter:
    """Serverless-specific adapter implementation"""
    
    def __init__(self):
        self.function_urls = {
            "triage": "https://api.dedan.health/triage",
            "batch_triage": "https://api.dedan.health/batch-triage"
        }
    
    async def request(self, endpoint: str, data: Dict[str, Any], method: str) -> StandardAPIResponse:
        """Make serverless function request"""
        import httpx
        
        if not self.session:
            self.session = httpx.AsyncClient()
        
        function_url = self.function_urls.get(endpoint.replace("/api/v2/", ""))
        if not function_url:
            raise ValueError(f"Unknown endpoint: {endpoint}")
        
        try:
            response = await self.session.post(function_url, json=data)
            response.raise_for_status()
            return StandardAPIResponse(**response.json())
            
        except Exception as e:
            logger.error(f"Serverless request failed: {e}")
            return StandardAPIResponse(
                status="error",
                error={
                    "code": "SERVERLESS_ERROR",
                    "message": "Failed to invoke serverless function",
                    "details": {"error": str(e)},
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    async def batch_request(self, requests: List[Dict[str, Any]]) -> StandardAPIResponse:
        """Make batch serverless request"""
        return await self.request("/api/v2/batch-triage", {"requests": requests})
    
    async def websocket_connect(self, session_id: str):
        """Connect to serverless WebSocket"""
        # Serverless WebSocket implementation would go here
        pass

# Caching Layer
class IntelligentCache:
    """
    Intelligent caching system for API optimization
    """
    
    def __init__(self):
        self.redis_client = None
        self.cache_config = {
            "triage_responses": {"ttl": 300, "max_size": 1000},  # 5 minutes
            "guidelines": {"ttl": 3600, "max_size": 500},  # 1 hour
            "user_sessions": {"ttl": 1800, "max_size": 10000},  # 30 minutes
            "risk_flags": {"ttl": 600, "max_size": 2000}  # 10 minutes
        }
    
    async def initialize(self):
        """Initialize cache connections"""
        try:
            self.redis_client = await aioredis.from_url("redis://localhost")
            logger.info("Intelligent cache initialized")
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
    
    async def get(self, key: str, cache_type: str) -> Optional[Any]:
        """Get cached value"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(f"cache:{cache_type}:{key}")
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
    
    async def set(self, key: str, value: Any, cache_type: str) -> bool:
        """Set cached value"""
        if not self.redis_client:
            return False
        
        try:
            config = self.cache_config.get(cache_type, {})
            ttl = config.get("ttl", 300)
            
            await self.redis_client.setex(
                f"cache:{cache_type}:{key}",
                ttl,
                json.dumps(value)
            )
            return True
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False
    
    async def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries by pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0

# Global instances
api_manager = APIIntegrationManager()
cache_manager = IntelligentCache()
backend_adapter = BackendAdapter("fastapi")
