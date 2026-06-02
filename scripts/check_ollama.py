from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.generation.ollama_client import OllamaClient


def main() -> int:
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
    num_ctx = int(os.environ.get("OLLAMA_NUM_CTX", "8192"))
    client = OllamaClient(base_url=base_url, model=model, num_ctx=num_ctx)
    status = client.status()

    print(f"OLLAMA_BASE_URL={base_url}")
    print(f"OLLAMA_MODEL={model}")
    print(f"OLLAMA_NUM_CTX={num_ctx}")

    if not status.available:
        print("Ollama server status: unavailable")
        print(status.error or "Could not reach Ollama.")
        print("Start it with: ollama serve")
        print(f"Then warm the model with: ollama run {model}")
        return 0

    print("Ollama server status: available")
    print(f"Installed models: {', '.join(status.models) if status.models else '(none)'}")
    if status.model_available:
        print(f"Model '{model}' is available.")
        print(f"Run it with: ollama run {model}")
    else:
        print(f"Model '{model}' is missing.")
        print(f"Pull it with: ollama pull {model}")
        print(f"Run it with: ollama run {model}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
