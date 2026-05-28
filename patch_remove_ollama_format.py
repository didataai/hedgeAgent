from pathlib import Path

path = Path("tools/run_mql5_to_python_translation_agent.py")
text = path.read_text(encoding="utf-8")

text = text.replace(', "format": "json"', '')

path.write_text(text, encoding="utf-8")
print("[OK] removed Ollama format=json")
