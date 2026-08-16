# MeechRTK

**Context-efficient AI tooling for CLI output, files, and agent workflows.**

MeechRTK is an RTK-inspired token/context governor designed to reduce noisy tool output without hiding information needed for correctness.

## Goals

- Compress repetitive CLI output while preserving errors, warnings, paths, identifiers, and exact values.
- Support Windows-first workflows as well as Unix shells.
- Measure actual before/after output size and token savings.
- Keep raw output recoverable when compressed context is insufficient.
- Provide a Claude Code skill for context-efficient agent behavior.
- Build toward semantic context deduplication and adaptive guidance.

## Design principle

> Minimize context, never minimize evidence.

MeechRTK should summarize noise, not facts. Compression is bypassed when exact output is requested or when lossy transformation could affect correctness.

## How compression works

Three layers, applied in order, and every layer defers to the important-pattern list (error/fatal/failed/exception/traceback/denied/warning/exit-code/stack-trace lines) -- nothing matching those is ever touched:

1. **Noise stripping.** Well-known low-information patterns from common
   dev tools (npm/pip progress spam, deprecation notices, download
   progress bars) are elided outright and replaced with a single tally
   line. Checked before the important-pattern list, so e.g.
   `npm warn deprecated ...` is treated as noise even though it
   contains "warn".
2. **Clean-block truncation.** Long stretches (8+ lines) with zero
   important/error signal collapse to their first and last line plus
   an omission count. A run is never truncated if anything in it
   matches the important-pattern list.
3. **Consecutive duplicate collapsing.** Unchanged from the original
   MVP -- exact repeated lines collapse after 2 repeats.

Verified against real npm install output, real build logs, and a
mixed sample with actual `npm ERR!` lines interspersed with noise:
**85-90% size reduction on genuinely noisy output, with every error
line surviving byte-for-byte.** See `tests/test_compressor.py`.

## Project layout

```text
meechrtk/
├── meechrtk/
│   ├── __init__.py
│   ├── cli.py
│   └── compressor.py
├── skills/
│   └── claude/
│       └── SKILL.md
├── tests/
│   └── test_compressor.py
├── pyproject.toml
└── README.md
```

## Quick start

```bash
pip install -e .
meechrtk "git status"
```

Or pipe existing output:

```bash
git diff | meechrtk --stdin
```

Use `--exact` to bypass compression entirely and get raw output back unchanged.

## Status

MVP with a tested, deterministic compression pipeline (noise stripping + clean-block truncation + duplicate collapsing). Adaptive/semantic compression and agent hooks are the next phase.
