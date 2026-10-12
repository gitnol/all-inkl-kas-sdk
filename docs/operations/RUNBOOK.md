# Runbook – all-inkl-kas-sdk

Häufige Operationen und Troubleshooting für die Wartungsskripte und die SDK-Nutzung. Abweichend von der
`python-cli`-Vorlage enthält dieses Runbook API-Troubleshooting, weil das Projekt ein HTTP-Client ist — aber nur
KAS-spezifische Fälle, keine generischen HTTP-Listen.

---

## Häufige Commands

```bash
# Empfehlung: erst ohne Schreibzugriff
python scripts/dns_remove_wildcards.py --domain example.com
KAS_DRY_RUN=1 python scripts/ssl_enforce_hsts.py

# Ausführen
python scripts/dns_remove_wildcards.py --domain example.com --execute
python scripts/ssl_enforce_hsts.py

# Konfigurationsexport (Ergebnis: scripts/output/kas_export_YYYY-MM-DD_HHMM.md)
python scripts/export_account.py

# Erneuter Lauf nach Abbruch: denselben Befehl erneut ausführen — Wildcard- und HSTS-Skript überspringen
# bereits erledigte Hosts (prüfen den Ist-Zustand vor jeder Änderung)
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'kas_sdk'`
→ Im Repo-Root `pip install -e .` ausführen (Skripte importieren das installierte Paket)
→ Virtuelle Umgebung aktiv? `.\.venv\Scripts\Activate.ps1` (Windows) / `source .venv/bin/activate` (Linux)
→ Prüfen ob richtiger Python-Interpreter genutzt wird: `python --version`

### `ModuleNotFoundError: No module named 'bs4'`
→ Nur `scripts/generate_source_of_truth.py` braucht es: `pip install -e ".[dev]"`

### `KasAuthError: KAS Login is required`
→ `KAS_LOGIN` setzen, Login als Argument übergeben oder Default-Login im Keyring hinterlegen
  (`docs/operations/SETUP.md` → Zugangsdaten)

### Warnung `No KAS Password found. API calls will likely fail.`
→ Passwort fehlt in Argument, `KAS_PASS`, `.env` und Keyring (Dienst `kas_api`, Benutzer = Login)
→ Skripte nutzen eine andere Reihenfolge als der Client (Keyring vor Env, `docs/architecture/CONFIGURATION.md`)

### `KasApiError: KAS API Fault: …`
→ Der Fault-Text ist der KAS-Fehlercode (z. B. `…_syntax_incorrect`, `missing_parameter`, `in_progress`);
  Bedeutung und Pflichtparameter je Aktion in `readme_KAS_API_SOURCE_OF_TRUTH.md` nachschlagen
→ `in_progress`: Die vorige Änderung am Objekt läuft noch — später erneut versuchen, nicht in Schleife wiederholen
→ Bei Verdacht auf falsche Zugangsdaten: **nicht** automatisch wiederholen (Sperrgefahr)

### `KasConnectionError: HTTP Request failed: 500 Server Error …`
→ Kann ein verdeckter SOAP-Fault sein (`docs/KNOWN_ISSUES.md` K7): Zugangsdaten und Parameter prüfen, bevor
  ein Netzwerkproblem vermutet wird
→ Sonderzeichen `&`/`<` im Passwort oder in Parametern ergeben einen ungültigen Request (K4) — Workaround:
  Passwort ohne diese Zeichen verwenden

### Skript läuft sehr langsam
→ Erwartet: Flood-Schutz wartet vor jedem Request bis zu 2 s (`flood_protection_delay`); bei vielen Domains/Hosts
  dauern Export und HSTS-Lauf mehrere Minuten
→ `--domain` nutzen, um Läufe zu begrenzen

### Dry-Run liefert leere oder unplausible Daten
→ SDK-Dry-Run (`KAS_DRY_RUN=1` bzw. `dry_run=True`) sendet **gar keine** Requests, auch keine lesenden; die
  Antwort ist ein Mock. Für „echt lesen, nicht schreiben" die Skript-Modi nutzen (`docs/architecture/CLI.md`)

### `delete_symlink` / `delete_softwareinstall` schlagen fehl
→ Die Aktionen stehen nicht in der KAS-Doku (`docs/KNOWN_ISSUES.md` K6); Löschen über die KAS-Weboberfläche

---

## Deployment-Checkliste

- [ ] Python ≥ 3.9 (empfohlen ≥ 3.11) auf dem System installiert
- [ ] `pip install -e .` (bzw. `.[dev]`) in aktiver venv ausgeführt
- [ ] Zugangsdaten im Keyring oder in der Umgebung, **nicht** im Skript
- [ ] Lauf ohne Schreibzugriff erfolgreich durchgelaufen und Ausgabe geprüft
- [ ] `.gitignore` prüfen: `scripts/output/`, `.env`, Logs, `.venv/` nicht versioniert
- [ ] Wenn automatisiert: Logs ohne `DEBUG`-Level und ohne SDK-Dry-Run (K1), Exporte nach Gebrauch löschen
