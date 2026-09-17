# Decisões do projeto

## Arquitetura

Usamos quatro etapas: Dados Originais, Dados Preparados, Indicadores e Consumo. Dados Originais guardam os arquivos capturados, inclusive defeitos, em Delta Lake. Dados Preparados limpam e validam. Indicadores calculam dívida, comprometimento e capacidade de pagamento. Consumo entrega o resumo para a pergunta gerencial. Essa separação permite reconstruir tudo de `data/raw` e impede que a consulta final leia ou trate dados de origem.

## O que cada linha representa

Cada linha de `resumo_proposta_quitacao` representa um mês de referência, uma secretaria municipal, uma faixa de comprometimento e um tipo de credor. Registros inválidos ficam fora desse resumo e permanecem em quarentena. A tabela reúne todas as métricas necessárias no mesmo recorte, para que consulta e dashboard não calculem regras.

## Dado ambíguo

Uma despesa declarada como básica pode não ser considerada essencial pela política da conciliação. Na PoC, usamos o valor declarado e protegemos o maior valor entre essa despesa e o piso mínimo existencial parametrizado. A regra real deve ser decidida pela área jurídica/social e pelo gestor da central.

## Destino do registro inválido

Renda nula, zero ou negativa; datas impossíveis; IDs ausentes; saldo ou parcela negativa; tipo de credor desconhecido e duplicidade técnica são enviados às tabelas de quarentena. Não descartamos nem substituímos por zero: o registro continua auditável e não distorce a capacidade de pagamento.

