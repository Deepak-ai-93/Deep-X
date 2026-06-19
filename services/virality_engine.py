import re
import math


def score_hook_strength(post: str) -> float:
    hooks = [
        r"(?i)how to", r"(?i)why (i|we|you)", r"(?i)the (truth|secret|real)",
        r"(?i)\d+ (ways|lessons|tips|strategies)", r"(?i)stop doing",
        r"(?i)most people", r"(?i)what (nobody|they) (won't|don't|never)",
        r"(?i)X (days|weeks|months) ago", r"(?i)the (best|worst|biggest)",
        r"(?i)i (learned|discovered|realized)", r"(?i)here('s| is) (why|how|what)",
    ]
    score = sum(2.0 for h in hooks if re.search(h, post[:200]))
    return min(score * 10, 100)


def score_readability(text: str) -> float:
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    if not sentences:
        return 50.0
    words = text.split()
    num_words = len(words)
    num_sentences = len(sentences)
    avg_sentence_len = num_words / num_sentences if num_sentences else 0
    num_syllables = sum(_count_syllables(w) for w in words)
    score = 206.835 - 1.015 * avg_sentence_len - 84.6 * (num_syllables / num_words)
    return max(0, min(round(score, 1), 100))


def _count_syllables(word: str) -> int:
    word = word.lower().strip(".,!?;:'\"")
    if not word:
        return 1
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    return max(count, 1)


def score_curiosity_gap(text: str) -> float:
    triggers = [
        r"(?i)here('s| is) (why|how|what)", r"(?i)the (reason|one thing|problem)",
        r"(?i)what (happens|if|most)", r"(?i)you (won't|need|didn't|might)",
        r"(?i)(surprising|unexpected|controversial)", r"(?i)(imagine|picture this)",
        r"(?i)(secret|hidden|underrated|overlooked)", r"(?i)(this is why|that's why)",
        r"(?i)(the moment|the day|the time)", r"(?i)(nobody tells you|they don't want)",
    ]
    score = sum(2.0 for t in triggers if re.search(t, text))
    return min(score * 10, 100)


def score_emotional_impact(text: str) -> float:
    emotional = [
        r"(?i)(frustrating|amazing|incredible|terrible|brilliant)",
        r"(?i)(love|hate|fear|excited|disappointed|grateful)",
        r"(?i)(game.?changer|mind.?blowing|eye.?opening)",
        r"(?i)(struggle|breakthrough|fail|succeed|transform)",
        r"(?i)(i was wrong|i changed my mind|hard lesson)",
    ]
    score = sum(2.5 for e in emotional if re.search(e, text))
    return min(score * 10, 100)


def score_cta_strength(post: str) -> float:
    ctas = [
        r"(?i)(follow|share|comment|like|retweet|repost|tag)",
        r"(?i)(what do you think|agree|disagree|your thoughts)",
        r"(?i)(save this|bookmark|remember this)",
        r"(?i)(try this|give it a try|let me know)",
        r"(?i)(who else|how many of you|anyone else)",
        r"(?i)(DMs|DM me|message me|link in bio|link in comments)",
    ]
    score = sum(3.0 for c in ctas if re.search(c, post[-400:]))
    return min(score * 10, 100)


def calculate(post: str) -> dict:
    hook = score_hook_strength(post)
    readability = score_readability(post)
    curiosity = score_curiosity_gap(post)
    emotional = score_emotional_impact(post)
    cta = score_cta_strength(post)

    overall = round(
        0.25 * hook +
        0.20 * readability +
        0.20 * curiosity +
        0.15 * emotional +
        0.20 * cta
    )

    return {
        "overall": overall,
        "hook_strength": round(hook),
        "readability": readability,
        "curiosity_gap": round(curiosity),
        "emotional_impact": round(emotional),
        "cta_strength": round(cta),
    }
