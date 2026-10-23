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
| `python-dotenv` | `≥ 1.2.2` ab Python 3.10, sonst `≥ 1.0.0` (I11) | lädt `.env` beim Import von `kas_sdk.client` | still übersprungen (`ImportError` wird ignoriert); Werte müssen in der Umgebung stehen |

### Sicherheits-Floors für transitive Pakete

Direkt eingetragen, aber **nicht direkt genutzt** — sie kommen über `requests` und stehen nur in `pyproject.toml`
und `requirements.txt`, damit pip keine Version mit bekannter Lücke installiert (I11, Sweep 2026-10-23,
`docs/security/DEPENDENCY_AUDIT.md`). `requests` selbst verlangt nur `certifi>=2023.5.7` und `urllib3>=1.26`.

| Paket | Untergrenze | Grund | Gilt für |
|-------|-------------|-------|----------|
| `certifi` | `≥ 2026.10.19` | GHSA-6q48-6c7w-9gw2 (Critical): kompromittierte emSign-Wurzeln entfernt; `requests` prüft das TLS-Zertifikat der KAS-API gegen dieses Bündel | alle Python-Versionen |
| `urllib3` | `≥ 2.8.0` | CVE-2026-97687 (HTTPS-Proxy-TLS), CVE-2026-97689, CVE-2026-97688 | nur Python ≥ 3.10 (Marker) — 2.8.0 verlangt Python ≥ 3.10; unter 3.9 wird `urllib3` 2.6.3 aufgelöst (`uv pip compile --python-version 3.9`), ohne diese Fixes (I6, ADR-001) |
| `python-dotenv` | `≥ 1.2.2` | CVE-2026-28684 (betrifft das SDK nicht, nur mitgezogen) | nur Python ≥ 3.10 (Marker), unter 3.9 bleibt `≥ 1.0.0` |

Prüfung ohne Netz: `tests/test_dependency_floors.py` vergleicht die installierten Versionen
(`importlib.metadata`) mit den Untergrenzen aus `pyproject.toml` und prüft, dass `requirements.txt` dieselben
Einträge führt. Eine veraltete Umgebung macht den Test rot. Einen Floor erst entfernen, wenn `requests` ihn selbst
verlangt.

### Optionale pip-Pakete

| Paket | Version | Zweck | Ohne dieses Paket |
|-------|---------|-------|-------------------|
| `beautifulsoup4` | `≥ 4.12.0` (Extra `dev`) | HTML-Parsing in `scripts/generate_source_of_truth.py` | nur der SOT-Generator ist nicht lauffähig |

---

## Entwicklungs-/Test-Pakete

| Paket | Zweck |
|-------|-------|
| `pytest` (`≥ 7.0`, Extra `dev`) | Test-Runner (Tests sind `unittest.TestCase`-Klassen, laufen unter pytest) |
| `packaging` (`≥ 22.0`, Extra `dev`) | Requirement-, Marker- und Versionsvergleich in `tests/test_dependency_floors.py` (I11) |
| `tomli` (`≥ 1.1.0`, Extra `dev`, nur Python < 3.11) | liest `pyproject.toml` im selben Test, wo `tomllib` fehlt (I11) |
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
