# Roteiro de demonstração

## Preparação

Siga a instalação do README e execute `python run.py` com o Python da `.venv-clickhouse`.
O fluxo deve terminar sem erro. Os totais dependem dos arquivos de entrada;
não confunda os dados ampliados locais com os dados publicados no Git.

## Evidências dos requisitos

| Requisito | Evidência a mostrar |
|---|---|
| 1. Fontes | `data/raw/`: formulários CSV e dívidas JSON; defeitos em DECISOES.md |
| 2. Ingestão | `src/pipeline.py`: leitura, metadados e persistência sem regras de negócio |
| 3. Bruto | Arquivos originais, Delta e reprocessamento `--from-delta` |
| 4. Transformações | Comentários SQL em `models/prepared/` e regras no DECISOES.md |
| 5. Consumo | Grão no topo de `models/consumption/resumo_proposta_quitacao.sql` |
| 6. Testes | `models/schema.yml`: 13 testes, quatro tipos; resultado do dbt build |
| 7. Linhagem | DAG no dbt docs, com sources e refs |
| 8. Resposta | `sql/consulta_final.sql`: leitura do consumo e filtro de período |
| 9. Delta | `python -m src.delta_demo`: mesmo SQL na versão anterior e atual |

## Mostrar a DAG

Na raiz, usando os executáveis da `.venv-clickhouse`, execute:

```text
dbt docs generate --project-dir . --profiles-dir .
dbt docs serve --project-dir . --profiles-dir . --port 8080
```

Abra http://localhost:8080 e acesse a visualização de linhagem. Selecione
`resumo_proposta_quitacao` e seus ancestrais. Mostre fontes, preparação,
indicadores e consumo. Encerre o servidor com Ctrl+C.

## Mostrar o time travel

```text
python -m src.delta_demo
```

Mostre o SQL impresso (também em `sql/time_travel.sql`), os números das versões
e os dois resultados. A contagem cresce com o lote 02 e `REC-TIME-TRAVEL` passa
a estar presente. Reexecute a ingestão: versões antigas continuam no histórico.

## Mostrar a resposta e o reprocessamento

`run.py` imprime o resultado de `sql/consulta_final.sql`. Explique que o WHERE
apenas seleciona agosto de 2026; regras financeiras já estão nos modelos.
Execute `python -m src.pipeline --from-delta` e depois `dbt build` para demonstrar
reconstrução a partir do bruto preservado. A apresentação ao vivo deve ser feita
pela equipe; este roteiro e os artefatos não substituem essa etapa.

## Ambiente ClickHouse

Antes da apresentação, execute `docker compose up -d --wait` e siga o README.
Use `python -m src.query` para mostrar a consulta final sem repetir toda a carga.
As variáveis de conexão devem ser iguais nas etapas Python e dbt.
A demonstração usa ClickHouse 25.8.4.13 e dbt-clickhouse 1.10.3, mantendo o Delta
para os snapshots. O arquivo antigo do banco anterior não participa da execução.

## Validação da migração

Executado em Windows/Python 3.13 contra ClickHouse 25.8.4.13 em Docker:

- `pip check`: sem conflitos no ambiente novo, com requisitos fixados.
- Dois testes Python aprovados: preservação/reprocessamento e falha de carga
  sem perda do snapshot anterior.
- Fontes ampliadas locais e fontes versionadas no Git: oito modelos e 16 testes
  dbt aprovados em cada conjunto, sem erros.
- Reconstrução `--from-delta` e novo `dbt build`: 24/24 etapas aprovadas.
- Documentação gerada; página, manifesto ClickHouse e catálogo servidos por HTTP.
- Time travel: SQL idêntico sobre 802/1.601 registros nas fontes ampliadas e
  6/7 registros nas fontes do Git. Consulta final executada nos dois conjuntos.

A CI Ubuntu foi atualizada para iniciar o mesmo servidor e repetir o fluxo.
Estas evidências correspondem à validação local; a apresentação ao vivo ainda
é responsabilidade da equipe. Os dados ampliados locais não são incluídos
nesta atualização de scripts e documentos.
