from __future__ import annotations
import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from .governor import TokenGovernor
from .policy import PolicyEngine
from .storage import Store
from .learning import GuidanceLearner
from .providers import get_adapter
from .capacity import CapacityManager

HOST,PORT="127.0.0.1",8765
GOV,POLICY,STORE,LEARNER,CAPACITY=TokenGovernor(),PolicyEngine(),Store(),GuidanceLearner(),CapacityManager()
class Handler(BaseHTTPRequestHandler):
 def _send(self,status,obj):
  body=json.dumps(obj).encode();self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(body)));self.send_header("Access-Control-Allow-Origin","*");self.send_header("Access-Control-Allow-Headers","Content-Type");self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS");self.end_headers();
  if status!=204:self.wfile.write(body)
 def _json(self):
  n=int(self.headers.get("Content-Length",0));return json.loads(self.rfile.read(n) or b"{}")
 def do_OPTIONS(self):self._send(204,{})
 def do_GET(self):
  u=urlparse(self.path);p=u.path
  if p=="/health":return self._send(200,{"ok":True,"service":"meechrtk-gateway","version":"1.1.0"})
  if p=="/v1/metrics":return self._send(200,{"ok":True,"metrics":STORE.summary()})
  if p=="/v1/policy":
   request=parse_qs(u.query).get("request",[""])[0];return self._send(200,{"ok":True,"policy":asdict(POLICY.classify(request))})
  if p=="/v1/providers":return self._send(200,{"ok":True,"providers":{k:asdict(v.capabilities) for k,v in __import__('meechrtk.providers',fromlist=['ADAPTERS']).ADAPTERS.items()}})
  if p=="/v1/capacity":return self._send(200,{"ok":True,"providers":CAPACITY.snapshot()})
  return self._send(404,{"ok":False,"error":"not found"})
 def do_POST(self):
  p=urlparse(self.path).path
  try:
   data=self._json()
   if p=="/v1/optimize":
    request=str(data.get("request","")).strip()
    if not request:return self._send(400,{"ok":False,"error":"request is required"})
    provider=str(data.get("provider","auto"));policy=POLICY.classify(request,provider,bool(data.get("stable_prefix")));budget=data.get("budget",policy.context_mode)
    result=GOV.optimize(request,str(data.get("context","")),budget,provider,data.get("project","default"),int(data.get("max_tokens",16000)))
    result["policy"]=asdict(policy);result["provider_capabilities"]=asdict(get_adapter(provider).capabilities);STORE.record(result)
    return self._send(200,{"ok":True,"result":result})
   if p=="/v1/route":
    request=str(data.get("request","")).strip()
    if not request:return self._send(400,{"ok":False,"error":"request is required"})
    return self._send(200,CAPACITY.route(request,int(data.get("required_tokens",0)),data.get("preferred"),bool(data.get("local_ok",True)),data.get("budget_usd")))
   if p=="/v1/capacity/configure":
    provider=str(data.get("provider","")).strip()
    if not provider:return self._send(400,{"ok":False,"error":"provider is required"})
    allowed={k:v for k,v in data.items() if k in {"context_window","reasoning_levels","cache_input","configured","available","tokens_remaining","tokens_used","cost_per_million_input","latency_ms"}}
    return self._send(200,{"ok":True,"provider":CAPACITY.configure(provider,**allowed)})
   if p=="/v1/capacity/usage":
    provider=str(data.get("provider","")).strip();tokens=int(data.get("tokens",0));CAPACITY.record_usage(provider,tokens,float(data.get("cost",0)),data.get("latency_ms"));return self._send(200,{"ok":True,"provider":asdict(CAPACITY.states[provider])})
   if p=="/v1/memory":
    text=str(data.get("text","")).strip()
    if not text:return self._send(400,{"ok":False,"error":"text is required"})
    mid=GOV.memory.add(text,data.get("project","default"),data.get("kind","fact"),float(data.get("importance",.7)));return self._send(200,{"ok":True,"id":mid})
   if p=="/v1/feedback":
    f=data.get("features",[]);label=float(data.get("label",0))
    if len(f)!=5 or label not in (0.,1.):return self._send(400,{"ok":False,"error":"features must contain 5 values and label must be 0 or 1"})
    return self._send(200,{"ok":True,"model":LEARNER.update([float(x) for x in f],label)})
   return self._send(404,{"ok":False,"error":"not found"})
  except Exception as e:return self._send(500,{"ok":False,"error":str(e)})
 def log_message(self,*args):pass
def main():print(f"MeechRTK Token Governor listening on http://{HOST}:{PORT}",flush=True);ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
if __name__=="__main__":main()
