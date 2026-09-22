-- Aloca a parcela sugerida entre credores proporcionalmente ao saldo devedor.
select
    d.*,
    i.divida_total, i.capacidade_pagamento, i.comprometimento_percentual, i.faixa_comprometimento,
    -- Limita ao saldo total e rateia por saldo para não propor mais que a dívida ou capacidade.
    -- NULLIF protege a divisão; dívidas admitidas têm saldo positivo.
    least(i.capacidade_pagamento, i.divida_total) * d.saldo_devedor / nullif(i.divida_total, 0) as parcela_sugerida_alocada
from {{ ref('fct_divida_servidor') }} d
join {{ ref('int_servidor_mes') }} i using (servidor_id, mes_referencia, secretaria_municipal)

