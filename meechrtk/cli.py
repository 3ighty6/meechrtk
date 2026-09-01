"""MeechRTK CLI: legacy output compression plus Token Governor."""
from __future__ import annotations
import argparse, json, subprocess, sys
from .compressor import compress
from .governor import TokenGovernor

def main() -> int:
    p=argparse.ArgumentParser(prog="meechrtk")
    sub=p.add_subparsers(dest="cmd")
    g=sub.add_parser("govern", help="select minimum useful context")
    g.add_argument("request")
    g.add_argument("--context", default="")
    g.add_argument("--budget", choices=["minimal","efficient","balanced","deep","maximum"], default="balanced")
    g.add_argument("--provider", default="auto")
    g.add_argument("--project", default="default")
    g.add_argument("--max-tokens", type=int, default=16000)
    c=sub.add_parser("compress", help="legacy deterministic output compressor")
    c.add_argument("--stdin", action="store_true")
    c.add_argument("--exact", action="store_true")
    c.add_argument("command", nargs=argparse.REMAINDER)
    args=p.parse_args()
    if args.cmd=="govern":
        result=TokenGovernor().optimize(args.request,args.context,args.budget,args.provider,args.project,args.max_tokens)
        print(json.dumps(result,indent=2)); return 0
    if args.cmd=="compress":
        if args.stdin: text=sys.stdin.read()
        elif args.command:
            cp=subprocess.run(args.command,text=True,capture_output=True); text=cp.stdout+cp.stderr
            if cp.returncode: text+=f"\n[MeechRTK exit code: {cp.returncode}]\n"
        else: p.error("compress requires --stdin or a command")
        r=compress(text,exact=args.exact); sys.stdout.write(r.compressed); return 0
    p.print_help(); return 0

if __name__=="__main__": raise SystemExit(main())
