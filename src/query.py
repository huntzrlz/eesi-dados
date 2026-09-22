"""Executa a consulta de consumo no banco ClickHouse configurado."""
from pathlib import Path
from src.clickhouse_client import connect


def main() -> None:
    sql = (Path(__file__).resolve().parents[1] / "sql/consulta_final.sql").read_text(encoding="utf-8")
    with connect() as client:
        result = client.query(sql)
        print(" | ".join(result.column_names))
        for row in result.result_rows:
            print(" | ".join(str(value) for value in row))


if __name__ == "__main__":
    main()
