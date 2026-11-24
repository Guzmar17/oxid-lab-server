-- R2 · The network's tables: A1's clean data, now with its rules in the database.
-- Run as the superuser in the database `ecb`; everything belongs to lab_owner.
--
-- A rule the database holds (a key, a check, a reference) cannot be skipped by a script that
-- forgot it. Every check here is one A1's validation (model.py) made in Polars.

create schema lab authorization lab_owner;
set role lab_owner;

create table lab.hospital (
    code text primary key check (code ~ '^[A-Z]{3}$'),
    name text not null,
    town text not null,
    beds int not null check (beds > 0)
);

-- Nullable only what the data leaves empty: sex (7 patients without one).
create table lab.patient (
    code text primary key check (code ~ '^[0-9]{7}$'),  -- text: '0108818' keeps its zero
    given_name text not null,
    family_name text not null,
    birth_date date not null check (birth_date > date '1900-01-01'),  -- 1900-01-01: a placeholder
    sex text check (sex in ('D', 'H')),
    postcode text not null check (postcode ~ '^[0-9]{5}$')
);

-- The times are the hospital's wall clock, as A1 recorded them: no time zone.
create table lab.sample (
    id text primary key check (id ~ '^[A-Z]{3}[0-9]{2}-[0-9]{5}$'),
    patient text not null references lab.patient,
    hospital text not null references lab.hospital,
    specimen text not null check (specimen in ('orina', 'sang', 'ferida', 'esput')),
    collected_at timestamp not null,
    received_at timestamp not null,
    reported_at timestamp,  -- null: still in the laboratory
    organism text check (organism in ('ECO', 'KPN', 'PAE', 'SAU', 'EFA')),  -- null: negative
    check (left(id, 3) = hospital),  -- RBX26-00001 is Riubaix's
    check (received_at > collected_at),
    check (reported_at > received_at)  -- null passes: not reported yet
);

create table lab.test (
    sample text not null references lab.sample on delete cascade,
    antibiotic text not null check (antibiotic ~ '^[A-Z]{3}$'),
    mic numeric check (mic > 0),  -- mg/L
    mic_censored boolean,  -- true: the MIC was <= or >
    diameter int check (diameter between 6 and 50),  -- mm; 6 is the disc itself
    sir text check (sir in ('S', 'I', 'R')),  -- null: pending
    primary key (sample, antibiotic),
    check ((mic is null) = (mic_censored is null))  -- a MIC carries its censoring mark, and only a MIC
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
