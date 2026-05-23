"""Lightweight, transparent sentiment scoring.

A small bilingual (EN/KO) lexicon scores headlines in [-1, 1]. This is
deliberately simple and dependency-free so the pipeline runs anywhere; it is
a placeholder good enough to rank "is recent coverage turning positive?".

To upgrade quality, swap `score_text` for a model-based scorer (e.g. a
FinBERT / KR-FinBERT pipeline) — the rest of the code only depends on this
function's [-1, 1] contract.
"""
from __future__ import annotations

POSITIVE = {
    # English
    "surge", "soar", "rally", "gain", "beat", "upgrade", "growth", "record",
    "profit", "rebound", "recovery", "bullish", "outperform", "breakthrough",
    "approval", "win", "strong", "expand", "boost", "rise", "jump",
    # Korean
    "급등", "상승", "호조", "흑자", "회복", "반등", "성장", "수주", "최대", "개선",
    "강세", "돌파", "기대", "호실적", "신고가", "확대", "승인",
}
NEGATIVE = {
    # English
    "plunge", "crash", "loss", "miss", "downgrade", "lawsuit", "bankruptcy",
    "decline", "fall", "drop", "weak", "cut", "warning", "fraud", "delay",
    "recall", "slump", "bearish", "default", "probe",
    # Korean
    "급락", "하락", "적자", "손실", "감소", "약세", "소송", "리콜", "부진", "경고",
    "파산", "지연", "위기", "충격", "하향", "우려",
}


def score_text(text: str) -> float:
    if not text:
        return 0.0
    lowered = text.lower()
    pos = sum(1 for w in POSITIVE if w in lowered)
    neg = sum(1 for w in NEGATIVE if w in lowered)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total
