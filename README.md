# Jornada de dados - Grupo 1

Pipeline de superendividamento com fontes sintéticas, Delta Lake, dbt e ClickHouse.
Pergunta: por secretaria, faixa de comprometimento e tipo de credor, qual a dívida
total, o comprometimento médio e a parcela sugerida respeitando o piso da PoC?

## Arquitetura

```text
CSV + JSON em data/raw -> bruto preservado em Delta -> Bronze no ClickHouse
    -> dbt: Preparados -> Indicadores -> Consumo no ClickHouse
```

O dbt fica na raiz: `dbt_project.yml`, `profiles.yml` e `models/`. Os modelos SQL
limpam, tipam, cruzam dados e calculam os indicadores. As regras e a escolha de
tabela larga estão em [DECISOES.md](DECISOES.md).

## Instalação e execução

Requisitos: Git, Python 3.13 e Docker com Compose v2. No Windows, inicie o Docker
Desktop com containers Linux. A primeira instalação precisa de internet.
O servidor é ClickHouse **25.8.4.13**, fixado em `compose.yaml`.

PowerShell, na raiz do repositório:

```powershell
git clone https://github.com/huntzrlz/eesi-dados.git
cd eesi-dados
docker compose up -d --wait
python -m venv .venv-clickhouse
.\.venv-clickhouse\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv-clickhouse\Scripts\python.exe run.py
```

Linux/macOS, com Python 3.13 disponível como `python3`:

```bash
git clone https://github.com/huntzrlz/eesi-dados.git
cd eesi-dados
docker compose up -d --wait
python3 -m venv .venv-clickhouse
.venv-clickhouse/bin/python -m pip install -r requirements-lock.txt
.venv-clickhouse/bin/python run.py
```

Se já clonou, atualize o código e execute os comandos a partir de `docker compose`.
O ambiente `.venv-clickhouse` separa as novas dependências do ambiente antigo.
`requirements.txt` fixa dependências diretas e o lock fixa também as transitivas.
O arquivo antigo `data/conciliacao.duckdb`, se existir, não é lido nem migrado:
os modelos são reconstruídos a partir das fontes ou do Delta preservado.

`run.py` executa ingestão, `dbt debug`, `dbt build`, geração da documentação,
time travel e consulta final. Interrompe ao encontrar erro. Todos os caminhos
são resolvidos a partir da raiz do script.

## Conexão ClickHouse

Python e dbt usam as mesmas variáveis de ambiente:

| Variável | Padrão local |
|---|---|
| `CLICKHOUSE_HOST` | `localhost` |
| `CLICKHOUSE_PORT` | `8123` (HTTP) |
| `CLICKHOUSE_USER` | `eesi` |
| `CLICKHOUSE_PASSWORD` | `eesi_local_only` |
| `CLICKHOUSE_DATABASE` | `conciliacao` |
| `CLICKHOUSE_SECURE` | `false` |

As credenciais padrão são exclusivamente para a demonstração local. O Compose
publica a porta apenas em `127.0.0.1` e mantém os dados em volume persistente.
Para outra instalação, defina as variáveis no terminal antes de executar Python
e dbt; para HTTPS, use `CLICKHOUSE_SECURE=true` e a porta do servidor (geralmente
8443). Os scripts não carregam `.env` automaticamente. O banco precisa usar o
engine `Atomic`; o usuário deve poder criar banco/tabelas, inserir, consultar,
trocar tabelas e removê-las. Os testes criam bancos exclusivos temporários.

Exemplo PowerShell de seleção de banco:

```powershell
$env:CLICKHOUSE_DATABASE = 'conciliacao'
```

Em bash: `export CLICKHOUSE_DATABASE=conciliacao`.

## Etapas individuais

PowerShell, na raiz e com o servidor ativo:

```powershell
.\.venv-clickhouse\Scripts\python.exe -m src.pipeline
.\.venv-clickhouse\Scripts\dbt.exe debug --project-dir . --profiles-dir .
.\.venv-clickhouse\Scripts\dbt.exe build --project-dir . --profiles-dir .
.\.venv-clickhouse\Scripts\dbt.exe docs generate --project-dir . --profiles-dir .
.\.venv-clickhouse\Scripts\dbt.exe docs serve --project-dir . --profiles-dir .
```

O servidor dbt docs fica ativo até Ctrl+C. Abra a página indicada no terminal
para mostrar a DAG. Para consultar o resultado e demonstrar time travel:

```powershell
.\.venv-clickhouse\Scripts\python.exe -m src.query
.\.venv-clickhouse\Scripts\python.exe -m src.delta_demo
```

A consulta final é `sql/consulta_final.sql`, executada no banco configurado.
O WHERE apenas filtra o mês. O time travel lê versões do Delta com `deltalake`,
carrega cada snapshot em uma tabela auxiliar exclusiva no ClickHouse e executa
o mesmo `sql/time_travel.sql`. A tabela auxiliar é removida ao terminar.
O snapshot anterior contém o lote 01; o atual inclui o lote 02 e
`REC-TIME-TRAVEL`. Números de versão aumentam a cada nova captura.

Em Linux/macOS, use `.venv-clickhouse/bin/python` e `.venv-clickhouse/bin/dbt`
no lugar dos executáveis em `Scripts`.

## Preservação e reprocessamento

`data/raw/` guarda CSV/JSON originais; Delta guarda os valores capturados e
metadados, inclusive defeitos. A ingestão não faz cálculos de negócio.
Reexecutar cria novos snapshots Delta, sem apagar os anteriores ou duplicar
registros no snapshot atual. Não execute VACUUM antes da demonstração.

Para reconstruir o Bronze ClickHouse sem reler fontes nem criar versões Delta:

```powershell
.\.venv-clickhouse\Scripts\python.exe -m src.pipeline --from-delta
.\.venv-clickhouse\Scripts\dbt.exe build --project-dir . --profiles-dir .
```

A carga insere em uma tabela intermediária e faz troca atômica por tabela após
concluir. O pipeline inteiro não é uma transação: execute uma instância por banco
e repita a carga se houver interrupção antes de construir o consumo.

## Testes

Com ClickHouse ativo:

```powershell
.\.venv-clickhouse\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

Os dois testes Python verificam bruto intacto, histórico entre reexecuções,
reconstrução via Delta e igualdade dos valores carregados no ClickHouse. Também
simulam falha de inserção para garantir que o snapshot anterior permaneça disponível.
O `dbt build` executa 13 testes de schema (quatro tipos) e três testes SQL:
quarentena fora dos fatos, proposta dentro da capacidade e conversões de datas/moeda.
A CI em Ubuntu inicia o mesmo Compose antes de executar testes e pipeline.

## Fontes, defeitos e apresentação

Todos os dados são sintéticos. Fontes: formulários CSV e dívidas JSON em dois
lotes. Há moeda com formatos diferentes, renda ausente/negativa, data impossível,
grafias de secretaria, saldo negativo, credor fora do domínio e dívida duplicada.
Variações recuperáveis são normalizadas; inválidos e todas as ocorrências de
IDs de dívida duplicados ficam na quarentena, fora do consumo.

Consulte [APRESENTACAO.md](APRESENTACAO.md) para mostrar os nove requisitos.
Para parar o servidor mantendo o volume: `docker compose down`.
Para reiniciar: `docker compose up -d --wait`.

Integrações utilizadas: [dbt-clickhouse](https://clickhouse.com/docs/integrations/dbt)
e [ClickHouse Connect](https://clickhouse.com/docs/integrations/language-clients/python/advanced-inserting).
