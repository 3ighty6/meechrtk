from __future__ import annotations

import math, re, sqlite3, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path.home() / ".meechrtk"
DB = ROOT / "memory.sqlite3"
ROOT.mkdir(parents=True, exist_ok=True)

TOKEN_RE = re.compile(r"\S+")
CODE_RE = re.compile(r"```[\s\S]*?```|\b(?:src|lib|app|tests?)/[\w./-]+\b|\b(?:line|ln)\s*\d+\b", re.I)
IMPORTANT_RE = re.compile(r"\b(error|fatal|failed|failure|exception|traceback|warning|constraint|requirement|must|cannot|don't|never|decision|goal|todo|current task)\b", re.I)
STOP = set("the a an and or but if then than this that with from for into your you are was were have has had not can will would should could to of in on is it as be by at we i my me our their for a project build make do does did".split())

@dataclass
class Chunk:
    id: str
    text: str
    source: str = "request"
    kind: str = "conversation"
    tokens: int = 0
    relevance: float = 0.0
    importance: float = 0.0
    redundancy: float = 0.0
    action: str = "DROP"

@dataclass
class Decision:
    chunk_id: str
    action: str
    score: float
    reason: str

class TinyNN:
    """Small deterministic local neural guidance model; no network/dependency required."""
    def __init__(self):
        self.w = [1.8, 1.5, 1.2, -1.1, 0.8]
        self.b = -1.0
    def score(self, x):
        z = sum(a*b for a,b in zip(self.w,x)) + self.b
        return 1/(1+math.exp(-max(-30,min(30,z))))
    def guide(self, chunk, query):
        txt = chunk.text
        q = set(self._terms(query)); t = set(self._terms(txt))
        overlap = len(q & t) / max(1,len(q))
        critical = 1.0 if IMPORTANT_RE.search(txt) else 0.0
        code = 1.0 if CODE_RE.search(txt) else 0.0
        density = min(1.0, len(txt)/1500)
        question = 1.0 if "?" in query else 0.0
        return self.score([overlap, critical, code, density, question])
    def _terms(self, s):
        return [x for x in re.findall(r"[a-zA-Z0-9_'-]{3,}", s.lower()) if x not in STOP]

class MemoryEngine:
    def __init__(self, db=DB):
        self.db = db
        self.db.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db) as c:
            c.execute("create table if not exists memories (id text primary key, project text, kind text, text text, importance real, created real, updated real)")
            c.execute("create index if not exists idx_memories_project on memories(project)")
    def add(self, text, project="default", kind="fact", importance=0.7):
        mid=str(uuid.uuid4())
        now=time.time()
        with sqlite3.connect(self.db) as c:
            c.execute("insert into memories values(?,?,?,?,?,?,?)", (mid,project,kind,text,importance,now,now))
        return mid
    def search(self, query, project="default", limit=12):
        q=set(TinyNN()._terms(query))
        with sqlite3.connect(self.db) as c:
            rows=c.execute("select id,kind,text,importance from memories where project=? order by updated desc",(project,)).fetchall()
        scored=[]
        for mid,kind,text,imp in rows:
            t=set(TinyNN()._terms(text)); overlap=len(q&t)/max(1,len(q))
            scored.append((overlap*0.75+imp*0.25,mid,kind,text))
        return [(x[1],x[2],x[3],x[0]) for x in sorted(scored,reverse=True)[:limit] if x[0]>0.08]

class QuantumInspiredOptimizer:
    """Budgeted bit-state search with deterministic simulated annealing."""
    def choose(self, chunks, budget):
        if not chunks: return []
        state=[False]*len(chunks)
        # seed with highest value/token
        order=sorted(range(len(chunks)), key=lambda i: (chunks[i].relevance+chunks[i].importance-chunks[i].redundancy)/max(1,chunks[i].tokens), reverse=True)
        used=0
        for i in order:
            if used+chunks[i].tokens<=budget:
                state[i]=True; used+=chunks[i].tokens
        best=state[:]; bestv=self._value(chunks,state)
        temp=max(0.05,bestv*0.15)
        for step in range(min(300,len(chunks)*8)):
            i=step%len(chunks); cand=state[:]; cand[i]=not cand[i]
            if sum(chunks[j].tokens for j,v in enumerate(cand) if v)>budget: continue
            v=self._value(chunks,cand)
            if v>bestv or (v>=self._value(chunks,state)-temp): state=cand
            if v>bestv: best,bestv=cand[:],v
            temp*=0.985
        return [c for c,v in zip(chunks,best) if v]
    def _value(self,chunks,state):
        return sum((c.relevance+c.importance*0.7-c.redundancy*0.5) for c,v in zip(chunks,state) if v)

