from pathlib import Path

path = Path("tools/run_mql5_to_python_translation_agent.py")
text = path.read_text(encoding="utf-8")

start = text.index("def build_prompt(context: str) -> str:")
end = text.index("\n\ndef call_ollama", start)

new_prompt = r'''def build_prompt(context: str) -> str:
    return f"""
TASK: Convert the provided MQL5 Expert Advisor logic into Python.

OUTPUT RULES:
Return ONLY valid JSON.
Do not explain.
Do not summarize.
Do not write markdown.
Do not say what the code appears to be.
Do not provide MQL4 examples.
Do not provide pseudo-code.

Required JSON schema:
{{
  "translation_summary": ["short item"],
  "source_unresolved": ["short item"],
  "assumptions": ["short item"],
  "python_code": "complete Python code as one string"
}}

python_code requirements:
- Must define class StrategyModel.
- Must implement:
  - __init__(self, params: dict)
  - on_start(self, price: float) -> None
  - on_bar(self, price: float, bar_index: int) -> None
  - get_positions(self) -> list[dict]
  - get_events(self) -> list[dict]
  - get_metrics_snapshot(self) -> dict
- Use only standard Python.
- No pandas, numpy, files, network, subprocess.
- If an MQL5 rule is unclear, put TODO_SOURCE_UNRESOLVED inside python_code.
- Positions must be dicts with side, lot, open_price, tag.
- Events must be dicts with event_type, price, bar_index, details.

CONTEXT:
{context}
""".strip()
'''

text = text[:start] + new_prompt + text[end:]
path.write_text(text, encoding="utf-8")
print("[OK] prompt patched")
