#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hedgeAgent - Analyze MQL5 Versions

Objetivo
--------
Este script é a segunda peça do hedgeAgent.

Ele foi criado para ler o manifesto gerado por:

    tools/analyze_strategy_family.py

E analisar cada arquivo `.mq5` real de uma família de estratégia, por exemplo:

    estrategias/P0/Hedge_P0_V4.mq5

A missão deste script NÃO é fazer backtest ainda.
A missão também NÃO é traduzir MQL5 para Python ainda.

A missão desta etapa é criar uma camada de conhecimento técnico sobre cada versão:

    1. Ler o manifesto real da família.
    2. Encontrar os arquivos `.mq5` registrados.
    3. Ler cada arquivo MQL5 com segurança de encoding.
    4. Extrair informações objetivas:
       - #property
       - #include
       - inputs
       - funções principais
       - comentários relevantes
       - chamadas de trade/ordens/posições
       - pistas de lote, hedge, pending, recovery e risco
    5. Gerar um arquivo JSON por versão.
    6. Gerar um resumo Markdown por versão.
    7. Gerar um resumo consolidado da família.

Por que isso existe?
--------------------
Antes de transformar um EA em Python/backtest, precisamos entender o que ele faz.

Mas este script deve ser conservador:

    - Ele NÃO deve inventar lógica.
    - Ele NÃO deve afirmar uma regra se ela não estiver clara no código.
    - Ele deve registrar pistas e marcar pontos desconhecidos como `needs_human_review`.

Exemplo de comportamento correto:

    Detectado:
        input double HedgeSmallLot = 0.03;

    Pode registrar:
        Existe um input chamado HedgeSmallLot com valor padrão 0.03.

    Não pode inventar:
        A estratégia é lucrativa em consolidação.

Entradas
--------
--manifest:
    Caminho para o manifesto da família.

    Exemplo:
        knowledge/P0/P0_manifest.json

--strategy-dir:
    Opcional. Sobrescreve a pasta de estratégia presente no manifesto.

    Exemplo:
        estrategias/P0

--out-dir:
    Pasta de saída para os artefatos de análise.

    Exemplo:
        knowledge/P0

Saídas
------
O script cria:

    knowledge/P0/versions/P0_BASE_analysis.json
    knowledge/P0/versions/P0_BASE_analysis.md
    knowledge/P0/versions/P0_V1_analysis.json
    knowledge/P0/versions/P0_V1_analysis.md
    ...
    knowledge/P0/P0_mql5_version_analysis_summary.md
    knowledge/P0/P0_mql5_version_analysis_index.json

O que este script NÃO faz
-------------------------
Este script não faz backtest.
Este script não traduz MQL5 para Python.
Este script não altera arquivos de estratégia.
Este script não decide se uma estratégia é boa ou ruim.
Este script não cria ordens, não executa MetaTrader e não depende de MQL5 instalado.

Compatibilidade
---------------
Este script foi desenhado para funcionar em Windows e Linux.
Ele usa apenas biblioteca padrão do Python e pathlib.

Regras do projeto
-----------------
- Nunca quebrar o que já funciona.
- Nunca inventar arquivos, funções ou regras.
- Sempre ler arquivos reais.
- Sempre pensar multiativo e multitimeframe.
- Sempre usar pathlib para caminhos.
- Sempre gerar saídas rastreáveis.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TRADE_KEYWORDS = [
    "OrderSend", "OrderCheck", "CTrade", "trade.Buy", "trade.Sell",
    "trade.BuyLimit", "trade.SellLimit", "trade.BuyStop", "trade.SellStop",
    "PositionSelect", "PositionSelectByTicket", "PositionsTotal", "OrdersTotal",
    "PositionClose", "PositionClosePartial", "OrderDelete",
]

LOT_KEYWORDS = [
    "lot", "Lot", "lote", "HedgeSmallLot", "HedgeLargeLot", "DirectionalLot",
    "LotIncrease", "StepLot", "MinLot", "MaxLot",
]

HEDGE_KEYWORDS = [
    "hedge", "Hedge", "travamento", "small", "Small", "large", "Large",
    "directional", "Directional", "direcional", "isolating", "Isolating", "base", "Base",
]

