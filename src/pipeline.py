"""Captura fontes sintéticas em Delta Lake e recria as fontes Bronze no DuckDB.

Não há regra de negócio aqui: conversões, validações e métricas pertencem ao dbt.
"""
from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DELTA = ROOT / "data" / "bronze_delta"
DATABASE = ROOT / "data" / "conciliacao.duckdb"


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


def load_delta_into_duckdb(connection: duckdb.DuckDBPyConnection, delta_path: Path, table_name: str) -> None:
    arrow_table = DeltaTable(str(delta_path)).to_pyarrow_table()
    connection.register("captura_delta", arrow_table)
    connection.execute(f"create or replace table {table_name} as select * from captura_delta")
    connection.unregister("captura_delta")


def main() -> None:
    formularios = capture_metadata(read_csv("formularios_servidores.csv"), "formularios_servidores.csv", "lote_01")
    dividas_lote_01 = capture_metadata(read_json("dividas_credores_lote_01.json"), "dividas_credores_lote_01.json", "lote_01")
    dividas_lote_02 = capture_metadata(read_json("dividas_credores_lote_02.json"), "dividas_credores_lote_02.json", "lote_02")

    # A recriação deliberada garante que a execução parte sempre de data/raw.
    if DELTA.exists():
        shutil.rmtree(DELTA)
    DELTA.mkdir(parents=True, exist_ok=True)
    write_delta(DELTA / "formularios", formularios, "overwrite")
    write_delta(DELTA / "dividas", dividas_lote_01, "overwrite")  # versão 0
    write_delta(DELTA / "dividas", dividas_lote_02, "append")  # versão 1

    with duckdb.connect(str(DATABASE)) as connection:
        load_delta_into_duckdb(connection, DELTA / "formularios", "bronze_formularios")
        load_delta_into_duckdb(connection, DELTA / "dividas", "bronze_dividas")

    print("Ingestão concluída.")
    print(f"DuckDB: {DATABASE}")
    print("Delta dividas: versões 0 e 1 registradas.")


if __name__ == "__main__":
    main()

