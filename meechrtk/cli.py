"""Command-line interface for MeechRTK."""

from __future__ import annotations

import subprocess
import sys

from .compressor import compress

USAGE = "usage: meechrtk [--stdin] [--exact] <command> [args...]"

# meechrtk's own flags, only recognized while they appear before the
# wrapped command starts. Anything after that -- including things
# that look like flags, e.g. `tsc -b` or `npm run build --verbose` --
# is passed through untouched. A naive argparse setup here would try
# to interpret the wrapped command's own flags as meechrtk's, which
# breaks on basically any real command that takes options.
OWN_FLAGS = {"--stdin", "--exact", "-h", "--help"}


def main() -> int:
    argv = sys.argv[1:]

    use_stdin = False
    exact = False
    i = 0
    while i < len(argv) and argv[i] in OWN_FLAGS:
        flag = argv[i]
        if flag in ("-h", "--help"):
            print(USAGE)
            return 0
        if flag == "--stdin":
            use_stdin = True
        elif flag == "--exact":
            exact = True
        i += 1

    command = argv[i:]

    if use_stdin:
        text = sys.stdin.read()
    elif command:
        completed = subprocess.run(command, text=True, capture_output=True)
        text = completed.stdout
        if completed.stderr:
            text += completed.stderr
        if completed.returncode:
            text += f"\n[MeechRTK exit code: {completed.returncode}]\n"
    else:
        print(USAGE, file=sys.stderr)
        print("error: provide a command or use --stdin", file=sys.stderr)
        return 2

    result = compress(text, exact=exact)
    sys.stdout.write(result.compressed)
    if not exact:
        print(
            f"\n[MeechRTK: {result.original_bytes} → {result.compressed_bytes} bytes; "
            f"{result.savings_ratio:.1%} output reduction]",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
