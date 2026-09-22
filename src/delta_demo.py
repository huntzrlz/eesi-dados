"""Executa a mesma consulta SQL nos snapshots anterior e atual do Delta."""
from pathlib import Path
import duckdb
from deltalake import DeltaTable

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "data" / "bronze_delta" / "dividas"


def main() -> None:
    latest = DeltaTable(str(TABLE))
    current = latest.version()
    if current < 1:
        raise SystemExit("Execute python -m src.pipeline para registrar pelo menos duas versoes.")
    query = (ROOT / "sql" / "time_travel.sql").read_text(encoding="utf-8")
    print("Consulta identica nas duas versoes:\n" + query)
    print("Historico:")
    for item in latest.history():
        print(f"versao {item['version']}: {item['operation']}")
    with duckdb.connect() as connection:
        for version in (current - 1, current):
            connection.register("dividas_snapshot", DeltaTable(str(TABLE), version=version).to_pyarrow_table())
            result = connection.sql(query)
            print(f"Versao {version}: {result.columns} = {result.fetchall()}")
            connection.unregister("dividas_snapshot")


if __name__ == "__main__":
    main()