PENDING_KEYWORDS = [
    "pending", "Pending", "pendente", "BUY_LIMIT", "SELL_LIMIT", "BUY_STOP", "SELL_STOP",
    "BuyLimit", "SellLimit", "BuyStop", "SellStop",
]

RISK_KEYWORDS = [
    "StopThreshold", "MaxSpread", "drawdown", "Drawdown", "DD", "risk", "Risk",
    "risco", "stop", "Stop", "margin", "Margin", "margem",
]

MQL_EVENT_FUNCTIONS = {
    "OnInit", "OnDeinit", "OnTick", "OnTimer", "OnTrade", "OnTradeTransaction", "OnChartEvent",
}


@dataclass
class ExtractedInput:
    """Representa um input MQL5 extraído de forma objetiva."""
    line: int
    raw: str
    type: str
    name: str
    default: str | None
    comment: str | None


@dataclass
class ExtractedFunction:
    """Representa uma função detectada no arquivo MQL5."""
    line: int
    name: str
    return_type: str
    parameters: str
    is_event_function: bool


@dataclass
class ExtractedProperty:
    """Representa uma diretiva #property detectada."""
    line: int
    name: str
    value: str


@dataclass
class ExtractedInclude:
    """Representa uma diretiva #include detectada."""
    line: int
    value: str


@dataclass
class Mql5VersionAnalysis:
    """Resultado consolidado da análise de uma versão MQL5."""
    family_id: str
    version_id: str
    source_file: str
    source_path: str
    generated_at_utc: str
    line_count: int
    char_count: int
    properties: list[dict[str, Any]]
    includes: list[dict[str, Any]]
    inputs: list[dict[str, Any]]
    functions: list[dict[str, Any]]
    event_functions: list[str]
    trade_keyword_hits: dict[str, int]
    logic_cues: dict[str, Any]
    comments_sample: list[str]
    candidate_strengths: list[dict[str, str]]
    candidate_weaknesses: list[dict[str, str]]
    unknown_points: list[str]
    needs_human_review: bool


def now_utc_iso() -> str:
    """Retorna timestamp UTC em formato ISO para rastreabilidade."""
    return datetime.now(timezone.utc).isoformat()


def read_text_with_fallback(path: Path) -> str:
    """Lê texto tentando UTF-8, UTF-8 BOM, CP1252 e latin-1."""
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise RuntimeError(f"Could not decode file {path}. Last error: {last_error}")


def load_json(path: Path) -> Any:
    """Carrega JSON em UTF-8."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    """Salva JSON formatado em UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_spaces(value: str) -> str:
    """Normaliza espaços para melhorar relatórios."""
    return re.sub(r"\s+", " ", value).strip()


def split_code_and_comment(line: str) -> tuple[str, str | None]:
    """Separa uma linha em código e comentário de linha `//` de forma simples."""
    if "//" not in line:
        return line, None
    code, comment = line.split("//", 1)
    return code, comment.strip() or None


def extract_properties(lines: list[str]) -> list[ExtractedProperty]:
    """Extrai diretivas #property."""
    result: list[ExtractedProperty] = []
    pattern = re.compile(r"^\s*#property\s+(\w+)\s*(.*)$")
    for line_no, line in enumerate(lines, start=1):
        match = pattern.match(line)
        if match:
            result.append(ExtractedProperty(line=line_no, name=match.group(1), value=normalize_spaces(match.group(2))))
    return result


def extract_includes(lines: list[str]) -> list[ExtractedInclude]:
    """Extrai diretivas #include."""
    result: list[ExtractedInclude] = []
    pattern = re.compile(r"^\s*#include\s+(.+)$")
    for line_no, line in enumerate(lines, start=1):
        match = pattern.match(line)
        if match:
            result.append(ExtractedInclude(line=line_no, value=normalize_spaces(match.group(1))))
    return result


