---
name: meechrtk
version: 0.1.0
description: Minimize redundant context and noisy tool output while preserving evidence needed for correctness.
---

# MeechRTK for Claude

## Core rule

**Minimize context; never minimize evidence.**

## Operating rules

1. Prefer compact, relevant tool output over raw repetitive output.
2. Preserve errors, warnings, failures, exceptions, stack traces, paths, identifiers, hashes, versions, exit codes, and exact values.
3. Never summarize away evidence needed for a technical decision.
4. If the user asks for exact/full/raw output, bypass compression.
5. When compressed output is insufficient, retrieve the smallest raw section needed.
6. Do not repeatedly restate context already established in the conversation or project.
7. For large files, inspect structure first and retrieve relevant ranges before loading everything.
8. Treat token savings as an optimization metric, not a correctness goal.
9. When benchmarking, record before/after sizes and savings.
10. If uncertain whether information is safe to discard, keep it.

## Preferred workflow

```text
Task → identify required evidence → run tool → compress noise → preserve evidence → act
                                      ↑                         ↓
                                      └── retrieve raw detail if needed ──┘
```

## Never compress when

- The user requests complete/raw output.
- Exact ordering or counts affect correctness.
- Full debugging traces are required.
- Compression could hide security or data-integrity evidence.

## Safety principle

**Minimize context, never minimize evidence.**
