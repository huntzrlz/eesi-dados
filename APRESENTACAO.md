# Roteiro de demonstração

## Preparação

Siga a instalação do README e execute `python run.py` com o Python da `.venv`.
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

Na raiz, usando os executáveis da `.venv`, execute:

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

## Validação realizada

Validação local em Windows/Python 3.13, com as dependências fixadas:

- Fontes publicadas no Git: oito modelos e 15 testes dbt concluídos sem erros;
  mesma consulta Delta retornou 6 registros na versão 0 e 7 na versão 1.
- Cópia dos dados ampliados locais: oito modelos e 15 testes concluídos sem erros;
  snapshots comparados retornaram 802 e 1.601 registros.
- Teste Python de preservação, reexecução e reconstrução via Delta: aprovado.
- `dbt docs serve`: página inicial, manifest.json e catalog.json responderam por HTTP.
- Consulta final executada nos dois conjuntos. A exclusão de todas as duplicatas
  removeu `DIV-004` dos fatos; o teste SQL impede sua reintrodução pela quarentena.

Os dados ampliados locais não fazem parte desta atualização de scripts e documentos.
A CI foi configurada para repetir os testes em Windows e Linux; esta evidência
registra a execução local, sem afirmar execução remota ou apresentação ao vivo.
