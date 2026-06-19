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
        model=settings.model_analysis if hasattr(settings, 'model_analysis') else None,
    )

    virality = virality_calculate(input_data.content)

    if not raw:
        return AnalyzeOutput(
            clarity=round(virality["readability"], 1),
            virality=virality["overall"],
            engagement=float(virality["overall"]),
            weaknesses=_default_weaknesses(input_data.content),
            suggestions=_default_suggestions(input_data.content),
        )

    import json
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        parsed = json.loads(cleaned.strip())
    except (json.JSONDecodeError, ValueError):
        parsed = {}

    return AnalyzeOutput(
        clarity=float(parsed.get("clarity", virality["readability"])),
        virality=virality["overall"],
        engagement=float(parsed.get("engagement", virality["overall"])),
        weaknesses=parsed.get("weaknesses", _default_weaknesses(input_data.content)),
        suggestions=parsed.get("suggestions", _default_suggestions(input_data.content)),
    )


def _default_weaknesses(content: str) -> list[str]:
    w = []
    words = len(content.split())
    if words > 200:
        w.append("Content is too long for social media")
    if words < 20:
        w.append("Content is too short to convey value")
    if "?" not in content:
        w.append("No questions to drive engagement")
    return w or ["Consider adding a stronger hook"]


def _default_suggestions(content: str) -> list[str]:
    return [
        "Add a compelling hook in the first line",
        "Include a clear call-to-action",
        "Break into shorter paragraphs for readability",
        "Add emotional triggers or storytelling elements",
    ]
