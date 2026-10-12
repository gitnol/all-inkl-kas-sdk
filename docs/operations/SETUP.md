# Entwicklungsumgebung Setup – all-inkl-kas-sdk

---

## Voraussetzungen

- Python ≥ 3.9 (`python --version` prüfen); empfohlen eine noch unterstützte Version (3.11–3.14), da 3.9 EOL ist
- pip (kommt mit Python), Git
- Für Tests und Entwicklung: **kein** KAS-Account nötig — alle Tests laufen offline
- Für echte Läufe der Skripte: ein KAS-Login mit Passwort (möglichst ein Unter-Account, `docs/security/AUTHENTICATION.md`)

---

## Installation

### Windows (PowerShell)

```powershell
cd all-inkl-kas-sdk
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> **Hinweis:** Falls PowerShell Scripts blockiert:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

```powershell
pip install -e ".[dev]"

# Installation prüfen
python -c "import kas_sdk; print('OK')"
```

### Linux / macOS

```bash
cd all-inkl-kas-sdk
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

`pip install -e .` ist Pflicht: Skripte unter `scripts/`, `debug/` und die Tests importieren `kas_sdk` als
installiertes Paket. `requirements.txt` enthält nur die Laufzeit-Pakete (ohne `pytest`, `beautifulsoup4`).

### Git-Hooks (einmal pro Klon)

```bash
git config core.hooksPath tools/git-hooks
# .internal-terms im Repo-Root anlegen (gitignored): ein interner Begriff pro Zeile, # = Kommentar
```

Der Interna-Hook verhindert, dass interne Begriffe aus `.internal-terms` in Commits oder Commit-Messages landen
(`docs/CONVENTIONS_COMMON.md` 3.1). Ohne `.internal-terms` warnt er nur.

---

## Zugangsdaten hinterlegen (nur für echte Läufe)

Bevorzugt im System-Keyring:

```bash
keyring set kas_api w0123456          # fragt das Passwort ab (Login fiktiv)
keyring set kas_api default_kas_login # Wert: w0123456 — Default-Login für die Skripte
```

Alternativ für die laufende Shell `KAS_LOGIN`/`KAS_PASS` setzen oder `.env` aus `.env.example` anlegen
(nur Einzelplatz-Entwicklung, `.env` ist gitignored). Reihenfolge und Unterschiede: `docs/architecture/CONFIGURATION.md`.

---

## Wichtige Commands

```bash
# Tests (offline, wie CI)
pytest tests/ -v

# SDK ohne Netz ausprobieren (Mock-Antworten; Achtung K1: loggt Parameter)
KAS_DRY_RUN=1 python example_usage.py

# Skripte: Aufrufe, Flags und Laufmodi
#   → docs/architecture/CLI.md
python scripts/dns_remove_wildcards.py --help
```

---

## Konfiguration

Zugangsdaten über Keyring/Umgebung, Skriptoptionen als CLI-Argumente. Vollständige Tabelle:
`docs/architecture/CONFIGURATION.md`.

| Parameter | Beschreibung | Beispiel |
|-----------|-------------|---------|
| `KAS_LOGIN` | KAS-Login | `w0123456` |
| `KAS_PASS` | KAS-Passwort (besser Keyring) | — |
| `KAS_DRY_RUN` | SDK sendet keine Requests | `1` |
| `--execute` | `dns_remove_wildcards.py`: Änderungen ausführen | `--execute` |
| `--show-passwords` | `export_account.py`: Passwörter im Klartext exportieren | `--show-passwords` |