def extract_inputs(lines: list[str]) -> list[ExtractedInput]:
    """Extrai inputs MQL5 de forma conservadora."""
    result: list[ExtractedInput] = []
    pattern = re.compile(r"^\s*input\s+(.+?)\s+([A-Za-z_]\w*)\s*(?:=\s*(.*?))?\s*;\s*$")
    for line_no, line in enumerate(lines, start=1):
        code, comment = split_code_and_comment(line)
        match = pattern.match(code)
        if not match:
            continue
        raw_default = match.group(3)
        default = normalize_spaces(raw_default) if raw_default is not None else None
        result.append(ExtractedInput(
            line=line_no, raw=line.strip(), type=normalize_spaces(match.group(1)),
            name=match.group(2), default=default, comment=comment,
        ))
    return result


def extract_functions(lines: list[str]) -> list[ExtractedFunction]:
    """Extrai assinaturas de funções MQL5 por regex conservador."""
    result: list[ExtractedFunction] = []
    pattern = re.compile(r"^\s*([A-Za-z_][\w:<>&\*\s]*?)\s+([A-Za-z_]\w*)\s*\(([^;{}]*)\)\s*(?:\{|$)")
    blocked_names = {"if", "for", "while", "switch", "return"}
    for line_no, line in enumerate(lines, start=1):
        code, _comment = split_code_and_comment(line)
        stripped = code.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = pattern.match(stripped)
        if not match:
            continue
        return_type = normalize_spaces(match.group(1))
        name = match.group(2)
        parameters = normalize_spaces(match.group(3))
        if name in blocked_names:
            continue
        result.append(ExtractedFunction(
            line=line_no, name=name, return_type=return_type, parameters=parameters,
            is_event_function=name in MQL_EVENT_FUNCTIONS,
        ))
    return result


def extract_comment_sample(lines: list[str], max_items: int = 40) -> list[str]:
    """Extrai uma amostra de comentários relevantes."""
    comments: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("//"):
            text = stripped.lstrip("/").strip()
            if text and len(text) > 3:
                comments.append(text)
        elif "//" in line:
            _code, comment = split_code_and_comment(line)
            if comment and len(comment) > 3:
                comments.append(comment)
        if len(comments) >= max_items:
            break
    return comments


def count_keyword_hits(text: str, keywords: list[str]) -> dict[str, int]:
    """Conta ocorrências literais de palavras/pistas no código."""
    result: dict[str, int] = {}
    for keyword in keywords:
        count = text.count(keyword)
        if count > 0:
            result[keyword] = count
    return result


def build_logic_cues(text: str, inputs: list[ExtractedInput], functions: list[ExtractedFunction]) -> dict[str, Any]:
    """Cria pistas sobre a lógica sem afirmar demais."""
    input_names = {item.name for item in inputs}
    function_names = {item.name for item in functions}
    text_lower = text.lower()
    return {
        "has_magic_number": any("magic" in name.lower() for name in input_names) or "magic" in text_lower,
        "has_spread_filter": "MaxSpread" in input_names or "spread" in text_lower,
        "has_initial_hedge_cue": "hedge" in text_lower and ("small" in text_lower or "large" in text_lower),
        "has_directional_cue": "directional" in text_lower or "direcional" in text_lower,
        "has_lot_increase_cue": any("increase" in name.lower() for name in input_names) or "aumento" in text_lower,
        "has_no_lot_increase_cue": "naoamentalot" in text_lower or "não aumenta" in text_lower or "nao aumenta" in text_lower,
        "has_pending_order_cue": any(keyword.lower() in text_lower for keyword in PENDING_KEYWORDS),
        "has_recovery_cue": "recovery" in text_lower or "recuper" in text_lower or "resolve" in text_lower,
        "has_close_all_button_cue": "close_all" in text_lower or "botao" in text_lower or "button" in text_lower,
        "has_reset_state_cue": "reset" in text_lower,
        "has_timer_event": "OnTimer" in function_names,
        "has_tick_event": "OnTick" in function_names,
        "has_chart_event": "OnChartEvent" in function_names,
        "trade_keyword_hits": count_keyword_hits(text, TRADE_KEYWORDS),
        "lot_keyword_hits": count_keyword_hits(text, LOT_KEYWORDS),
        "hedge_keyword_hits": count_keyword_hits(text, HEDGE_KEYWORDS),
        "pending_keyword_hits": count_keyword_hits(text, PENDING_KEYWORDS),
        "risk_keyword_hits": count_keyword_hits(text, RISK_KEYWORDS),
    }


