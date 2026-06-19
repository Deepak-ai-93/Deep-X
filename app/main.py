import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from mcp_server.server import list_tools, call_tool
from middleware.auth import authenticate_request
from middleware.rate_limit import check_rate_limit
from payments.x402 import get_tool_price
from storage.models import init_db

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logging.getLogger("mcp").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Viral Content MCP server")
    init_db(settings.database_url)
    yield
    logger.info("Shutting down Viral Content MCP server")


app = FastAPI(
    title="Viral Content MCP",
    description="MCP-compliant server for viral content generation and analysis",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "elapsed_ms": round(elapsed * 1000),
        },
    )
    return response


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": "1.0.0",
    }


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")

    if method == "tools/list":
        tools = await list_tools()
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": [t.model_dump() for t in tools]},
        }

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})

        try:
            user_id = await authenticate_request(request)
        except Exception:
            rate_ok, retry = check_rate_limit(request.client.host if request.client else "unknown")
            if not rate_ok:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "retry_after": retry},
                )

        result = await call_tool(name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result.model_dump(),
        }

    return JSONResponse(status_code=400, content={"error": f"Unknown method: {method}"})


@app.get("/pricing")
async def pricing():
    from payments.x402 import PRICING
    return PRICING


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )
