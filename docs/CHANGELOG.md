# Changelog – all-inkl-kas-sdk

Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/).
Einträge chronologisch absteigend (neueste oben). Jeder Eintrag entspricht
genau einem Inkrement (= einem Commit oder einer eng zusammengehörigen
Commit-Serie). Roadmap-Änderungen (KICKOFF Phase 1 Punkt 2a), Reflexions-Refreshs und
Post-Mortems erhalten einen kurzen Eintrag ohne I#.

Nicht alle Sektionen sind in jedem Eintrag nötig — leere Sektionen weglassen.

Die Projekthistorie vor der Doku-Baseline steht nur in `git log` (34 Commits bis `412a2ff`, 2026-02-05 bis
2026-02-13); sie wird hier nicht rückwirkend nachgetragen.

---

## [2026-10-23] I11 – Untergrenzen für transitive Sicherheitsfixes (`certifi`, `urllib3`)

Aus dem Kadenz-Sweep 2026-10-23 (Critical, vor I2 gezogen). Phase 1 Punkt 2a: Überschneidung mit I6 (gleiche
Dateien `pyproject.toml`/`requirements.txt`, gleiche Bedrohung 5) bewusst **getrennt gelassen** — I6 braucht die
ADR zur Python-Mindestversion, I11 sollte als Critical-Fix sofort und ohne diese Entscheidung kommen.

### Security
- `pyproject.toml` und `requirements.txt`: `certifi>=2026.10.19` (alle Python-Versionen), `urllib3>=2.8.0` und
  `python-dotenv>=1.2.2` (je mit Marker `python_version >= "3.10"`), Kommentar „nur Sicherheits-Floor". Werte gegen
  PyPI JSON geprüft (2026-10-23): alle drei Versionen veröffentlicht, nicht zurückgezogen.
- **Abweichung vom Plan:** `urllib3` 2.8.0 und `python-dotenv` 1.2.2 verlangen laut PyPI `requires_python` Python
  ≥ 3.10; ohne Marker wäre das Paket unter 3.9 (CI-Matrix, `requires-python >=3.9`) nicht installierbar. Unter 3.9
  bleibt `python-dotenv>=1.0.0`, `urllib3` ohne Floor (aufgelöst 2.6.3) — Rest als Aufgabe in I6.

### Added
- `tests/test_dependency_floors.py`: liest die Floors aus `pyproject.toml` (`tomllib`, unter 3.11 `tomli`),
  wertet Marker aus und vergleicht mit `importlib.metadata.version()`; prüft, dass `requirements.txt` dieselben
  Einträge führt. Kein Netz.
- Extra `dev`: `packaging>=22.0`, `tomli>=1.1.0; python_version < "3.11"` (nur für diesen Test).

### Changed
- `docs/architecture/DEPENDENCIES.md` (Abschnitt „Sicherheits-Floors für transitive Pakete", dev-Pakete),
  `docs/security/DEPENDENCY_AUDIT.md` (Maßnahme umgesetzt, Rest Python 3.9), `docs/security/THREAT_MODEL.md`
  Bedrohung 5, `docs/testing/UNIT_TESTS.md` (Testdatei), `docs/STATE.md` (Risiko `certifi` geschlossen, Kennzahl
  Tests), `docs/TODO.md` (I11 entfernt, Rest in I6).

### Nachweis
```
ITERATION 1 — I11 Sicherheits-Floors
Ziel:         veraltete Umgebung (certifi < 2026.10.19) fällt im Test auf
RED-Beweis:   Wegwerf-venv (Python 3.13.14) mit `pip install -e ".[dev]" "certifi==2026.7.22"`
              a) vor der Manifest-Änderung: 6 failed, u. a.
                 AssertionError: unexpectedly None : certifi has no entry in [project].dependencies
              b) nach der Manifest-Änderung, ohne Neuinstallation:
                 AssertionError: <Version('2026.7.22')> not greater than or equal to <Version('2026.10.19')> :
                 certifi 2026.7.22 is below the security floor 2026.10.19
                 1 failed, 3 passed, 8 subtests passed
GREEN-Beweis: `pip install -e ".[dev]"` in derselben venv → certifi 2026.10.19;
              pytest -p no:cacheprovider tests/ → 34 passed, 9 subtests passed
Gate:         ruff check ✓, ruff format --check ✓, mypy ✓ (nur neue Testdatei, per uvx — Projekt-Gates 1–3 erst
              mit I5); pytest 34 passed ✓
```

DoD — frische venv (Python 3.13.14, Scratch-Ordner außerhalb des Repos):
```
$ python -m venv <scratch>/allinkl_venv_dod
$ <scratch>/allinkl_venv_dod/Scripts/python.exe -m pip install -e ".[dev]"
Successfully installed beautifulsoup4-4.15.0 certifi-2026.10.19 charset_normalizer-3.5.2 colorama-0.4.6
idna-3.20 iniconfig-2.3.1 jaraco.classes-3.4.0 jaraco.context-6.1.2 jaraco.functools-4.6.0 kas-sdk-1.0.0
keyring-25.7.0 more-itertools-11.2.1 packaging-26.3 pluggy-1.7.0 pygments-2.21.0 pytest-9.1.1
python-dotenv-1.2.4 pywin32-ctypes-0.2.3 requests-2.34.2 soupsieve-3.0.4 tabulate-0.10.0
typing-extensions-4.16.0 urllib3-2.8.0
$ python -c "…importlib.metadata.version…"
certifi 2026.10.19 | urllib3 2.8.0 | python-dotenv 1.2.4
```

Auflösung je Python-Version ohne Installation (`uv pip compile pyproject.toml --extra dev --python-version X`):
3.9 → certifi 2026.10.19, urllib3 2.6.3, python-dotenv 1.2.1, tomli 2.5.0; 3.10 → certifi 2026.10.19,
urllib3 2.8.0, python-dotenv 1.2.4; 3.11 → wie 3.10 ohne tomli.

### Confidence / Ungeprüft
- (a) Nicht getestet: Testlauf unter Python 3.9/3.10/3.11 (lokal nur 3.13) — für 3.9 nur die Auflösung per
  `uv pip compile` und die Marker-Auswahl per `Marker.evaluate({"python_version": "3.9"})` geprüft; den echten
  Lauf liefert erst die CI-Matrix nach dem Push. Projekt-Gates 1–3 (ruff, mypy) gibt es noch nicht (I5); nur die
  neue Testdatei per `uvx` geprüft. `pip-audit` weiterhin nicht gelaufen (I6).
- (b) Ungeprüft übernommen: Fix-Versionen und Advisory-Inhalte aus dem Sweep (`security/DEPENDENCY_AUDIT.md`);
  `packaging`/`tomli` als dev-Pakete statt Eigenbau — `packaging` kommt ohnehin mit `pytest`.
- (c) Ohne vollständiges Lesen geändert: `docs/security/THREAT_MODEL.md` (nur Bedrohung 5),
  `docs/testing/UNIT_TESTS.md` (nur Abschnitt 1).
- Bestehende Umgebungen (auch die lokale Entwicklungsumgebung) bleiben auf dem alten `certifi`, bis sie neu
  installiert werden — der Test macht das sichtbar, behebt es aber nicht.

### Lessons Learned
- Vor dem Eintragen eines Sicherheits-Floors die `requires_python` der Fix-Version gegen die unterstützten
  Python-Versionen des Projekts prüfen (PyPI JSON) — sonst bricht die Installation auf der ältesten Laufzeit
  (`LESSONS_LEARNED.md` L2).

---

## [2026-10-23] Kadenz-Security-Sweep (vorgezogen, fällig 2026-10-25)

Nur `docs/`, kein Code. Protokoll: `security/DEPENDENCY_AUDIT.md` → „2026-10-23 – Kadenz-Sweep".

### Security
- `certifi` < 2026.10.19 (transitiv über `requests`) betrifft uns: GHSA-6q48-6c7w-9gw2 (Critical, kompromittierte
  emSign-Wurzeln, MITM auf die API-Verbindung). `urllib3` < 2.8.0 (drei Advisories vom 2026-09-15, im Init-Sweep
  nicht erfasst) betrifft Nutzer mit älteren Umgebungen. Neues Inkrement I11 (Untergrenzen), laut
  Schweregrad-Politik vor I2. `python-dotenv` CVE-2026-28684 betrifft uns nicht (nur `load_dotenv`).
- `security/THREAT_MODEL.md` Bedrohung 5 ergänzt; Marker „Nächster Security-Sweep" auf 2026-11-06.

### Confidence / Ungeprüft
- (a) Nicht getestet: `pip-audit` nicht gelaufen (nicht installiert, Installation unterlassen); ersatzweise
  OSV-Abfrage je lokal installierter Version — erfasst nur die Stichprobe der lokalen Umgebung.
- (b) Ungeprüft übernommen: Fix-Version von `certifi` (GHSA nennt 2026.10.18, OSV 2026.10.19; Untergrenze daher
  2026.10.19).
- (c) Nicht abschließend bewertet: libexpat 2.9.0 (CVE-2026-102633, CVE-2026-77214) — ob CPythons `pyexpat`
  `XML_ParseBuffer` nutzt, nicht geprüft; beim nächsten Sweep nachholen.

---

## [2026-10-11] I1 – docs_template-Baseline eingeführt (Bestand übernommen)

Initialisiert mit docs_template v27@5ce0f84, Stack `python-cli` (nur teilweise passend), keine Overlays.
Commit-Serie: `docs: snapshot before docs_template baseline` (Diff-Anker) → `chore: enforce LF line endings
(.gitattributes + normalize)` (von `rollout_eol.sh`) → `chore: extend .gitignore (…)` → Doku-Commit (I1) →
Hash-Nachtrag.

### Added
- Template-Baseline unter `docs/`: Steuerung (`KICKOFF.md`, `STATE.md`, `TODO.md`, `CHANGELOG.md`, `BACKLOG.md`,
  `KNOWN_ISSUES.md`, `GLOSSARY.md`, `LESSONS_LEARNED.md`, `REFLECTION.md`, `BOOTSTRAP.md`), Konventionen
  (`CONVENTIONS_COMMON.md`, `CONVENTIONS.md`), `architecture/` (OVERVIEW mit Datenfluss, PROJECT_LAYOUT,
  CONFIGURATION, ERROR_HANDLING, CLI, DEPENDENCIES, ADR-Vorlage), `security/` (THREAT_MODEL mit 6 Bedrohungen aus dem
  Code — 4 belegt, 2 mit gekennzeichneter Annahme —, DATA_HANDLING, DEPENDENCY_AUDIT, AUTHENTICATION, THREAT_MODEL_GUIDE), `operations/` (SETUP, RUNBOOK,
  MONITORING, DEPLOYMENT, SECRETS_MANAGEMENT, INCIDENT_RESPONSE), `testing/` (UNIT_TESTS, INTEGRATION_TESTS),
  `principles/` (20 Prinzipien + INDEX), `features/KAS_CLIENT.md` (Hauptfeature) neben `features/FEATURE-template.md`
- Inkrementplan I2–I9 in `docs/TODO.md` (Secrets in Logs/Exporten zuerst)
- Repo-Root: `AGENTS.md` (Zeiger auf `docs/KICKOFF.md`, keine eigenen Regeln) und `CLAUDE.md` (`@AGENTS.md`)
- Interna-Hook `tools/git-hooks/pre-commit` und `commit-msg` (öffentliches Repo, `CONVENTIONS_COMMON.md` 3.1)

### Changed
- Vorhandene API-Referenz `docs/01_account.md`, `docs/02_domains_dns.md`, `docs/03_email.md`, `docs/04_system.md`:
  **unverändert** an ihrem Ort belassen, im Lese-Pfad von `docs/architecture/OVERVIEW.md` verlinkt; gefundene
  Abweichungen zum Code als `docs/KNOWN_ISSUES.md` K8 erfasst statt still korrigiert
- `.gitignore` um `.pytest_cache/`, `*.db`, `*.pfx`, `*.pem`, `*.key`, `/docs/local/`, `/.internal-terms` ergänzt;
  `.gitattributes` (`* text=auto eol=lf`) angelegt — je eigener `chore:`-Commit vor dem Doku-Commit

### Removed
- Conditional-Dateien nicht übernommen: `architecture/DATABASE.md` (Projekt nutzt keine Datenbank) und
  `architecture/DOMAIN_MODEL.md` (keine eigenen Entities; die KAS-Regeln stehen in `architecture/OVERVIEW.md` →
  Constraints und in den Services)

### Security
- Security-Currency-Abgleich beim Init durchgeführt und datiert (`docs/security/THREAT_MODEL.md`,
  `docs/security/DEPENDENCY_AUDIT.md`): `requests`-Untergrenze erlaubt CVE-2024-47081/CVE-2023-32681,
  Python 3.9 EOL, CI-Härtung fehlt
- Bestandsanalyse: KAS-Passwort im Dry-Run-Log (K1) und ungültiges XML bei `&`/`<` (K4) per lokalem Lauf belegt;
  Secret-Scan von Arbeitsbaum und History ohne Fund (nur Platzhalterwerte)

### Confidence / Ungeprüft
- (a) Nicht getestet: kein Aufruf der echten KAS-API (bewusst); K7 (Faults mit HTTP 500) und die Annahme in K2
  (Massenabfrage liefert private Schlüssel) sind unbelegt. `pip-audit` nicht gelaufen (nicht installiert,
  Installation unterlassen). Quality Gates 1–3 (ruff, mypy) im Projekt nicht eingerichtet — nur Gate 4:
  `pytest -p no:cacheprovider tests/` → 31 passed (Python 3.13, lokal).
- (b) Ungeprüft übernommen: zulässige `kas_auth_type`-Werte (die öffentliche Hoster-Doku nennt keine Werteliste);
  Python-EOL-Daten aus Sekundärquellen (herodevs/endoflife-Zusammenfassungen des Python Developer's Guide).
- (c) Nicht vollständig gelesen: `readme_KAS_API_SOURCE_OF_TRUTH.md` (nur Kopf, gezielte Greps und maschineller
  Abgleich), `example_usage.py` (erste 60 Zeilen), `tests/test_integration.py` (Fixtures überflogen), die
  Prinzipien-Dateien außer ADVOCATUS_DIABOLI, SECURITY_CURRENCY und dem Projektabschnitt von LOGGING (unverändert
  aus dem Template übernommen).
- Advocatus-Diaboli-Hook (`.claude/settings.json`, KICKOFF Phase 1 Punkt 7) bewusst nicht angelegt (öffentliches
  Repo, Zustimmung des Maintainers nötig) — Gate für diesen Commit von Hand ausgeführt.
- Doku-Sprache: Baseline deutsch, Nutzer-Doku (README, docs/01–04) englisch — Entscheidung ohne Prompter,
  vermerkt in `docs/CONVENTIONS.md`.

### Lessons Learned
- Bestandsdoku-Codebeispiele maschinell gegen Signaturen prüfen — Scope: generisch-stack
  Backport-Ziel: `stacks/python-cli/testing/UNIT_TESTS.md` | Status: offen
  Ein AST-Abgleich der Codebeispiele gegen die echten Signaturen fand 14 Abweichungen in vier übernommenen
  Doku-Dateien; billiger und belastbarer als Lesen, als Ratchet-Test wiederverwendbar.
  → Spiegel-Eintrag in `LESSONS_LEARNED.md` als `## L1:`.
