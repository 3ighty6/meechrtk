$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$claude = Join-Path $HOME ".claude"
$dest = Join-Path $claude "meechrtk"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item (Join-Path $repo "hooks\claude_posttool.py") (Join-Path $dest "claude_posttool.py") -Force
$settings = Join-Path $claude "settings.json"
if (Test-Path $settings) { $cfg = Get-Content $settings -Raw | ConvertFrom-Json } else { $cfg = [pscustomobject]@{} }
if (-not $cfg.PSObject.Properties["hooks"]) { $cfg | Add-Member NoteProperty hooks ([pscustomobject]@{}) }
if (-not $cfg.hooks.PSObject.Properties["PostToolUse"]) { $cfg.hooks | Add-Member NoteProperty PostToolUse @() }
$hook = [pscustomobject]@{ matcher = "Bash"; hooks = @([pscustomobject]@{ type = "command"; command = "python `"$dest\claude_posttool.py`""; timeout = 30 }) }
$exists = @($cfg.hooks.PostToolUse | Where-Object { $_.hooks -and (($_.hooks | ConvertTo-Json -Compress) -match "claude_posttool.py") }).Count -gt 0
if (-not $exists) { $cfg.hooks.PostToolUse = @($cfg.hooks.PostToolUse) + $hook }
$cfg | ConvertTo-Json -Depth 20 | Set-Content $settings -Encoding UTF8
Write-Host "MeechRTK Claude Code hook installed. Restart Claude Code and run /hooks to verify."