from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .governor import TokenGovernor
from .policy import PolicyEngine
from .storage import Store
from .learning import GuidanceLearner

HOST, PORT = "127.0.0.1", 8765
GOV, POLICY, STORE, LEARNER = TokenGovernor(), PolicyEngine(), Store(), GuidanceLearner()

class Handler(BaseHTTPRequestHandler):
    def _send(self,status,obj):
        body=json.dumps(obj).encode(); self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(body)))
        self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type"); self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS"); self.end_headers()
        if status!=204:self.wfile.write(body)
    def _json(self):
        n=int(self.headers.get("Content-Length",0)); return json.loads(self.rfile.read(n) or b"{}")
    def do_OPTIONS(self): self._send(204,{})
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/health": return self._send(200,{"ok":True,"service":"meechrtk-gateway","version":"1.0.0"})
        if path=="/v1/metrics": return self._send(200,{"ok":True,"metrics":STORE.summary()})
        if path=="/v1/policy":
            q=urlparse(self.path).query; request=q.split("request=",1)[1] if "request=" in q else ""; return self._send(200,{"ok":True,"policy":POLICY.classify(request)})
        return self._send(404,{"ok":False,"error":"not found"})
    def do_POST(self):
        path=urlparse(self.path).path
        try:
            data=self._json()
            if path=="/v1/optimize":
                request=str(data.get("request","")).strip()
                if not request:return self._send(400,{"ok":False,"error":"request is required"})
                provider=data.get("provider","auto"); stable=bool(data.get("stable_prefix"))
                policy=POLICY.classify(request,provider,stable)
                budget=data.get("budget",policy.context_mode)
                result=GOV.optimize(request,str(data.get("context","")),budget,provider,data.get("project","default"),int(data.get("max_tokens",16000)))
                result["policy"]={"complexity":policy.complexity,"context_mode":policy.context_mode,"response_budget":policy.response_budget,"reasoning":policy.reasoning,"cache_action":policy.cache_action}
                STORE.record(result)
                return self._send(200,{"ok":True,"result":result})
            if path=="/v1/memory":
                text=str(data.get("text","")).strip()
                if not text:return self._send(400,{"ok":False,"error":"text is required"})
                mid=GOV.memory.add(text,data.get("project","default"),data.get("kind","fact"),float(data.get("importance",0.7)))
                return self._send(200,{"ok":True,"id":mid})
            if path=="/v1/feedback":
                features=data.get("features",[]); label=float(data.get("label",0))
                if len(features)!=5 or label not in (0.0,1.0):return self._send(400,{"ok":False,"error":"features must contain 5 values and label must be 0 or 1"})
                return self._send(200,{"ok":True,"model":LEARNER.update([float(x) for x in features],label)})
            return self._send(404,{"ok":False,"error":"not found"})
        except Exception as e:return self._send(500,{"ok":False,"error":str(e)})
    def log_message(self,*args): pass

def main():
    print(f"MeechRTK Token Governor listening on http://{HOST}:{PORT}",flush=True)
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()

if __name__=="__main__":main()
