"""Captura fontes sintéticas em Delta Lake e recria as fontes Bronze no ClickHouse.

Não há regra de negócio aqui: conversões, validações e métricas pertencem ao dbt.
"""
from __future__ import annotations

import csv
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

from src.clickhouse_client import connect, replace_arrow
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DELTA = ROOT / "data" / "bronze_delta"


def capture_metadata(rows: list[dict[str, str]], file_name: str, batch: str) -> list[dict[str, str]]:
    captured_at = datetime.now(timezone.utc).isoformat()
    return [
        {**row, "arquivo_origem": file_name, "lote": batch, "capturado_em": captured_at}
        for row in rows
    ]


def read_csv(name: str) -> list[dict[str, str]]:
    with (RAW / name).open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def read_json(name: str) -> list[dict[str, str]]:
    with (RAW / name).open(encoding="utf-8") as source:
        return json.load(source)


def write_delta(path: Path, rows: list[dict[str, str]], mode: str) -> None:
    write_deltalake(str(path), pa.Table.from_pylist(rows), mode=mode)


def load_delta_into_clickhouse(connection, delta_path: Path, table_name: str) -> None:
    replace_arrow(connection, table_name, DeltaTable(str(delta_path)).to_pyarrow_table())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-delta", action="store_true", help="Recria o ClickHouse a partir do Delta atual, sem reler as fontes")
    args = parser.parse_args()
    if args.from_delta:
        with connect() as connection:
            load_delta_into_clickhouse(connection, DELTA / "formularios", "bronze_formularios")
            load_delta_into_clickhouse(connection, DELTA / "dividas", "bronze_dividas")
        print("Bronze ClickHouse reconstruido a partir do Delta preservado.")
        return
    formularios = capture_metadata(read_csv("formularios_servidores.csv"), "formularios_servidores.csv", "lote_01")
    dividas_lote_01 = capture_metadata(read_json("dividas_credores_lote_01.json"), "dividas_credores_lote_01.json", "lote_01")
    dividas_lote_02 = capture_metadata(read_json("dividas_credores_lote_02.json"), "dividas_credores_lote_02.json", "lote_02")

    # Overwrite cria um novo snapshot sem apagar os arquivos e commits anteriores.
    # Cada captura contém lote 01 e, no commit seguinte, lote 01 + lote 02.
    DELTA.mkdir(parents=True, exist_ok=True)
    write_delta(DELTA / "formularios", formularios, "overwrite")
    write_delta(DELTA / "dividas", dividas_lote_01, "overwrite")  # snapshot do lote 01
    write_delta(DELTA / "dividas", dividas_lote_02, "append")  # snapshot dos dois lotes

    with connect() as connection:
        load_delta_into_clickhouse(connection, DELTA / "formularios", "bronze_formularios")
        load_delta_into_clickhouse(connection, DELTA / "dividas", "bronze_dividas")

    print("Ingestão concluída.")
    print(f"Delta dividas: versao atual = {DeltaTable(str(DELTA / 'dividas')).version()}; historico preservado.")


if __name__ == "__main__":
    main()

