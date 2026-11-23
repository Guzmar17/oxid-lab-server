-- R6 · Which rows. A clinician sees and writes only their hospital; a microbiologist, all of
-- the network. The person is the request's: `lab.login`, set by the server with
-- set_config(…, true) inside the request's transaction (lab/db.py), after it checked the token.
--
-- Run as the superuser in `ecb`, after 3_privileges.sql. The functions belong to lab_owner.

set role lab_owner;

-- Given: the request's person from their token, for ecb_app only (security definer: ecb_app
-- cannot read lab.staff, the function's owner can).
create function lab.whoami(token text) returns table (login text, role text, hospital text)
language sql stable security definer set search_path = pg_catalog, lab
as $$
    select login, role, hospital from lab.staff
    where token_hash = encode(sha256(convert_to(token, 'UTF8')), 'hex')
$$;
revoke execute on function lab.whoami(text) from public;
grant usage on schema lab to ecb_app;  -- to reach the function: no table of it
grant execute on function lab.whoami(text) to ecb_app;

-- TODO R6

reset role;