def build_candidate_strengths(logic_cues: dict[str, Any]) -> list[dict[str, str]]:
    """Gera pontos fortes candidatos com base em pistas objetivas."""
    strengths: list[dict[str, str]] = []
    if logic_cues.get("has_magic_number"):
        strengths.append({"confidence": "medium", "point": "Possui pista de MagicNumber/magic, útil para separar instâncias e multi-EA."})
    if logic_cues.get("has_spread_filter"):
        strengths.append({"confidence": "medium", "point": "Possui pista de filtro de spread, útil para evitar entradas em condição ruim."})
    if logic_cues.get("has_initial_hedge_cue"):
        strengths.append({"confidence": "low", "point": "Possui pistas de estrutura hedge small/large ou travamento inicial."})
    if logic_cues.get("has_close_all_button_cue"):
        strengths.append({"confidence": "medium", "point": "Possui pista de botão/rotina de fechamento ou reset operacional."})
    return strengths


def build_candidate_weaknesses(logic_cues: dict[str, Any]) -> list[dict[str, str]]:
    """Gera pontos fracos candidatos com base em pistas objetivas."""
    weaknesses: list[dict[str, str]] = []
    if logic_cues.get("has_lot_increase_cue"):
        weaknesses.append({"confidence": "medium", "point": "Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida."})
    if not logic_cues.get("has_spread_filter"):
        weaknesses.append({"confidence": "low", "point": "Não foi detectada pista clara de filtro de spread nesta análise textual."})
    if not logic_cues.get("has_magic_number"):
        weaknesses.append({"confidence": "medium", "point": "Não foi detectada pista clara de MagicNumber/magic. Isso pode limitar multi-instância."})
    return weaknesses


def build_unknown_points(inputs: list[ExtractedInput], functions: list[ExtractedFunction], logic_cues: dict[str, Any]) -> list[str]:
    """Lista pontos que ainda precisam de análise humana/profunda."""
    unknowns: list[str] = []
    function_names = {item.name for item in functions}
    if "OnTick" not in function_names and "OnTimer" not in function_names:
        unknowns.append("Não foi detectado OnTick nem OnTimer; fluxo principal precisa ser confirmado.")
    if logic_cues.get("has_lot_increase_cue"):
        unknowns.append("Há pistas de aumento de lote, mas esta etapa ainda não prova quando e por que o lote aumenta.")
    if logic_cues.get("has_pending_order_cue"):
        unknowns.append("Há pistas de ordens pendentes, mas a sequência exata de criação/renovação ainda precisa ser interpretada.")
    if logic_cues.get("has_recovery_cue"):
        unknowns.append("Há pistas de recovery/resolve, mas a regra matemática de recuperação ainda precisa ser validada.")
    if not inputs:
        unknowns.append("Nenhum input foi extraído; confirmar se o arquivo possui parâmetros configuráveis.")
    unknowns.append("Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código.")
    return unknowns


def analyze_mql5_file(family_id: str, version_id: str, source_file: str, source_path: Path) -> Mql5VersionAnalysis:
    """Analisa um arquivo MQL5 e retorna estrutura rastreável."""
    text = read_text_with_fallback(source_path)
    lines = text.splitlines()
    properties = extract_properties(lines)
    includes = extract_includes(lines)
    inputs = extract_inputs(lines)
    functions = extract_functions(lines)
    logic_cues = build_logic_cues(text=text, inputs=inputs, functions=functions)
    unknown_points = build_unknown_points(inputs=inputs, functions=functions, logic_cues=logic_cues)
    return Mql5VersionAnalysis(
        family_id=family_id,
        version_id=version_id,
        source_file=source_file,
        source_path=str(source_path),
        generated_at_utc=now_utc_iso(),
        line_count=len(lines),
        char_count=len(text),
        properties=[asdict(item) for item in properties],
        includes=[asdict(item) for item in includes],
        inputs=[asdict(item) for item in inputs],
        functions=[asdict(item) for item in functions],
        event_functions=[item.name for item in functions if item.is_event_function],
        trade_keyword_hits=count_keyword_hits(text, TRADE_KEYWORDS),
        logic_cues=logic_cues,
        comments_sample=extract_comment_sample(lines),
        candidate_strengths=build_candidate_strengths(logic_cues),
        candidate_weaknesses=build_candidate_weaknesses(logic_cues),
        unknown_points=unknown_points,
        needs_human_review=bool(unknown_points),
    )


