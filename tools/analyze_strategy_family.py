#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hedgeAgent - Analyze Strategy Family

Objetivo
--------
Este script é a primeira peça do hedgeAgent.

Ele foi criado para analisar uma pasta de estratégias, por exemplo:

    estrategias/P0/

Dentro dessa pasta podem existir arquivos como:

    .mq5   -> códigos MetaTrader 5 / MQL5
    .txt   -> prompts, ideias, observações
    .md    -> documentação em Markdown
    .json  -> specs manuais ou metadados
    .csv   -> tabelas simples
    .xlsx  -> planilhas

A missão deste script NÃO é fazer backtest ainda.
A missão também NÃO é traduzir MQL5 para Python ainda.

A missão inicial é:

    1. Ler a pasta real informada pelo usuário.
    2. Identificar quais arquivos existem.
    3. Classificar os arquivos por tipo.
    4. Criar um manifesto da família da estratégia.
    5. Criar uma base inicial de conhecimento.
    6. Registrar observações úteis para a próxima etapa.

Por que isso existe?
--------------------
No hedgeAgent, cada estratégia pode ter várias versões.

Exemplo:

    P0/
        hedge_P0-NaoAmentaLot.mq5
        Hedge_P00_V1-TravamentoNoInicioNaoJuntocomDirecional.mq5
        Hedge_P0_V2-RangeAumentoLot-NaoFunciona2EAS.mq5
        Hedge_P0_V3.mq5
        Hedge_P0_V4.mq5
        PromptEA-P0.txt

Esses arquivos pertencem à mesma família de pesquisa: P0.

Mas cada arquivo pode representar uma tentativa diferente, com regras,
parâmetros, fases, lógica de hedge e limitações diferentes.

Por isso, o projeto deve tratar:

    P0        = família de estratégia
    P0_V1     = versão/tentativa específica
    P0_V2     = versão/tentativa específica
    P0_V3     = versão/tentativa específica
    P0_V4     = versão/tentativa específica

O script prepara essa separação sem inventar comportamento.

Entradas
--------
--strategy-dir:
    Caminho da pasta da família de estratégia.

    Exemplo Windows:
        C:\\Users\\diego\\Desktop\\Python\\hedgeAgent\\estrategias\\P0

    Exemplo Linux:
        /opt/hedgeAgent/estrategias/P0

--family-id:
    Nome curto da família.

    Exemplo:
        P0

--out-dir:
    Pasta onde os artefatos de conhecimento serão salvos.

    Exemplo:
        knowledge/P0

Saídas
------
O script cria arquivos como:

    knowledge/P0/P0_manifest.json
    knowledge/P0/P0_source_inventory.json
    knowledge/P0/P0_analysis_notes.jsonl
    knowledge/P0/P0_family_summary.md

O que este script NÃO faz
-------------------------
Este script não faz backtest.
Este script não traduz MQL5 para Python.
Este script não decide se uma estratégia é boa ou ruim.
Este script não inventa regras que não estejam nos arquivos.

Quando ele não sabe algo, ele registra como:

    needs_human_review

Compatibilidade
---------------
Este script foi desenhado para funcionar em Windows e Linux.

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
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS = {
    ".mq5": "mql5_source",
    ".mqh": "mql5_include",
    ".txt": "text_note",
    ".md": "markdown_doc",
    ".json": "json_doc",
    ".csv": "csv_table",
    ".xlsx": "excel_table",
}


@dataclass
class SourceFileInfo:
    """
    Representa um arquivo encontrado dentro da família de estratégia.

    Este objeto não tenta interpretar toda a lógica do arquivo.
    Ele apenas registra metadados objetivos e rastreáveis.
    """

    file_name: str
    relative_path: str
    extension: str
    file_type: str
    size_bytes: int
    sha256: str
    version_id: str
    role_hint: str
    needs_human_review: bool


@dataclass
class FamilyManifest:
    """
    Manifesto oficial de uma família de estratégia.

    Este manifesto é a primeira camada de organização da base de conhecimento.

    Ele responde:

        - Qual família estamos analisando?
        - Quais arquivos existem?
        - Quais versões foram detectadas?
        - Quais arquivos precisam de revisão humana?
    """

    family_id: str
    generated_at_utc: str
    strategy_dir: str
    files_count: int
    mql5_files_count: int
    notes_files_count: int
    files: list[dict[str, Any]]
    warnings: list[str]


def now_utc_iso() -> str:
    """Retorna timestamp UTC em formato ISO para rastreabilidade."""
    return datetime.now(timezone.utc).isoformat()