class TokenGovernor:
    BUDGETS={"minimal":0.20,"efficient":0.40,"balanced":0.60,"deep":0.80,"maximum":1.0}
    def __init__(self, memory=None):
        self.nn=TinyNN(); self.memory=memory or MemoryEngine(); self.optimizer=QuantumInspiredOptimizer()
    @staticmethod
    def estimate_tokens(text): return max(0, math.ceil(len(text)/4))
    def chunk(self,text,source="request",kind="conversation"):
        blocks=re.split(r"\n\s*\n", text.strip()) if text.strip() else []
        return [Chunk(str(uuid.uuid4()),b,source,kind,self.estimate_tokens(b)) for b in blocks]
    def optimize(self, request, context="", budget=0.6, provider="auto", project="default", max_tokens=16000):
        if isinstance(budget,str): budget=self.BUDGETS.get(budget,0.6)
        request_tokens=self.estimate_tokens(request)
        memories=self.memory.search(request,project)
        chunks=self.chunk(context,"history","conversation")
        for mid,kind,text,score in memories:
            chunks.append(Chunk(mid,text,"memory",kind,self.estimate_tokens(text)))
        for c in chunks:
            c.relevance=self.nn.guide(c,request)
            c.importance=1.0 if IMPORTANT_RE.search(c.text) else (0.8 if CODE_RE.search(c.text) else 0.45)
            c.redundancy=0.0
            if c.source=="memory": c.importance=max(c.importance,0.75)
            c.action="KEEP" if c.relevance>=0.78 or c.importance>=0.95 else ("COMPRESS" if c.relevance>=0.28 else "DROP")
        budget_tokens=max(256,int(max_tokens*float(budget))-request_tokens)
        keep=[c for c in chunks if c.action=="KEEP"]
        optional=[c for c in chunks if c.action=="COMPRESS"]
        selected=self.optimizer.choose(keep+optional,budget_tokens)
        selected_ids={c.id for c in selected}
        for c in chunks:
            if c.id in selected_ids: c.action="KEEP"
            elif c.action=="KEEP": c.action="COMPRESS" if c.relevance>0.25 else "DROP"
        parts=[]
        decisions=[]
        for c in chunks:
            if c.action=="KEEP": parts.append(c.text); decisions.append(Decision(c.id,"KEEP",c.relevance,"high relevance/importance or optimizer-selected"))
            elif c.action=="COMPRESS":
                summary=self._safe_compress(c.text); parts.append(summary); decisions.append(Decision(c.id,"COMPRESS",c.relevance,"useful but budget-constrained"))
            else: decisions.append(Decision(c.id,"DROP",c.relevance,"low task relevance"))
        optimized=("\n\n".join(parts)).strip()
        if not optimized and context.strip(): optimized="[No historical context selected; current request is self-contained.]"
        original=self.estimate_tokens(context)+request_tokens
        final=request+"\n\n"+("Relevant context:\n"+optimized if optimized else "")
        final_tokens=self.estimate_tokens(final)
        return {"provider":provider,"project":project,"request":request,"optimized_context":optimized,"final_prompt":final,"original_tokens":original,"optimized_tokens":final_tokens,"reduction":round(max(0,1-final_tokens/max(1,original))*100,2),"information_coverage":round(100*sum(c.relevance for c in chunks if c.action=="KEEP")/max(0.01,sum(c.relevance for c in chunks)),2) if chunks else 100.0,"decisions":[asdict(d) for d in decisions],"budget_fraction":budget}
    def _safe_compress(self,text):
        lines=text.splitlines()
        if len(lines)<=4:return text
        important=[x for x in lines if IMPORTANT_RE.search(x) or CODE_RE.search(x)]
        return "\n".join((lines[:1]+important[:8]+lines[-1:]))
