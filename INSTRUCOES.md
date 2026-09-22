# INSTRUÇÕES — roteiro para defesa do projeto

## 1. Abertura: qual problema resolvemos?

**Fala sugerida:**

> “Construímos uma prova de conceito para analisar o superendividamento de
> servidores municipais. A pergunta é: por secretaria, faixa de comprometimento
> e tipo de credor, qual é a dívida total, o comprometimento médio e a parcela
> mensal sugerida que respeita a renda protegida definida para a PoC?”

Os dados são sintéticos. O resultado é uma proposta analítica de demonstração;
a política real de conciliação depende de definição jurídica, social e gerencial.
O piso configurado no projeto é de R$ 1.200, como parâmetro da PoC.

**Mostrar:** [README.md](README.md), a pergunta inicial, e
[DECISOES.md](DECISOES.md), a justificativa das regras.

## 2. O que foi construído e revisado

Organizamos fontes CSV e JSON, ingestão Python, preservação histórica em Delta
Lake, transformação e testes dbt e uma tabela de consumo orientada à pergunta.
A arquitetura tem quatro etapas: Originais, Preparados, Indicadores e Consumo.
Ela cumpre as funções do Medallion, embora use nomes próprios para as camadas.

Na revisão, esclarecemos que a configuração dbt fica na raiz do projeto,
centralizamos a execução em `run.py`, fixamos dependências e documentamos as
regras. Ajustamos as duplicatas para que todas as ocorrências permaneçam em
quarentena, preservamos versões Delta entre execuções e adicionamos testes.
Por fim, migramos o motor analítico de DuckDB para ClickHouse, incluindo SQL,
conexão, ingestão, consultas, testes e infraestrutura Docker.

**Argumento para a banca:** a solução separa captura, qualidade, cálculo e
apresentação. Isso permite explicar de onde vem cada resultado e reconstruí-lo.

## 3. Ordem de precedência: o que depende de quê?

A ordem alfabética das pastas no editor não determina a execução. Existem
pré-requisitos de ambiente e dependências de dados. O dbt resolve a ordem dos
modelos por `source()` e `ref()`, não pelo nome da pasta ou do arquivo.

```text
PRÉ-REQUISITOS
  requirements-lock.txt -> ambiente .venv-clickhouse
  compose.yaml          -> servidor ClickHouse disponível
  profiles.yml          -> conexão do dbt
  dbt_project.yml       -> modelos, materialização e parâmetros

FLUXO DOS DADOS
  data/raw/ (CSV + JSON)
    -> src/pipeline.py
    -> data/bronze_delta/ (valores brutos + metadados + versões)
    -> src/clickhouse_client.py
    -> bronze_formularios e bronze_dividas no ClickHouse
    -> models/sources.yml identifica essas tabelas para o dbt
    -> models/prepared/ usa macros/normalizacao.sql
    -> models/indicators/
    -> models/consumption/
    -> sql/consulta_final.sql, executada por src/query.py

VERIFICAÇÃO E EVIDÊNCIAS
  models/schema.yml + tests/*.sql -> testes durante dbt build
  tests/test_preservacao.py       -> testes Python executados separadamente
  dbt docs generate              -> target/ (catálogo e linhagem)
  src/delta_demo.py              -> compara snapshots Delta no ClickHouse
```

`profiles.yml` e `src/clickhouse_client.py` usam as mesmas variáveis de ambiente
`CLICKHOUSE_*`. Quando definidas, elas substituem os padrões locais de conexão.
O `schema` do perfil dbt corresponde ao database ClickHouse. Não é necessário
entrar em uma pasta `transformacao_dbt`: o projeto dbt está na raiz.

## 4. Como explicar cada diretório da imagem