def calculate_sha256(path: Path) -> str:
    """
    Calcula SHA256 do arquivo.

    Por que fazemos isso?
    ---------------------
    Para saber exatamente qual versão do arquivo foi analisada.

    Se o usuário mudar o .mq5 depois, o hash muda.
    Isso evita confundir resultados antigos com arquivos novos.
    """
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def infer_version_id(family_id: str, file_path: Path) -> str:
    """
    Tenta inferir um version_id simples a partir do nome do arquivo.

    Importante:
    -----------
    Esta função NÃO interpreta a estratégia.
    Ela apenas cria um identificador operacional para organização.

    Exemplos:
        Hedge_P0_V4.mq5  -> P0_V4
        alguma_base.mq5  -> P0_BASE_001

    Se a inferência não for perfeita, isso será ajustado depois no manifesto.
    """
    name_upper = file_path.stem.upper()

    # Procura padrões comuns como V1, V2, V3, V4.
    for i in range(0, 100):
        token = f"V{i}"
        if token in name_upper:
            return f"{family_id}_{token}"

    # Caso especial: nomes com P00 podem representar V1 ou variação inicial.
    if "P00" in name_upper:
        return f"{family_id}_P00"

    # Caso base.
    if "BASE" in name_upper or "NAOAMENTA" in name_upper or "NAO_AUMENTA" in name_upper:
        return f"{family_id}_BASE"

    return f"{family_id}_UNCLASSIFIED"


def infer_role_hint(path: Path, file_type: str) -> str:
    """
    Dá uma pista sobre o papel do arquivo dentro da família.

    Isso ajuda o agente e o humano a entenderem a pasta sem abrir tudo manualmente.
    """
    name = path.name.lower()

    if file_type == "mql5_source":
        return "strategy_implementation"

    if "prompt" in name:
        return "human_prompt_or_strategy_description"

    if file_type in {"markdown_doc", "text_note"}:
        return "documentation_or_notes"

    if file_type in {"csv_table", "excel_table"}:
        return "structured_table_or_manual_backtest"

    if file_type == "json_doc":
        return "structured_metadata_or_existing_spec"

    return "unknown"


def scan_strategy_family(strategy_dir: Path, family_id: str) -> list[SourceFileInfo]:
    """
    Lê a pasta da família e lista arquivos suportados.

    Regra importante:
    -----------------
    O script só trabalha com arquivos que existem fisicamente.
    Ele não inventa versões e não cria referência para arquivo ausente.
    """
    if not strategy_dir.exists():
        raise FileNotFoundError(f"Strategy directory not found: {strategy_dir}")

    if not strategy_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {strategy_dir}")

    source_files: list[SourceFileInfo] = []

    for path in sorted(strategy_dir.rglob("*")):
        if not path.is_file():
            continue

        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue

        file_type = SUPPORTED_EXTENSIONS[ext]
        relative_path = path.relative_to(strategy_dir).as_posix()

        version_id = infer_version_id(family_id=family_id, file_path=path)
        role_hint = infer_role_hint(path=path, file_type=file_type)

        # Se não conseguimos classificar bem a versão, marcamos para revisão humana.
        needs_human_review = version_id.endswith("_UNCLASSIFIED")

        source_files.append(
            SourceFileInfo(
                file_name=path.name,
                relative_path=relative_path,
                extension=ext,
                file_type=file_type,
                size_bytes=path.stat().st_size,
                sha256=calculate_sha256(path),
                version_id=version_id,
                role_hint=role_hint,
                needs_human_review=needs_human_review,
            )
        )

    return source_files


def build_manifest(
    family_id: str,
    strategy_dir: Path,
    files: list[SourceFileInfo],
) -> FamilyManifest:
    """
    Cria o manifesto da família de estratégia.

    O manifesto é a base para os próximos agentes:

        - analyze_each_version
        - build_strategy_spec
        - translate_to_python
        - run_backtest
        - build_rag_memory
    """
    warnings: list[str] = []

    if not files:
        warnings.append("No supported files found in strategy directory.")

    if not any(f.file_type == "mql5_source" for f in files):
        warnings.append("No .mq5 strategy source file found.")

    unclassified = [f.file_name for f in files if f.needs_human_review]
    if unclassified:
        warnings.append(
            "Some files could not be classified into clear version_id: "
            + ", ".join(unclassified)
        )

    mql5_count = sum(1 for f in files if f.file_type == "mql5_source")
    notes_count = sum(
        1 for f in files if f.file_type in {"text_note", "markdown_doc"}
    )

    return FamilyManifest(
        family_id=family_id,
        generated_at_utc=now_utc_iso(),
        strategy_dir=str(strategy_dir),
        files_count=len(files),
        mql5_files_count=mql5_count,
        notes_files_count=notes_count,
        files=[asdict(f) for f in files],
        warnings=warnings,
    )


