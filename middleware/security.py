import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request

# Simple rate limiting storage
RATE_LIMIT_STORE = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 120 # Requests per minute
RATE_LIMIT_WINDOW = 60 # Seconds

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Rate Limiting Check
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        
        # Clean up old timestamps
        RATE_LIMIT_STORE[client_ip] = [
            t for t in RATE_LIMIT_STORE[client_ip] if now - t < RATE_LIMIT_WINDOW
        ]
        
        if len(RATE_LIMIT_STORE[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down your requests."}
            )
            
        RATE_LIMIT_STORE[client_ip].append(now)

        # 2. Process Request
        response = await call_next(request)

        # 3. Add Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob: ws: wss:; "
            "img-src 'self' https: data: blob:; "
            "font-src 'self' https: data:;"
        )
        
        return response
