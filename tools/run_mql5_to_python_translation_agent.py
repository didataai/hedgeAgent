#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hedgeAgent - MQL5 -> Python Translation Agent v1.3 block-first

- Não envia o EA inteiro para a LLM.
- Extrai inputs e funções/blocos importantes.
- Monta prompt menor para gerar StrategyModel.
- Se a LLM falhar, gera scaffold determinístico validável.
"""

from __future__ import annotations

import argparse
import json
import re
import textwrap
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_METHODS = ["__init__", "on_start", "on_bar", "get_positions", "get_events", "get_metrics_snapshot"]

IMPORTANT_NAMES = [
    "OnInit", "OnDeinit", "OnTick", "OnTimer", "OnChartEvent",
    "OpenPosition", "ClosePosition", "CloseAllOurPositionsAndReset",
    "CountOurPositions", "GetPointsProfit", "GetProfit", "IsTriggered",
    "PositionExists", "AtualizarResumoNoGrafico",
]

KEYWORDS = [
    "OrderSend", "trade.", "Position", "GlobalVariable", "EA_State", "EA_Direction",
    "HedgeSmallLot", "HedgeLargeLot", "LotIncrease", "ExtraLotIncreaseOnRange",
    "RangeThresholdPts", "OpenPosition", "ClosePosition", "GetProfit", "IsTriggered",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            pass
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config(path: Path | None) -> dict[str, Any]:
    if path and path.exists():
        return read_json(path)
    return {
        "llm": {
            "active_profile": "local_ollama_qwen25_7b",
            "profiles": {
                "local_ollama_qwen25_7b": {
                    "provider": "ollama",
                    "model": "qwen2.5:7b-instruct",
                    "base_url": "http://localhost:11434",
                    "temperature": 0.1,
                    "top_p": 0.7,
                    "timeout_seconds": 300,
                    "max_context_chars": 8000,
                }
            },
        }
    }


def get_profile(config: dict[str, Any]) -> dict[str, Any]:
    llm = config.get("llm", {})
    active = llm.get("active_profile")
    profiles = llm.get("profiles", {})
    if active in profiles:
        profile = dict(profiles[active])
        profile["active_profile"] = active
        return profile
    return {
        "active_profile": active or "legacy",
        "provider": llm.get("provider", "ollama"),
        "model": llm.get("model", "qwen2.5:7b-instruct"),
        "base_url": llm.get("base_url", "http://localhost:11434"),
        "temperature": llm.get("temperature", 0.1),
        "top_p": llm.get("top_p", 0.7),
        "timeout_seconds": llm.get("timeout_seconds", 300),
        "max_context_chars": llm.get("max_context_chars", 8000),
    }


def find_version(spec: dict[str, Any], version_id: str) -> dict[str, Any]:
    for version in spec.get("versions", []):
        if version.get("version_id") == version_id:
            return version
    raise ValueError(f"version_id não encontrado no spec: {version_id}")


def get_float(version: dict[str, Any], name: str, default: float) -> float:
    try:
        params = version.get("parameter_candidates", {})
        value = params.get(name, {}).get("default", default)
        return float(str(value).replace('"', "").strip())
    except Exception:
        return default


def extract_inputs(source: str) -> list[dict[str, str]]:
    pattern = re.compile(r"^\s*input\s+([A-Za-z_][\w\s\*&<>:]*)\s+([A-Za-z_]\w*)\s*=\s*([^;]+);(?://\s*(.*))?", re.MULTILINE)
    rows = []
    for m in pattern.finditer(source):
        rows.append({"type": m.group(1).strip(), "name": m.group(2).strip(), "default": m.group(3).strip(), "comment": (m.group(4) or "").strip()})
    return rows


def find_function_start(source: str, name: str) -> int:
    pattern = re.compile(r"(^|\n)\s*(?:void|int|double|bool|long|ulong|string|datetime|ENUM_\w+|[A-Za-z_]\w*)\s+" + re.escape(name) + r"\s*\(", re.MULTILINE)
    m = pattern.search(source)
    return -1 if not m else m.start()


def extract_function_block(source: str, name: str, max_chars: int = 9000) -> str | None:
    start = find_function_start(source, name)
    if start < 0:
        return None
    brace = source.find("{", start)
    if brace < 0:
        return source[start:start + max_chars]
    depth = 0
    for i in range(brace, len(source)):
        ch = source[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[start:i + 1][:max_chars]
    return source[start:start + max_chars]


def extract_candidate_blocks(source: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for name in IMPORTANT_NAMES:
        block = extract_function_block(source, name)
        if block:
            blocks[name] = block

    func_pattern = re.compile(r"(^|\n)\s*(?:void|int|double|bool|long|ulong|string|datetime|ENUM_\w+|[A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
    for m in func_pattern.finditer(source):
        name = m.group(2)
        if name in blocks:
            continue
        block = extract_function_block(source, name, max_chars=6000)
        if not block:
            continue
        if any(k in block for k in KEYWORDS):
            blocks[name] = block
        if len(blocks) >= 18:
            break
    return blocks


def build_block_context(family_id: str, version_id: str, spec: dict[str, Any], version: dict[str, Any], source_path: Path, source: str, analysis: dict[str, Any] | None, max_chars: int) -> tuple[str, dict[str, Any]]:
    inputs = extract_inputs(source)
    blocks = extract_candidate_blocks(source)
    selected = []
    total = 0
    for name, block in blocks.items():
        chunk = f"\n\n// === FUNCTION {name} ===\n{block}"
        if total + len(chunk) > max_chars:
            continue
        selected.append(chunk)
        total += len(chunk)

    compact_spec = {
        "family_id": family_id,
        "version_id": version_id,
        "source_file": version.get("source_file"),
        "description": version.get("description"),
        "states": spec.get("states", []),
        "transitions": spec.get("transitions", []),
        "entities": spec.get("entities", []),
        "parameter_candidates": version.get("parameter_candidates", {}),
    }
    inventory = {"inputs_count": len(inputs), "selected_functions": list(blocks.keys()), "selected_chars": total, "source_path": str(source_path)}
    context = "\n".join([
        f"# Block Translation Context {family_id}/{version_id}",
        "",
        "## Spec compacto",
        json.dumps(compact_spec, ensure_ascii=False, indent=2),
        "",
        "## Inputs extraídos do MQL5",
        json.dumps(inputs, ensure_ascii=False, indent=2),
        "",
        "## Análise estática resumida",
        json.dumps(analysis or {}, ensure_ascii=False, indent=2)[:12000],
        "",
        "## Blocos MQL5 selecionados",
        "```mql5",
        "".join(selected),
        "```",
    ])
    return context, inventory


def build_prompt(context: str) -> str:
    return f"""
