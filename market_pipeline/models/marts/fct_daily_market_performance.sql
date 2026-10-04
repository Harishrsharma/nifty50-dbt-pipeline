{{ config(
    materialized='table'
) }}

with staging_data as (
    select
        trade_date,
        symbol,
        open_price,
        close_price,
        volume,
        fetched_at
    from {{ ref('stg_market_data') }}
),

daily_metrics as (
    select
        trade_date,
        symbol,
        open_price,
        close_price,
        volume,

        -- Absolute price movement
        round(close_price - open_price, 2) as price_spread,

        -- Daily percentage return: ((close - open) / open) * 100
        round(((close_price - open_price) / open_price) * 100, 2) as daily_return_pct,

        -- Market direction flag
        case
            when close_price > open_price then 'GAIN'
            when close_price < open_price then 'LOSS'
            else 'FLAT'
        end as market_trend,

        fetched_at
    from staging_data
)

select * from daily_metrics