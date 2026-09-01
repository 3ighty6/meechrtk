# MeechRTK — Universal Token Governor

**A local-first context governor for Claude, ChatGPT, Grok, Gemini, APIs, and local LLMs.**

MeechRTK does not optimize by blindly shortening prompts. It decides the minimum useful information required for the next task, preserves evidence, and reports measurable savings.

## 1.0 architecture

```text
Firefox / SDK / API client
          |
          v
     Local Gateway
          |
     +----+----------------+
     | Token Governor      |
     | Memory Engine       |
     | Context Router      |
     | Policy Engine       |
     | Budget Optimizer    |
     | Metrics + Learning  |
     +----+----------------+
          |
   provider-neutral result
          |
 Claude | OpenAI | xAI | Gemini | OpenRouter | Ollama | LM Studio
```

### Context governor

Each request is split into context chunks. A local neural guidance model scores task relevance, critical/error signal, code signal, density, and query shape. A quantum-inspired budget search then selects the highest-value combination under the requested context budget.

Chunks are classified as:

- **KEEP** — directly useful or critical evidence.
- **COMPRESS** — useful but not worth carrying verbatim.
- **DROP** — low-value or redundant for this task.

Critical evidence is prioritized over token savings. Savings are never guaranteed; they are measured from estimated before/after tokens.

### Persistent memory

Memory lives locally in `~/.meechrtk/memory.sqlite3`. Store project facts, decisions, constraints, and active state, then retrieve only memories relevant to the current request.

### Adaptive learning

`POST /v1/feedback` supports an opt-in local online logistic update for the five guidance features. The learned weights are stored in `~/.meechrtk/guidance.json` and are used by the next governor process.

### Response policy

The policy engine classifies requests as LOW, MEDIUM, or HIGH complexity and recommends context depth, response size, and reasoning effort. Provider adapters declare whether reasoning or caching controls exist. For consumer websites, hidden server-side reasoning cannot be controlled by a browser extension; MeechRTK only controls supplied context and explicit prompt instructions.

### Cache awareness

MeechRTK identifies stable-prefix situations and reports a cache policy recommendation. It does not claim to control provider-side cache internals. API adapters can use the provider capability metadata when implementing actual requests.

## Linux Mint installation

```bash
cd ~/meechrtk
git pull --ff-only origin main
bash install-linux.sh
```

The installer creates a Python virtual environment and a user-level systemd service listening only on `127.0.0.1:8765`.

Health check:

```bash
curl http://127.0.0.1:8765/health
```

Metrics:

```bash
curl http://127.0.0.1:8765/v1/metrics
```

## Firefox

Open `about:debugging#/runtime/this-firefox`, choose **This Firefox → Load Temporary Add-on**, and select `extension/manifest.json`.

The extension is provider-neutral and uses the active AI site's hostname only as a provider hint. It does not send page data to the internet; optimized requests go to the local gateway.

## Python SDK

```python
from meechrtk.sdk import MeechRTK

rtk = MeechRTK()
result = rtk.govern(
    "Fix the production build error",
    context=conversation_history,
    provider="openai",
    budget="balanced",
    project="my-project",
)
print(result["final_prompt"])
print(result["reduction"])
```

## Gateway API

`GET /health`

`GET /v1/metrics`

`GET /v1/providers`

`GET /v1/policy?request=...`

`POST /v1/optimize` with `{request, context, provider, budget, project, max_tokens, stable_prefix}`

`POST /v1/memory` with `{text, project, kind, importance}`

`POST /v1/feedback` with `{features:[5 numbers], label:0|1}`

## Product metrics

The product dashboard should report actual measurements such as:

```text
Requests optimized       100
Original tokens        1.82M
Optimized tokens       612K
Measured reduction      66.4%
Tokens saved           1.21M
Quality failures             2
```

These are examples of the metric schema, not promises about performance.

## Safety and privacy principles

1. Local-first by default.
2. Bind the gateway to loopback only.
3. Never log raw prompts by default.
4. Keep raw source recoverable when a client provides it, but do not transmit it unnecessarily.
5. Preserve errors, exact values, identifiers, code, and explicit constraints.
6. Measure quality and savings separately.
7. Never claim control over provider internals that the provider does not expose.

## License

See `LICENSE`.
