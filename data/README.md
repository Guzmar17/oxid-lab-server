# Les dades

**Inventades**, com a l'A1: cap persona ni cap hospital existeix. Són les taules netes de la
pràctica `ecb-microbiology` (A1-P1), el que en quedava després de carregar, netejar, validar i
ajuntar: mig any (5 de gener – 5 de juliol de 2026) de la Xarxa de microbiologia del Riubaix.
Tracta-les com si fossin reals.

Totes amb `,`, capçalera, dates `aaaa-mm-dd` i hores `aaaa-mm-dd hh:mm`; buit és `null`.

| fitxer | taula | files | què és una fila |
|---|---|---:|---|
| `hospitals.csv` | `lab.hospital` | 3 | un hospital: `code` (RBX, OLV, CSA), `name`, `town`, `beds` |
| `patients.csv` | `lab.patient` | 896 | un pacient: `code` (7 xifres, **un codi**), `given_name`, `family_name`, `birth_date`, `sex` (D/H; 7 sense), `postcode` |
| `samples.csv` | `lab.sample` | 2 122 | una mostra: `id` (`RBX26-00001`: les tres lletres són l'hospital), `patient`, `hospital`, `specimen` (orina, sang, ferida, esput), `collected_at`, `received_at`, `reported_at` (buit: encara al laboratori), `organism` (ECO, KPN, PAE, SAU, EFA; buit: negatiu) |
| `tests.csv` | `lab.test` | 6 783 | un antibiòtic provat en una mostra: `sample`, `antibiotic`, `mic` (mg/L), `mic_censored` (`true`: era `<=` o `>`), `diameter` (mm), `sir` (S, I, R; buit: pendent) |
| `staff.csv` | `lab.staff` | 6 | qui fa servir el servidor: `login`, `name`, `role` (`clinician`, `microbiologist`), `hospital` (el del clínic; buit per als microbiòlegs, que són de la xarxa) |

El personal:

| login | nom | rol | hospital |
|---|---|---|---|
| `laia.puig` | Laia Puig | clínica | RBX |
| `oriol.mas` | Oriol Mas | clínic | RBX |
| `pau.serra` | Pau Serra | clínic | OLV |
| `marta.vidal` | Marta Vidal | clínica | CSA |
| `jordi.camps` | Jordi Camps | microbiòleg | la xarxa |
| `nuria.roca` | Núria Roca | microbiòloga | la xarxa |
