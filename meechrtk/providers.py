from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol

@dataclass(frozen=True)
class ProviderCapabilities:
    name: str
    supports_reasoning_control: bool = False
    supports_prompt_cache: bool = False
    supports_system_messages: bool = True
    mode: str = "browser"

class ProviderAdapter(Protocol):
    capabilities: ProviderCapabilities
    def normalize(self, payload: dict[str, Any]) -> dict[str, Any]: ...
    def build_request(self, governed: dict[str, Any]) -> dict[str, Any]: ...

class GenericAdapter:
    def __init__(self, name: str, *, reasoning=False, cache=False):
        self.capabilities=ProviderCapabilities(name, reasoning, cache)
    def normalize(self,payload):
        return {"provider":self.capabilities.name,"request":str(payload.get("request", "")),"context":str(payload.get("context", ""))}
    def build_request(self,governed):
        return {"provider":self.capabilities.name,"prompt":governed["final_prompt"],"usage":{k:governed[k] for k in ("original_tokens","optimized_tokens","reduction")}}

ADAPTERS={
    "claude":GenericAdapter("anthropic",cache=True),
    "openai":GenericAdapter("openai",reasoning=True,cache=True),
    "xai":GenericAdapter("xai",reasoning=True,cache=True),
    "google":GenericAdapter("google",cache=True),
    "openrouter":GenericAdapter("openrouter",cache=True),
    "ollama":GenericAdapter("ollama"),
    "lmstudio":GenericAdapter("lmstudio"),
}

def get_adapter(provider: str) -> ProviderAdapter:
    return ADAPTERS.get(provider, GenericAdapter(provider or "unknown"))
