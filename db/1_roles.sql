-- R1 · The cluster's roles. Run as the superuser (postgres) by `lab.setup`, after the
-- database `ecb` has been dropped: a role that still owns something cannot be dropped.
--
-- Nobody logs in as a role that owns or reads data. `ecb_app` (the server) logs in and has no
-- privilege of its own; per request it becomes one of the two groups with `set local role`.
-- Passwords are not here: `lab.setup` sets them from the environment (a file in git is public).

drop role if exists ecb_app, ecb_backup, clinician, microbiologist, lab_owner;

-- TODO R1
