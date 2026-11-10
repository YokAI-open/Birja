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
