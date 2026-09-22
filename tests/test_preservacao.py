"""Regressões de preservação, repetição e reprocessamento em diretório temporário."""
import csv
import json
from collections import Counter
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import duckdb
from deltalake import DeltaTable
from src import pipeline


def values(rows):
    return Counter(json.dumps({k: v for k, v in row.items()
        if k not in {"arquivo_origem", "lote", "capturado_em"}}, sort_keys=True) for row in rows)


class PreservacaoTest(unittest.TestCase):
    def test_captura_repeticao_e_reprocessamento(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw"
            shutil.copytree(pipeline.RAW, raw)
            original = {p.name: p.read_bytes() for p in raw.iterdir()}
            with patch.multiple(pipeline, RAW=raw, DELTA=root / "delta", DATABASE=root / "db.duckdb"):
                with patch("sys.argv", ["pipeline"]):
                    pipeline.main()
                    first = DeltaTable(str(root / "delta/dividas"))
                    self.assertEqual(first.version(), 1)
                    with (raw / "formularios_servidores.csv").open(encoding="utf-8", newline="") as source:
                        forms = list(csv.DictReader(source))
                    debts = sum([json.loads((raw / f"dividas_credores_lote_0{i}.json").read_text(encoding="utf-8")) for i in (1, 2)], [])
                    self.assertEqual(values(forms), values(DeltaTable(str(root / "delta/formularios")).to_pyarrow_table().to_pylist()))
                    self.assertEqual(values(debts), values(first.to_pyarrow_table().to_pylist()))
                    pipeline.main()
                    self.assertEqual(DeltaTable(str(root / "delta/dividas")).version(), 3)
                    self.assertEqual(values(debts), values(DeltaTable(str(root / "delta/dividas"), version=1).to_pyarrow_table().to_pylist()))
                    self.assertEqual(values(debts), values(DeltaTable(str(root / "delta/dividas")).to_pyarrow_table().to_pylist()))
                with patch("sys.argv", ["pipeline", "--from-delta"]), patch.object(pipeline, "read_csv", side_effect=AssertionError("Não reler CSV")), patch.object(pipeline, "read_json", side_effect=AssertionError("Não reler JSON")):
                    pipeline.main()
                with duckdb.connect(str(root / "db.duckdb")) as connection:
                    self.assertEqual(connection.sql("select count(*) from bronze_dividas").fetchone()[0], len(debts))
                self.assertEqual(DeltaTable(str(root / "delta/dividas")).version(), 3)
                self.assertEqual(original, {p.name: p.read_bytes() for p in raw.iterdir()})
