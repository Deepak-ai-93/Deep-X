# Viral Content MCP

A production-ready MCP (Model Context Protocol) server that generates and analyzes social media content. Works with any MCP-compatible LLM client — no API keys required.

## Features

- **LinkedIn Posts** - Generate high-engagement LinkedIn posts with hooks, CTAs, and virality scoring
- **X/Twitter Content** - Generate viral tweets and threads with engagement scoring
- **Content Analysis** - Analyze content for clarity, virality, engagement, and improvement suggestions
- **Multi-Platform Content Packs** - Generate coordinated content for LinkedIn, X, newsletters, and blogs from one idea
- **Virality Engine** - Score content on hook strength, readability, curiosity gap, emotional impact, and CTA strength

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

No API keys, no .env file needed. The server works out of the box.

> **No install?** Use the hosted instance: `https://viral-content-mcp.onrender.com/mcp`

## Hosted Instance

A public instance is available at:

```
https://viral-content-mcp.onrender.com/mcp
```

Connect any MCP client directly — no installation needed. Example config:

```json
{
  "mcpServers": {
    "viral-content": {
      "url": "https://viral-content-mcp.onrender.com/mcp"
    }
  }
}
```

## Connecting MCP Clients

### Claude Code (Claude CLI)

Add to your `~/.claude.json` or `claude.json`:

```json
{
  "mcpServers": {
    "viral-content": {
      "command": "uvicorn",
      "args": ["app.main:app", "--host", "127.0.0.1", "--port", "10000"]
    }
  }
}
```

Or connect to the hosted instance:

```json
{
  "mcpServers": {
    "viral-content": {
      "url": "https://viral-content-mcp.onrender.com/mcp"
    }
  }
}
```

Then ask Claude:
> *"Create a LinkedIn post about AI agents for SaaS founders"*
> *"Write an X thread about MCP servers"*
> *"Analyze this post for virality: [paste content]"*

### Gemini CLI

Add to your Gemini CLI config:

```json
{
  "mcp": {
    "servers": [
      {
        "name": "viral-content",
        "url": "https://viral-content-mcp.onrender.com/mcp"
      }
    ]
  }
}
```

### Cursor

In Cursor Settings → MCP Servers → Add Server:

```
Name: viral-content
Type: command
Command: uvicorn app.main:app --host 127.0.0.1 --port 10000
```

Then in Cursor chat:
> *"Use the viral-content tools to write a LinkedIn post about remote work"*

### Windsurf

In Windsurf → Settings → MCP Servers:

```json
{
  "mcpServers": {
    "viral-content": {
      "command": "uvicorn",
      "args": ["app.main:app", "--host", "127.0.0.1", "--port", "10000"]
    }
  }
}
```

### Continue (VS Code)

In `~/.continue/config.json`:

```json
{
  "experimental": {
    "mcpServers": {
      "viral-content": {
        "command": "uvicorn",
        "args": ["app.main:app", "--host", "127.0.0.1", "--port", "10000"]
      }
    }
  }
}
```

### Cline (VS Code)

In Cline → MCP Servers → Add:

```
Name: viral-content
Command: uvicorn app.main:app --host 127.0.0.1 --port 10000
```

### Generic MCP Client

Any MCP-compatible client can connect via stdio:

```json
{
  "mcpServers": {
    "viral-content": {
      "command": "uvicorn",
      "args": ["app.main:app", "--host", "127.0.0.1", "--port", "10000"]
    }
  }
}
```

Or via HTTP (hosted instance):

```
URL: https://viral-content-mcp.onrender.com/mcp
```

## MCP Tools

| Tool | Description | Price |
|------|-------------|-------|
| `generate_linkedin_post` | Generate a LinkedIn post | $0.01 |
| `generate_x_content` | Generate X tweet/thread | $0.01 |
| `analyze_content` | Analyze content | $0.005 |
| `improve_content` | Improve content | $0.005 |
| `generate_content_pack` | Multi-platform pack | $0.03 |

## Tool Schemas

### `generate_linkedin_post`
```json
{
  "topic": "AI agents for SaaS",
  "audience": "SaaS founders",
  "tone": "professional"
}
```
Returns: `post`, `hook`, `cta`, `virality_score`, `readability_score`, `analysis`

### `generate_x_content`
```json
{
  "topic": "MCP servers",
  "include_thread": true
}
```
Returns: `tweet`, `thread`, `engagement_score`, `analysis`

### `analyze_content`
```json
{
  "content": "Your post text here..."
}
```
Returns: `clarity`, `virality`, `engagement`, `weaknesses`, `suggestions`

### `generate_content_pack`
```json
{
  "topic": "Remote work productivity",
  "audience": "tech leaders"
}
```
Returns: `linkedin_post`, `x_thread`, `newsletter_outline`, `blog_outline`, `virality_score`, `analysis`

## Default Prompts

Use these prompts with any MCP client (Claude Code, Cursor, Continue, etc.):

### LinkedIn Post
> Create a LinkedIn post about **{topic}** for **{audience}** in a **{tone}** tone.

### X/Twitter Thread
> Write an X thread about **{topic}** that drives engagement.

### Content Analysis
> Analyze this content and tell me how to improve it: **{paste content}**

### Multi-Platform Content Pack
> Generate a full content pack for **{topic}** including LinkedIn, X thread, newsletter outline, and blog outline.

### Virality Check
> Score this post for virality and tell me what to improve: **{paste post}**

### Content Repurpose
> Take this blog post and repurpose it into a LinkedIn post and X thread: **{paste content}**

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

## Running as a Background Service

For local CLI usage (Claude Code, Gemini CLI), run the server in the background:

```bash
# Start server in background
nohup uvicorn app.main:app --host 127.0.0.1 --port 10000 &

# Or use tmux/screen
tmux new-session -d -s mcp 'uvicorn app.main:app --host 127.0.0.1 --port 10000'
```

## Testing

```bash
pytest tests/ -v
```
