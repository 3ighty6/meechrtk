from __future__ import annotations
import json
from pathlib import Path
from .governor import ROOT

class GuidanceLearner:
    """Tiny online logistic learner. Feedback is local and opt-in via /feedback."""
    def __init__(self,path=ROOT/'guidance.json'):
        self.path=Path(path); self.state={'weights':[1.8,1.5,1.2,-1.1,0.8],'bias':-1.0,'examples':0}
        if self.path.exists():
            try:self.state.update(json.loads(self.path.read_text()))
            except Exception:pass
    def update(self,features,label,lr=0.05):
        w=self.state['weights']; b=self.state['bias']; z=sum(a*x for a,x in zip(w,features))+b
        p=1/(1+__import__('math').exp(-max(-30,min(30,z)))); err=label-p
        self.state['weights']=[a+lr*err*x for a,x in zip(w,features)]; self.state['bias']=b+lr*err; self.state['examples']+=1
        self.path.write_text(json.dumps(self.state,indent=2))
        return self.state