def write_version_markdown(path: Path, analysis: Mql5VersionAnalysis) -> None:
    """Gera resumo Markdown por versão."""
    lines: list[str] = []
    lines.append(f"# Análise MQL5 — {analysis.version_id}")
    lines.append("")
    lines.append("## Objetivo deste relatório")
    lines.append("")
    lines.append("Este relatório organiza informações extraídas automaticamente do arquivo MQL5. Ele não executa backtest e não afirma lucratividade.")
    lines.append("")
    lines.append("## Fonte")
    lines.append("")
    lines.append(f"- Família: `{analysis.family_id}`")
    lines.append(f"- Versão: `{analysis.version_id}`")
    lines.append(f"- Arquivo: `{analysis.source_file}`")
    lines.append(f"- Linhas: `{analysis.line_count}`")
    lines.append(f"- Gerado em UTC: `{analysis.generated_at_utc}`")
    lines.append("")

    lines.append("## Properties")
    lines.append("")
    if analysis.properties:
        for prop in analysis.properties:
            lines.append(f"- Linha {prop['line']}: `{prop['name']}` = `{prop['value']}`")
    else:
        lines.append("- Nenhuma diretiva #property detectada.")
    lines.append("")

    lines.append("## Includes")
    lines.append("")
    if analysis.includes:
        for inc in analysis.includes:
            lines.append(f"- Linha {inc['line']}: `{inc['value']}`")
    else:
        lines.append("- Nenhum include detectado.")
    lines.append("")

    lines.append("## Inputs detectados")
    lines.append("")
    if analysis.inputs:
        lines.append("| linha | tipo | nome | default | comentário |")
        lines.append("|---:|---|---|---|---|")
        for item in analysis.inputs:
            lines.append(f"| {item['line']} | `{item['type']}` | `{item['name']}` | `{item['default']}` | {item['comment'] or ''} |")
    else:
        lines.append("- Nenhum input detectado.")
    lines.append("")

    lines.append("## Funções detectadas")
    lines.append("")
    if analysis.functions:
        lines.append("| linha | função | retorno | evento MQL5 |")
        lines.append("|---:|---|---|---|")
        for item in analysis.functions:
            event = "sim" if item["is_event_function"] else "não"
            lines.append(f"| {item['line']} | `{item['name']}` | `{item['return_type']}` | {event} |")
    else:
        lines.append("- Nenhuma função detectada pelo parser conservador.")
    lines.append("")

    lines.append("## Pistas de lógica")
    lines.append("")
    for key, value in analysis.logic_cues.items():
        if isinstance(value, dict):
            if value:
                lines.append(f"- `{key}`: `{value}`")
        else:
            lines.append(f"- `{key}`: `{value}`")
    lines.append("")

    lines.append("## Pontos fortes candidatos")
    lines.append("")
    if analysis.candidate_strengths:
        for item in analysis.candidate_strengths:
            lines.append(f"- ({item['confidence']}) {item['point']}")
    else:
        lines.append("- Nenhum ponto forte candidato detectado nesta etapa.")
    lines.append("")

    lines.append("## Pontos fracos / riscos candidatos")
    lines.append("")
    if analysis.candidate_weaknesses:
        for item in analysis.candidate_weaknesses:
            lines.append(f"- ({item['confidence']}) {item['point']}")
    else:
        lines.append("- Nenhum ponto fraco candidato detectado nesta etapa.")
    lines.append("")

    lines.append("## Pontos desconhecidos")
    lines.append("")
    for item in analysis.unknown_points:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Amostra de comentários")
    lines.append("")
    if analysis.comments_sample:
        for comment in analysis.comments_sample:
            lines.append(f"- {comment}")
    else:
        lines.append("- Nenhum comentário relevante extraído.")
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_family_summary(path: Path, family_id: str, analyses: list[Mql5VersionAnalysis]) -> None:
    """Gera resumo consolidado das versões MQL5."""
    lines: list[str] = []
    lines.append(f"# Resumo de Análise MQL5 — Família {family_id}")
    lines.append("")
    lines.append("## Objetivo")
    lines.append("")
    lines.append("Este relatório consolida a leitura automática das versões MQL5 da família. Ele serve como base para documentação, comparação e futura tradução para Python/backtest.")
    lines.append("")
    lines.append("## Versões analisadas")
    lines.append("")
    lines.append("| versão | arquivo | inputs | funções | eventos | revisão humana |")
    lines.append("|---|---|---:|---:|---|---|")
    for analysis in analyses:
        events = ", ".join(analysis.event_functions) if analysis.event_functions else "-"
        review = "sim" if analysis.needs_human_review else "não"
        lines.append(f"| {analysis.version_id} | `{analysis.source_file}` | {len(analysis.inputs)} | {len(analysis.functions)} | {events} | {review} |")
    lines.append("")
    lines.append("## Leituras importantes")
    lines.append("")
    lines.append("- Esta etapa ainda não interpreta matematicamente a estratégia; ela organiza sinais do código.")
    lines.append("- A próxima etapa deve comparar as regras entre versões e montar uma especificação `strategy_spec.json` por versão.")
    lines.append("- Qualquer ponto marcado como revisão humana precisa ser validado antes do backtest.")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def resolve_strategy_dir(manifest: dict[str, Any], manifest_path: Path, override: str | None) -> Path:
    """Resolve a pasta da estratégia de forma cross-platform."""
    if override:
        return Path(override)
    raw = manifest.get("strategy_dir")
    if not raw:
        raise ValueError("Manifest does not contain strategy_dir. Use --strategy-dir.")
    candidate = Path(raw)
    if candidate.exists():
        return candidate
    return manifest_path.parent.parent.parent / raw


