with raw_source as (
    select
        id as bronze_id,
        fetched_at,
        raw_payload
    from {{ source('market_warehouse', 'bronze_raw_options') }}
),

expanded_assets as (
    select
        bronze_id,
        fetched_at,
        (raw_payload ->> 'date')::date as trade_date,
        raw_payload ->> 'source' as source_vendor,
        jsonb_array_elements(raw_payload -> 'assets') as asset_json
    from raw_source
)

select
    bronze_id,
    fetched_at,
    trade_date,
    source_vendor,
    (asset_json ->> 'symbol')::varchar(30) as symbol,
    (asset_json ->> 'open')::numeric(12, 2) as open_price,
    (asset_json ->> 'close')::numeric(12, 2) as close_price,
    (asset_json ->> 'volume')::bigint as volume
from expanded_assets