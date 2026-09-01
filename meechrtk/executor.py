from __future__ import annotations
import json, os, time, urllib.request, urllib.error

class ProviderError(RuntimeError):
    pass

class Executor:
    """Small dependency-free execution layer for cloud and local providers.

    API keys stay in the local systemd EnvironmentFile; the browser extension never sees them.
    Model names are configurable through MEECHRTK_*_MODEL variables.
    """
    def __init__(self):
        self.defaults = {
            "claude": ("ANTHROPIC_API_KEY", "https://api.anthropic.com/v1/messages", os.getenv("MEECHRTK_CLAUDE_MODEL", "claude-sonnet-4-5")),
            "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1/responses", os.getenv("MEECHRTK_OPENAI_MODEL", "gpt-5")),
            "xai": ("XAI_API_KEY", "https://api.x.ai/v1/responses", os.getenv("MEECHRTK_XAI_MODEL", "grok-4")),
            "google": ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta", os.getenv("MEECHRTK_GOOGLE_MODEL", "gemini-2.5-flash")),
            "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions", os.getenv("MEECHRTK_OPENROUTER_MODEL", "openai/gpt-5")),
        }

    def execute(self, provider, prompt, max_output_tokens=2048, reasoning="auto", model=None):
        provider = (provider or "auto").lower().strip()
        if provider == "auto":
            raise ProviderError("Auto must be resolved by the gateway before execution")
        started = time.time()
        if provider in ("ollama", "lmstudio"):
            result = self._local(provider, prompt, max_output_tokens, model)
        elif provider in self.defaults:
            keyenv, url, default_model = self.defaults[provider]
            key = os.getenv(keyenv)
            if not key:
                raise ProviderError(f"{keyenv} is not configured")
            result = self._cloud(provider, key, url, prompt, max_output_tokens, reasoning, model or default_model)
        else:
            raise ProviderError(f"Unsupported execution provider: {provider}")
        result["latency_ms"] = round((time.time() - started) * 1000, 1)
        result["provider"] = provider
        return result

    def _cloud(self, provider, key, url, prompt, max_tokens, reasoning, model):
        if provider == "claude":
            body = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
            if reasoning in ("low", "medium", "high"):
                budget = {"low": 1024, "medium": 4096, "high": 8192}[reasoning]
                # Anthropic thinking consumes output budget, so leave room for the answer.
                body["max_tokens"] = max(max_tokens, budget + 256)
                body["thinking"] = {"type": "enabled", "budget_tokens": budget}
            headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
        elif provider in ("openai", "xai"):
            body = {"model": model, "input": prompt, "max_output_tokens": max_tokens}
            if reasoning in ("none", "low", "medium", "high"):
                body["reasoning"] = {"effort": reasoning}
            headers = {"Authorization": f"Bearer {key}"}
        elif provider == "google":
            url = f"{url}/models/{model}:generateContent?key={key}"
            body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": max_tokens}}
            headers = {}
        else:
            body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
            if reasoning in ("low", "medium", "high"):
                body["reasoning_effort"] = reasoning
            headers = {"Authorization": f"Bearer {key}", "X-OpenRouter-Metadata": "enabled"}
        return self._request(url, headers, body, provider)

    def _request(self, url, headers, body, provider):
        headers = {**headers, "Content-Type": "application/json", "User-Agent": "MeechRTK/1.3"}
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=600) as response:
                raw = json.loads(response.read())
                status = response.status
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise ProviderError(f"{provider} HTTP {exc.code}: {detail[:1500]}") from exc
        except Exception as exc:
            raise ProviderError(f"{provider}: {exc}") from exc
        return {
            "text": self._extract(raw, provider),
            "model": raw.get("model"),
            "usage": self._usage(raw, provider),
            "raw_id": raw.get("id"),
            "http_status": status,
        }

    def _extract(self, raw, provider):
        if provider == "claude":
            return "".join(x.get("text", "") for x in raw.get("content", []) if x.get("type") == "text")
        if provider in ("openai", "xai"):
            if raw.get("output_text"):
                return raw["output_text"]
            return "".join(c.get("text", "") for x in raw.get("output", []) for c in x.get("content", []) if c.get("text"))
        if provider == "google":
            candidates = raw.get("candidates") or []
            if not candidates:
                return ""
            return "".join(part.get("text", "") for part in candidates[0].get("content", {}).get("parts", []))
        if provider == "ollama":
            return raw.get("response", "")
        return (raw.get("choices") or [{}])[0].get("message", {}).get("content", "")

    def _usage(self, raw, provider):
        u = raw.get("usage", {}) or {}
        return {
            "input_tokens": u.get("input_tokens", u.get("prompt_tokens", u.get("promptTokenCount", 0))) or 0,
            "output_tokens": u.get("output_tokens", u.get("completion_tokens", u.get("candidatesTokenCount", 0))) or 0,
            "total_tokens": u.get("total_tokens", u.get("totalTokenCount", 0)) or 0,
        }

    def _local(self, provider, prompt, max_tokens, model):
        if provider == "ollama":
            url = "http://127.0.0.1:11434/api/generate"
            selected = model or os.getenv("MEECHRTK_OLLAMA_MODEL", "qwen3:1.7b")
            body = {"model": selected, "prompt": prompt, "stream": False, "options": {"num_predict": max_tokens}}
            result = self._request(url, {}, body, provider)
            result["model"] = selected
            return result
        url = "http://127.0.0.1:1234/v1/chat/completions"
        selected = model or os.getenv("MEECHRTK_LMSTUDIO_MODEL", "local-model")
        body = {"model": selected, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
        result = self._request(url, {}, body, provider)
        result["model"] = selected
        return result
