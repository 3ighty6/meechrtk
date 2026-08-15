# MeechRTK — Claude Skill

## Purpose

Reduce unnecessary context consumption while preserving information required for correctness.

## Operating rules

1. Prefer compact, relevant tool output over raw repetitive output.
2. Preserve errors, warnings, stack traces, file paths, identifiers, exit codes, and exact values.
3. Never summarize away evidence needed to make a technical decision.
4. If the user asks for exact/full/raw output, bypass compression.
5. When compressed output is insufficient, retrieve the smallest raw section needed.
6. Do not repeatedly restate context already established in the conversation or project.
7. For large files, inspect structure first and retrieve relevant ranges before loading everything.
8. Treat token savings as an optimization metric, not a correctness goal.
9. Record before/after sizes when benchmarking compression.
10. When uncertain whether information is safe to discard, keep it.

## Preferred workflow

```text
Task → identify required evidence → run tool → compress noise → preserve evidence → act
                                      ↑                         ↓
                                      └── retrieve raw detail if needed ──┘
```

## Safety principle

**Minimize context, never minimize evidence.**
