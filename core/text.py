"""Small text utilities."""

from __future__ import annotations

import re

TOKEN_REGEX = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Tokenize text into normalized lowercase tokens."""
    return [_normalize_token(token) for token in TOKEN_REGEX.findall(text.lower())]


def _normalize_token(token: str) -> str:
    """Apply crude MVP token normalization.

    This is not a production stemmer. It exists to make the demo retrieval
    less brittle for common plural and past-tense variations.
    """
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"

    if token.endswith("ed") and len(token) > 4:
        token = token[:-2]
    elif token.endswith("ing") and len(token) > 5:
        token = token[:-3]

    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        token = token[:-1]

    return token
