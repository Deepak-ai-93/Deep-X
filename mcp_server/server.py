import logging
from mcp.types import Tool, TextContent, CallToolResult

from tools.linkedin import generate_linkedin_post, LinkedInInput
from tools.twitter import generate_x_content, XInput
from tools.analyzer import analyze_content, AnalyzeInput
from tools.content_pack import generate_content_pack, ContentPackInput
from payments.x402 import get_tool_price

logger = logging.getLogger(__name__)


_TOOL_DEFS: list[Tool] = [
    Tool(
        name="generate_linkedin_post",
        description="Generate a high-engagement LinkedIn post with virality scoring",
        inputSchema=LinkedInInput.model_json_schema(),
    ),
    Tool(
        name="generate_x_content",
        description="Generate a viral X/Twitter tweet or thread with engagement scoring",
        inputSchema=XInput.model_json_schema(),
    ),
    Tool(
        name="analyze_content",
        description="Analyze content for clarity, virality, engagement, and improvement suggestions",
        inputSchema=AnalyzeInput.model_json_schema(),
    ),
    Tool(
        name="generate_content_pack",
        description="Generate a multi-platform content pack (LinkedIn, X, newsletter, blog)",
        inputSchema=ContentPackInput.model_json_schema(),
    ),
]


async def list_tools() -> list[Tool]:
    return _TOOL_DEFS


async def call_tool(name: str, arguments: dict) -> CallToolResult:
    price = get_tool_price(name)
    logger.info("Tool called: %s (price: $%.3f)", name, price)

    try:
        match name:
            case "generate_linkedin_post":
                inp = LinkedInInput(**arguments)
                result = await generate_linkedin_post(inp)
                return CallToolResult(
                    content=[TextContent(type="text", text=result.model_dump_json(indent=2))]
                )

            case "generate_x_content":
                inp = XInput(**arguments)
                result = await generate_x_content(inp)
                return CallToolResult(
                    content=[TextContent(type="text", text=result.model_dump_json(indent=2))]
                )

            case "analyze_content":
                inp = AnalyzeInput(**arguments)
                result = await analyze_content(inp)
                return CallToolResult(
                    content=[TextContent(type="text", text=result.model_dump_json(indent=2))]
                )

            case "generate_content_pack":
                inp = ContentPackInput(**arguments)
                result = await generate_content_pack(inp)
                return CallToolResult(
                    content=[TextContent(type="text", text=result.model_dump_json(indent=2))]
                )

            case _:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                    isError=True,
                )

    except Exception as e:
        logger.exception("Tool %s failed", name)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error executing {name}: {e}")],
            isError=True,
        )
