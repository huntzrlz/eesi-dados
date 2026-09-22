"""Regressões de preservação, repetição e reprocessamento em diretório temporário."""
import csv
import json
from collections import Counter
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import os
from uuid import uuid4
from src.clickhouse_client import connect, identifier, replace_arrow
import pyarrow as pa
from deltalake import DeltaTable
from src import pipeline


def values(rows):
    return Counter(json.dumps({k: v for k, v in row.items()
        if k not in {"arquivo_origem", "lote", "capturado_em"}}, sort_keys=True) for row in rows)


class PreservacaoTest(unittest.TestCase):
    def setUp(self):
        self.database = "test_preservacao_" + uuid4().hex
        self.environment = patch.dict(os.environ, {"CLICKHOUSE_DATABASE": self.database})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.drop_database)

    def drop_database(self):
        with connect() as client:
            client.command(f"DROP DATABASE {identifier(self.database)}")

    def test_captura_repeticao_e_reprocessamento(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw"
            shutil.copytree(pipeline.RAW, raw)
            original = {p.name: p.read_bytes() for p in raw.iterdir()}
            with patch.multiple(pipeline, RAW=raw, DELTA=root / "delta"):
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
                with connect() as connection:
                    self.assertEqual(connection.query("select count(*) from bronze_dividas").first_row[0], len(debts))
                    self.assertEqual(values(debts), values(list(connection.query("select * from bronze_dividas").named_results())))
                self.assertEqual(DeltaTable(str(root / "delta/dividas")).version(), 3)
                self.assertEqual(original, {p.name: p.read_bytes() for p in raw.iterdir()})

    def test_falha_na_carga_preserva_snapshot_publicado(self):
        original = pa.table({"id": ["1", "2"], "valor": ["R$ 1.234,56", None]})
        with connect() as client:
            replace_arrow(client, "bronze_teste", original)
            with patch.object(client, "insert_arrow", side_effect=RuntimeError("Falha simulada de transporte")):
                with self.assertRaisesRegex(RuntimeError, "Falha simulada"):
                    replace_arrow(client, "bronze_teste", pa.table({"id": ["3"], "valor": ["novo"]}))
            self.assertEqual(client.query("select id, valor from bronze_teste order by id").result_rows,
                             [("1", "R$ 1.234,56"), ("2", None)])
            self.assertEqual(client.query("SHOW TABLES").result_rows, [("bronze_teste",)])
