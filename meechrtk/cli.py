"""Command-line interface for MeechRTK."""

from __future__ import annotations

import argparse
import subprocess
import sys

from .compressor import compress


def main() -> int:
    parser = argparse.ArgumentParser(description="MeechRTK — safe AI context compression")
    parser.add_argument("command", nargs="*", help="command to execute")
    parser.add_argument("--stdin", action="store_true", help="compress stdin instead of running a command")
    parser.add_argument("--exact", action="store_true", help="disable compression")
    args = parser.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    elif args.command:
        completed = subprocess.run(args.command, text=True, capture_output=True)
        text = completed.stdout
        if completed.stderr:
            text += completed.stderr
        if completed.returncode:
            text += f"\n[MeechRTK exit code: {completed.returncode}]\n"
    else:
        parser.error("provide a command or use --stdin")

    result = compress(text, exact=args.exact)
    sys.stdout.write(result.compressed)
    if not args.exact:
        print(
            f"\n[MeechRTK: {result.original_bytes} → {result.compressed_bytes} bytes; "
            f"{result.savings_ratio:.1%} output reduction]",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
