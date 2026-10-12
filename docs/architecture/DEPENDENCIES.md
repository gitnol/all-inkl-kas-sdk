# Externe Abhängigkeiten – all-inkl-kas-sdk

Quelle: `pyproject.toml` (maßgeblich, `[project].dependencies` und `[project.optional-dependencies].dev`) und
`requirements.txt` (gleiche Laufzeit-Pakete). Es gibt kein Lockfile; die Versionen sind nur nach unten begrenzt.
Sicherheitsbewertung: `docs/security/DEPENDENCY_AUDIT.md`.

---

## Laufzeit-Pakete (pip)

| Paket | Version | Zweck | Risiko bei Ausfall |
|-------|---------|-------|-------------------|
| `requests` | `≥ 2.0.0` (geplant `≥ 2.32.4`, I6) | HTTPS-POST an die SOAP-API (`kas_sdk/client.py`) | SDK funktionslos — einziger Transport |
| `keyring` | `≥ 25.0.0` | Passwort aus dem System-Keyring (Client: optional per `import` im `try`; `kas_sdk/utils.py`: Pflicht-Import) | Client: Warnung, Passwort muss per Argument/Env kommen; Skripte über `utils`: Import-Fehler |
| `tabulate` | `≥ 0.9.0` | Tabellenausgabe in Skripten und im Export (`kas_sdk/utils.py`, `scripts/*.py`) | Skripte brechen beim Import ab; die Bibliothek selbst nicht |
| `python-dotenv` | `≥ 1.0.0` | lädt `.env` beim Import von `kas_sdk.client` | still übersprungen (`ImportError` wird ignoriert); Werte müssen in der Umgebung stehen |

### Optionale pip-Pakete

| Paket | Version | Zweck | Ohne dieses Paket |
|-------|---------|-------|-------------------|
| `beautifulsoup4` | `≥ 4.12.0` (Extra `dev`) | HTML-Parsing in `scripts/generate_source_of_truth.py` | nur der SOT-Generator ist nicht lauffähig |

---

## Entwicklungs-/Test-Pakete

| Paket | Zweck |
|-------|-------|
| `pytest` (`≥ 7.0`, Extra `dev`) | Test-Runner (Tests sind `unittest.TestCase`-Klassen, laufen unter pytest) |
| `ruff`, `mypy` | Gate 1–3 — **noch nicht** eingetragen, Einführung `docs/TODO.md` I5 |
| `pip-audit` | Dependency-Scan — **noch nicht** eingetragen, Einführung `docs/TODO.md` I6 |

---

## Externe Binaries

Keine. Das Projekt ruft keine externen Programme per `subprocess` auf.

---

## Externe Services

| Service | Adresse | Zweck | Fallback |
|---------|---------|-------|---------|
| KAS SOAP-API des Hosters | `https://kasapi.kasserver.com/soap/KasApi.php` | sämtliche Verwaltungsaktionen (21 Pakete, 77 genutzte Aktionen) | keiner; Dry-Run liefert Mock-Antworten ohne Netz |
| KAS-Weboberfläche (SSO) | `https://kas.all-inkl.com/` | Ziel der mit `add_session` erzeugten Session-Tokens (Beispiel in `docs/01_account.md`) | — |
| GitHub Actions | `github.com` | CI (`.github/workflows/ci.yml`) | lokale Testläufe |

Die KAS-API ist ein Fremdsystem ohne Testumgebung: Jeder echte Aufruf wirkt auf einen produktiven Account.

---

## Systemabhängigkeiten

| Ressource | Version / Pfad | Zweck |
|-----------|---------------|-------|
| Python | ≥ 3.9 (`requires-python`) | keine Sprachfeatures jenseits 3.9 im Einsatz; 3.9 ist EOL (I6) |
| System-Keyring-Backend | Windows Credential Manager / macOS Keychain / Secret Service (Linux) | Ablage des KAS-Passworts (Dienst `kas_api`) |
| Expat (über Python) | lokal geprüft 2.8.1 | XML-Parsing der Antworten |

---

## Upgrade-Hinweise

- **`requests`:** Untergrenze erst nach Prüfung anheben; Verhalten bei `raise_for_status()` und Exceptions ist
  Teil des Fehlervertrags (`docs/architecture/ERROR_HANDLING.md`).
- **`keyring` (Major-Updates):** Backend-Auswahl kann sich ändern; nach Update prüfen, ob gespeicherte Einträge
  (Dienst `kas_api`) noch gefunden werden.
- **KAS-API:** Änderungen kündigt nur die Hoster-Doku an. Nach einer neuen `API Funktionen.html`
  `scripts/generate_source_of_truth.py` laufen lassen und den Diff von `readme_KAS_API_SOURCE_OF_TRUTH.md` gegen die
  Services prüfen (Abdeckung: `docs/STATE.md` → Kennzahlen).