| Diretório | Papel e momento de uso | Como apresentar |
|---|---|---|
| `.github/` | Contém o workflow que inicia ClickHouse e executa testes/pipeline em Ubuntu nos eventos de push e pull request. | “Automatizamos a verificação para facilitar a reprodução por outros colegas.” A configuração não substitui mostrar o resultado de uma execução da CI. |
| `.validation/` | Cópias e logs locais usados nas verificações da revisão; ignorados pelo Git. | Apoio de desenvolvimento, sem dependência no fluxo oficial. |
| `.venv/` | Ambiente Python anterior, que pode permanecer na máquina. | A migração usa o ambiente novo; esta pasta não é uma camada de dados. |
| `.venv-clickhouse/` | Ambiente Python da versão atual, com as bibliotecas do lock. | Necessário antes de executar scripts e dbt; não é versionado. |
| `data/` | `raw/` contém fontes; `bronze_delta/` contém snapshots e logs Delta gerados. | Mostrar a diferença entre arquivo de origem e representação histórica capturada. |
| `logs/` | Logs gerados pelo dbt para diagnóstico. | Evidência de execução e investigação de falhas; não é dado de negócio. |
| `macros/` | SQL reutilizável para converter moeda e data no ClickHouse. | As mesmas regras são reutilizadas pelos modelos, evitando divergência entre colunas. |
| `models/` | Declara fontes, transforma, calcula indicadores, consolida consumo e define testes de schema. | É o núcleo da transformação, executado pelo dbt no ClickHouse. |
| `sql/` | Consultas de resposta e comparação temporal. | A consulta final lê métricas prontas; o SQL temporal compara snapshots. |
| `src/` | Código Python de ingestão, conexão, consulta e demonstração Delta. | O Python transporta dados e coordena acesso; as regras financeiras ficam no dbt. |
| `target/` | SQL compilado e artefatos dbt, como `manifest.json`, `catalog.json` e `index.html`. | Saída gerada para inspeção e linhagem; não deve ser editada manualmente. |
| `tests/` | Testes SQL adicionais e testes Python de preservação/carga. | Explicar as garantias testadas, além de simplesmente mostrar uma mensagem de sucesso. |

As tabelas analíticas não ficam em arquivos dentro de `models/`: os arquivos
são suas definições SQL; os dados materializados ficam no ClickHouse, no volume
Docker persistente definido no Compose.

## 5. Como explicar os arquivos da raiz

| Arquivo | Responsabilidade | Precedência ou relação |
|---|---|---|
| `.gitignore` | Evita versionar ambientes, logs, resultados locais e credenciais em `.env`. | Atua no versionamento; não executa o pipeline. Não remove automaticamente arquivos que já foram rastreados. |
| `.user.yml` | Metadado local gerado pelo dbt, ignorado pelo Git. | Não define a conexão nem contém regras de transformação. |
| `compose.yaml` | Define versão do servidor, porta local, usuário, volume e healthcheck. | O servidor precisa estar disponível antes da carga e do dbt. |
| `requirements.txt` | Declara e fixa dependências diretas do projeto. | Explica as bibliotecas escolhidas. |
| `requirements-lock.txt` | Fixa também as dependências transitivas. | É o arquivo usado na instalação reproduzível. |
| `profiles.yml` | Configura o adaptador ClickHouse e a conexão do dbt. | É lido por `dbt debug`, `build` e comandos de documentação. |
| `dbt_project.yml` | Define projeto, diretório de modelos, tabelas MergeTree e piso da PoC. | Orienta a compilação e a execução dos modelos. |
| `run.py` | Coordena a execução completa e interrompe em caso de falha. | Executa as etapas na sequência descrita abaixo. |
| `README.md` | Guia operacional de instalação, conexão e execução. | Use para preparar a máquina. |
| `DECISOES.md` | Justifica arquitetura, grão, regras, limitações e migração. | Use para defender as escolhas técnicas e de negócio. |
| `APRESENTACAO.md` | Checklist das evidências dos nove requisitos e comandos de demonstração. | Use para conferir se todas as evidências foram mostradas. |
| `INSTRUCOES.md` | Este roteiro: narrativa, dependências e papel dos componentes. | Use como guia de fala durante a defesa. |

Os documentos se complementam; não são etapas executáveis. Os símbolos `M` e
`U` exibidos pelo editor indicam, respectivamente, arquivo modificado e arquivo
não rastreado pelo Git. Eles não representam prioridade nem ordem de execução.

## 6. Roteiro da apresentação por etapa

### Etapa 1 — Fontes e defeitos deliberados

**Mostrar:** `data/raw/formularios_servidores.csv` e os dois arquivos
`dividas_credores_lote_01.json` e `dividas_credores_lote_02.json`.

**Fala sugerida:**

