# Backlog – all-inkl-kas-sdk

Parkplatz für Ideen, Verbesserungen und Aufgaben, die noch **nicht** für ein
konkretes Inkrement priorisiert sind.

**Abgrenzung:**

- `TODO.md` = aktuelle, priorisierte Arbeit mit Definition of Done
- `BACKLOG.md` = noch nicht eingeplant, kein DoD nötig
- `KNOWN_ISSUES.md` = bekannte Probleme mit Workaround, nicht aktiv geplant

Wenn ein Backlog-Punkt für ein Inkrement vorgesehen wird → Verschiebung von
`BACKLOG.md` nach `TODO.md` (mit DoD ergänzen).

---

## Ideen / Features

- Session-basierte Authentifizierung prüfen — Passwort nicht mehr bei jedem Request senden; die öffentliche
  KAS-Doku listet die zulässigen `kas_auth_type`-Werte nicht auf (Recherche 2026-10-11), Status von `sha1` ebenfalls
  offen. Erst klären, dann ggf. ADR.
- Live-Smoke-Test mit Marker `live` für lesende Aktionen (`get_space`, `get_domains`) gegen einen Test-Unter-Account —
  nur manuell, nie in CI (`docs/testing/INTEGRATION_TESTS.md`).
- Advocatus-Diaboli-Hook in `.claude/settings.json` (`docs/KICKOFF.md` Phase 1 Punkt 7) — beim Init bewusst nicht
  angelegt: öffentliches Repo, eine Agenten-spezifische Hook-Konfiguration betrifft alle Mitwirkenden und braucht die
  Zustimmung des Maintainers. Bis dahin Gate von Hand (Phase 3b Punkt 5).
- `defusedxml` für das Antwort-Parsing — nur, wenn Antworten künftig aus weniger vertrauenswürdigen Quellen kommen
  (Proxy, aufgezeichnete Dateien); Recherche-Stand in `docs/security/DEPENDENCY_AUDIT.md`.

---

## Refactoring-Kandidaten

- Schichtregel als Check (`import-linter`: `kas_sdk.client`/`kas_sdk.services` importieren nicht `kas_sdk.utils`) —
  Auslöser: zweites Paket oder erste Verletzung (`docs/architecture/PROJECT_LAYOUT.md`).
- SSL-Feldinterpretation (`ssl_certificate_sni_is_active` = `j`/`Y`, Force-HTTPS/HSTS-Ermittlung) ist in
  `scripts/ssl_enforce_hsts.py` und `debug/ssl_inspect_verbose.py` doppelt — in eine testbare Funktion (Service oder
  Helfer) ziehen, sobald eines der Skripte geändert wird.
- Skripte melden Fehler pro Host nur auf der Konsole und enden mit Exit 0; für Cron/CI Exit-Code ≠ 0 bei Fehlern und
  Abbruch nach dem ersten Auth-Fehler (`docs/architecture/ERROR_HANDLING.md`, `docs/operations/MONITORING.md`).

---

## Technische Schuld

- Kosmetik in Skripten: Docstring nennt `ensure_ssl_hsts.py` (`scripts/ssl_enforce_hsts.py:11`), Export-Footer nennt
  `export_settings.py` (`scripts/export_account.py:347`), ungenutzter `get_subdomains()`-Aufruf
  (`scripts/ssl_update_hsts_manual.py:60`, kostet einen Request + Flood-Wartezeit), `except Exception: pass` in
  derselben Datei.
- `KAS_DRY_RUN=0` unterdrückt die Warnung „No KAS Password found" (Wahrheitswert-Prüfung per `os.getenv`,
  `kas_sdk/client.py:71`) — kosmetisch, Dry-Run selbst wird korrekt ausgewertet.
- Implizites `Optional` (`str = None`) in fast allen Service-Signaturen — wird mit Gate 3 (`docs/TODO.md` I5) sichtbar.
- Export wird nicht atomar und mit Standard-Dateirechten geschrieben (`scripts/export_account.py`).
- `ssl_update_hsts_manual.py` schreibt ohne Probelauf — Probelauf-Default nachrüsten oder Skript zugunsten von
  `ssl_enforce_hsts.py` entfernen (Entscheidung offen).

---

## Template-Evolution / Stack-Lücken

Hier landen Projekt-Charakteristiken, für die kein passender Stack/Overlay
existierte. Jeder Eintrag ist eine potenzielle Template-Erweiterung — so sind
z.B. `react-web` und die document-intelligence-Overlays entstanden.

- Stack-Lücke: Python-Bibliothek (SDK) als HTTP/SOAP-Client einer externen API plus Wartungsskripte — weder lokales
  CLI-Tool ohne Netz (`python-cli`) noch Server (`python-api`). In `python-cli` passten nicht: `AUTHENTICATION.md`
  („kein Netz, keine Credentials" — ersetzt durch die Gliederung aus `python-api`), `RUNBOOK.md` (schließt
  HTTP-Troubleshooting aus), `DEPENDENCIES.md` („kein externer Service", `tools/` ignorieren), `CLI.md`
  (ein Einstiegspunkt, `build_config()`), Testing-Vorlagen (subprocess/SQLite/Pipeline statt gemocktem HTTP-Transport
  und Antwort-Fixtures). — 2026-10-11 all-inkl-kas-sdk

---

## Verworfen (mit Begründung)

Punkte, die geprüft und bewusst nicht weiterverfolgt wurden. Bleiben als Spur
sichtbar, damit derselbe Punkt nicht in jeder Session erneut diskutiert wird.

- ~~Umstellung auf `src/`-Layout und `tests/unit` / `tests/integration`~~ — 2026-10-11 kein belegter Bedarf; das
  flache Layout funktioniert mit `pip install -e .`, eine Umstellung bricht Nutzer-Klone ohne Nutzen
  (`docs/architecture/PROJECT_LAYOUT.md`).
