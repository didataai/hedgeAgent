import json
from pathlib import Path

path = Path("config/hedge_agent_config.json")
data = json.loads(path.read_text(encoding="utf-8"))

llm = data.setdefault("llm", {})
active = llm.get("active_profile", "local_ollama_qwen25_7b")
profile = llm.setdefault("profiles", {}).setdefault(active, {})

profile["timeout_seconds"] = 300
profile["max_context_chars"] = 8000
profile["temperature"] = 0.0
profile["top_p"] = 0.7

path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("[OK] config patched for smaller strict prompt")