> “Temos duas fontes lógicas em dois formatos: formulários em CSV e dívidas em
> JSON, recebidas em dois lotes. Inserimos defeitos deliberados para demonstrar
> como o pipeline identifica e trata problemas de qualidade.”

Exemplos: moeda brasileira e decimal com ponto, renda vazia ou negativa, data
impossível, variações de secretaria, saldo negativo, credor fora do domínio e
ID de dívida duplicado. Não apresente o segundo lote JSON como um terceiro
formato: são dois formatos e duas fontes lógicas.

### Etapa 2 — Captura sem regra de negócio

**Mostrar:** `src/pipeline.py`, funções de leitura e `capture_metadata`.

**Fala sugerida:**

> “Nesta etapa, não calculamos capacidade nem corrigimos renda. Lemos as fontes
> e registramos arquivo de origem, lote e instante da captura para rastreabilidade.”

Depois da leitura, o pipeline grava Delta e carrega os snapshots no ClickHouse.
`src/clickhouse_client.py` centraliza a conexão e a publicação das tabelas Bronze.
A carga usa texto com possibilidade de NULL para manter os valores de origem.

### Etapa 3 — Preservação e histórico Delta

**Mostrar:** `data/bronze_delta/`, incluindo os diretórios `_delta_log`.

**Fala sugerida:**

> “Preservamos os arquivos originais e mantemos seus valores capturados no Delta.
> Isso permite reconstruir as camadas derivadas sem corrigir ou apagar a evidência
> de origem. O histórico também permite consultar estados anteriores.”

O lote 01 cria um snapshot; o lote 02 acrescenta registros no seguinte.
Reexecutar cria novas versões, preservando as anteriores, sem acumular cópias de
execuções passadas no snapshot atual. Delta preserva valores e metadados; os
arquivos CSV/JSON preservam a formatação textual original.

### Etapa 4 — ClickHouse e entrada no dbt

**Mostrar:** `compose.yaml`, `profiles.yml`, `models/sources.yml`.

**Fala sugerida:**

> “Usamos ClickHouse como motor analítico e Delta como preservação histórica.
> O Compose padroniza o servidor para a equipe. O dbt identifica as duas tabelas
> Bronze como fontes e passa a controlar as dependências das transformações.”

A versão do servidor é fixada. A carga usa tabela intermediária e troca atômica
após concluir a inserção: uma falha de carga não deve publicar uma tabela vazia.
A atomicidade é por tabela, não pelo pipeline inteiro. A PoC deve executar uma
instância do fluxo por banco de cada vez.

### Etapa 5 — Preparação e quarentena

**Mostrar:** `macros/normalizacao.sql` e `models/prepared/`.

| Modelo | O que faz | Por que faz |
|---|---|---|
| `stg_formularios.sql` | Tipagem de renda/despesa/data, padronização de secretaria e validação. | Evita calcular indicadores com renda inválida ou separar a mesma secretaria por grafia. |
| `stg_dividas.sql` | Tipagem monetária, padronização de credor, validação e contagem de IDs repetidos. | Evita somas com saldos inválidos e identifica duplicidade entre lotes. |
| `quarentena_formularios.sql` | Mantém formulários rejeitados e o motivo. | Preserva a possibilidade de auditoria e correção na fonte. |
| `quarentena_dividas.sql` | Mantém dívidas inválidas e todas as ocorrências duplicadas. | Impede escolher arbitrariamente uma dívida como correta. |

**Fala sugerida:**

> “Variações de formato recuperáveis são normalizadas. Valores inválidos não
> viram zero: continuam auditáveis na quarentena. Para uma dívida duplicada,
> excluímos todas as ocorrências dos fatos até que a fonte seja corrigida.”

Os modelos `stg_*` conservam registros e sinalizam validade; a filtragem para
cálculo acontece na camada seguinte. As duas quarentenas são ramificações da
preparação, não etapas que precisam ser lidas para calcular os indicadores.

### Etapa 6 — Indicadores e regras financeiras

**Mostrar nesta ordem:**

1. `models/indicators/fct_divida_servidor.sql`: cruza dívidas válidas e não
   duplicadas com formulários válidos. Grão: dívida, servidor e mês.
2. `models/indicators/int_servidor_mes.sql`: consolida por servidor e mês,
   calcula renda protegida, capacidade e comprometimento e classifica a faixa.