def write_json(path: Path, data: Any) -> None:
    """Salva JSON formatado com UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """
    Salva JSONL.

    JSONL é bom para memória incremental/RAG porque cada linha representa
    um evento ou conhecimento independente.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_family_summary(path: Path, manifest: FamilyManifest) -> None:
    """
    Cria um resumo Markdown legível para humanos.

    Esse arquivo ajuda na documentação e também pode ser usado futuramente
    como fonte para RAG.
    """
    lines: list[str] = []

    lines.append(f"# Família de Estratégia: {manifest.family_id}")
    lines.append("")
    lines.append("## Objetivo deste relatório")
    lines.append("")
    lines.append(
        "Este relatório foi gerado automaticamente pelo hedgeAgent para "
        "organizar os arquivos reais encontrados na família de estratégia."
    )
    lines.append("")
    lines.append("Nesta etapa, o sistema ainda não faz backtest e não traduz MQL5.")
    lines.append("Ele apenas cria a base inicial de conhecimento.")
    lines.append("")
    lines.append("## Resumo")
    lines.append("")
    lines.append(f"- Gerado em UTC: `{manifest.generated_at_utc}`")
    lines.append(f"- Pasta analisada: `{manifest.strategy_dir}`")
    lines.append(f"- Total de arquivos suportados: `{manifest.files_count}`")
    lines.append(f"- Arquivos MQL5: `{manifest.mql5_files_count}`")
    lines.append(f"- Arquivos de notas/documentação: `{manifest.notes_files_count}`")
    lines.append("")

    lines.append("## Arquivos encontrados")
    lines.append("")
    lines.append("| version_id | arquivo | tipo | tamanho | revisão humana |")
    lines.append("|---|---|---|---:|---|")

    for file_info in manifest.files:
        lines.append(
            "| {version_id} | `{file_name}` | {file_type} | {size_bytes} | {review} |".format(
                version_id=file_info["version_id"],
                file_name=file_info["relative_path"],
                file_type=file_info["file_type"],
                size_bytes=file_info["size_bytes"],
                review="sim" if file_info["needs_human_review"] else "não",
            )
        )

    lines.append("")

    lines.append("## Avisos")
    lines.append("")

    if manifest.warnings:
        for warning in manifest.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- Nenhum aviso crítico nesta etapa.")

    lines.append("")
    lines.append("## Próxima etapa sugerida")
    lines.append("")
    lines.append(
        "Executar o agente `analyze_each_version`, que deverá ler cada `.mq5` "
        "individualmente, extrair inputs, funções, comentários, regras de lote, "
        "regras de hedge/recovery, pontos fortes, pontos fracos e pontos desconhecidos."
    )
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_initial_analysis_notes(
    family_id: str,
    files: list[SourceFileInfo],
) -> list[dict[str, Any]]:
    """
    Cria notas iniciais em JSONL.

    Essas notas são simples, mas já começam a base de memória.

    Futuramente, novos agentes vão adicionar linhas como:
        - strategy_strength
        - strategy_weakness
        - failure_pattern
        - hypothesis
        - backtest_result
    """
    rows: list[dict[str, Any]] = []

    for file_info in files:
        rows.append(
            {
                "created_at_utc": now_utc_iso(),
                "family_id": family_id,
                "version_id": file_info.version_id,
                "source_file": file_info.relative_path,
                "note_type": "source_file_registered",
                "file_type": file_info.file_type,
                "role_hint": file_info.role_hint,
                "needs_human_review": file_info.needs_human_review,
                "summary": (
                    "Arquivo registrado como parte da família de estratégia. "
                    "Ainda não houve interpretação da lógica interna."
                ),
            }
        )

    return rows


def run(strategy_dir: Path, family_id: str, out_dir: Path) -> None:
    """
    Executa o fluxo principal do script.

    Este é o fluxo da primeira etapa:

        scan_strategy_family
            ↓
        build_manifest
            ↓
        write knowledge artifacts
    """
    files = scan_strategy_family(strategy_dir=strategy_dir, family_id=family_id)
    manifest = build_manifest(
        family_id=family_id,
        strategy_dir=strategy_dir,
        files=files,
    )

    out_dir.mkdir(parents=True, exist_ok=True)

    write_json(
        out_dir / f"{family_id}_manifest.json",
        asdict(manifest),
    )

    write_json(
        out_dir / f"{family_id}_source_inventory.json",
        [asdict(f) for f in files],
    )

    write_jsonl(
        out_dir / f"{family_id}_analysis_notes.jsonl",
        build_initial_analysis_notes(family_id=family_id, files=files),
    )

    write_family_summary(
        out_dir / f"{family_id}_family_summary.md",
        manifest=manifest,
    )

    print("[OK] Strategy family analyzed")
    print(f"[OK] family_id: {family_id}")
    print(f"[OK] files found: {len(files)}")
    print(f"[OK] output dir: {out_dir}")


def parse_args() -> argparse.Namespace:
    """Configura argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Analyze a hedge strategy family folder and build initial knowledge artifacts."
    )

    parser.add_argument(
        "--strategy-dir",
        required=True,
        help="Path to the strategy family directory, e.g. estrategias/P0",
    )

    parser.add_argument(
        "--family-id",
        required=True,
        help="Strategy family id, e.g. P0",
    )

    parser.add_argument(
        "--out-dir",
        required=True,
        help="Output directory for knowledge artifacts, e.g. knowledge/P0",
    )

    return parser.parse_args()


def main() -> None:
    """Ponto de entrada CLI."""
    args = parse_args()

    run(
        strategy_dir=Path(args.strategy_dir),
        family_id=args.family_id,
        out_dir=Path(args.out_dir),
    )


if __name__ == "__main__":
    main()