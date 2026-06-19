import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse

from app.config import settings
from mcp_server.server import list_tools, call_tool
from middleware.auth import authenticate_request
from middleware.rate_limit import check_rate_limit
from payments.x402 import get_tool_price, deduct_balance, get_balance, get_pricing_with_balance, add_credits, get_transactions, get_all_balances, ensure_user
from storage.models import init_db

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logging.getLogger("mcp").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def _get_user(request: Request, x_x402_user: str = "") -> str:
    if x_x402_user:
        return x_x402_user
    return request.client.host if request.client else "anonymous"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Viral Content MCP server")
    await init_db(settings.database_url)
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
async def mcp_endpoint(
    request: Request,
    x_x402_token: str = Header(None, alias="X-x402-Token"),
    x_x402_user: str = Header("", alias="X-x402-User"),
):
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
        user_id = _get_user(request, x_x402_user)

        rate_ok, retry = check_rate_limit(user_id)
        if not rate_ok:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "retry_after": retry},
            )

        price = get_tool_price(name)
        ensure_user(user_id)

        if not deduct_balance(user_id, price, tool=name):
            if settings.x402_enabled:
                return JSONResponse(
                    status_code=402,
                    content={
                        "error": "Insufficient x402 credits",
                        "balance": get_balance(user_id),
                        "required": price,
                        "tool": name,
                    },
                )

        result = await call_tool(name, arguments)

        resp = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result.model_dump(),
        }

        return JSONResponse(
            content=resp,
            headers={
                "X-x402-Cost": str(price),
                "X-x402-Balance": str(get_balance(user_id)),
            },
        )

    return JSONResponse(status_code=400, content={"error": f"Unknown method: {method}"})


@app.get("/pricing")
async def pricing():
    from payments.x402 import PRICING
    return PRICING


@app.get("/x402/balance")
async def x402_balance(
    request: Request,
    x_x402_user: str = Header("", alias="X-x402-User"),
):
    user_id = _get_user(request, x_x402_user)
    return get_pricing_with_balance(user_id)


@app.post("/x402/credits")
async def x402_add_credits(
    request: Request,
    amount: float = 0.1,
    user: str = "",
    x_x402_user: str = Header("", alias="X-x402-User"),
):
    user_id = user or x_x402_user or (request.client.host if request.client else "anonymous")
    add_credits(user_id, amount, note="admin top-up")
    return {"balance": get_balance(user_id), "added": amount}


@app.get("/admin/wallets")
async def admin_wallets():
    return {
        "total_users": len(get_all_balances()),
        "total_credits": round(sum(get_all_balances().values()), 4),
        "wallets": get_all_balances(),
    }


@app.get("/admin/transactions")
async def admin_transactions(user: str = "", limit: int = 50):
    return {
        "transactions": get_transactions(user_id=user or None, limit=limit),
        "count": len(get_transactions(user_id=user or None, limit=limit)),
    }


@app.get("/admin/debug")
async def admin_debug():
    import os
    from payments.x402 import DATA_FILE
    path = DATA_FILE
    exists = os.path.exists(path)
    content = None
    if exists:
        try:
            with open(path) as f:
                content = json.load(f)
        except Exception as e:
            content = {"error": str(e)}
    return {
        "data_file_path": path,
        "data_file_exists": exists,
        "cwd": os.getcwd(),
        "content": content,
    }


if __name__ == "__main__":
    import json
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )
