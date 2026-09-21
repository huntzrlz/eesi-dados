"""Executa ingestão, modelos/testes dbt, documentação e consulta final."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main() -> None:
    import duckdb

    # Cada processo usa o mesmo Python e fecha suas conexões antes da próxima etapa.
    subprocess.run([sys.executable, '-m', 'src.pipeline'], cwd=ROOT, check=True)
    for command in (['build'], ['docs', 'generate']):
        subprocess.run(
            [sys.executable, '-c', 'from dbt.cli.main import cli; cli()', *command,
             '--project-dir', str(ROOT), '--profiles-dir', str(ROOT)],
            cwd=ROOT, check=True,
        )
    subprocess.run([sys.executable, '-m', 'src.delta_demo'], cwd=ROOT, check=True)
    with duckdb.connect(str(ROOT / 'data' / 'conciliacao.duckdb'), read_only=True) as connection:
        result = connection.sql((ROOT / 'sql' / 'consulta_final.sql').read_text(encoding='utf-8'))
        print(' | '.join(result.columns))
        for row in result.fetchall():
            print(' | '.join(str(value) for value in row))


if __name__ == '__main__':
    main()
