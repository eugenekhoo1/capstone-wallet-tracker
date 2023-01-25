--Dune Engine v2 (Dune SQL)

with
    trade_log as(
            SELECT 
                date_trunc('minute', t.block_time) as time,
                t.tx_hash,
                t.tx_from,
                token_pair,
                t.token_bought_address,
                case when t.token_bought_symbol is null then t.token_bought_address else t.token_bought_symbol end as token_bought,
                t.token_bought_amount,
                t.token_sold_address,
                case when t.token_sold_symbol is null then t.token_sold_address else t.token_sold_symbol end as token_sold,
                t.token_sold_amount,
                t.amount_usd as usd_value
            FROM uniswap_v2_ethereum.trades t
            WHERE t.block_time > now() - Interval '12' month
    ),
    trade_log_price as(
            SELECT
                tl.*,
                p.price * tl.token_bought_amount as token_bought_value_at_txn
            FROM trade_log tl
            LEFT JOIN prices.usd p
                ON p.contract_address = tl.token_bought_address AND p.minute = tl.time AND p.blockchain = 'ethereum'
    ),
    trade_log_price_ as(
             SELECT
                tlp.*,
                p.price * tlp.token_sold_amount as token_sold_value_at_txn
            FROM trade_log_price tlp
            LEFT JOIN prices.usd p
                ON p.contract_address = tlp.token_sold_address AND p.minute = tlp.time AND p.blockchain = 'ethereum' 
    ),
    trade_log_final as(
            SELECT
                tlp.time,
                tlp.tx_hash,
                tlp.tx_from,
                tlp.token_pair,
                tlp.token_bought,
                tlp.token_bought_address,
                tlp.token_bought_amount,
                tlp.token_sold,
                tlp.token_sold_address,
                tlp.token_sold_amount,
                tlp.usd_value,
                case when tlp.token_bought_value_at_txn is null then tlp.token_sold_value_at_txn else tlp.token_bought_value_at_txn end as usd_value_at_txn
            FROM trade_log_price_ tlp
            ORDER BY tlp.time ASC
    )

  select
    tlf.time,
    tlf.tx_from,
    tlf.token_pair,
    tlf.token_bought,
    tlf.token_bought_address,
    tlf.token_bought_amount,
    tlf.token_sold,
    tlf.token_sold_address,
    tlf.token_sold_amount,
    tlf.usd_value_at_txn,
    tlf_count.txn_count
  from trade_log_final tlf
  inner join
    (select 
        tx_from, 
        count(tx_from) as txn_count
    from trade_log_final
    group by tx_from
    having count(tx_from) > 25 and min(usd_value_at_txn) > 85) tlf_count
  on tlf_count.tx_from = tlf.tx_from

