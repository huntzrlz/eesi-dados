# Jornada de dados - Grupo 1

Pipeline reprodutível para analisar superendividamento de servidores municipais com dados sintéticos. A pergunta respondida é: por secretaria, faixa de comprometimento e tipo de credor, qual dívida total, comprometimento médio e parcela mensal sugerida respeitam o piso mínimo existencial da PoC?

## Privacidade

Todos os dados em `data/raw/` são sintéticos. Não há CPF, nomes, matrículas reais, telefones ou e-mails.

## Estrutura

```text
data/raw -> Dados Originais em Delta -> Dados Preparados no dbt -> Indicadores -> Consumo
```

`src/pipeline.py` apenas captura e persiste as fontes. Limpeza, tipagem, quarentena e métricas são feitas nos modelos dbt.

## Execução em clone limpo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.pipeline
dbt build --project-dir . --profiles-dir .
```

Para mostrar a linhagem:

```powershell
dbt docs generate --project-dir . --profiles-dir .
dbt docs serve --project-dir . --profiles-dir .
```

Para demonstrar Delta Lake e time travel:

```powershell
python -m src.delta_demo
```

O resultado deve mostrar duas versões da tabela de dívidas: a versão 0 não contém `REC-TIME-TRAVEL`; a versão 1 contém.

Para executar a consulta final:

```powershell
python -c "import duckdb; print(duckdb.connect('data/conciliacao.duckdb').sql(open('sql/consulta_final.sql', encoding='utf-8').read()))"
```

## Defeitos deliberados

As fontes incluem moeda em formatos diferentes, renda vazia ou negativa, data inválida, secretaria com grafia variável, dívida negativa, credor fora do domínio e ID duplicado. Os defeitos permanecem nos Dados Originais e seguem para quarentena durante a preparação.

## Mapa de dependências

```text
bronze_formularios -> stg_formularios -> fct_divida_servidor -> int_servidor_mes -> int_divida_com_proposta -> resumo_proposta_quitacao
bronze_dividas     -> stg_dividas     -> fct_divida_servidor
stg_formularios -> quarentena_formularios
stg_dividas     -> quarentena_dividas
```

O dbt docs desenha automaticamente esse mapa a partir das referências entre modelos.

