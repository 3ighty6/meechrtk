"""Deterministic, safety-first output compression.

Design principle: minimize context, never minimize evidence. Three
layers, applied in order:

1. Noise stripping -- lines matching well-known low-information
   patterns from common dev tools (npm/pip/apt progress spam,
   deprecation notices, download progress bars) are elided outright,
   replaced by a single tally line. These patterns are checked BEFORE
   the important-line check, since e.g. "npm warn deprecated" contains
   "warn" but is noise, not a real warning about *this* command.
2. Block truncation -- long stretches (8+ lines) containing zero
   important/error signal are collapsed to their first and last line
   plus an omission count. A run is never truncated if it contains
   anything from the important-pattern list.
3. Consecutive duplicate collapsing -- unchanged from the original
   MVP behavior.

Anything matching the important-pattern list is never touched by any
layer, full stop.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

IMPORTANT_PATTERNS = (
    r"\b(error|fatal|failed|failure|exception|traceback)\b",
    r"\b(denied|unauthorized|forbidden|not found|cannot|could not)\b",
    r"\b(exit code|status code|npm ERR|ERR!)\b",
    r"^\s*(at .+|Traceback \(most recent call last\))",
    # A bare "warning" is important UNLESS it's already matched by a
    # noise pattern first (checked earlier in the pipeline).
    r"\bwarning\b",
)

# Known low-information patterns from common package managers and
# build tools. Matched BEFORE the important-pattern check, so e.g.
# "npm warn deprecated" is treated as noise even though it contains
# the word "warn".
NOISE_PATTERNS = (
    r"^npm notice\b",
    r"^npm warn deprecated\b",
    r"^npm warn (optional|old lockfile)\b",
    r"^\s*npm notice$",
    r"^Requirement already satisfied\b",
    r"^\s*Downloading\s",
    r"^\s*Collecting\s",
    r"^\s*Using cached\b",
    r"\d+%\|[█▏▎▍▌▋▊▉ ]*\|",  # tqdm-style progress bars
    r"^\s*\d+/\d+\s*\[[#=\-\s]*\]",  # generic [====>   ] progress
    r"^\s*(transforming|rendering chunks|computing gzip size)\.\.\.\s*$",
    r"^\s*added \d+ packages?.*in \d+",
    r"^\s*\d+ packages? (are|is) looking for funding\b",
    r"^\s*run `npm fund`",
)

_NOISE_RE = [re.compile(p, re.I) for p in NOISE_PATTERNS]
_IMPORTANT_RE = [re.compile(p, re.I) for p in IMPORTANT_PATTERNS]


@dataclass(frozen=True)
class CompressionResult:
    original: str
    compressed: str
    original_bytes: int
    compressed_bytes: int
    savings_ratio: float


def _is_noise(line: str) -> bool:
    return any(p.search(line) for p in _NOISE_RE)


def _is_important(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if _is_noise(line):
        return False
    return any(p.search(s) for p in _IMPORTANT_RE)


def _strip_noise(lines: list[str]) -> list[str]:
    """Layer 1: elide known-noise lines, tally them at each contiguous run.

    Blank lines adjacent to noise are absorbed into the run rather than
    breaking it -- npm/pip routinely pad noise blocks with blank
    separator lines, and without this a single noisy block fragments
    into several small "elided" messages instead of one clean tally.
    """
    out: list[str] = []
    noise_run = 0
    pending_blanks = 0

    def flush():
        nonlocal noise_run, pending_blanks
        if noise_run > 0:
            out.append(f"… [MeechRTK elided {noise_run} noise line(s): package manager/progress spam] …")
        noise_run = 0
        pending_blanks = 0

    for line in lines:
        is_blank = not line.strip()
        if is_blank and noise_run > 0:
            # Might be a separator inside a noise block, or the true end
            # of it -- hold it and decide once we see the next real line.
            pending_blanks += 1
            continue
        if _is_noise(line) and not _is_important(line):
            noise_run += 1
            pending_blanks = 0  # any held blanks were mid-block separators
        else:
            flush()
            out.extend([""] * pending_blanks)
            pending_blanks = 0
            out.append(line)
    flush()
    out.extend([""] * pending_blanks)
    return out


def _truncate_clean_blocks(lines: list[str], min_block: int = 8, keep_edges: int = 1) -> list[str]:
    """Layer 2: collapse long runs with zero important/error signal."""
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        if _is_important(lines[i]):
            out.append(lines[i])
            i += 1
            continue
        # Find the extent of this "clean" run (no important lines)
        j = i
        while j < n and not _is_important(lines[j]):
            j += 1
        run = lines[i:j]
        if len(run) >= min_block:
            head = run[:keep_edges]
            tail = run[-keep_edges:] if keep_edges else []
            omitted = len(run) - len(head) - len(tail)
            out.extend(head)
            out.append(f"… [MeechRTK omitted {omitted} line(s), no errors/warnings in this stretch] …")
            out.extend(tail)
        else:
            out.extend(run)
        i = j
    return out


def _collapse_consecutive_duplicates(lines: list[str], max_repeated: int = 2) -> list[str]:
    """Layer 3: unchanged from the original MVP -- collapse exact repeats."""
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
                out.append(f"… [MeechRTK suppressed {repeats - max_repeated} repeated line(s)] …")
        else:
            previous = normalized if normalized else previous
            repeats = 0
            out.append(line)
    return out


def compress(text: str, *, max_repeated: int = 2, exact: bool = False) -> CompressionResult:
    """Compress noisy tool output while always preserving errors, warnings,
    paths, identifiers, and exact values. Exact mode returns input unchanged.
    """
    if exact or not text:
        compact = text
    else:
        lines = text.splitlines()
        lines = _strip_noise(lines)
        lines = _truncate_clean_blocks(lines)
        lines = _collapse_consecutive_duplicates(lines, max_repeated=max_repeated)
        compact = "\n".join(lines)
        if text.endswith("\n"):
            compact += "\n"

    original_bytes = len(text.encode("utf-8"))
    compressed_bytes = len(compact.encode("utf-8"))
    ratio = 0.0 if original_bytes == 0 else 1 - (compressed_bytes / original_bytes)
    return CompressionResult(text, compact, original_bytes, compressed_bytes, ratio)
