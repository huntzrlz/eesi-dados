with origem as (
    select * from {{ source('bronze', 'bronze_formularios') }}
), tipado as (
    select
    -- Espaços e IDs vazios não identificam entidades; NULL permite encaminhar à quarentena.
        nullif(trim(servidor_id), '') as servidor_id,
    -- Aceita os três formatos das fontes; datas impossíveis viram NULL para quarentena.
        {{ data_referencia('mes_referencia') }} as mes_referencia,
    -- Padroniza caixa e acentos para não separar a mesma secretaria em grupos distintos.
        translateUTF8(upperUTF8(trim(secretaria_municipal)), 'ÁÀÃÂÉÊÍÓÔÕÚÜÇ', 'AAAAEEIOOOUUC') as secretaria_municipal,
    -- Aceita moeda brasileira e decimal com ponto; Conversão tolerante mantém erro como NULL, nunca como zero.
        {{ moeda('renda_liquida') }} as renda_liquida,
    -- Aceita moeda brasileira e decimal com ponto; Conversão tolerante mantém erro como NULL, nunca como zero.
        {{ moeda('despesa_basica_informada') }} as despesa_basica,
        arquivo_origem, lote, capturado_em
    from origem
)
select *,
    -- Exige identificadores e valores válidos para impedir indicadores sem renda ou com dívidas inválidas.
    case when servidor_id is not null and mes_referencia is not null and renda_liquida > 0 and despesa_basica >= 0 then true else false end as registro_valido
from tipado
