"""Lightweight sentiment detection for frustration and escalation."""

from __future__ import annotations

import re
from dataclasses import dataclass

NEGATIVE_PATTERNS = {
    "angry": 2,
    "frustrated": 2,
    "upset": 2,
    "annoyed": 1,
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


@dataclass(frozen=True)
class SentimentResult:
    label: str
    score: int
    escalate: bool


def analyze_sentiment(text: str) -> SentimentResult:
    lowered = text.lower()
    score = 0
    for phrase, weight in NEGATIVE_PATTERNS.items():
        if phrase in lowered:
            score -= weight
    if lowered.count("!") >= 2:
        score -= 1
    if re.search(r"\b(no help|not helping|still waiting|already told you)\b", lowered):
        score -= 2

    if score <= -4:
        label = "negative"
    elif score >= 1:
        label = "positive"
    else:
        label = "neutral"

    escalate = score <= -4 or any(term in lowered for term in ("human", "agent", "manager", "supervisor"))
    return SentimentResult(label=label, score=score, escalate=escalate)

