# CLI-Schnittstelle – all-inkl-kas-sdk

Das Projekt hat keinen einzelnen Einstiegspunkt: Die Bibliothek wird importiert (`from kas_sdk import KasClient`),
dazu kommen eigenständige Skripte. Diese Datei beschreibt die Aufrufschnittstelle der Skripte. Die Python-API der
Services steht in der API-Referenz `docs/01_account.md` bis `docs/04_system.md`.

Voraussetzung für alle Skripte: `pip install -e .` im Repo-Root (sonst scheitert `import kas_sdk`), Zugangsdaten
laut `docs/architecture/CONFIGURATION.md`.

---

## Aufruf

```bash
python scripts/export_account.py [--show-passwords]
python scripts/dns_remove_wildcards.py [--execute] [--domain DOMAIN]
python scripts/generate_source_of_truth.py [--html PFAD] [--output PFAD]
python scripts/ssl_enforce_hsts.py                  # Steuerung nur über Umgebungsvariablen
python scripts/ssl_update_hsts_manual.py            # Hostliste als Konstante DOMAINS im Skript
python debug/ssl_inspect_host.py                    # Zielhost als Konstante im Skript
python debug/ssl_inspect_verbose.py                 # Zielhost als Konstante TARGET_HOST
python example_usage.py                             # interaktiv
```

---

## Argument-Tabelle

| Skript | Argument | Typ | Pflicht | Default | Validierung | Beschreibung |
|--------|----------|-----|---------|---------|-------------|-------------|
| `export_account.py` | `--show-passwords` | Flag | Nein | `False` | — | Passwortfelder im Export im Klartext statt `***` |
| `dns_remove_wildcards.py` | `--execute` | Flag | Nein | `False` | — | Änderungen wirklich ausführen (ohne Flag: nur lesen und anzeigen) |
| `dns_remove_wildcards.py` | `--domain` | `str` | Nein | alle Domains des Accounts | exakter Vergleich mit `domain_name` | Lauf auf eine Domain begrenzen |
| `generate_source_of_truth.py` | `--html` | `str` (Pfad) | Nein | `<repo>/API Funktionen.html` | muss existieren, sonst Exit 1 | lokale Kopie der KAS-Funktionsdoku |
| `generate_source_of_truth.py` | `--output` | `str` (Pfad) | Nein | `<repo>/readme_KAS_API_SOURCE_OF_TRUTH.md` | — | Zieldatei (wird überschrieben) |
| `ssl_enforce_hsts.py` | `KAS_LOGIN`, `KAS_PASS` (Env) | `str` | Ja | — | beide gesetzt, sonst Exit 1 | Zugangsdaten (kein Keyring, keine Rückfrage) |
| `ssl_enforce_hsts.py` | `KAS_AUTH_TYPE` (Env) | `str` | Nein | `plain` | — | Auth-Typ |
| `ssl_enforce_hsts.py` | `KAS_DRY_RUN` (Env) | Bool-String | Nein | aus | `true`/`1`/`yes` | echte Lesezugriffe, Schreibzugriffe nur angezeigt |

---

## Laufmodi

| Modus | Aktivierung | Verhalten |
|-------|------------|-----------|
| SDK-Dry-Run | `KasClient(dry_run=True)` oder `KAS_DRY_RUN=1` | **Kein** Request — weder lesend noch schreibend; Mock-Antwort `ReturnString=TRUE` |
| Skript-Dry-Run `dns_remove_wildcards.py` | Default (ohne `--execute`) | echte Lesezugriffe, geplante Änderungen werden nur ausgegeben |
| Skript-Dry-Run `ssl_enforce_hsts.py` | `KAS_DRY_RUN=1` | Skript entfernt die Variable, damit das SDK echt liest; Schreibzugriffe nur angezeigt |
| Ausführen | `--execute` bzw. `ssl_enforce_hsts.py` ohne `KAS_DRY_RUN` | schreibt in den KAS-Account |
| Ohne Schutz | `ssl_update_hsts_manual.py` | schreibt **immer** (kein Dry-Run), Hostliste vorher im Skript prüfen |

> Achtung Uneinheitlichkeit: `ssl_enforce_hsts.py` schreibt standardmäßig, `dns_remove_wildcards.py` nicht.
> Neue Skripte folgen dem Muster „Dry-Run als Default" (`docs/CONVENTIONS.md` §4).

---

## Exit-Codes

| Code | Bedeutung | Wann |
|------|-----------|------|
| `0` | Ende des Skripts | auch nach gefangenen Fehlern pro Host/Domain und bei fehlenden Zugangsdaten in `export_account.py`/`dns_remove_wildcards.py`/`ssl_update_hsts_manual.py` |
| `1` | Abbruch | `ssl_enforce_hsts.py` ohne `KAS_LOGIN`/`KAS_PASS`; `generate_source_of_truth.py` ohne HTML-Datei; nicht gefangene Exception (Traceback) |
| `2` | Ungültige Eingabe | unbekannte Argumente (argparse) |
| `130` | Abbruch | `KeyboardInterrupt` (Strg+C), Python-Standard |

Dass Fehler pro Host mit Exit 0 enden, ist für automatisierte Läufe ein bekanntes Defizit (`docs/BACKLOG.md`).

---

## Konfigurationsaufbau (Reihenfolge)

```
argparse (falls vorhanden)
    ↓
get_kas_credentials()  — Keyring → Env → interaktive Eingabe (bzw. nur Env in ssl_enforce_hsts.py/debug)
    ↓
KasClient(kas_login, kas_auth_data, …)  — Login-Pflicht, Dry-Run-Auflösung
    ↓
Skriptlogik (Schleife über Domains/Hosts, pro Element try/except)
```

Ein zentrales `build_config()` gibt es nicht; Validierung passiert verteilt (argparse, Konstruktor, Services).

---

## Beispielaufrufe

```bash
# Konfigurationsexport (Passwörter maskiert), Ausgabe unter scripts/output/
python scripts/export_account.py

# Wildcard-Analyse ohne Änderung für eine Domain
python scripts/dns_remove_wildcards.py --domain example.com

# Wildcard-Entfernung ausführen (vorher Dry-Run-Ausgabe prüfen, docs/KNOWN_ISSUES.md K5)
python scripts/dns_remove_wildcards.py --domain example.com --execute

# HSTS-Prüfung ohne Schreibzugriff
KAS_DRY_RUN=1 python scripts/ssl_enforce_hsts.py

# Source of Truth neu erzeugen (benötigt pip install -e ".[dev]" wegen beautifulsoup4)
python scripts/generate_source_of_truth.py --html "API Funktionen.html"
```

---

## Bekannte Validierungsfallstricke

- **Python Chained Comparisons:** `if 0 > x > MAX:` ist immer `False` (logisch unmöglich).
  Korrekt: `if not (0 <= x <= MAX):` — diese Falle bei allen Bereichs-Validierungen prüfen
  (Bestand korrekt: `logage` in `AccountService`).
- **Zwei Dry-Run-Begriffe:** SDK-Dry-Run unterdrückt auch Lesezugriffe; Skript-Dry-Runs lesen echt. `.env.example`
  beschreibt den SDK-Dry-Run falsch („reads still work", `docs/KNOWN_ISSUES.md` K11).
