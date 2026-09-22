select servidor_id, mes_referencia from {{ ref('int_divida_com_proposta') }} group by 1, 2 having sum(parcela_sugerida_alocada) > max(capacidade_pagamento) + 0.01 or sum(parcela_sugerida_alocada) < 0
