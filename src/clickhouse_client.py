"""Conexão compartilhada pelo Python; variáveis idênticas às do profiles.yml."""
from contextlib import contextmanager
import os
import re
from uuid import uuid4

import clickhouse_connect
import pyarrow as pa


def identifier(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Identificador ClickHouse inválido: {name!r}")
    return f"`{name}`"


@contextmanager
def connect():
    database = os.getenv("CLICKHOUSE_DATABASE", "conciliacao")
    quoted = identifier(database)
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "eesi"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "eesi_local_only"),
        secure=os.getenv("CLICKHOUSE_SECURE", "false").lower() == "true",
        database="default", settings={"join_use_nulls": 1},
    )
    try:
        client.command(f"CREATE DATABASE IF NOT EXISTS {quoted} ENGINE = Atomic")
        client.database = database
        yield client
    finally:
        client.close()


def replace_arrow(client, name: str, table: pa.Table) -> None:
    """Carga técnica: preserva texto/NULL e só publica após inserir todo o snapshot.

    Tabela intermediária evita expor um Bronze vazio se a inserção falhar.
    Requer banco Atomic; a troca é atômica por tabela, não por pipeline.
    """
    target = identifier(name)
    staging = identifier(f"{name}_load_{uuid4().hex}")
    for field in table.schema:
        if not (pa.types.is_string(field.type) or pa.types.is_large_string(field.type) or pa.types.is_null(field.type)):
            raise TypeError(f"Fonte esperada como texto bruto: {field.name} ({field.type})")
    columns = ", ".join(f"{identifier(field.name)} Nullable(String)" for field in table.schema)
    client.command(f"CREATE TABLE {staging} ({columns}) ENGINE = MergeTree ORDER BY tuple()")
    try:
        client.insert_arrow(staging.strip("`"), table)
        client.command(f"CREATE TABLE IF NOT EXISTS {target} ({columns}) ENGINE = MergeTree ORDER BY tuple()")
        client.command(f"EXCHANGE TABLES {target} AND {staging}")
    finally:
        client.command(f"DROP TABLE IF EXISTS {staging}")
