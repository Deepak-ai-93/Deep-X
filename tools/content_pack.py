from typing import Optional
from pydantic import BaseModel, Field
from services.llm_router import get_provider
from services.virality_engine import calculate as virality_calculate
from app.config import settings


class ContentPackInput(BaseModel):
    topic: str = Field(..., description="Main idea for the content pack")
    audience: str = Field("general", description="Target audience")
    provider: Optional[str] = None


class ContentPackOutput(BaseModel):
    linkedin_post: str
    x_thread: list[str]
    newsletter_outline: str
    blog_outline: str
    virality_score: int
    analysis: dict


CONTENT_PACK_PROMPT = """You are a multi-platform content strategist. Create a content pack for this topic.

Topic: {topic}
Target Audience: {audience}

Return a complete content pack with these sections separated by the exact markers shown:

---LINKEDIN---
(Full LinkedIn post, 150-250 words, professional tone, with hook and CTA)

---X THREAD---
(5 tweets, one per line, each under 280 chars, numbered)

---NEWSLETTER---
(Newsletter outline: subject line + 3-5 bullet points for sections)

---BLOG---
(Blog outline: SEO title + introduction hook + 5-7 H2 section headings + conclusion CTA)

Be creative and make each piece of content platform-appropriate."""


async def generate_content_pack(input_data: ContentPackInput) -> ContentPackOutput:
    provider = get_provider(input_data.provider)
    prompt = CONTENT_PACK_PROMPT.format(
        topic=input_data.topic,
        audience=input_data.audience,
    )
    raw = await provider.generate(
        prompt,
        model=settings.model_content_pack if hasattr(settings, 'model_content_pack') else None,
    )

    if not raw:
        linkedin = f"**{input_data.topic}**\n\nHere's what I've learned about {input_data.topic}.\n\nWhat's your take? Share below."
        x_thread = [
            f"1/ {input_data.topic} — a thread 🧵",
            f"2/ Most people overlook this about {input_data.topic}",
            f"3/ Here's what actually matters",
            f"4/ The key insight changes everything",
            f"5/ What do you think? RT/follow for more",
        ]
        newsletter = f"Subject: {input_data.topic}\n- Why {input_data.topic} matters now\n- Key trends to watch\n- Actionable takeaways"
        blog = f"SEO Title: {input_data.topic}: The Complete Guide\n- Introduction\n- Why {input_data.topic}?\n- Key Strategies\n- Common Mistakes\n- Best Practices\n- Case Studies\n- Conclusion with CTA"
    else:
        linkedin = _extract(raw, "---LINKEDIN---", "---X THREAD---")
        x_section = _extract(raw, "---X THREAD---", "---NEWSLETTER---")
        newsletter = _extract(raw, "---NEWSLETTER---", "---BLOG---")
        blog = _extract(raw, "---BLOG---", None)
        x_thread = [t.strip() for t in x_section.split("\n") if t.strip()]

    full_text = linkedin + " " + " ".join(x_thread)
    virality = virality_calculate(full_text)

    return ContentPackOutput(
        linkedin_post=linkedin.strip(),
        x_thread=x_thread,
        newsletter_outline=newsletter.strip(),
        blog_outline=blog.strip(),
        virality_score=virality["overall"],
        analysis=virality,
    )


def _extract(text: str, start: str, end: Optional[str]) -> str:
    if start not in text:
        return ""
    idx = text.index(start) + len(start)
    if end and end in text[idx:]:
        return text[idx:text.index(end, idx)]
    return text[idx:].strip()
