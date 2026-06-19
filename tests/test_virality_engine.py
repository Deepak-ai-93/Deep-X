import pytest
from services.virality_engine import (
    calculate,
    score_hook_strength,
    score_readability,
    score_curiosity_gap,
    score_emotional_impact,
    score_cta_strength,
)


class TestHookStrength:
    def test_strong_hook(self):
        post = "How to build an AI startup in 2025. The secret most founders miss."
        score = score_hook_strength(post)
        assert 0 <= score <= 100
        assert score > 10

    def test_no_hook(self):
        score = score_hook_strength("The weather is nice today.")
        assert score <= 20


class TestReadability:
    def test_readable_text(self):
        score = score_readability("This is a short clear sentence. It is easy to read. Everyone understands it.")
        assert 0 <= score <= 100

    def test_complex_text(self):
        text = "Notwithstanding the aforementioned aforementioned, the aforementioned."
        score = score_readability(text)
        assert score >= 0


class TestCuriosityGap:
    def test_curiosity_triggers(self):
        text = "Here's why most startups fail. The one thing nobody tells you."
        score = score_curiosity_gap(text)
        assert score > 10

    def test_no_triggers(self):
        score = score_curiosity_gap("The meeting is at 3pm.")
        assert score <= 10


class TestEmotionalImpact:
    def test_emotional_content(self):
        text = "This game-changing strategy was absolutely incredible. I was wrong for years."
        score = score_emotional_impact(text)
        assert score > 10

    def test_flat_content(self):
        score = score_emotional_impact("Please submit the report by Friday.")
        assert score <= 10


class TestCtaStrength:
    def test_with_cta(self):
        post = "Great content here. Follow me for more tips on AI. What do you think?"
        score = score_cta_strength(post)
        assert score > 0

    def test_no_cta(self):
        score = score_cta_strength("This is a simple statement without a call to action.")
        assert score <= 10


class TestCalculate:
    def test_returns_all_fields(self):
        result = calculate("How to build an AI startup. Here's the secret most people miss. It changed everything for me. Follow for more.")
        assert "overall" in result
        assert "hook_strength" in result
        assert "readability" in result
        assert "curiosity_gap" in result
        assert "emotional_impact" in result
        assert "cta_strength" in result
        assert 0 <= result["overall"] <= 100

    def test_overall_score_range(self):
        result = calculate("Test post content here. Just some words. More words.")
        assert 0 <= result["overall"] <= 100
