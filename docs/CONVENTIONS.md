# Coding Conventions – all-inkl-kas-sdk

Stack: Python 3.9+ (laut `pyproject.toml`; CI 3.9/3.11/3.13) | `requests`, `keyring`, `tabulate`, `python-dotenv`;
dev: `pytest`, `beautifulsoup4` | Datenbank: keine

> Gilt **zusammen mit** `docs/CONVENTIONS_COMMON.md` (stack-übergreifend: Commit-Format, Encoding,
> öffentliche Repos/Interna, Quality Gates, parallele Agenten). Diese Datei regelt die
> Stack-Spezifika und hat dort Vorrang.

> **Projekttyp:** Bibliothek (SDK) mit HTTP-Client plus Wartungsskripte — der Stack `python-cli` passt nur
> teilweise (`docs/BACKLOG.md` → Template-Evolution). Abschnitte zu `subprocess`, Workspace-Pfaden und Datenbank
> sind gestrichen, weil das Projekt sie nicht hat.

> **Sprache:** Die Projektdoku nach docs_template (`docs/` ohne die Dateien `01_*`–`04_*`) ist deutsch
> (Template-Standard, `CONVENTIONS_COMMON.md` §3). Die Nutzer-Doku für das öffentliche Publikum — `README.md` und
> die API-Referenz `docs/01_account.md` bis `docs/04_system.md` — ist englisch und bleibt englisch. Code-Bezeichner
> und Log-/Fehlermeldungen: Englisch; Docstrings im Bestand gemischt — neue Docstrings Englisch.

---

## 1. Git & Versionierung

Commit-Format, Scope-Wahl, `git add`-Regeln und Zeilenenden: `docs/CONVENTIONS_COMMON.md` §1–§2;
Commit-Pflicht pro Inkrement: `docs/KICKOFF.md` Phase 3b. Stack-spezifisch nur:

- Scope-Beispiele: `fix(I2): mask secrets in dry-run log`, `test(dns): wildcard verification`, `feat(services): …`
- Öffentliches Repo: Commit-Messages enthalten keine Interna (Interna-Hook `tools/git-hooks/commit-msg`).

## 2. Python Code-Richtlinien

- **Type Hints:** Vollständig für alle Parameter und Rückgabewerte neuer oder geänderter Funktionen. Optionale
  Parameter explizit als `Optional[str] = None` (der Bestand nutzt oft `str = None` — beim Anfassen korrigieren).
  Mindestversion 3.9: kein `X | None` in Laufzeit-Annotationen ohne `from __future__ import annotations`.
- **mypy streng:** `pyproject.toml` → `[tool.mypy]` mit `strict = true` (Gate 3). Lockerungen nur per
  `[[tool.mypy.overrides]]` für ein benanntes Modul mit Begründung als Kommentar (z. B. Drittbibliothek ohne Typen);
  `# type: ignore` nur mit Fehlercode (`# type: ignore[attr-defined]`), nie pauschal. **Stand:** mypy ist noch nicht
  eingerichtet (§8); Einführung in `docs/TODO.md` I5, Anhebung auf `strict = true` in I10.
- **Fehlerbehandlung:** SDK-Fehler als Unterklasse von `KasApiError` (`kas_sdk/exceptions.py`) — niemals nackte
  `Exception` werfen. Ungültige Aufruferparameter in Services: `ValueError` mit erlaubten Werten in der Meldung
  (Bestandsmuster). Kein leeres `except:` ohne Logging.
- **Eingabevalidierung:** Enum-artige KAS-Parameter gegen Klassenkonstanten-Tupel prüfen (`_YES_NO`,
  `_LOGGING_VALUES`, …), bevor der Request gebaut wird (Fail Fast).
  - **Bereichsvalidierung:** `if not (MIN <= x <= MAX):` statt `if MIN > x > MAX:`. Python wertet `MIN > x > MAX` als chained comparison aus: beide Bedingungen müssen gleichzeitig wahr sein, was für jeden `x` zwischen `MIN` und `MAX` unmöglich ist → Ausdruck ist immer `False`.
- **Keine Magic Strings:** KAS-Aktionsnamen und Enum-Werte als Konstanten bzw. Klassenattribute; Parameternamen
  exakt wie in `readme_KAS_API_SOURCE_OF_TRUTH.md`.
- **Keine Debug-`print()`-Calls in `kas_sdk/`:** Die Bibliothek nutzt nur `logging` (Logger `kas_sdk.client`);
  `print()` ist Skripten (`scripts/`, `debug/`, `kas_sdk/utils.py`) vorbehalten.
- **Builtin-Shadowing verboten:** Keine Klassen/Funktionen die Python-Builtins überschreiben (`ImportError`, `list`, `open` etc.).
  Bestand: Parameter `logging` in `AccountService` und `filter` in `MailFilterService` spiegeln KAS-Parameternamen —
  nicht umbenennen (öffentliche API), aber in neuen Funktionen vermeiden.

## 3. Dateiorganisation

- **200–400 Zeilen** pro Datei, max. 500 Zeilen. Größte Datei heute: `scripts/export_account.py` (358),
  `kas_sdk/services/account.py` (326).
