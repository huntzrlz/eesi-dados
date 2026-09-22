-- Mesmo SQL para comparar o snapshot anterior com o atual, sem alterar o bruto.
select count(*) as registros,
       count(*) filter (where divida_id = 'REC-TIME-TRAVEL') as registros_demonstracao
from dividas_snapshot;
