from __future__ import annotations
from typing import Any
from .governor import TokenGovernor
from .policy import PolicyEngine
from .providers import get_adapter

class MeechRTK:
    """Embed the governor in applications without coupling to an AI vendor."""
    def __init__(self, governor=None):
        self.governor=governor or TokenGovernor(); self.policy=PolicyEngine()
    def govern(self, request: str, context: str = "", *, provider: str = "auto", budget: str = "balanced", project: str = "default", max_tokens: int = 16000, stable_prefix: bool = False) -> dict[str,Any]:
        policy=self.policy.classify(request,provider,stable_prefix)
        result=self.governor.optimize(request,context,budget,provider,project,max_tokens)
        result["policy"]={"complexity":policy.complexity,"context_mode":policy.context_mode,"response_budget":policy.response_budget,"reasoning":policy.reasoning,"cache_action":policy.cache_action}
        result["provider_capabilities"]={"name":get_adapter(provider).capabilities.name,"supports_reasoning_control":get_adapter(provider).capabilities.supports_reasoning_control,"supports_prompt_cache":get_adapter(provider).capabilities.supports_prompt_cache}
        return result
