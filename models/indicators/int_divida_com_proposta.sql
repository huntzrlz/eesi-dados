-- Aloca a parcela sugerida entre credores proporcionalmente ao saldo devedor.
select
    d.*,
    i.divida_total, i.capacidade_pagamento, i.comprometimento_percentual, i.faixa_comprometimento,
    -- Limita ao saldo total e rateia por saldo para não propor mais que a dívida ou capacidade.
    -- Float64 no rateio evita overflow de multiplicação Decimal; tolerância dos testes: um centavo.
    -- NULLIF protege a divisão; dívidas admitidas têm saldo positivo.
    toFloat64(least(i.capacidade_pagamento, i.divida_total)) * toFloat64(d.saldo_devedor) / nullif(toFloat64(i.divida_total), 0) as parcela_sugerida_alocada
from {{ ref('fct_divida_servidor') }} d
join {{ ref('int_servidor_mes') }} i using (servidor_id, mes_referencia, secretaria_municipal)

