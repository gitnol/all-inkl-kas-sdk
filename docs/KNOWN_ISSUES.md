# Bekannte Probleme – all-inkl-kas-sdk

Bugs, Quirks und Einschränkungen, die **nicht** akut behoben werden, aber
dokumentiert sein müssen, damit niemand zweimal darüber stolpert.

**Abgrenzung:**

- `TODO.md` = Arbeit, die in einem priorisierten Inkrement aufgeräumt wird
- `KNOWN_ISSUES.md` = bekannt, akzeptiert oder verschoben; mit Workaround
- `BACKLOG.md` = noch unpriorisierte Ideen, keine konkreten Probleme

Alle Einträge stammen aus der Bestandsanalyse beim Init (2026-10-11, Code-Stand `412a2ff`). Fehler im Bestand —
auch in der vorhandenen API-Referenz `docs/01_account.md` bis `docs/04_system.md` — wurden **nicht** still
korrigiert, sondern hier erfasst (`NEUES_PROJECT_INITIALISIEREN.md` 3d.5). „Annahme" = ohne echten API-Aufruf
nicht prüfbar.

---

## Aktive Probleme

| # | Beschreibung | Reproduktion | Workaround | Akzeptanzgrund | Geplant für |
|---|---|---|---|---|---|
| K1 | Dry-Run loggt Request-Parameter (`INFO`) und SOAP-Body inkl. KAS-Passwort (`DEBUG`) — `kas_sdk/client.py:163-164` | `KasClient("w0000000", "PW-X", dry_run=True)`, Logger `kas_sdk.client` auf `DEBUG`, beliebigen Service aufrufen → `PW-X` steht im Log | Dry-Run nicht mit `DEBUG`-Logging in geteilten Umgebungen; Logs nicht weitergeben | I1 ist reine Doku-Baseline, kein Code | `I2` |
| K2 | Export maskiert private TLS-Schlüssel nicht (`ssl_certificate_sni_key` fehlt in `SENSITIVE_KEYWORDS`); verschachtelte Werte ungekürzt — `scripts/export_account.py:41,121` (Annahme: Massenabfrage liefert den Schlüssel) | `python scripts/export_account.py` auf einem Account mit eigenem SNI-Zertifikat, Export nach `BEGIN PRIVATE KEY` durchsuchen | Export nach `PRIVATE KEY` durchsuchen und Zeilen entfernen, Datei nicht weitergeben | I1 ist reine Doku-Baseline | `I2` |
| K3 | Debug-Skripte geben alle `ssl*`-Felder inkl. privatem Schlüssel aus — `debug/ssl_inspect_host.py:30`, `debug/ssl_inspect_verbose.py:72` | Skript mit Host mit eigenem Zertifikat ausführen | Ausgabe nicht teilen/aufzeichnen | Diagnosewerkzeug, selten genutzt | `I2` |
| K4 | SOAP-Envelope wird per f-String gebaut, JSON-Payload nicht XML-escaped: `&`/`<` in Passwort oder Parametern → ungültiges XML — `kas_sdk/client.py:149,156` | `KasClient("w0000000", "a&b<c")` mit gepatchtem `requests.post`; gesendeten Body mit `ET.fromstring` parsen → `ParseError` (lokal belegt) | Passwörter und Werte ohne `&`/`<` | Fix ändert den Transportkern, eigenes Inkrement mit Tests | `I3` |
| K5 | Wildcard-Skript prüft nur Record-Namen, nicht Name+Typ: AAAA-Wildcard wird gelöscht, obwohl `www` nur als A-Record existiert; TXT/MX-Name verhindert das Anlegen des A-Records — `scripts/dns_remove_wildcards.py:93,130` | Zone mit `*` A + `*` AAAA und nur `www` A; `--execute` → AAAA-Wildcard wird gelöscht, `www` hat kein AAAA | Dry-Run-Ausgabe prüfen, fehlende AAAA-Records vorher von Hand anlegen, `--domain` nutzen | Default ist Dry-Run | `I4` |
| K6 | `SymlinkService.delete_symlink` und `SoftwareInstallService.delete_softwareinstall` rufen Aktionen auf, die weder in `readme_KAS_API_SOURCE_OF_TRUTH.md` noch in der offiziellen KAS-Doku stehen; `docs/04_system.md` dokumentiert sie trotzdem — `kas_sdk/services/symlink.py:24`, `softwareinstall.py:54` | Abgleich der Aktionsnamen im Code gegen die SOT (2 Treffer) | Löschen über die KAS-Weboberfläche | Verhalten der API ungeprüft; Entfernen wäre API-Bruch | `I8` |
| K7 | `raise_for_status()` läuft vor dem Fault-Parsing; liefert die API Faults mit HTTP 500, wird jeder API-Fehler zu `KasConnectionError` ohne Fault-Text (Annahme) — `kas_sdk/client.py:182` | nur gegen die echte API prüfbar | Bei `KasConnectionError … 500` Zugangsdaten/Parameter prüfen | Annahme, Orakel fehlt | `I3` |
| K8 | API-Referenz weicht vom Code ab: 14 Signatur-Abweichungen (unbekannte/fehlende Argumente) plus Wertfehler (`logging="Y"`, `hostname_part2` bei `hostname_art="domain"`, `hostname_art` „or None"). U. a. `get_accountresources`/`get_accountsettings` ohne Parameter im Code; `update_accountsettings` kennt `account_login`/`inst_htaccess` nicht, `logging="Y"` ist ungültig; `update_superusersettings` erwartet `account_login`, `ssh_access`, `ssh_keys`; `add_mailaccount` heißt `local_part`/`domain_part`, `mail_comment` existiert nicht; `update_mailaccount` erwartet `mail_new_password`; `add/update_directoryprotection` brauchen `directory_authname` (und `directory_password` beim Update), `directory_new_password` existiert nicht; `update_chown` braucht `chown_user`; `add_account` mit `hostname_art="domain"` erwartet als `hostname_part2` die TLD | AST-Abgleich der Codebeispiele in `docs/01_account.md`, `docs/03_email.md`, `docs/04_system.md` gegen die Methodensignaturen | Signatur im Code (`kas_sdk/services/*.py`) ist maßgeblich | Bestandsdoku bleibt bis zum Abgleich unverändert | `I7` |
| K9 | Falsche Zugangsdaten werden als `KasApiError` (SOAP-Fault) gemeldet, nicht als `KasAuthError`; `README.md` behauptet „Missing or invalid credentials" für `KasAuthError` | `tests/test_integration.py` `test_soap_fault_raises_kas_api_error` (Fault „Wrong credentials" → `KasApiError`) | `KasApiError` fangen und Fault-Text prüfen | Code- und Doku-Änderung | `I3` (Code), `I7` (README) |
| K10 | Passwort-Reihenfolge widersprüchlich: `KasClient` Env vor Keyring, `kas_sdk/utils.get_kas_credentials` Keyring vor Env | Keyring-Eintrag und abweichendes `KAS_PASS` setzen; Skript nutzt Keyring, eigener Code mit `KasClient()` nutzt Env | Nur eine Quelle befüllen | Verhaltensänderung braucht Entscheidung (ADR) | `I9` |
| K11 | `.env.example` beschreibt Dinge falsch: `KAS_AUTH_TYPE` liest `KasClient` nicht (nur `ssl_enforce_hsts.py` und `debug/`); `KAS_DRY_RUN` „reads still work" — der SDK-Dry-Run unterdrückt auch Lesezugriffe | `.env.example` mit `kas_sdk/client.py` vergleichen | `docs/architecture/CONFIGURATION.md` ist maßgeblich | Doku-Korrektur | `I7` |

---

## Behobene Probleme

Letzte Einträge behalten bis zur nächsten Aufräum-Iteration (Spur für
Lessons Learned). Danach archivieren oder löschen.

| # | Beschreibung | Behoben in | Commit |
|---|---|---|---|
| (noch keine Einträge) | | | |

---

## Pflege

- Neuer Bug ohne sofortigen Fix → Eintrag hier; TODO-Punkt **nur**, wenn
  priorisiert wird.
- Eintrag wird behoben → in „Behobene Probleme" verschieben, in der nächsten
  Aufräum-Iteration löschen.
- Diese Datei steht in der Trigger-Matrix in `KICKOFF.md` Phase 3a.
