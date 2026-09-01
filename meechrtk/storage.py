from __future__ import annotations
import sqlite3, time, uuid
from pathlib import Path
from .governor import DB

class Store:
    def __init__(self, db=DB):
        self.db=Path(db); self.db.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.db) as c:
            c.execute("create table if not exists events (id text primary key, provider text, project text, original_tokens integer, optimized_tokens integer, reduction real, coverage real, quality_label text, created real)")
            c.execute("create index if not exists idx_events_created on events(created)")
    def record(self,result,quality_label=None):
        with sqlite3.connect(self.db) as c:
            c.execute("insert into events values(?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),result.get('provider'),result.get('project'),result.get('original_tokens',0),result.get('optimized_tokens',0),result.get('reduction',0),result.get('information_coverage',0),quality_label,time.time()))
    def summary(self,days=30):
        cutoff=time.time()-days*86400
        with sqlite3.connect(self.db) as c:
            r=c.execute("select count(*),coalesce(sum(original_tokens),0),coalesce(sum(optimized_tokens),0),coalesce(avg(reduction),0),sum(case when quality_label='failure' then 1 else 0 end) from events where created>=?",(cutoff,)).fetchone()
        n,orig,opt,avg_red,fail=r
        return {'requests_optimized':n,'original_tokens':orig,'optimized_tokens':opt,'tokens_saved':max(0,orig-opt),'average_reduction_percent':round(avg_red,2),'quality_failures':fail or 0}
