from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .governor import TokenGovernor

HOST, PORT = "127.0.0.1", 8765
GOV = TokenGovernor()

class Handler(BaseHTTPRequestHandler):
    def _send(self, status, obj):
        body=json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS")
        self.end_headers(); self.wfile.write(body)
    def do_OPTIONS(self): self._send(204,{})
    def do_GET(self):
        if self.path=="/health": self._send(200,{"ok":True,"service":"meechrtk-gateway","version":"1.0.0"})
        else: self._send(404,{"ok":False,"error":"not found"})
    def do_POST(self):
        if self.path!="/v1/optimize": return self._send(404,{"ok":False,"error":"not found"})
        try:
            n=int(self.headers.get("Content-Length",0)); data=json.loads(self.rfile.read(n) or b"{}")
            if not data.get("request"): return self._send(400,{"ok":False,"error":"request is required"})
            result=GOV.optimize(data["request"],data.get("context", ""),data.get("budget",0.6),data.get("provider","auto"),data.get("project","default"),int(data.get("max_tokens",16000)))
            self._send(200,{"ok":True,"result":result})
        except Exception as e: self._send(500,{"ok":False,"error":str(e)})
    def log_message(self,*args): pass

def main():
    print(f"MeechRTK Token Governor listening on http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()

if __name__=="__main__": main()
