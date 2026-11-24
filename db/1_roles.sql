-- R1 · The cluster's roles. Run as the superuser (postgres) by `lab.setup`, after the
-- database `ecb` has been dropped: a role that still owns something cannot be dropped.
--
-- Nobody logs in as a role that owns or reads data. `ecb_app` (the server) logs in and has no
-- privilege of its own; per request it becomes one of the two groups with `set local role`.
-- Passwords are not here: `lab.setup` sets them from the environment (a file in git is public).

drop role if exists ecb_app, ecb_backup, clinician, microbiologist, lab_owner;

-- The owner of the schema and its tables. Nobody logs in as it: an owner skips grants.
create role lab_owner nologin nosuperuser nocreatedb nocreaterole noinherit nobypassrls;

-- The two groups: what a request may do is granted to these, never to a login.
create role clinician nologin nosuperuser nocreatedb nocreaterole nobypassrls;
create role microbiologist nologin nosuperuser nocreatedb nocreaterole nobypassrls;

-- The server. `noinherit`: being a member of both groups gives it nothing until it says
-- `set local role clinician` (or `microbiologist`), so on its own it reads and writes nothing.
create role ecb_app login noinherit nosuperuser nocreatedb nocreaterole nobypassrls
    in role clinician, microbiologist;

-- The backup. `bypassrls`: a copy must see every row, not only the rows a policy lets through.
create role ecb_backup login nosuperuser nocreatedb nocreaterole bypassrls;
