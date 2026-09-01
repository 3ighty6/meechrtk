# MeechRTK Universal Token Governor

MeechRTK 1.0 changes the optimization target from shortening text to selecting the smallest useful context for the next task.

## Core loop

1. Normalize request/context from a client.
2. Retrieve relevant local semantic memory.
3. Score chunks with the local TinyNN guidance model.
4. Classify chunks as KEEP, COMPRESS, or DROP.
5. Select a budget-fitting context with the quantum-inspired optimizer.
6. Return the optimized prompt plus auditable decisions and metrics.

## Local-first

The gateway binds to `127.0.0.1:8765`. Memory is stored in `~/.meechrtk/memory.sqlite3`. No provider API key is required for browser-mode context governance.

## Provider neutrality

The browser adapter identifies Claude, ChatGPT/OpenAI, Grok/xAI, and Gemini. The governor itself has no provider-specific scoring logic. Future API adapters should translate the normalized result into each provider's request format and capabilities.

## Important limitation

For consumer AI websites, MeechRTK can control the prompt/context it supplies but cannot claim to control hidden server-side reasoning tokens. API adapters may expose provider-specific reasoning controls where the provider supports them.

## Metrics

Every optimization reports estimated original tokens, optimized tokens, reduction percentage, information coverage, and a KEEP/COMPRESS/DROP decision list. Savings are measured per request; no fixed 60–90% guarantee is assumed.
