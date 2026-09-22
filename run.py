"""Executa ingestão, modelos/testes dbt, documentação e consulta final."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main() -> None:
    # Cada processo usa o mesmo Python e fecha suas conexões antes da próxima etapa.
    subprocess.run([sys.executable, '-m', 'src.pipeline'], cwd=ROOT, check=True)
    for command in (['debug'], ['build'], ['docs', 'generate']):
        subprocess.run(
            [sys.executable, '-c', 'from dbt.cli.main import cli; cli()', *command,
             '--project-dir', str(ROOT), '--profiles-dir', str(ROOT)],
            cwd=ROOT, check=True,
        )
    subprocess.run([sys.executable, '-m', 'src.delta_demo'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, '-m', 'src.query'], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
