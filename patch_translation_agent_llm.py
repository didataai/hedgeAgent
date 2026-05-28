from pathlib import Path

path = Path("tools/run_mql5_to_python_translation_agent.py")
text = path.read_text(encoding="utf-8")

# 1) Remove format=json do payload Ollama.
text = text.replace(
'''        "stream": False,
        "format": "json",
        "options": {''',
'''        "stream": False,
        "options": {'''
)

# 2) Substitui parse_llm por parser mais tolerante.
start = text.index("def parse_llm(raw: str) -> dict[str, Any]:")
end = text.index("\n\ndef scaffold_code", start)

new_parse = r'''def parse_llm(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()

    # Remove code fences comuns.
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    # Se o modelo colocou texto antes/depois, tenta extrair o primeiro JSON.
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first >= 0 and last > first:
        cleaned = cleaned[first:last + 1]

    data = json.loads(cleaned)

    required = ("translation_summary", "source_unresolved", "assumptions", "python_code")
    for key in required:
        if key not in data:
            raise ValueError(f"LLM JSON sem chave obrigatória: {key}")

    if not isinstance(data["python_code"], str):
        raise ValueError("python_code não é string")

    if "class StrategyModel" not in data["python_code"]:
        raise ValueError("python_code não contém class StrategyModel")

    return data
'''

text = text[:start] + new_parse + text[end:]

path.write_text(text, encoding="utf-8")
print("[OK] patched", path)
