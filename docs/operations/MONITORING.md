# Monitoring & Betrieb – all-inkl-kas-sdk

Das SDK hat keinen Dauerbetrieb; „Monitoring" heißt hier: einen Skriptlauf bzw. den CI-Lauf bewerten.

---

## Erfolgsindikatoren

| Indikator | Erwarteter Wert | Prüfung |
|-----------|----------------|---------|
| Exit-Code | `0` — **aber** auch bei Fehlern pro Host (siehe unten) | `echo $?` (Bash) / `$LASTEXITCODE` (PowerShell) |
| Konsolenausgabe | keine Zeile mit `ERROR`, `FAILED`, `[ABORT]` | Ausgabe lesen bzw. `… | grep -E "ERROR|FAILED|ABORT"` |
| `scripts/output/` nach Export | neue Datei `kas_export_<Zeitstempel>.md`, Abschnitte ohne `Error:` | `ls scripts/output/` |
| `dns_remove_wildcards.py --execute` | je Zone `[OK] All explicit records verified.` vor dem Löschen | Konsolenausgabe |
| `ssl_enforce_hsts.py` | je Host `OK (Already enforced)` oder `SUCCESS.` | Konsolenausgabe |
| CI | Workflow „CI" grün für alle Python-Versionen der Matrix | GitHub Actions |

---

## Exit-Codes

| Code | Bedeutung |
|------|-----------|
| `0` | Skriptende erreicht — Fehler pro Host/Domain werden nur ausgegeben, nicht im Exit-Code gemeldet |
| `1` | Fehlende Zugangsdaten (`ssl_enforce_hsts.py`), fehlende HTML-Datei (`generate_source_of_truth.py`) oder unbehandelte Exception |
| `2` | Ungültige Argumente (argparse) |
| `130` | KeyboardInterrupt (Strg+C / SIGINT) |

---

## Manuelle Checks

```bash
# Fehlerzeilen eines protokollierten Laufs
python scripts/ssl_enforce_hsts.py 2>&1 | tee hsts.log      # *.log ist gitignored
grep -nE "ERROR|FAILED" hsts.log

# Stichprobe nach DNS-Änderung (Auflösung A und AAAA)
nslookup -type=A www.example.com
nslookup -type=AAAA www.example.com
```

---

## Bekannte Warnsignale

| Signal | Mögliche Ursache | Maßnahme |
|--------|-----------------|---------|
| `KAS SDK is running in DRY-RUN mode` | `KAS_DRY_RUN` gesetzt (auch über `.env`) | gewollt? Sonst Variable entfernen; Dry-Run-Logs nicht weitergeben (K1) |
| `No KAS Password found` | Passwort fehlt | `docs/operations/RUNBOOK.md` |
| `Keyring lookup failed: …` | kein Keyring-Backend (z. B. Linux ohne Secret Service) | `KAS_PASS` nutzen oder Backend installieren |
| `ERROR: SSL is active but keys are missing in response` | API liefert in der Massenabfrage keine Schlüssel | Host einzeln prüfen (`debug/ssl_inspect_verbose.py` — Ausgabe enthält Schlüsselmaterial, K3) |
| `[ERROR] Verification FAILED! Missing records` | Anlegen expliziter Records gescheitert | Wildcard bleibt erhalten (gewollt); Ursache im Fault-Text prüfen |
| `KasConnectionError … 500` | Netzwerk oder verdeckter Fault (K7) | `docs/operations/RUNBOOK.md` |

---

## Scheduling / Automatisierung

**Manueller Betrieb** (Standard): Alle Skripte sind für den manuellen Aufruf gebaut. `export_account.py` und
`example_usage.py` fragen fehlende Zugangsdaten interaktiv ab und sind ohne hinterlegte Zugangsdaten nicht
unbeaufsichtigt lauffähig.

**Automatisierter Betrieb** — nur für `ssl_enforce_hsts.py` (liest ausschließlich Umgebungsvariablen) sinnvoll und
erst, wenn Fehler zu einem Exit-Code ≠ 0 führen (`docs/BACKLOG.md`). Bis dahin die Ausgabe nach `ERROR`/`FAILED`
auswerten:

```bash
# Cron-Beispiel (Linux/macOS), Passwort über die Umgebung des Dienstkontos, nicht in der crontab
0 3 * * 1  cd /opt/all-inkl-kas-sdk && .venv/bin/python scripts/ssl_enforce_hsts.py > /var/log/kas-hsts.txt 2>&1
```
