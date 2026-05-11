from __future__ import annotations

import re


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def extract_candidate_claims(message: str) -> list[str]:
    claims: list[str] = []
    for sentence in SENTENCE_SPLIT_RE.split(message.strip()):
        clean = sentence.strip()
        if clean:
            claims.append(clean)
    return claims or ([message.strip()] if message.strip() else [])

