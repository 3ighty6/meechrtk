# MeechRTK — Universal Token Governor

**A local-first context governor for Claude, ChatGPT, Grok, Gemini, APIs, and local LLMs.**

MeechRTK does not optimize by blindly shortening prompts. It decides the minimum useful information required for the next task, preserves evidence, and reports measurable savings.

## Capacity Manager

MeechRTK now adds a capacity/routing layer that tracks declared context windows, known remaining quotas, cache capability, cost, and observed latency. It chooses a legal route across configured providers and local models. Unknown quotas stay `null`; MeechRTK never mints tokens, bypasses limits, or fabricates capacity.

Gateway endpoints:

- `GET /v1/capacity`
- `POST /v1/capacity/configure`
- `POST /v1/capacity/usage`
- `POST /v1/route`

## 1.0 architecture

```text
Firefox / SDK / API client
          |
          v
     Local Gateway
          |
     +----+----------------------+
     | Token Governor             |
     | Memory Engine              |
     | Context Router             |
     | Policy Engine              |
     | Capacity Manager           |
     | Budget Optimizer            |
     | Metrics + Learning          |
     +----+----------------------+
          |
   provider-neutral result
          |
 Claude | OpenAI | xAI | Gemini | OpenRouter | Ollama | LM Studio
```

## Context governor

Each request is split into context chunks. A local neural guidance model scores task relevance, critical/error signal, code signal, density, and query shape. A quantum-inspired budget search then selects the highest-value combination under the requested context budget.

Chunks are classified as **KEEP**, **COMPRESS**, or **DROP**. Critical evidence is prioritized over token savings. Savings are measured rather than guaranteed.

## Persistent memory

Memory lives locally in `~/.meechrtk/memory.sqlite3`. Store project facts, decisions, constraints, and active state, then retrieve only memories relevant to the current request.

## Adaptive learning

`POST /v1/feedback` supports an opt-in local online update for the five guidance features. Learned weights are stored in `~/.meechrtk/guidance.json`.

## Response policy and cache awareness

The policy engine classifies LOW/MEDIUM/HIGH complexity and recommends context depth, response size, and reasoning effort. Provider adapters declare exposed capabilities. Consumer websites cannot expose hidden server-side reasoning controls to an extension. Stable-prefix/cache recommendations are treated as policy hints, not fabricated provider behavior.

## Linux Mint

```bash
cd ~/meechrtk
git pull --ff-only origin main
bash install-linux.sh
curl http://127.0.0.1:8765/health
```

## Firefox

Open `about:debugging#/runtime/this-firefox`, choose **This Firefox → Load Temporary Add-on**, and select `extension/manifest.json`.

The extension is provider-neutral and sends optimized context only to the local gateway.

## Python SDK

```python
from meechrtk.sdk import MeechRTK
rtk = MeechRTK()
result = rtk.govern("Fix the production build error", context=history, provider="openai", budget="balanced", project="my-project")
```

## Product principle

The objective is not to create provider tokens. The objective is to maximize **useful intelligence per token, dollar, and unit of context capacity** while preserving correctness and continuity.

## Safety and privacy

1. Local-first by default.
2. Gateway binds to loopback only.
3. Raw prompts are not logged by the governor by default.
4. Preserve errors, exact values, identifiers, code, and explicit constraints.
5. Measure quality and savings separately.
6. Never claim control over provider internals that are not exposed.

See `LICENSE`.
