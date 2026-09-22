"""Executa a mesma consulta SQL nos snapshots anterior e atual do Delta."""
from pathlib import Path
from uuid import uuid4
from src.clickhouse_client import connect, replace_arrow, identifier
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
    # Nome exclusivo para não substituir o Bronze nem colidir com outra demonstração.
    name = "delta_demo_" + uuid4().hex
    query = query.replace("dividas_snapshot", identifier(name))
    with connect() as client:
        try:
            for version in (current - 1, current):
                replace_arrow(client, name, DeltaTable(str(TABLE), version=version).to_pyarrow_table())
                result = client.query(query)
                print(f"Versao {version}: {result.column_names} = {result.result_rows}")
        finally:
            client.command(f"DROP TABLE IF EXISTS {identifier(name)}")


if __name__ == "__main__":
    main()
