from __future__ import annotations
from dataclasses import dataclass, asdict
import math, time, os
from .providers import ADAPTERS

@dataclass
class ProviderState:
    provider:str
    context_window:int
    reasoning_levels:list[str]
    cache_input:bool
    configured:bool=False
    available:bool=True
    tokens_remaining:int|None=None
    tokens_used:int=0
    cost_per_million_input:float|None=None
    latency_ms:float|None=None
    last_checked:float=0.0

class CapacityManager:
    """Tracks declared/provider-reported capacity and chooses the best legal route."""
    def __init__(self):
        self.states={k:ProviderState(k,v.capabilities.context_window,v.capabilities.reasoning_levels,v.capabilities.cache_input) for k,v in ADAPTERS.items()}
        envs={'claude':'ANTHROPIC_API_KEY','openai':'OPENAI_API_KEY','xai':'XAI_API_KEY','google':'GEMINI_API_KEY','openrouter':'OPENROUTER_API_KEY'}
        for p,e in envs.items(): self.states[p].configured=bool(os.getenv(e))
        self.states['ollama'].configured=True; self.states['lmstudio'].configured=True
    def configure(self,provider,**kwargs):
        if provider not in self.states: raise KeyError(provider)
        s=self.states[provider]
        for k,v in kwargs.items():
            if hasattr(s,k): setattr(s,k,v)
        s.configured=True;s.last_checked=time.time();return asdict(s)
    def record_usage(self,provider,tokens,cost=0.0,latency_ms=None):
        s=self.states[provider];s.tokens_used+=max(0,int(tokens))
        if s.tokens_remaining is not None:s.tokens_remaining=max(0,s.tokens_remaining-int(tokens))
        if latency_ms is not None:s.latency_ms=float(latency_ms)
    def route(self,task,required_tokens=0,preferred=None,local_ok=True,budget_usd=None):
        t=task.lower(); complexity='high' if any(x in t for x in ('architect','debug','reason','analyze','security','complex')) else ('medium' if len(t)>500 or any(x in t for x in ('code','build','design','compare')) else 'low')
        candidates=[]
        for name,s in self.states.items():
            is_local=name in ('ollama','lmstudio')
            if is_local and not local_ok:continue
            if not preferred and not s.configured:continue
            if required_tokens and s.context_window and required_tokens>s.context_window:continue
            if s.tokens_remaining is not None and required_tokens>s.tokens_remaining:continue
            score={'low':1.0,'medium':2.0,'high':3.0}[complexity] if not is_local else {'low':3.0,'medium':1.5,'high':.5}[complexity]
            if preferred and name==preferred:score+=4
            if s.cache_input:score+=.5
            if s.latency_ms is not None:score+=max(0,1-s.latency_ms/5000)
            if s.cost_per_million_input is not None and budget_usd is not None:score += max(0,2-s.cost_per_million_input/10)
            candidates.append((score,name,s))
        if not candidates:return {'ok':False,'error':'No configured provider has sufficient declared capacity','complexity':complexity}
        candidates.sort(reverse=True,key=lambda x:x[0]);best=candidates[0]
        return {'ok':True,'provider':best[1],'complexity':complexity,'required_tokens':required_tokens,'score':round(best[0],3),'reason':self._reason(best[1],best[2],complexity),'alternatives':[{'provider':n,'score':round(sc,3)} for sc,n,_ in candidates[1:4]]}
    def snapshot(self):return {k:asdict(v) for k,v in self.states.items()}
    @staticmethod
    def _reason(name,s,complexity):
        bits=[f'{complexity} task']
        if name in ('ollama','lmstudio'):bits.append('local/low-cost route')
        if s.cache_input:bits.append('cache-capable')
        if s.tokens_remaining is not None:bits.append(f'{s.tokens_remaining:,} tokens remaining')
        else:bits.append('quota unknown; no quota claim made')
        return ', '.join(bits)
