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

```powershell
python -m meechrtk.cli "git status"
```

Or pipe existing output:

```powershell
git diff | python -m meechrtk.cli --stdin
```

## Status

Early MVP. The first implementation focuses on deterministic, safe compression. Adaptive/semantic compression and agent hooks will be added after the benchmark harness is established.
