"""Demonstra time travel na tabela Delta de dívidas."""
from pathlib import Path

from deltalake import DeltaTable

TABLE = Path(__file__).resolve().parents[1] / "data" / "bronze_delta" / "dividas"


def main() -> None:
    latest = DeltaTable(str(TABLE))
    print("Histórico:")
    for item in latest.history():
        print(f"versão {item['version']}: {item['operation']}")
    for version in (0, 1):
        rows = DeltaTable(str(TABLE), version=version).to_pyarrow_table().to_pylist()
        ids = {row["divida_id"] for row in rows}
        print(f"Versão {version}: {len(rows)} registros; REC-TIME-TRAVEL presente = {'REC-TIME-TRAVEL' in ids}")


if __name__ == "__main__":
    main()

