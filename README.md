# Jornada de dados - Grupo 1

Pipeline para analisar superendividamento de servidores municipais com dados sintéticos.
Por secretaria, faixa de comprometimento e tipo de credor, calcula dívida total,
comprometimento médio e parcela mensal sugerida respeitando o piso da PoC.

## Transformação e enriquecimento dos dados

A transformação é realizada pelo dbt, com os modelos SQL organizados em
`models/`. Esses modelos fazem a limpeza, o cruzamento dos dados e o cálculo
dos indicadores.

A configuração do dbt (`dbt_project.yml` e `profiles.yml`) fica na raiz do
repositório. Execute os comandos apresentados a seguir dentro da pasta
`eesi-dados`.

## Execução em clone limpo

Pré-requisitos: Git e Python 3.13 (versão usada na validação).
A instalação das dependências requer internet. Não é necessário servidor de banco.

Windows / PowerShell, sem necessidade de ativar o ambiente virtual:

```powershell
git clone https://github.com/huntzrlz/eesi-dados.git
cd eesi-dados
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe run.py
```

Linux / macOS, com Python 3.13 disponível como `python3`:

```bash
git clone https://github.com/huntzrlz/eesi-dados.git
cd eesi-dados
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python run.py
```

`run.py` executa ingestão, modelos e testes (`dbt build`), geração da documentação,
demonstração Delta e consulta final. Interrompe em caso de falha. Resolve os caminhos
a partir do script, mesmo quando chamado por caminho absoluto de outra pasta.

`requirements.txt` fixa dependências diretas; `requirements-lock.txt` fixa também
as transitivas usadas na validação. Use o lock para reproduzir o ambiente.

Cada execução registra novos snapshots em `data/bronze_delta/` e atualiza
`data/conciliacao.duckdb`. O histórico anterior é preservado; o snapshot atual
não acumula duplicações entre execuções. Os resultados são locais e não devem
ser versionados. Não apague os arquivos Delta nem execute VACUUM antes da apresentação.
Feche outras conexões ao DuckDB antes de executar novamente.

## Etapas individuais

Execute a partir da raiz, após instalar as dependências:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline
.\.venv\Scripts\dbt.exe build --project-dir . --profiles-dir .
.\.venv\Scripts\dbt.exe docs generate --project-dir . --profiles-dir .
.\.venv\Scripts\dbt.exe docs serve --project-dir . --profiles-dir .
```

O servidor de documentação fica ativo até Ctrl+C. A linhagem é gerada a partir
das referências entre modelos.

Demonstração Delta Lake e time travel:

```powershell
.\.venv\Scripts\python.exe -m src.delta_demo
```

O script executa o mesmo SQL de `sql/time_travel.sql` na versão anterior e na
atual. Na primeira execução, são as versões 0 e 1; nas seguintes, os números
aumentam. O snapshot anterior contém o lote 01; o atual contém os dois lotes.
O registro `REC-TIME-TRAVEL` aparece somente no segundo lote.

Consulta final:

```powershell
.\.venv\Scripts\python.exe -c "import duckdb; print(duckdb.connect('data/conciliacao.duckdb', read_only=True).sql(open('sql/consulta_final.sql', encoding='utf-8').read()).fetchall())"
```

Em Linux/macOS, substitua `.\.venv\Scripts\python.exe` por `.venv/bin/python`
e `.\.venv\Scripts\dbt.exe` por `.venv/bin/dbt` nos comandos individuais.

## Estrutura e privacidade

Todos os dados em `data/raw/` são sintéticos. Não há CPF, nomes, matrículas reais,
telefones ou e-mails. `src/pipeline.py` apenas captura e persiste as fontes.
Limpeza, tipagem, quarentena e métricas são feitas nos modelos dbt.

```text
data/raw -> Dados Originais em Delta -> Dados Preparados no dbt -> Indicadores -> Consumo
```

As fontes incluem moeda em formatos diferentes, renda vazia ou negativa, data
inválida, secretaria com grafia variável, dívida negativa, credor fora do domínio
e ID duplicado. Os defeitos permanecem nos Dados Originais. Variações de formato são
normalizadas; registros inválidos e todas as ocorrências de IDs de dívida
duplicados seguem para quarentena e ficam fora do consumo.

```text
bronze_formularios -> stg_formularios -> fct_divida_servidor -> int_servidor_mes -> int_divida_com_proposta -> resumo_proposta_quitacao
bronze_dividas     -> stg_dividas     -> fct_divida_servidor
stg_formularios -> quarentena_formularios
stg_dividas     -> quarentena_dividas
```

## Reprocessamento do bruto preservado

Para reconstruir as tabelas Bronze do DuckDB sem reler CSV/JSON nem gerar novos
commits Delta, execute na raiz:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline --from-delta
.\.venv\Scripts\dbt.exe build --project-dir . --profiles-dir .
```

Os arquivos originais ficam em `data/raw/`; Delta preserva os valores capturados,
inclusive defeitos, mais metadados técnicos. O reprocessamento usa o snapshot
atual de cada tabela Delta. A captura das duas tabelas não é uma transação única;
se for interrompida, execute a ingestão novamente antes de reconstruir o consumo.

## Verificação e apresentação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

O `dbt build` executa os 13 testes de `models/schema.yml` (quatro tipos) e dois
testes SQL adicionais: ausência de dívidas em quarentena nos fatos e respeito
à capacidade de pagamento. Os testes Python verificam a preservação do bruto,
o histórico entre reexecuções e o reprocessamento sem acesso às fontes.

Veja [DECISOES.md](DECISOES.md) para as regras e
[APRESENTACAO.md](APRESENTACAO.md) para demonstrar os nove requisitos.
