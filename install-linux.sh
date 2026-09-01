#!/usr/bin/env bash
set -euo pipefail
REPO="${MEECHRTK_REPO:-https://github.com/3ighty6/meechrtk.git}"
DIR="${MEECHRTK_DIR:-$HOME/meechrtk}"

echo "== MeechRTK Universal Token Governor installer =="
command -v python3 >/dev/null || { echo "Python 3 is required."; exit 1; }
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull --ff-only
else
  git clone "$REPO" "$DIR"
fi
cd "$DIR"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/meechrtk.service" <<EOF
[Unit]
Description=MeechRTK Universal Token Governor
After=network.target

[Service]
Type=simple
WorkingDirectory=$DIR
ExecStart=$DIR/.venv/bin/python -m meechrtk
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now meechrtk.service
sleep 1
curl -fsS http://127.0.0.1:8765/health
printf '\n\nMeechRTK gateway is running at http://127.0.0.1:8765\n'
printf 'Firefox extension: %s/extension/manifest.json\n' "$DIR"
