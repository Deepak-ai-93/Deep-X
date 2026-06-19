from typing import Optional
from pydantic import BaseModel, Field
from services.llm_router import get_provider
from services.virality_engine import calculate as virality_calculate
from app.config import settings


class LinkedInInput(BaseModel):
    topic: str = Field(..., description="Topic for the LinkedIn post")
    audience: str = Field("general", description="Target audience")
    tone: str = Field("professional", description="Writing tone")
    provider: Optional[str] = None


class LinkedInOutput(BaseModel):
    post: str
    hook: str
    cta: str
    virality_score: int
    readability_score: float
    analysis: dict


LINKEDIN_PROMPT = """You are a top LinkedIn content strategist. Write a high-engagement LinkedIn post.

Topic: {topic}
Target Audience: {audience}
Tone: {tone}

Requirements:
- Start with a strong hook (first line)
- Include a clear call-to-action at the end
- Use short paragraphs (1-3 sentences each)
- Add line breaks between paragraphs
- Keep it 150-300 words
- Make it authentic and opinionated

Return your response in this exact format:
---HOOK---
<hook text>
---POST---
<full post body>
---CTA---
<call to action text>
"""


async def generate_linkedin_post(input_data: LinkedInInput) -> LinkedInOutput:
    provider = get_provider(input_data.provider)
    prompt = LINKEDIN_PROMPT.format(
        topic=input_data.topic,
        audience=input_data.audience,
        tone=input_data.tone,
    )
    raw = await provider.generate(prompt, model=settings.model_linkedin if hasattr(settings, 'model_linkedin') else None)

    if not raw:
        post = f"**{input_data.topic}**\n\nShare your thoughts on {input_data.topic} in the comments below."
        hook = f"How to master {input_data.topic}"
        cta = "What do you think? Share in the comments."
    else:
        hook = _extract_section(raw, "---HOOK---", "---POST---")
        post = _extract_section(raw, "---POST---", "---CTA---")
        cta = _extract_section(raw, "---CTA---", None)
        if not post:
            post = raw
            hook = post.split("\n")[0] if post else ""
            cta = ""

    virality = virality_calculate(post)

    return LinkedInOutput(
        post=post.strip(),
        hook=hook.strip(),
        cta=cta.strip(),
        virality_score=virality["overall"],
        readability_score=virality["readability"],
        analysis=virality,
    )


def _extract_section(text: str, start: str, end: Optional[str]) -> str:
    if start not in text:
        return ""
    idx = text.index(start) + len(start)
    if end and end in text[idx:]:
        return text[idx:text.index(end, idx)]
    return text[idx:]
