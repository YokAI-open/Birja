-- Private equality manifest in the exported REPEATABLE READ transaction.
-- All columns explicit; NUMERIC text and UTC six-microsecond timestamps.
WITH canonical(table_name, row_key, body) AS (
 SELECT 'users', id, json_build_array(id,email,to_char(created_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))::text FROM users
 UNION ALL SELECT 'accounts', id, json_build_array(id,user_id,cash::text,starting_cash::text,to_char(created_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))::text FROM accounts
 UNION ALL SELECT 'auth_sessions', id, json_build_array(id,user_id,to_char(created_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),to_char(revoked_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))::text FROM auth_sessions
 UNION ALL SELECT 'refresh_tokens', id, json_build_array(id,session_id,token_hash,to_char(expires_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),to_char(used_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),to_char(created_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))::text FROM refresh_tokens
 UNION ALL SELECT 'coins', id, json_build_array(id,symbol,name,kraken_pair,sort_order,is_active)::text FROM coins
 UNION ALL SELECT 'prices', coin_id, json_build_array(coin_id,mid::text,to_char(as_of,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),source)::text FROM prices
 UNION ALL SELECT 'holdings', id, json_build_array(id,user_id,coin_id,quantity::text,cost_basis::text)::text FROM holdings
 UNION ALL SELECT 'trades', id, json_build_array(id,user_id,coin_id,side,input_kind,input_value::text,quantity::text,mid_price::text,to_char(price_as_of,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),exec_price::text,fee::text,cash_delta::text,cash_after::text,idempotency_key::text,to_char(created_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))::text FROM trades
 UNION ALL SELECT 'alembic_version', 0, json_build_array(version_num)::text FROM alembic_version
), names(name) AS (
 VALUES ('users'),('accounts'),('auth_sessions'),('refresh_tokens'),('coins'),('prices'),('holdings'),('trades'),('alembic_version')
), summaries AS (
 SELECT name, count(row_key) AS count,
 encode(sha256(convert_to(coalesce(string_agg(encode(sha256(convert_to(body,'UTF8')),'hex'),'' ORDER BY row_key),''),'UTF8')),'hex') AS sha256
 FROM names LEFT JOIN canonical ON table_name=name GROUP BY name
)
SELECT json_build_object(
 'schema',json_build_object(
  'constraints',(SELECT json_agg(json_build_array(c.conrelid::regclass::text,c.conname,c.contype,c.convalidated,pg_get_constraintdef(c.oid)) ORDER BY c.conrelid::regclass::text,c.conname) FROM pg_constraint c WHERE c.connamespace='public'::regnamespace),
  'indexes',(SELECT json_agg(json_build_array(c.relname,i.indisvalid,i.indisready,pg_get_indexdef(i.indexrelid)) ORDER BY c.relname) FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE c.relnamespace='public'::regnamespace),
  'identities',(SELECT json_agg(json_build_array(c.relname,a.attname,a.attidentity,format_type(a.atttypid,a.atttypmod)) ORDER BY c.relname,a.attnum) FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid WHERE c.relnamespace='public'::regnamespace AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped)
 ),
 'tables',(SELECT json_object_agg(name,json_build_object('count',count,'sha256',sha256) ORDER BY name) FROM summaries),
 'revision',(SELECT string_agg(version_num,',' ORDER BY version_num) FROM alembic_version),
 'server_version',current_setting('server_version'),
 'financial',json_build_object(
   'cash',(SELECT coalesce(sum(cash),0)::text FROM accounts),
   'starting_cash',(SELECT coalesce(sum(starting_cash),0)::text FROM accounts),
   'quantity',(SELECT coalesce(sum(quantity),0)::text FROM holdings),
   'cost_basis',(SELECT coalesce(sum(cost_basis),0)::text FROM holdings),
   'fees',(SELECT coalesce(sum(fee),0)::text FROM trades),
   'cash_delta',(SELECT coalesce(sum(cash_delta),0)::text FROM trades),
   'negative_cash',(SELECT count(*) FROM accounts WHERE cash<0),
   'fractional_cents',(SELECT count(*) FROM accounts WHERE cash<>round(cash,2)),
   'negative_holdings',(SELECT count(*) FROM holdings WHERE quantity<0 OR cost_basis<0)
 ));

