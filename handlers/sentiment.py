from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

NEGATIVE_PATTERNS = {
    "angry": 2,
    "frustrated": 2,
    "upset": 2,
    "annoyed": 1,
    "furious": 4,
    "ridiculous": 2,
    "useless": 3,
    "terrible": 2,
    "hate": 2,
    "refund now": 3,
    "cancel immediately": 3,
    "human": 1,
    "agent": 1,
    "scam": 3,
    "chargeback": 3,
    "lawsuit": 4,
    "sue": 4,
    "worst": 3,
    "disappointed": 2,
    "unacceptable": 3,
    "never buying": 3,
}

POSITIVE_PATTERNS = {
    "love": 2,
    "great": 1,
    "excellent": 2,
    "awesome": 2,
    "good": 1,
    "fantastic": 2,
    "happy": 1,
    "amazing": 2,
    "perfect": 2,
    "satisfied": 2,
    "helpful": 1,
}


@dataclass(frozen=True)
class SentimentResult:
    label: str
    score: int
    escalate: bool


def analyze_sentiment(text: str) -> SentimentResult:
    lowered = text.lower()
    score = 0

    for phrase, weight in POSITIVE_PATTERNS.items():
        if phrase in lowered:
            score += weight
    for phrase, weight in NEGATIVE_PATTERNS.items():
        if phrase in lowered:
            score -= weight

    if lowered.count("!") >= 2:
        score -= 1

    frustration_patterns = [
        r"\b(no help|not helping|still waiting|already told you)\b",
        r"\b(waste|useless|horrible|awful)\b",
        r"\b(complaint|unhappy|unacceptable)\b",
    ]
    for pattern in frustration_patterns:
        if re.search(pattern, lowered):
            score -= 2

    ALL_CAPS_WORDS = sum(1 for word in lowered.split() if len(word) > 2 and word.isupper())
    if ALL_CAPS_WORDS >= 3:
        score -= 2

    if score <= -6:
        label = "negative"
    elif score >= 1:
        label = "positive"
    else:
        label = "neutral"

    escalate = score <= -6 or any(
        term in lowered for term in ("human", "agent", "manager", "supervisor")
    )

    return SentimentResult(label=label, score=score, escalate=escalate)
