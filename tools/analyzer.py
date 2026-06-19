from pydantic import BaseModel, Field
from services.virality_engine import calculate as virality_calculate
from services.llm_router import get_provider
from app.config import settings
from typing import Optional


class AnalyzeInput(BaseModel):
    content: str = Field(..., description="Content to analyze")


class AnalyzeOutput(BaseModel):
    clarity: float
    virality: int
    engagement: float
    weaknesses: list[str]
    suggestions: list[str]


ANALYSIS_PROMPT = """Analyze this social media content and provide scores and improvement suggestions.

Content:
{content}

Return a JSON object with these fields:
- clarity: 0-100 score for how clear and understandable the content is
- engagement: 0-100 score for how likely people are to engage
- weaknesses: array of specific weaknesses as strings
- suggestions: array of actionable improvement suggestions as strings

Return ONLY valid JSON, no other text."""


async def analyze_content(input_data: AnalyzeInput) -> AnalyzeOutput:
    provider = get_provider()
    raw = await provider.generate(
        ANALYSIS_PROMPT.format(content=input_data.content),
        model=settings.model_analysis,
    )

    virality = virality_calculate(input_data.content)
    import json
    try:
        parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
    except (json.JSONDecodeError, ValueError):
        parsed = {}

    return AnalyzeOutput(
        clarity=float(parsed.get("clarity", 70)),
        virality=virality["overall"],
        engagement=float(parsed.get("engagement", 70)),
        weaknesses=parsed.get("weaknesses", []),
        suggestions=parsed.get("suggestions", []),
    )
