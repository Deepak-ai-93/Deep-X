# Viral Content MCP

A production-ready MCP (Model Context Protocol) server that generates and analyzes social media content. Works with any MCP-compatible LLM client (Claude, Gemini, Cursor, Windsurf, Continue, Cline, etc.).

## Features

- **LinkedIn Posts** - Generate high-engagement LinkedIn posts with hooks, CTAs, and virality scoring
- **X/Twitter Content** - Generate viral tweets and threads with engagement scoring
- **Content Analysis** - Analyze content for clarity, virality, engagement, and improvement suggestions
- **Multi-Platform Content Packs** - Generate coordinated content for LinkedIn, X, newsletters, and blogs from one idea
- **Virality Engine** - Score content on hook strength, readability, curiosity gap, emotional impact, and CTA strength

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

## MCP Tools

| Tool | Description | Price |
|------|-------------|-------|
| `generate_linkedin_post` | Generate a LinkedIn post | $0.01 |
| `generate_x_content` | Generate X tweet/thread | $0.01 |
| `analyze_content` | Analyze content | $0.005 |
| `improve_content` | Improve content | $0.005 |
| `generate_content_pack` | Multi-platform pack | $0.03 |

## API

- `GET /health` - Health check
- `GET /pricing` - Tool pricing
- `POST /mcp` - MCP endpoint (tools/list, tools/call, prompts/list)

## Architecture

```
LLM Client → MCP Server → Content Generator
                         → Analysis Engine
                         → Virality Engine
                         → Payment Middleware (x402)
                         → Storage (PostgreSQL)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `DATABASE_URL` | Database connection string |
| `X402_SECRET` | x402 payment secret |
| `LOG_LEVEL` | Logging level (default: INFO) |

## Deployment

```bash
docker build -t viral-content-mcp .
docker run -p 10000:10000 --env-file .env viral-content-mcp
```

## Testing

```bash
pytest tests/ -v
```
