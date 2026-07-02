"""Lightweight sentiment detection for frustration and escalation."""

from __future__ import annotations

import re
from dataclasses import dataclass

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
}


@dataclass(frozen=True)
class SentimentResult:
    label: str
    score: int
    escalate: bool


def analyze_sentiment(text: str) -> SentimentResult:
    lowered = text.lower()
    score = 0
    # apply positive and negative lexicons
    for phrase, weight in POSITIVE_PATTERNS.items():
        if phrase in lowered:
            score += weight
    for phrase, weight in NEGATIVE_PATTERNS.items():
        if phrase in lowered:
            score -= weight
    if lowered.count("!") >= 2:
        score -= 1
    if re.search(r"\b(no help|not helping|still waiting|already told you)\b", lowered):
        score -= 2
    if score <= -6:
        label = "negative"
    elif score >= 1:
        label = "positive"
    else:
        label = "neutral"

    # escalate only for very negative scores or explicit escalation keywords
    escalate = score <= -6 or any(
        term in lowered for term in ("human", "agent", "manager", "supervisor")
    )
    return SentimentResult(label=label, score=score, escalate=escalate)
