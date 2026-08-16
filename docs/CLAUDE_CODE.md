# MeechRTK + Claude Code

The PostToolUse hook creates the real interception path:

Claude Code → Bash → raw output → MeechRTK → compact output → Claude Code

## Windows install

1. Install Python 3.10+.
2. Clone the repo:

```powershell
git clone https://github.com/3ighty6/meechrtk.git
cd meechrtk
```

3. Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

4. Restart Claude Code.
5. Run `/hooks` and verify a `PostToolUse` hook matching `Bash` exists.

## What it does

After a Bash tool call, MeechRTK removes consecutive repetitive lines, preserves error/warning evidence, reports byte reduction, and saves the raw output under `%TEMP%\meechrtk\raw\`.

The hook fails open: if the optimizer errors, the original tool result is not intentionally replaced.

## Important limitation

This integration is for **Claude Code**, where local tool hooks are available. It does not intercept terminal output in the normal claude.ai web chat.