3. `models/indicators/int_divida_com_proposta.sql`: distribui a proposta entre
   dívidas proporcionalmente ao saldo.

**Fala sugerida:**

> “Primeiro garantimos a qualidade dos registros, depois aplicamos as regras.
> Protegemos o maior valor entre a despesa básica declarada e o piso parametrizado.
> A capacidade é o excedente da renda, nunca negativo. A proposta é limitada
> tanto pela capacidade quanto pelo saldo total.”

```text
renda protegida = maior(despesa básica, piso da PoC)
capacidade = maior(renda líquida - renda protegida, 0)
comprometimento (%) = 100 × parcelas atuais / renda líquida
proposta total = menor(capacidade, dívida total)
proposta de cada dívida = proposta total × saldo da dívida / dívida total
```

Renda e despesa não são somadas uma vez por dívida: o modelo evita esse efeito
antes de calcular a capacidade. Valores monetários são Decimal; percentuais e
rateio usam Float64, com tolerância de um centavo no teste de capacidade.

### Etapa 7 — Camada de consumo e resposta

**Mostrar:** `models/consumption/resumo_proposta_quitacao.sql`, especialmente o
comentário inicial que declara o grão; depois `sql/consulta_final.sql`.

**Fala sugerida:**

> “Cada linha da tabela de consumo representa um mês, uma secretaria, uma faixa
> de comprometimento e um tipo de credor. Escolhemos uma tabela larga agregada
> porque a pergunta é conhecida e o relatório pode ler todas as métricas sem
> refazer joins ou cálculos de negócio.”

A consulta final, executada por `src/query.py`, seleciona resultados prontos.
Seu WHERE apenas delimita agosto de 2026. O comprometimento médio atual é uma
média por dívida no grupo: servidores com mais dívidas têm maior peso. Não o
apresente como média de pessoas distintas. A contagem de servidores é distinta
dentro de cada grupo e não deve ser somada entre grupos como se fosse um total
único de pessoas.

### Etapa 8 — Testes e linhagem

**Mostrar:** `models/schema.yml`, `tests/` e a DAG no dbt docs.

**Fala sugerida:**

> “Validamos presença, unicidade, domínios e relacionamentos. Também verificamos
> que a quarentena não entra nos fatos, que a proposta respeita a capacidade e
> que as conversões no ClickHouse tratam os formatos e as datas inválidas.”

Há 13 testes de schema, dos tipos `not_null`, `unique`, `accepted_values` e
`relationships`, mais três testes SQL: total de 16 testes dbt. Somados aos oito
modelos, o build validado apresenta 24 etapas bem-sucedidas. São 16 testes,
não 24 testes. Dois testes Python adicionais verificam preservação,
reprocessamento e manutenção do snapshot anterior quando uma carga falha.

A DAG mostra a procedência dos dados e as dependências declaradas com `ref()`
e `source()`. `dbt docs generate` produz os artefatos; `dbt docs serve` os exibe.
O servidor de documentação precisa ser iniciado separadamente de `run.py`.

### Etapa 9 — Time travel e reconstrução

**Mostrar:** `src/delta_demo.py`, `sql/time_travel.sql` e os dois resultados.

**Fala sugerida:**

> “Lemos a versão anterior e a atual do Delta e executamos exatamente a mesma
> consulta sobre cada snapshot no ClickHouse. Assim, a diferença do resultado
> decorre da versão dos dados, não de uma mudança no SQL.”

O script usa uma tabela auxiliar exclusiva, removida ao terminar. O lote 02
introduz `REC-TIME-TRAVEL`, e a consulta evidencia essa inclusão. Nas fontes
publicadas usadas na validação, os snapshots tinham 6 e 7 dívidas; na cópia
ampliada validada, 802 e 1.601. Confirme os números do conjunto usado na banca:
os dados locais ampliados ainda não foram incluídos nos commits da migração.

A opção `--from-delta` reconstrói as tabelas Bronze do ClickHouse sem reler os
CSV/JSON nem criar novas versões Delta. Depois, `dbt build` recompõe as demais
camadas. Isso demonstra a utilidade prática do bruto preservado.

## 7. Sequência de execução para ensaiar

Pré-requisitos: Git, Python 3.13 e Docker Desktop ativo com containers Linux
no Windows. Abra o PowerShell na raiz do projeto. Para instalar do zero,
consulte também [README.md](README.md).

