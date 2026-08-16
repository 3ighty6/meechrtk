import json
import os
import re
import sys
from pathlib import Path

IMPORTANT = re.compile(r"\b(error|fatal|failed|failure|exception|traceback|warning|warn|denied|unauthorized|forbidden|not found|cannot|could not|exit code|status code|npm ERR|ERR!)\b", re.I)


def compact(text: str, repeat_limit: int = 2) -> str:
    lines = text.splitlines()
    out = []
    previous = None
    repeats = 0
    for line in lines:
        normalized = re.sub(r"\s+", " ", line.strip())
        if normalized and normalized == previous and not IMPORTANT.search(line):
            repeats += 1
            if repeats <= repeat_limit:
                out.append(line)
            elif repeats == repeat_limit + 1:
                out.append(f"… [MeechRTK suppressed repeated output; {repeat_limit} shown] …")
        else:
            previous = normalized if normalized else previous
            repeats = 0
            out.append(line)
    return "\n".join(out)


def main():
    try:
        event = json.load(sys.stdin)
        if event.get("tool_name") != "Bash":
            return
        response = event.get("tool_response") or {}
        if not isinstance(response, dict) or response.get("isImage"):
            return
        stdout = response.get("stdout") or ""
        stderr = response.get("stderr") or ""
        original = stdout + ("\n" if stdout and stderr else "") + stderr
        if not original.strip():
            return
        command = ((event.get("tool_input") or {}).get("command") or "").strip().lower()
        if any(command.startswith(x) for x in ("cat ", "type ", "get-content ", "xxd ", "hexdump", "base64")):
            return
        new_stdout = compact(stdout)
        new_stderr = compact(stderr)
        before = len(original.encode("utf-8"))
        after_text = new_stdout + ("\n" if new_stdout and new_stderr else "") + new_stderr
        after = len(after_text.encode("utf-8"))
        session = event.get("session_id", "unknown")
        raw_dir = Path(os.environ.get("TEMP", ".")) / "meechrtk" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_file = raw_dir / f"{session}-{event.get('tool_use_id','tool')}.txt"
        raw_file.write_text(original, encoding="utf-8")
        reduction = (1 - after / before) if before else 0
        updated = dict(response)
        updated["stdout"] = new_stdout
        updated["stderr"] = new_stderr + f"\n[MeechRTK: {before:,} → {after:,} bytes; {reduction:.1%} output reduction; raw: {raw_file}]\n"
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedToolOutput": updated, "additionalContext": "MeechRTK compressed repetitive Bash output. Errors, warnings and exact evidence were preserved; inspect the raw path if more detail is needed."}}))
    except Exception as exc:
        print(f"MeechRTK hook bypassed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
