# Decisões do projeto

## Arquitetura

Usamos quatro etapas: Dados Originais, Dados Preparados, Indicadores e Consumo. Dados Originais guardam os arquivos capturados, inclusive defeitos, em Delta Lake. Dados Preparados limpam e validam. Indicadores calculam dívida, comprometimento e capacidade de pagamento. Consumo entrega o resumo para a pergunta gerencial. Essa separação permite reconstruir tudo de `data/raw` e impede que a consulta final leia ou trate dados de origem.

## O que cada linha representa

Cada linha de `resumo_proposta_quitacao` representa um mês de referência, uma secretaria municipal, uma faixa de comprometimento e um tipo de credor. Registros inválidos ficam fora desse resumo e permanecem em quarentena. A tabela reúne todas as métricas necessárias no mesmo recorte, para que consulta e dashboard não calculem regras.

## Dado ambíguo

Uma despesa declarada como básica pode não ser considerada essencial pela política da conciliação. Na PoC, usamos o valor declarado e protegemos o maior valor entre essa despesa e o piso mínimo existencial parametrizado. A regra real deve ser decidida pela área jurídica/social e pelo gestor da central.

## Destino do registro inválido

Renda nula, zero ou negativa; datas impossíveis; IDs ausentes; saldo ou parcela negativa; tipo de credor desconhecido e duplicidade técnica são enviados às tabelas de quarentena. Não descartamos nem substituímos por zero: o registro continua auditável e não distorce a capacidade de pagamento.


## Escolha de armazenamento e modelo de consumo

Adotamos as funções do Medallion com quatro etapas: Originais (Bronze),
Preparados (Silver), Indicadores e Consumo (Gold). Delta Lake no bruto permite
consultar snapshots anteriores sem Spark; DuckDB integra os dados locais ao dbt
sem servidor. Esta arquitetura é adequada à PoC local, sem requisito de escrita
concorrente distribuída. As fontes são formulários CSV e lotes de dívidas JSON.

Escolhemos uma tabela larga agregada para consumo, em vez de esquema estrela:
a pergunta usa um recorte conhecido e poucas métricas, dispensando joins no
relatório. O grão é mês, secretaria, faixa de comprometimento e tipo de credor.
O comprometimento médio é calculado por dívida no recorte, não como média de
pessoas distintas; uma pessoa com mais dívidas tem maior peso nessa métrica.

## Regras e justificativas

- IDs: remover espaços e transformar vazio em NULL evita relacionamentos fictícios.
- Moeda: aceitar vírgula decimal brasileira e ponto decimal permite reunir as
  duas convenções. Conversões impossíveis viram NULL para não inventar valores.
- Datas: aceitar ISO, dia/mês/ano e ano/mês/dia; datas impossíveis são rejeitadas.
- Secretaria: caixa alta e remoção de acentos evitam grupos separados por grafia.
  O domínio de secretarias é verificado por teste dbt; novas secretarias exigem
  atualização deliberada do domínio antes da aprovação do build.
- Credor: caixa baixa e equivalência cartão/cartao permitem validar o domínio.
- Validade: renda e saldo devem ser positivos; despesa e parcela podem ser zero,
  mas não negativas. Identificadores obrigatórios não podem ser vazios.
- Duplicidade: todas as ocorrências de um ID de dívida duplicado ficam em
  quarentena. Não há fonte autoritativa para escolher uma delas. `DIV-004`
  não deve aparecer nos fatos. A quarentena mostra o primeiro motivo encontrado.
- Parcelas totais: tipadas para uso futuro; quantidade não entra na regra atual.
- Relacionamento: somente dívidas com formulário válido entram nos indicadores.
  A PoC pressupõe um formulário por servidor no período; o teste de unicidade
  nos indicadores impede aprovar multiplicidade de períodos sem rever o grão.
- Capacidade: máximo entre zero e renda menos o maior valor de despesa e piso.
- Proposta: limitada à capacidade e ao saldo total; distribuída entre dívidas
  proporcionalmente ao saldo para preservar os limites no total do servidor.
- Faixas: até 20%, até 40%, até 60% e acima de 60%, com limites inclusivos.

## Defeitos deliberados

As fontes incluem moedas com formatos diferentes, renda ausente/negativa,
data impossível, grafias de secretaria, saldo negativo, credor fora do domínio
e ID de dívida duplicado. Variações de formato recuperáveis são normalizadas;
erros de validade são mantidos na quarentena. Os arquivos originais não são
editados pela ingestão e seus valores são preservados no Delta.

## Histórico e reprocessamento

Cada captura grava o lote 01 por overwrite transacional e acrescenta o lote 02.
Overwrite substitui o snapshot ativo, mas não apaga o histórico Delta: após
reexecutar, os snapshots antigos continuam consultáveis. Não usamos VACUUM.
A versão anterior à atual contém o lote 01 da captura e a atual os dois lotes.
A consulta de demonstração é idêntica nos dois snapshots.

`python -m src.pipeline --from-delta` reconstrói o Bronze DuckDB sem reler as
fontes. Em seguida, `dbt build` reconstrói as camadas derivadas. Não há transação
conjunta entre as duas tabelas Delta: em caso de interrupção da captura, ela deve
ser repetida antes do consumo. CSV/JSON preservam o arquivo original; Delta
preserva os valores e metadados, não a formatação textual do arquivo.