- Ein Modul = ein KAS-Paket (Services) bzw. eine Aufgabe (Skripte) — `docs/architecture/PROJECT_LAYOUT.md`.
- Imports: stdlib → Drittanbieter → eigene Module. Keine Wildcard-Imports.
- Neue Services werden in `KasClient._SERVICE_MAP` und `kas_sdk/services/__init__.py` registriert.

## 4. Netzwerk, SOAP & Secrets

- **Ein Transportpfad:** Alle API-Aufrufe laufen über `KasClient.request(action, params)`; Services und Skripte
  rufen nie selbst `requests` auf.
- **Parameter sind Strings:** `request` wandelt Werte per `str()` um und lässt `None` weg — Services übergeben
  optionale Parameter nur, wenn sie gesetzt sind.
- **Nie Request-Bodys, Parameter-Dicts oder `kas_auth_data` loggen** — auch nicht auf `DEBUG` oder im Dry-Run.
- **Werte im SOAP-Envelope XML-escapen** (nach `docs/TODO.md` I3 verbindlich; heute verletzt, K4).
- **Schreibende Skripte:** Dry-Run als Default, Ausführung nur mit explizitem Flag (`--execute`, Muster
  `scripts/dns_remove_wildcards.py`).
- **Pfade als `pathlib.Path`** in neuem Code; Ausgabedateien mit Zeitstempel im Namen, nie bestehende überschreiben.

## 5. Security-Checkliste vor jedem Commit

- [ ] Keine Hardcoded-Pfade (keine absoluten Pfade im Quellcode)
- [ ] Keine sensiblen Daten (Passwörter, private Schlüssel, Session-Tokens, PII) in Log-Ausgaben, Exporten oder
      Exception-Texten
- [ ] Neue Antwortfelder mit Secret-Charakter in die Maskierung von `scripts/export_account.py` aufgenommen
- [ ] Beispielwerte fiktiv (`example.com`, `w0123456`), keine echten Hostnamen/Logins (öffentliches Repo)
- [ ] Neue Abhängigkeit mit Untergrenze ohne bekannte CVE (`docs/security/DEPENDENCY_AUDIT.md`)

---

## 6. Autonomes Arbeiten & Fehlerbehebung

- Bei Fehlern: nicht sofort abbrechen. Logs/Tracebacks lesen, einen Lösungsversuch starten.
- Nur Dateien verändern, die für das aktuelle Inkrement relevant sind.
- **Keine Aufrufe gegen die echte KAS-API** durch Agenten — Verifikation über Dry-Run, gemocktes `requests.post`
  und XML-Fixtures; Live-Prüfungen macht ein Mensch mit eigenem Account.
- Am Ende jedes Inkrements: `docs/TODO.md`, `docs/CHANGELOG.md`, `docs/STATE.md` aktualisieren.
- Vor jedem Commit: Security-Checkliste (Abschnitt 5) durchgehen.

---

## 7. Dokumentationspflichten (Trigger-Regeln)

Vollständige Trigger-Matrix in `docs/KICKOFF.md` Phase 3. Kurzfassung:

### Neue Funktion / Klasse / Modul
→ `docs/architecture/OVERVIEW.md` → Modul-Verantwortlichkeiten

### Neue oder geänderte Service-Methode (öffentliche SDK-API)
→ API-Referenz `docs/01_account.md` … `docs/04_system.md` (englisch) + `README.md` → „Supported Services Overview"

### Neuer CLI-Parameter / Konfigurationsoption
→ `README.md` + `docs/architecture/CLI.md` + `docs/architecture/CONFIGURATION.md` + betroffene `docs/features/`

### Neue externe Abhängigkeit (Paket oder Binary)
→ `docs/architecture/DEPENDENCIES.md`

### Datenfluss oder CLI-Verhalten geändert
→ `docs/architecture/OVERVIEW.md` → Mermaid `flowchart TD` + `docs/architecture/CLI.md`

### STATE.md (immer nach jedem Inkrement)
1. Freitext "Letztes abgeschlossenes Inkrement: …"
2. Tabelle: neue Zeile `| I# | Titel | Datum | Commit-Hash |`

---

## 8. Quality Gates — pre-commit (Definition of Done)

Die vier Gates der Definition of Done müssen lokal grün sein
(„grün im Test-Runner ≠ commit-bereit"):

```bash
ruff check .            # Gate 1 — Linter (Imports I001, ungenutzte F401, Stil)
ruff format --check .   # Gate 2 — Formatter (Check-Modus)
mypy kas_sdk            # Gate 3 — Typ-Korrektheit (flaches Layout, kein src/)
pytest tests/           # Gate 4 — Offline-Tests (keine Marker registriert; alle Tests laufen ohne Netz)
```

**Stand bei Init (2026-10-11):** Nur Gate 4 ist eingerichtet (CI und lokal, 31 Tests grün). `ruff` und `mypy`
sind weder in `[project.optional-dependencies].dev` noch konfiguriert; Einführung inklusive Baseline-Bereinigung in
`docs/TODO.md` I5. Bis dahin ist Gate 4 verbindlich, das Fehlen von Gate 1–3 wird im Confidence-Block jedes
`CHANGELOG.md`-Eintrags vermerkt. Lokaler Hook: projekteigene Prüfungen gehören nach
`tools/git-hooks/pre-commit.local` (der Interna-Hook ruft sie auf, `CONVENTIONS_COMMON.md` 3.1).
