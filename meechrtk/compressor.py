"""Deterministic, safety-first output compression."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CompressionResult:
    original: str
    compressed: str
    original_bytes: int
    compressed_bytes: int
    savings_ratio: float


def _is_important(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    patterns = (
        r"\b(error|fatal|failed|failure|exception|traceback|warning|warn)\b",
        r"\b(denied|unauthorized|forbidden|not found|cannot|could not)\b",
        r"\b(exit code|status code|npm ERR|ERR!)\b",
        r"^\s*(at .+|Traceback \(most recent call last\))",
    )
    return any(re.search(p, s, re.I) for p in patterns)


def compress(text: str, *, max_repeated: int = 2, exact: bool = False) -> CompressionResult:
    """Compress consecutive duplicate/repetitive lines without removing evidence.

    This MVP deliberately avoids semantic deletion. Important/error lines are always
    retained. Exact mode returns the original output unchanged.
    """
    if exact or not text:
        compact = text
    else:
        lines = text.splitlines()
        out: list[str] = []
        previous = None
        repeats = 0
        for line in lines:
            normalized = re.sub(r"\s+", " ", line.strip())
            if normalized and normalized == previous and not _is_important(line):
                repeats += 1
                if repeats <= max_repeated:
                    out.append(line)
                elif repeats == max_repeated + 1:
                    out.append(f"… [MeechRTK suppressed {repeats - max_repeated} repeated lines] …")
            else:
                previous = normalized if normalized else previous
                repeats = 0
                out.append(line)
        compact = "\n".join(out)
        if text.endswith("\n"):
            compact += "\n"

    original_bytes = len(text.encode("utf-8"))
    compressed_bytes = len(compact.encode("utf-8"))
    ratio = 0.0 if original_bytes == 0 else 1 - (compressed_bytes / original_bytes)
    return CompressionResult(text, compact, original_bytes, compressed_bytes, ratio)
