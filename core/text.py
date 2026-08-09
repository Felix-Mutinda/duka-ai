"""Small text utilities."""

from __future__ import annotations

import re

TOKEN_REGEX = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return TOKEN_REGEX.findall(text.lower())