TASK: Convert MQL5 EA blocks into one Python StrategyModel.

Return ONLY valid JSON. No markdown. No explanation outside JSON.

JSON schema:
{{
  "translation_summary": ["short item"],
  "source_unresolved": ["short item"],
  "assumptions": ["short item"],
  "python_code": "complete Python code as a single string"
}}

python_code must:
- define class StrategyModel
- implement __init__, on_start, on_bar, get_positions, get_events, get_metrics_snapshot
- use only standard Python
- not use files, network, subprocess, pandas, numpy
- store positions as dicts with side, lot, open_price, tag
- store events as dicts with event_type, price, bar_index, details
- preserve MQL5 logic as much as possible
- mark unclear rules as TODO_SOURCE_UNRESOLVED

Context:
{context}
""".strip()


def call_ollama(prompt: str, profile: dict[str, Any]) -> str:
    base_url = str(profile.get("base_url", "http://localhost:11434")).rstrip("/")
    payload = {"model": str(profile.get("model", "qwen2.5:7b-instruct")), "prompt": prompt, "stream": False, "options": {"temperature": float(profile.get("temperature", 0.1)), "top_p": float(profile.get("top_p", 0.7))}}
    request = urllib.request.Request(f"{base_url}/api/generate", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    timeout = int(profile.get("timeout_seconds", 300))
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc
    raw = data.get("response")
    if not isinstance(raw, str):
        raise RuntimeError("Ollama response sem campo string 'response'")
    return raw


def parse_llm(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first >= 0 and last > first:
        cleaned = cleaned[first:last + 1]
    data = json.loads(cleaned)
    for key in ("translation_summary", "source_unresolved", "assumptions", "python_code"):
        if key not in data:
            raise ValueError(f"LLM JSON sem chave obrigatória: {key}")
    if "class StrategyModel" not in data["python_code"]:
        raise ValueError("python_code não contém class StrategyModel")
    return data


def scaffold_code(family_id: str, version_id: str, version: dict[str, Any]) -> str:
    small = get_float(version, "HedgeSmallLot", 0.03)
    large = get_float(version, "HedgeLargeLot", 0.04)
    lot_inc = get_float(version, "LotIncrease", 0.01)
    directional = get_float(version, "DirectionalLot", max(0.01, large - small + lot_inc))
    range_pts = get_float(version, "RangeThresholdPts", 400.0)
    stop_usd = get_float(version, "StopThresholdUSD", -8.0)
    return textwrap.dedent(f'''
    # -*- coding: utf-8 -*-
    from __future__ import annotations

    class StrategyModel:
        def __init__(self, params: dict):
            self.params = dict(params or {{}})
            self.family_id = {family_id!r}
            self.version_id = {version_id!r}
            self.small_lot = float(self.params.get("HedgeSmallLot", {small!r}))
            self.large_lot = float(self.params.get("HedgeLargeLot", {large!r}))
            self.lot_increase = float(self.params.get("LotIncrease", {lot_inc!r}))
            self.directional_lot = float(self.params.get("DirectionalLot", {directional!r}))
            self.range_threshold_points = float(self.params.get("RangeThresholdPts", {range_pts!r}))
            self.stop_threshold_usd = float(self.params.get("StopThresholdUSD", {stop_usd!r}))
            self.money_per_point_per_lot = float(self.params.get("money_per_point_per_lot", 1.0))
            self.started = False
            self.initial_price = None
            self.state = "S0_EMPTY_OR_RESET"
            self.positions = []
            self.events = []
            self.realized_pnl = 0.0

        def _event(self, event_type: str, price: float, bar_index: int, details: dict | None = None) -> None:
            self.events.append({{"event_type": event_type, "price": float(price), "bar_index": int(bar_index), "state": self.state, "details": details or {{}}}})

        def _open_position(self, side: str, lot: float, price: float, tag: str) -> None:
            self.positions.append({{"side": side, "lot": float(lot), "open_price": float(price), "tag": tag}})

        def _position_pnl(self, pos: dict, price: float) -> float:
            direction = 1.0 if pos["side"] == "BUY" else -1.0
            return (float(price) - pos["open_price"]) * direction * pos["lot"] * self.money_per_point_per_lot

        def _floating_pnl(self, price: float) -> float:
            return sum(self._position_pnl(pos, price) for pos in self.positions)

        def on_start(self, price: float) -> None:
            if self.started:
                return
            self.started = True
            self.initial_price = float(price)
            self.state = "S1_INITIAL_MARKET_HEDGE"
            self._open_position("BUY", self.small_lot, price, "initial_small_buy")
            self._open_position("SELL", self.small_lot, price, "initial_small_sell")
            self._open_position("BUY", self.large_lot, price, "initial_large_buy")
            self._open_position("SELL", self.large_lot, price, "initial_large_sell")
            self._event("initial_market_hedge_opened", price, 0, {{"source": "block_scaffold"}})

        def on_bar(self, price: float, bar_index: int) -> None:
            if not self.started:
                self.on_start(price)
            if self.state == "S1_INITIAL_MARKET_HEDGE":
                distance = float(price) - float(self.initial_price)
                if abs(distance) >= self.range_threshold_points:
                    direction = "UP" if distance > 0 else "DOWN"
                    self.state = "S2_RANGE_TRIGGER_REACHED"
                    self._event("range_trigger_reached", price, bar_index, {{"direction": direction, "distance_points": distance, "todo": "TODO_SOURCE_UNRESOLVED"}})
                    if direction == "UP":
                        close_tags = ["initial_large_buy", "initial_small_sell"]
                        side = "BUY"
                    else:
                        close_tags = ["initial_large_sell", "initial_small_buy"]
                        side = "SELL"
                    remaining = []
                    closed = 0.0
                    for pos in self.positions:
                        if pos["tag"] in close_tags:
                            closed += self._position_pnl(pos, price)
                        else:
                            remaining.append(pos)
                    self.positions = remaining
                    self.realized_pnl += closed
                    self._open_position(side, self.directional_lot, price, "directional_after_elimination")
                    self.state = "S3_PARTIAL_ELIMINATION_AND_DIRECTIONAL"
                    self._event("partial_elimination_and_directional_opened", price, bar_index, {{"closed_tags": close_tags, "closed_pnl": closed, "todo": "TODO_SOURCE_UNRESOLVED"}})
            elif self.state == "S3_PARTIAL_ELIMINATION_AND_DIRECTIONAL":
                floating = self._floating_pnl(price)
                if floating <= self.stop_threshold_usd:
                    self.state = "S4_RETURN_STOP_OR_RECOVERY"
                    self._event("recovery_or_stop_threshold_reached", price, bar_index, {{"floating_pnl": floating, "todo": "TODO_SOURCE_UNRESOLVED"}})

        def get_positions(self) -> list[dict]:
            return [dict(pos) for pos in self.positions]

        def get_events(self) -> list[dict]:
            return [dict(event) for event in self.events]

        def get_metrics_snapshot(self) -> dict:
            return {{"family_id": self.family_id, "version_id": self.version_id, "state": self.state, "positions_count": len(self.positions), "gross_lot": sum(abs(pos["lot"]) for pos in self.positions), "net_lot": sum((1 if pos["side"] == "BUY" else -1) * pos["lot"] for pos in self.positions), "realized_pnl": self.realized_pnl, "events_count": len(self.events), "model_status": "deterministic_block_scaffold_with_source_unresolved"}}
    ''').strip() + "\n"


def validate_code(code: str, code_path: Path) -> dict[str, Any]:
    result = {"compiled": False, "has_strategy_model": False, "required_methods": {}, "smoke_test_ok": False, "errors": [], "positions_count": None, "events_count": None, "metrics_snapshot": None}
    try:
        compiled = compile(code, str(code_path), "exec")
        result["compiled"] = True
    except Exception as exc:
        result["errors"].append(f"compile_error: {exc}")
        return result
    ns: dict[str, Any] = {}
    try:
        exec(compiled, ns)
    except Exception as exc:
        result["errors"].append(f"exec_error: {exc}")
        return result
    cls = ns.get("StrategyModel")
    if cls is None:
        result["errors"].append("StrategyModel não encontrado")
        return result
    result["has_strategy_model"] = True
    for method in REQUIRED_METHODS:
        result["required_methods"][method] = hasattr(cls, method)
    missing = [m for m, ok in result["required_methods"].items() if not ok]
    if missing:
        result["errors"].append(f"missing_methods: {missing}")
        return result
    try:
        model = cls({})
        model.on_start(3000.0)
        for idx, price in enumerate([3100, 3400, 3500, 3600, 3300], start=1):
            model.on_bar(float(price), idx)
        result["smoke_test_ok"] = True
        result["positions_count"] = len(model.get_positions())
        result["events_count"] = len(model.get_events())
        result["metrics_snapshot"] = model.get_metrics_snapshot()
    except Exception as exc:
        result["errors"].append(f"smoke_test_error: {exc}")
        result["traceback"] = traceback.format_exc()
    return result


def write_report(path: Path, data: dict[str, Any]) -> None:
    lines = [
        f"# MQL5 -> Python Block Translation Report — {data['family_id']} / {data['version_id']}",
        "", "## Status", "",
        f"- Gerado UTC: `{now_utc()}`",
        f"- Source MQL5: `{data['source_path']}`",
        f"- LLM usada: `{data['used_llm']}`",
        f"- Translation source: `{data['translation_source']}`",
        f"- Compilou: `{data['validation'].get('compiled')}`",
        f"- Smoke test OK: `{data['validation'].get('smoke_test_ok')}`",
        f"- Funções selecionadas: `{data['block_inventory'].get('selected_functions')}`",
        "", "## Runtime LLM", "", "```json",
        json.dumps(data["llm_runtime"], ensure_ascii=False, indent=2),
        "```", "", "## Summary", "",
    ]
    for item in data["translation_summary"]:
        lines.append(f"- {item}")
    lines += ["", "## Source unresolved", ""]
    for item in data["source_unresolved"]:
        lines.append(f"- {item}")
    lines += ["", "## Validation", "", "```json", json.dumps(data["validation"], ensure_ascii=False, indent=2), "```", ""]
    write_text(path, "\n".join(lines))


def run(args: argparse.Namespace) -> None:
    spec_path = Path(args.spec)
    strategy_dir = Path(args.strategy_dir)
    out_dir = Path(args.out_dir)
    config_path = Path(args.config) if args.config else None
    spec = read_json(spec_path)
    family_id = spec.get("family_id", "UNKNOWN")
    version = find_version(spec, args.version_id)
    source_name = version.get("source_file")
    if not source_name:
        raise ValueError("source_file ausente no spec da versão")
    source_path = strategy_dir / source_name
    if not source_path.exists():
        raise FileNotFoundError(f"Arquivo MQL5 não encontrado: {source_path}")
    source = read_text(source_path)
    analysis_path = spec_path.parent / "versions" / f"{args.version_id}_analysis.json"
    analysis = read_json(analysis_path) if analysis_path.exists() else None
    config = load_config(config_path)
    profile = get_profile(config)
    max_chars = int(args.max_block_chars or profile.get("max_context_chars", 8000))
    translation_dir = out_dir / args.version_id / "translation"
    translation_dir.mkdir(parents=True, exist_ok=True)
    context, block_inventory = build_block_context(family_id, args.version_id, spec, version, source_path, source, analysis, max_chars)
    prompt = build_prompt(context)
    write_text(translation_dir / f"{args.version_id}_block_translation_context.md", context)
    write_text(translation_dir / f"{args.version_id}_block_translation_prompt.md", prompt)
    write_json(translation_dir / f"{args.version_id}_block_inventory.json", block_inventory)
    raw = ""
    parsed = None
    llm_error = None
    used_llm = False
    if args.use_llm:
        try:
            raw = call_ollama(prompt, profile)
            write_text(translation_dir / f"{args.version_id}_block_llm_raw_response.txt", raw)
            parsed = parse_llm(raw)
            used_llm = True
        except Exception as exc:
            llm_error = str(exc)
            write_text(translation_dir / f"{args.version_id}_block_llm_raw_response.txt", raw or f"[LLM_ERROR] {llm_error}")
    if parsed:
        code = parsed["python_code"]
        summary = parsed.get("translation_summary", [])
        unresolved = parsed.get("source_unresolved", [])
        assumptions = parsed.get("assumptions", [])
        translation_source = "llm_block_translation"
    else:
        code = scaffold_code(family_id, args.version_id, version)
        summary = ["Scaffold determinístico gerado em modo block-first.", "LLM não usada ou retorno da LLM não foi aceito pelo schema."]
        unresolved = ["Resolver lógica real a partir dos blocos MQL5 selecionados.", "Confirmar sequência de abertura/fechamento, triggers e recovery."]
        assumptions = ["Scaffold mantém contrato StrategyModel e proxy mínimo por range."]
        translation_source = "deterministic_block_scaffold" if not args.use_llm else "deterministic_block_scaffold_after_llm_error"
    code_path = translation_dir / f"{args.version_id}_translated_strategy.py"
    write_text(code_path, code)
    validation = validate_code(code, code_path)
    runtime = {"used": used_llm, "provider": profile.get("provider"), "active_profile": profile.get("active_profile"), "model": profile.get("model"), "base_url": profile.get("base_url"), "timeout_seconds": profile.get("timeout_seconds"), "translation_source": translation_source, "error": llm_error}
    payload = {"family_id": family_id, "version_id": args.version_id, "source_path": str(source_path), "analysis_path": str(analysis_path) if analysis_path.exists() else None, "used_llm": used_llm, "translation_source": translation_source, "llm_runtime": runtime, "block_inventory": block_inventory, "translation_summary": summary, "source_unresolved": unresolved, "assumptions": assumptions, "validation": validation}
    write_json(translation_dir / f"{args.version_id}_translation_validation.json", payload)
    write_report(translation_dir / f"{args.version_id}_translation_report.md", payload)
    print("[OK] MQL5 block translation agent completed")
    print(f"[OK] family_id: {family_id}")
    print(f"[OK] version_id: {args.version_id}")
    print(f"[OK] used_llm: {used_llm}")
    print(f"[OK] translation_source: {translation_source}")
    print(f"[OK] selected_functions: {len(block_inventory.get('selected_functions', []))}")
    print(f"[OK] smoke_test_ok: {validation.get('smoke_test_ok')}")
    print(f"[OK] output dir: {translation_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MQL5 -> Python block-first translation agent")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--strategy-dir", required=True)
    parser.add_argument("--version-id", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--config", default=None)
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument("--max-block-chars", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