/* STOCK_COINS
 SELECT 'coins', id, json_build_array(id,symbol,name,kraken_pair,sort_order,is_active,asset_class)::text FROM coins
STOCK_COINS */
/* STOCK_ROWS
 UNION ALL SELECT 'stock_instruments', coin_id, json_build_array(coin_id,provider_asset_id,to_char(provider_verified_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),listing_exchange,currency,security_type,source,source_ref)::text FROM stock_instruments
 UNION ALL SELECT 'stock_quotes', coin_id, json_build_array(coin_id,bid::text,ask::text,mid::text,source,feed,to_char(event_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),to_char(collected_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),session_date::text,admission_generation)::text FROM stock_quotes
 UNION ALL SELECT 'stock_sessions', id, json_build_array(id,exchange,session_date::text,to_char(opens_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),to_char(closes_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),coverage_start::text,coverage_end::text,calendar_admission_generation)::text FROM stock_sessions
 UNION ALL SELECT 'stock_data_admissions', id, json_build_array(id,product,state,generation,to_char(reviewed_at,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),to_char(valid_from,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),to_char(valid_until,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),evidence_ref,terms_version,collection_allowed,display_allowed,derived_allowed,retention_allowed,scope,quota,allowed_fields,attribution,calendar)::text FROM stock_data_admissions
STOCK_ROWS */
/* STOCK_INVALID
SELECT
 (SELECT count(*) FROM coins WHERE asset_class NOT IN ('crypto','stock') OR (asset_class='crypto' AND kraken_pair IS NULL) OR (asset_class='stock' AND kraken_pair IS NOT NULL))
 + (SELECT count(*) FROM stock_instruments s JOIN coins c ON c.id=s.coin_id WHERE c.asset_class<>'stock' OR currency<>'USD' OR security_type<>'common_stock' OR listing_exchange NOT IN ('NYSE','NASDAQ') OR source NOT IN ('sec','alpaca') OR length(source_ref) NOT BETWEEN 1 AND 2048 OR (provider_verified_at IS NOT NULL AND provider_asset_id IS NULL))
 + (SELECT count(*) FROM stock_quotes WHERE NOT (bid>0 AND bid<'Infinity'::numeric AND ask>0 AND ask<'Infinity'::numeric AND mid>0 AND mid<'Infinity'::numeric) OR bid>ask OR mid <> trunc((bid+ask)/2,8)+CASE WHEN mod((bid+ask)*50000000,1)=0.5 AND mod(trunc((bid+ask)*50000000),2)=1 THEN 0.00000001 ELSE 0 END OR source<>'alpaca' OR feed<>'iex' OR event_at>collected_at OR admission_generation<=0)
 + (SELECT count(*) FROM stock_sessions WHERE exchange NOT IN ('NYSE','NASDAQ') OR calendar_admission_generation<=0 OR NOT (coverage_start<=session_date AND session_date<=coverage_end AND coverage_end-coverage_start<=135) OR NOT ((opens_at IS NULL AND closes_at IS NULL) OR (opens_at IS NOT NULL AND closes_at IS NOT NULL AND opens_at<closes_at AND closes_at-opens_at<=interval '1 day')))
 + (SELECT count(*) FROM stock_data_admissions WHERE product NOT IN ('reference','quotes','actions','status','calendar') OR state NOT IN ('denied','approved','revoked') OR generation<=0 OR (valid_from IS NOT NULL AND valid_until IS NOT NULL AND valid_from>=valid_until) OR (state='approved' AND (reviewed_at IS NULL OR valid_from IS NULL OR valid_until IS NULL OR evidence_ref IS NULL OR terms_version IS NULL)) OR jsonb_typeof(scope)<>'object' OR octet_length(scope::text)>16384 OR jsonb_typeof(quota)<>'object' OR octet_length(quota::text)>4096 OR jsonb_typeof(allowed_fields)<>'array' OR octet_length(allowed_fields::text)>4096 OR jsonb_typeof(calendar)<>'object' OR octet_length(calendar::text)>32768 OR (product<>'calendar' AND calendar<>'{}'::jsonb))
STOCK_INVALID */
-- Revision0011 is assembled by backup-snapshot.manifest_sql using its explicit
-- reviewed accounting columns, exact catalogue fingerprint and identity states.
-- Keep the legacy query and STOCK_* fragments byte-compatible for0007–0010.

-- Revision0012 additionally inventories the independently pinned scoped function,
-- Revision0013 adds exact immutable fill/status rows, invoker function bodies,
-- owners, search paths, ACLs and enabled trigger definitions, pinned independently.
-- actual owner/EXECUTE ACL and operator boundaries in backup-snapshot.py.
