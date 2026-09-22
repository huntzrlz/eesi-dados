-- Regressão do dialeto: não aceitar datas impossíveis nem alterar centavos na conversão.
select 'moeda_brasileira' as falha where coalesce({{ moeda("'R$ 1.234,56'") }} != toDecimal64('1234.56', 2), true)
union all
select 'moeda_decimal' where coalesce({{ moeda("'3800.50'") }} != toDecimal64('3800.50', 2), true)
union all
select 'moeda_invalida' where {{ moeda("'sem renda'") }} is not null
union all
select 'data_iso' where coalesce({{ data_referencia("'2026-08-01'") }} != toDate('2026-08-01'), true)
union all
select 'data_brasileira' where coalesce({{ data_referencia("'01/08/2026'") }} != toDate('2026-08-01'), true)
union all
select 'data_barras' where coalesce({{ data_referencia("'2026/08/01'") }} != toDate('2026-08-01'), true)
union all
select 'data_impossivel' where {{ data_referencia("'2026-02-30'") }} is not null
