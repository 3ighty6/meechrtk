from __future__ import annotations
import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from . import __version__
from .governor import TokenGovernor
from .policy import PolicyEngine
from .storage import Store
from .learning import GuidanceLearner
from .providers import get_adapter, ADAPTERS
from .capacity import CapacityManager
from .executor import Executor, ProviderError

HOST, PORT = "127.0.0.1", 8765
GOV, POLICY, STORE, LEARNER, CAPACITY, EXECUTOR = TokenGovernor(), PolicyEngine(), Store(), GuidanceLearner(), CapacityManager(), Executor()
PROVIDER_ALIASES = {
    "auto": "auto", "chatgpt": "openai", "gpt": "openai", "openai": "openai",
    "grok": "xai", "x.ai": "xai", "xai": "xai",
    "claude.ai": "claude", "anthropic": "claude", "claude": "claude",
    "gemini": "google", "google": "google", "openrouter": "openrouter",
    "ollama": "ollama", "lmstudio": "lmstudio", "lm studio": "lmstudio",
}


def normalize_provider(value):
    raw = str(value or "auto").strip().lower()
    return PROVIDER_ALIASES.get(raw, raw)


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST,GET,OPTIONS")
        self.end_headers()
        if status != 204:
            self.wfile.write(body)

    def _json(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/health":
            return self._send(200, {"ok": True, "service": "meechrtk-gateway", "version": __version__})
        if p == "/v1/metrics":
            return self._send(200, {"ok": True, "metrics": STORE.summary()})
        if p == "/v1/policy":
            request = parse_qs(urlparse(self.path).query).get("request", [""])[0]
            return self._send(200, {"ok": True, "policy": asdict(POLICY.classify(request))})
        if p == "/v1/providers":
            return self._send(200, {"ok": True, "providers": {k: asdict(v.capabilities) for k, v in ADAPTERS.items()}})
        if p == "/v1/capacity":
            return self._send(200, {"ok": True, "providers": CAPACITY.snapshot()})
        return self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        p = urlparse(self.path).path
        try:
            data = self._json()
            if p == "/v1/optimize":
                request = str(data.get("request", "")).strip()
                if not request:
                    return self._send(400, {"ok": False, "error": "request is required"})
                provider = normalize_provider(data.get("provider", "auto"))
                policy = POLICY.classify(request, provider, bool(data.get("stable_prefix")))
                budget = data.get("budget", policy.context_mode)
                result = GOV.optimize(request, str(data.get("context", "")), budget, provider, data.get("project", "default"), int(data.get("max_tokens", 16000)))
                result["policy"] = asdict(policy)
                result["provider_capabilities"] = asdict(get_adapter(provider).capabilities)
                STORE.record(result)
                return self._send(200, {"ok": True, "result": result})

            if p == "/v1/execute":
                request = str(data.get("request", "")).strip()
                if not request:
                    return self._send(400, {"ok": False, "error": "request is required"})
                requested = normalize_provider(data.get("provider", "auto"))
                project = data.get("project", "default")
                optimized = GOV.optimize(request, str(data.get("context", "")), data.get("budget", "balanced"), requested, project, int(data.get("max_context_tokens", 16000)))
                route = CAPACITY.route(request, optimized["optimized_tokens"], None if requested == "auto" else requested, bool(data.get("local_ok", True)), data.get("budget_usd"))
                if not route.get("ok"):
                    return self._send(503, route)
                provider = route["provider"]
                complexity = route.get("complexity", "medium")
                reasoning = data.get("reasoning", "auto")
                if reasoning == "auto":
                    reasoning = "high" if complexity == "high" else ("medium" if complexity == "medium" else "low")
                try:
                    result = EXECUTOR.execute(provider, optimized["final_prompt"], int(data.get("max_output_tokens", 2048)), reasoning, data.get("model"))
                except ProviderError as exc:
                    return self._send(424, {"ok": False, "error": str(exc), "provider": provider, "route": route, "optimized": optimized})
                usage = result.get("usage", {})
                input_tokens = int(usage.get("input_tokens") or optimized["optimized_tokens"])
                CAPACITY.record_usage(provider, input_tokens, 0, result.get("latency_ms"))
                telemetry = {**optimized, "execution_provider": provider, "execution_usage": usage, "execution_latency_ms": result.get("latency_ms"), "execution_model": result.get("model")}
                STORE.record(telemetry)
                return self._send(200, {"ok": True, "provider": provider, "route": route, "optimized": optimized, "response": result})

            if p == "/v1/route":
                request = str(data.get("request", "")).strip()
                if not request:
                    return self._send(400, {"ok": False, "error": "request is required"})
                preferred = normalize_provider(data.get("preferred")) if data.get("preferred") else None
                return self._send(200, CAPACITY.route(request, int(data.get("required_tokens", 0)), preferred, bool(data.get("local_ok", True)), data.get("budget_usd")))

            if p == "/v1/capacity/configure":
                provider = normalize_provider(data.get("provider"))
                if not provider or provider == "auto":
                    return self._send(400, {"ok": False, "error": "provider is required"})
                allowed = {k: v for k, v in data.items() if k in {"context_window", "reasoning_levels", "cache_input", "configured", "available", "tokens_remaining", "tokens_used", "cost_per_million_input", "latency_ms"}}
                return self._send(200, {"ok": True, "provider": CAPACITY.configure(provider, **allowed)})

            if p == "/v1/capacity/usage":
                provider = normalize_provider(data.get("provider"))
                tokens = int(data.get("tokens", 0))
                CAPACITY.record_usage(provider, tokens, float(data.get("cost", 0)), data.get("latency_ms"))
                return self._send(200, {"ok": True, "provider": asdict(CAPACITY.states[provider])})

            if p == "/v1/memory":
                text = str(data.get("text", "")).strip()
                if not text:
                    return self._send(400, {"ok": False, "error": "text is required"})
                mid = GOV.memory.add(text, data.get("project", "default"), data.get("kind", "fact"), float(data.get("importance", .7)))
                return self._send(200, {"ok": True, "id": mid})

            if p == "/v1/feedback":
                features, label = data.get("features", []), float(data.get("label", 0))
                if len(features) != 5 or label not in (0.0, 1.0):
                    return self._send(400, {"ok": False, "error": "features must contain 5 values and label must be 0 or 1"})
                return self._send(200, {"ok": True, "model": LEARNER.update([float(x) for x in features], label)})

            return self._send(404, {"ok": False, "error": "not found"})
        except Exception as exc:
            return self._send(500, {"ok": False, "error": str(exc)})

    def log_message(self, *args):
        pass


def main():
    print(f"MeechRTK Token Governor {__version__} listening on http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
