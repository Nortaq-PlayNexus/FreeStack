#!/usr/bin/env bash
# ollama-setup.sh - self-host open LLMs on your free VM. Run ON the VM (07).
# Result: a private OpenAI-compatible API at http://<vm-ip>:11434 with ZERO quotas.
set -euo pipefail

if ! command -v docker >/dev/null; then
  echo ">> installing Docker (see 07-Cloud-VMs-Compute if this fails)..."
  curl -fsSL https://get.docker.com | sh
fi

if command -v ollama >/dev/null; then
  echo ">> ollama already installed"
else
  echo ">> installing ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi

# default models: a strong small + a chat + an embeddings model for RAG (14)
MODELS="${MODELS:-llama3.2:3b nomic-embed-text}"
for m in $MODELS; do
  ollama pull "$m"
done

# serve on 0.0.0.0:11434 (or via the tunnel from 03 for a public endpoint)
systemctl enable --now ollama || true
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0:11434"\n' | \
  sudo tee /etc/systemd/system/ollama.service.d/host.conf >/dev/null
sudo systemctl daemon-reload && sudo systemctl restart ollama

echo ""
echo "   Ollama ready: http://localhost:11434  (OpenAI-compatible: /v1/chat/completions)"
echo "   Test:  curl http://localhost:11434/v1/chat/completions -d '{\"model\":\"llama3.2\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}'"
echo "   Public: ssh -R 11434:localhost:11434 root@yourname.is-a.dev  (see 03)"
echo "   Wire the router (05/llm_router.py) to it via OLLAMA_BASE_URL=http://localhost:11434"
