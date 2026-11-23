-- R2 · The network's tables: A1's clean data, now with its rules in the database.
-- Run as the superuser in the database `ecb`; everything belongs to lab_owner.
--
-- A rule the database holds (a key, a check, a reference) cannot be skipped by a script that
-- forgot it. Every check here is one A1's validation (model.py) made in Polars.

create schema lab authorization lab_owner;
set role lab_owner;

create table lab.hospital (
    -- TODO R2
);

create table lab.patient (
    -- TODO R2
);

create table lab.sample (
    -- TODO R2
);

create table lab.test (
    -- TODO R2
);

-- Given: who uses the server. A token is never stored, only its SHA-256 (lab.staff.issue).
create table lab.staff (
    login text primary key,
    name text not null,
    role text not null check (role in ('clinician', 'microbiologist')),
    hospital text references lab.hospital,
    token_hash text unique,
    check ((role = 'clinician') = (hospital is not null))
);

-- Given (R9 writes it): one PDF report per sample, kept in RustFS; the row says where and what it was.
create table lab.report (
    sample text primary key references lab.sample on delete cascade,
    object_key text not null unique,
    sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
    bytes int not null check (bytes > 0),
    uploaded_by text not null references lab.staff,
    uploaded_at timestamptz not null default now()
);

create index on lab.sample (hospital);
create index on lab.sample (patient);

reset role;
