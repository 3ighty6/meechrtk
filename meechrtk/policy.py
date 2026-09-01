from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class RequestPolicy:
    complexity: str
    context_mode: str
    response_budget: str
    reasoning: str
    cache_action: str

class PolicyEngine:
    HIGH=re.compile(r"\b(architect|design|refactor|debug|security|migration|analy[sz]e|compare|research|implement|build|production|critical|root cause)\b",re.I)
    LOW=re.compile(r"\b(what is|define|yes or no|translate|spell|shorten|summari[sz]e|quick|simple)\b",re.I)
    def classify(self, request: str, provider: str = "auto", has_stable_prefix: bool = False) -> RequestPolicy:
        words=len(request.split()); high=bool(self.HIGH.search(request)); low=bool(self.LOW.search(request))
        complexity="HIGH" if high or words>180 else ("LOW" if low or words<25 else "MEDIUM")
        mode={"LOW":"minimal","MEDIUM":"balanced","HIGH":"deep"}[complexity]
        response={"LOW":"short","MEDIUM":"standard","HIGH":"large"}[complexity]
        reasoning={"LOW":"low","MEDIUM":"medium","HIGH":"high"}[complexity]
        cache="PRESERVE_STABLE_PREFIX" if has_stable_prefix else "NONE"
        if provider in {"openai","xai"}:
            return RequestPolicy(complexity,mode,response,reasoning,cache)
        return RequestPolicy(complexity,mode,response,"UNCONTROLLED" if complexity!="LOW" else "UNCONTROLLED",cache)