```powershell
# 1. Iniciar o banco e aguardar sua disponibilidade.
docker compose up -d --wait

# 2. Preparar o Python (criar o ambiente somente se ainda não existir).
python -m venv .venv-clickhouse
.\.venv-clickhouse\Scripts\python.exe -m pip install -r requirements-lock.txt

# 3. Executar os dois testes Python separadamente.
.\.venv-clickhouse\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"

# 4. Executar o fluxo completo.
.\.venv-clickhouse\Scripts\python.exe run.py
```

A ordem real de `run.py` é:

1. `src.pipeline`: captura, preserva no Delta e carrega Bronze no ClickHouse.
2. `dbt debug`: verifica configuração e conexão.
3. `dbt build`: executa modelos e testes na ordem da DAG.
4. `dbt docs generate`: gera catálogo e linhagem em `target/`.
5. `src.delta_demo`: demonstra a consulta nas duas versões Delta.
6. `src.query`: imprime a resposta da consulta final.

Para apresentar sem repetir a carga completa:

```powershell
# Resultado final.
.\.venv-clickhouse\Scripts\python.exe -m src.query

# Comparação entre versões.
.\.venv-clickhouse\Scripts\python.exe -m src.delta_demo

# DAG: abrir http://localhost:8080; encerrar o servidor com Ctrl+C.
.\.venv-clickhouse\Scripts\dbt.exe docs serve --project-dir . --profiles-dir . --port 8080
```

Após encerrar o servidor de documentação, a reconstrução pode ser demonstrada:

```powershell
.\.venv-clickhouse\Scripts\python.exe -m src.pipeline --from-delta
.\.venv-clickhouse\Scripts\dbt.exe build --project-dir . --profiles-dir .
```

Em Linux/macOS, os executáveis correspondentes ficam em
`.venv-clickhouse/bin/python` e `.venv-clickhouse/bin/dbt`.

## 8. Perguntas prováveis da banca

| Pergunta | Resposta sustentada pelo projeto |
|---|---|
| Por que ClickHouse e Delta juntos? | ClickHouse executa transformações e consultas analíticas; Delta preserva os snapshots de origem para histórico e reprocessamento. |
| Onde está a transformação? | Em `models/`, executada pelo dbt no ClickHouse, com macros reutilizáveis. Não depende de uma pasta chamada `transformacao_dbt`. |
| Por que não limpar na ingestão? | Para manter a captura auditável e concentrar as regras em modelos SQL documentados, testados e com linhagem. |
| Por que não descartar os erros? | Eles permanecem no bruto e na quarentena, permitindo explicar exclusões e corrigir a fonte. |
| Por que remover todas as dívidas duplicadas do consumo? | Não temos evidência para decidir qual ocorrência é a correta; escolher uma arbitrariamente poderia distorcer a proposta. |
| Por que uma tabela larga? | O recorte gerencial é conhecido; centralizar as métricas facilita a consulta e evita regras diferentes em relatórios. |
| O piso é uma regra legal definitiva? | Não. É um parâmetro da PoC; a política real precisa de validação da área responsável. |
| O fluxo inteiro é transacional? | Não. A publicação Bronze é atômica por tabela; execução sequencial e reprocessamento tratam a recuperação do fluxo. |
| Podemos adicionar vários meses sem rever o modelo? | Não automaticamente. A PoC pressupõe um formulário por servidor no período e tem teste de unicidade por servidor; múltiplos períodos exigem rever chaves, joins e testes. |
| Como outro colega reproduz? | Código e fontes versionadas, dependências fixadas, Compose, variáveis de conexão documentadas e execução por `run.py`. |

## 9. Fechamento sugerido

> “Entregamos um fluxo reproduzível que parte de fontes com defeitos, preserva
> o bruto e seu histórico, aplica regras explícitas, testa a qualidade e produz
> uma resposta gerencial rastreável. A banca pode acompanhar cada resultado
> desde a origem até a consulta final, inspecionar as exclusões e comparar versões.”

Antes de apresentar, confirme o conjunto de fontes utilizado, execute os testes
e deixe a consulta final e a DAG prontas. As evidências de validação da migração
estão em [APRESENTACAO.md](APRESENTACAO.md); o roteiro não substitui a execução
ao vivo das demonstrações exigidas.
