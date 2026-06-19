from typing import Optional
from pydantic import BaseModel, Field
from services.llm_router import get_provider
from services.virality_engine import calculate as virality_calculate
from app.config import settings


class XInput(BaseModel):
    topic: str = Field(..., description="Topic for the X/Twitter content")
    include_thread: bool = Field(False, description="Generate a thread instead of single tweet")
    provider: Optional[str] = None


class XOutput(BaseModel):
    tweet: str
    thread: list[str] = []
    engagement_score: int
    analysis: dict


TWEET_PROMPT = """You are a top X/Twitter content writer. Write a viral tweet.

Topic: {topic}

Requirements:
- Under 280 characters
- Strong hook in first line
- Include 2-3 relevant hashtags
- Make it concise and punchy
- Use bold opinions or hot takes

Return ONLY the tweet text, no explanations."""

THREAD_PROMPT = """You are a top X/Twitter content writer. Write a viral thread.

Topic: {topic}

Requirements:
- 4-8 tweets in the thread
- Tweet 1 must be a strong hook to drive engagement
- Each tweet under 280 characters
- Number each tweet
- Include a CTA in the last tweet
- Add 2-3 relevant hashtags in tweet 1

Return each tweet separated by "---TWEOT---" on its own line.
Start with the first tweet immediately, no preamble."""


async def generate_x_content(input_data: XInput) -> XOutput:
    provider = get_provider(input_data.provider)

    if input_data.include_thread:
        raw = await provider.generate(THREAD_PROMPT.format(topic=input_data.topic), model=settings.model_twitter)
        thread = [t.strip() for t in raw.split("---TWEOT---") if t.strip()]
        tweet = thread[0] if thread else raw
        full_text = " ".join(thread)
    else:
        tweet = await provider.generate(TWEET_PROMPT.format(topic=input_data.topic), model=settings.model_twitter)
        tweet = tweet.strip().strip('"')
        thread = []
        full_text = tweet

    virality = virality_calculate(full_text)

    return XOutput(
        tweet=tweet,
        thread=thread,
        engagement_score=virality["overall"],
        analysis=virality,
    )
