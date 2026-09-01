#!/usr/bin/env bash
set -euo pipefail
REPO="${MEECHRTK_REPO:-https://github.com/3ighty6/meechrtk.git}"
DIR="${MEECHRTK_DIR:-$HOME/meechrtk}"
ENV_DIR="$HOME/.config/meechrtk"
ENV_FILE="$ENV_DIR/providers.env"
echo "== MeechRTK Universal Token Governor installer =="
command -v python3 >/dev/null || { echo "Python 3 is required."; exit 1; }
python3 -m venv /tmp/meechrtk-venv-test >/dev/null 2>&1 || { echo "Installing Python venv support..."; sudo apt install -y python3-venv; }
rm -rf /tmp/meechrtk-venv-test
if [ -d "$DIR/.git" ]; then git -C "$DIR" pull --ff-only origin main; else git clone "$REPO" "$DIR"; fi
cd "$DIR"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
mkdir -p "$ENV_DIR" "$HOME/.config/systemd/user"
if [ ! -f "$ENV_FILE" ]; then
cat > "$ENV_FILE" <<'EOF'
# Add API keys here, then restart: systemctl --user restart meechrtk.service
# ANTHROPIC_API_KEY=
# OPENAI_API_KEY=
# XAI_API_KEY=
# GEMINI_API_KEY=
# OPENROUTER_API_KEY=
MEECHRTK_OLLAMA_MODEL=qwen3:1.7b
MEECHRTK_LMSTUDIO_MODEL=local-model
EOF
chmod 600 "$ENV_FILE"
fi
cat > "$HOME/.config/systemd/user/meechrtk.service" <<EOF
[Unit]
Description=MeechRTK Universal Token Governor
After=network.target

[Service]
Type=simple
WorkingDirectory=$DIR
ExecStart=$DIR/.venv/bin/python -m meechrtk
Restart=on-failure
RestartSec=2
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-$ENV_FILE

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now meechrtk.service
loginctl enable-linger "$USER" >/dev/null 2>&1 || true
sleep 2
curl -fsS http://127.0.0.1:8765/health
printf '\nMeechRTK gateway is running at http://127.0.0.1:8765\n'
printf 'Firefox extension directory: %s/extension\n' "$DIR"
printf 'Provider config: %s\n' "$ENV_FILE"
printf 'Load extension at about:debugging#/runtime/this-firefox using extension/manifest.json\n'
