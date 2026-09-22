with origem as (
    select * from {{ source('bronze', 'bronze_dividas') }}
), tipado as (
    select
    -- Espaços e IDs vazios não identificam entidades; NULL permite encaminhar à quarentena.
        nullif(trim(divida_id), '') as divida_id,
    -- Espaços e IDs vazios não identificam entidades; NULL permite encaminhar à quarentena.
        nullif(trim(servidor_id), '') as servidor_id,
    -- Remove espaços externos para comparar a mesma denominação de credor.
        trim(credor) as credor,
    -- Normaliza caixa e acento para comparar o domínio de credores sem variantes gráficas.
        case lower(trim(tipo_credor)) when 'cartão' then 'cartao' else lower(trim(tipo_credor)) end as tipo_credor,
    -- Aceita moeda brasileira e decimal com ponto; TRY_CAST mantém erro como NULL, nunca como zero.
        case when strpos(saldo_devedor, ',') > 0 then try_cast(replace(replace(replace(saldo_devedor, 'R$', ''), '.', ''), ',', '.') as decimal(18,2)) else try_cast(replace(replace(saldo_devedor, 'R$', ''), ' ', '') as decimal(18,2)) end as saldo_devedor,
    -- Aceita moeda brasileira e decimal com ponto; TRY_CAST mantém erro como NULL, nunca como zero.
        case when strpos(valor_parcela_mensal, ',') > 0 then try_cast(replace(replace(replace(valor_parcela_mensal, 'R$', ''), '.', ''), ',', '.') as decimal(18,2)) else try_cast(replace(replace(valor_parcela_mensal, 'R$', ''), ' ', '') as decimal(18,2)) end as valor_parcela_mensal,
    -- Tipa parcelas para uso futuro; este atributo não participa do cálculo atual de capacidade.
        try_cast(qtd_parcelas as integer) as qtd_parcelas,
        arquivo_origem, lote, capturado_em
    from origem
)
select *,
    -- Conta o ID em todos os lotes para bloquear duplicatas antes das somas financeiras.
    count(*) over (partition by divida_id) as ocorrencias_divida_id,
    -- Exige identificadores e valores válidos para impedir indicadores sem renda ou com dívidas inválidas.
    case when divida_id is not null and servidor_id is not null and saldo_devedor > 0 and valor_parcela_mensal >= 0 and tipo_credor in ('banco', 'cartao', 'varejo', 'servico_publico') then true else false end as registro_valido
from tipado

