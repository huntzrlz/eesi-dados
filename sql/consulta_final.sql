-- A consulta somente lê indicadores já calculados na camada de Consumo.
SELECT
    mes_referencia,
    secretaria_municipal,
    faixa_comprometimento,
    tipo_credor,
    servidores_validos,
    divida_total,
    parcela_mensal_atual_total,
    parcela_mensal_sugerida_total,
    comprometimento_medio_percentual
FROM resumo_proposta_quitacao
WHERE mes_referencia = toDate('2026-08-01')
ORDER BY secretaria_municipal, faixa_comprometimento, tipo_credor;

