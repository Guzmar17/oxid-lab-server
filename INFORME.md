# Informe · ecb-lab-server

Nom i cognoms: Abraham Cristopher Guzman Martinez

URL pública: `https://ecb-<nom>-<cognom>.francecentral.cloudapp.azure.com/lab/api/me`

Tokens per al professor (un clínic i un microbiòleg): al comentari privat del lliurament a
Moodle, **mai aquí**.

## R1–R6 · La base de dades

Per a cada grup (`clinician`, `microbiologist`) i el `ecb_app` sense `set role`: què pot llegir
i escriure de cada taula, i quina línia de quin fitxer ho diu. Una taula.

La sortida de `\dp lab.*` i de `select * from pg_policies where schemaname = 'lab'`, com a
`ecb_app` a Isard.

Per què `ecb_app` és `noinherit`, i què passaria si no ho fos.

**R1 · `noinherit`.** `ecb_app` és membre de `clinician` i de `microbiologist`
([db/1_roles.sql](db/1_roles.sql)), però amb `noinherit` no hereta cap privilegi dels dos grups:
connectat i sense `set role`, no pot llegir ni escriure cap taula de `lab`. Només té els drets
d'un grup després de `set local role clinician` (o `microbiologist`), que el servidor fa a cada
petició segons qui l'envia, i que s'acaba amb la transacció. Així cada consulta s'executa amb
els privilegis i les polítiques d'un sol grup, i el mínim que pot fer `ecb_app` per si sol és
res.

Si fos `inherit`, `ecb_app` tindria sempre la unió dels privilegis dels dos grups sense fer
`set role`: una petició que oblidés el `set local role`, o algú que aconseguís enviar SQL per
la connexió del servidor, podria llegir i escriure tot el que pot qualsevol dels dos grups (un
clínic faria coses de microbiòleg i al revés). A més, les polítiques escrites per a
`current_user = clinician` o `microbiologist` no s'aplicarien bé, perquè `current_user` seria
`ecb_app`: la separació entre grups dependria només que el codi no s'equivoqués mai.

## R7 · La sessió

Què fa que el que una petició fixa (`lab.login`, el rol) no arribi a la següent. Si algú pogués
enviar SQL per la connexió de `ecb_app`, què podria fer i què no.

## R8, R9 · El servidor i els informes

Les ordres `curl` i les respostes: la Laia veu una mostra de Riubaix i no una de l'Olivar (404);
la Laia intenta registrar una mostra de l'Olivar (403); el Jordi puja un informe i la Laia el
llegeix.

## R10 · La còpia

La sortida d'una còpia del temporitzador i d'una restauració (`python -m lab.backup restore`), amb
els recomptes. Què passa si la còpia es fa amb un rol sense `bypassrls`, i per què és millor així.

## R11 · Isard

`isard list` amb les quatre màquines, `rc admin info cluster cluster` amb `Disks: 3 (3 online)`
i `EC Parity`, i `table pg_hba_file_rules`. Apaga `rustfs-3` amb `isard stop`, puja un informe i
llegeix-lo: les ordres i les respostes.

## R12 · Azure

`sudo wg show isard` a Azure, `systemctl list-timers ecb-backup.timer`, i per què el `DNS` de
la configuració d'Isard no hi pot ser.

## Autoavaluació

| # | Punts que em dono | Evidència |
|---:|---:|---|
| R1 | / 6 | |
| R2 | / 10 | |
| R3 | / 7 | |
| R4 | / 9 | |
| R5 | / 5 | |
| R6 | / 13 | |
| R7 | / 9 | |
| R8 | / 11 | |
| R9 | / 7 | |
| R10 | / 8 | |
| R11 | / 9 | |
| R12 | / 6 | |
