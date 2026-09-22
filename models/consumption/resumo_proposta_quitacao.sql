-- Cada linha representa um mês, uma secretaria, uma faixa de comprometimento e um tipo de credor.
select
    mes_referencia,
    secretaria_municipal,
    faixa_comprometimento,
    tipo_credor,
    -- Conta pessoas distintas mesmo quando têm mais de uma dívida no grupo.
    count(distinct servidor_id) as servidores_validos,
    -- Consolida métricas já calculadas para manter a consulta final sem regras.
    sum(saldo_devedor) as divida_total,
    sum(valor_parcela_mensal) as parcela_mensal_atual_total,
    sum(parcela_sugerida_alocada) as parcela_mensal_sugerida_total,
    -- Média por dívida no recorte: servidores com mais dívidas têm maior peso.
    avg(comprometimento_percentual) as comprometimento_medio_percentual
from {{ ref('int_divida_com_proposta') }}
group by 1, 2, 3, 4