def run(manifest_path: Path, out_dir: Path, strategy_dir_override: str | None = None) -> None:
    """Executa análise das versões MQL5 registradas no manifesto."""
    manifest = load_json(manifest_path)
    family_id = manifest["family_id"]
    strategy_dir = resolve_strategy_dir(manifest=manifest, manifest_path=manifest_path, override=strategy_dir_override)
    version_out_dir = out_dir / "versions"
    analyses: list[Mql5VersionAnalysis] = []

    for file_info in manifest.get("files", []):
        if file_info.get("file_type") != "mql5_source":
            continue
        version_id = file_info["version_id"]
        relative_path = file_info["relative_path"]
        source_path = strategy_dir / relative_path
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        analysis = analyze_mql5_file(family_id=family_id, version_id=version_id, source_file=relative_path, source_path=source_path)
        analyses.append(analysis)
        write_json(version_out_dir / f"{version_id}_analysis.json", asdict(analysis))
        write_version_markdown(version_out_dir / f"{version_id}_analysis.md", analysis=analysis)

    write_json(out_dir / f"{family_id}_mql5_version_analysis_index.json", [asdict(item) for item in analyses])
    write_family_summary(out_dir / f"{family_id}_mql5_version_analysis_summary.md", family_id=family_id, analyses=analyses)
    print("[OK] MQL5 versions analyzed")
    print(f"[OK] family_id: {family_id}")
    print(f"[OK] versions analyzed: {len(analyses)}")
    print(f"[OK] output dir: {out_dir}")


def parse_args() -> argparse.Namespace:
    """Configura argumentos de linha de comando."""
    parser = argparse.ArgumentParser(description="Analyze MQL5 versions listed in a hedgeAgent family manifest.")
    parser.add_argument("--manifest", required=True, help="Path to family manifest JSON, e.g. knowledge/P0/P0_manifest.json")
    parser.add_argument("--strategy-dir", required=False, default=None, help="Optional override for strategy source directory, e.g. estrategias/P0")
    parser.add_argument("--out-dir", required=True, help="Output directory for analysis artifacts, e.g. knowledge/P0")
    return parser.parse_args()


def main() -> None:
    """Ponto de entrada CLI."""
    args = parse_args()
    run(manifest_path=Path(args.manifest), strategy_dir_override=args.strategy_dir, out_dir=Path(args.out_dir))


if __name__ == "__main__":
    main()
