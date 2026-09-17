-- Uma linha por servidor e mês, com indicadores calculados antes da camada de consumo.
with consolidado as (
    select servidor_id, mes_referencia, secretaria_municipal,
        max(renda_liquida) as renda_liquida,
        max(despesa_basica) as despesa_basica,
        sum(saldo_devedor) as divida_total,
        sum(valor_parcela_mensal) as parcela_mensal_atual
    from {{ ref('fct_divida_servidor') }}
    group by 1, 2, 3
)
select *,
    greatest(despesa_basica, cast({{ var('piso_minimo_existencial') }} as decimal(18,2))) as renda_protegida,
    greatest(renda_liquida - greatest(despesa_basica, cast({{ var('piso_minimo_existencial') }} as decimal(18,2))), 0) as capacidade_pagamento,
    100 * parcela_mensal_atual / nullif(renda_liquida, 0) as comprometimento_percentual,
    case
        when 100 * parcela_mensal_atual / nullif(renda_liquida, 0) <= 20 then '0-20%'
        when 100 * parcela_mensal_atual / nullif(renda_liquida, 0) <= 40 then '20-40%'
        when 100 * parcela_mensal_atual / nullif(renda_liquida, 0) <= 60 then '40-60%'
        else 'acima de 60%'
    end as faixa_comprometimento
from consolidado

