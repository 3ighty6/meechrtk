from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol

@dataclass(frozen=True)
class ProviderCapabilities:
    name: str
    context_window: int = 128000
    reasoning_levels: tuple[str, ...] = ()
    cache_input: bool = False
    supports_reasoning_control: bool = False
    supports_prompt_cache: bool = False
    supports_system_messages: bool = True
    mode: str = "browser"

class ProviderAdapter(Protocol):
    capabilities: ProviderCapabilities
    def normalize(self, payload: dict[str, Any]) -> dict[str, Any]: ...
    def build_request(self, governed: dict[str, Any]) -> dict[str, Any]: ...

class GenericAdapter:
    def __init__(self, name: str, *, context_window=128000, reasoning=(), cache=False, mode="browser"):
        levels=tuple(reasoning) if not isinstance(reasoning,bool) else (("none","low","medium","high") if reasoning else ())
        self.capabilities=ProviderCapabilities(name,context_window,levels,cache,bool(levels),cache,True,mode)
    def normalize(self,payload):
        return {"provider":self.capabilities.name,"request":str(payload.get("request", "")),"context":str(payload.get("context", ""))}
    def build_request(self,governed):
        return {"provider":self.capabilities.name,"prompt":governed["final_prompt"],"usage":{k:governed[k] for k in ("original_tokens","optimized_tokens","reduction")}}

ADAPTERS={
    "claude":GenericAdapter("anthropic",context_window=200000,cache=True),
    "openai":GenericAdapter("openai",context_window=128000,reasoning=("low","medium","high"),cache=True),
    "xai":GenericAdapter("xai",context_window=131072,reasoning=("none","low","medium","high"),cache=True),
    "google":GenericAdapter("google",context_window=1000000,cache=True),
    "openrouter":GenericAdapter("openrouter",context_window=200000,cache=True),
    "ollama":GenericAdapter("ollama",context_window=32768,mode="local"),
    "lmstudio":GenericAdapter("lmstudio",context_window=32768,mode="local"),
}

def get_adapter(provider: str) -> ProviderAdapter:
    return ADAPTERS.get(provider, GenericAdapter(provider or "unknown"))
