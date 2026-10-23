# Unit Test Conventions – all-inkl-kas-sdk

Framework: pytest als Runner; die bestehenden Tests sind `unittest.TestCase`-Klassen mit `unittest.mock.patch`.
Neue Tests dürfen pytest-Stil (Funktionen, `monkeypatch`, `caplog`) nutzen.

---

## 1. Grundregeln

- Test-Dateien beginnen mit `test_` (pytest-Default), liegen flach unter `tests/` (`testpaths = ["tests"]` in
  `pyproject.toml`):
  ```
  tests/
  ├── test_payloads.py      # Request-Aufbau: gesendetes SOAP-XML → JSON-Payload → Parameter
  ├── test_integration.py   # Parsing realistischer SOAP-Antworten, Exceptions, Dry-Run, Account-Validierung
  └── test_dependency_floors.py  # Sicherheits-Floors: installierte Versionen ≥ Untergrenzen aus pyproject.toml
  ```
- Jeder Test läuft ohne Netz: `kas_sdk.client.requests.post` wird gepatcht oder `dry_run=True` gesetzt.
  **Kein Test ruft die echte KAS-API auf** — es gibt keine Testumgebung beim Hoster.
- Zugangsdaten in Tests sind fiktiv (`'user'`, `'pass'`, `w999`); Umgebungsvariablen nur über
  `patch.dict('os.environ', …)` setzen.
- Achtung Seiteneffekt: `import kas_sdk.client` lädt eine `.env` aus dem Arbeitsverzeichnis; Tests deshalb nicht
  in einem Verzeichnis mit echter `.env` ausführen (sonst greifen echte Werte, z. B. `KAS_DRY_RUN`).

---

## 1b. TDD-Disziplin (Python-Idiome)

Die Disziplin selbst (behaviorales Rot, erster-Lauf-grün → STOPPEN, Mutationsprüfung, Iterations-Log, Einsatzgrenze)
steht in `docs/KICKOFF.md` Phase 2 #2, die Gate-Reihenfolge in `docs/CONVENTIONS_COMMON.md` §5. Für diesen Stack:

- **Strukturelles Rot** sind `ImportError`/`NameError`/`AttributeError` (Symbol fehlt) — zulässiges Zwischenrot.
  Vor der echten Implementierung muss pytest an einer **scheiternden `assert`-Zeile** rot sein; diesen Output
  zitieren (`../principles/VERIFY_BEFORE_CITE.md`).
- **Gate-Reihenfolge konkret:** `ruff check` → `ruff format --check` → `mypy` → `pytest` (Aufrufe:
  `docs/CONVENTIONS.md`, Abschnitt „Quality Gates"; Gate 1–3 erst ab I5 eingerichtet); Gate-Zeile im Iterations-Log z. B.
  `Gate: ruff — (nicht eingerichtet)  mypy — (nicht eingerichtet)  pytest 31 passed ✓`.
- **Einsatzgrenze:** Das Verhalten der echten KAS-API (Fault-Codes, HTTP-Status, Antwortfelder) ist nicht
  TDD-bar. Orakel sind `readme_KAS_API_SOURCE_OF_TRUTH.md` und dokumentierte bzw. von Menschen aufgezeichnete
  Antworten als XML-Fixture (`../principles/ORACLE_AND_RATCHET.md`) — nie vom Agenten erfundene Antworten als
  „echt" ausgeben.

---

## 2. Typisierung & Syntax

- Type Hints in neuen Testfunktionen; bestehende `unittest`-Klassen beim Anfassen nicht umschreiben
- Mock-Variablen nicht mit `None` initialisieren ohne vorher den Typ zu definieren

---

## 3. Gemeinsame Fixtures

Es gibt keine `conftest.py`; XML-Fixtures liegen als Modulkonstanten in `tests/test_integration.py`
(`XML_SUCCESS_SIMPLE`, `XML_DNS_RECORDS`, `XML_SOAP_FAULT`, `XML_WITH_NAMESPACES`). Werden Fixtures von mehreren
Dateien gebraucht, in eine `tests/conftest.py` bzw. `tests/fixtures/*.xml` verschieben — nicht kopieren.

Muster für das Auslesen des gesendeten Payloads (aus `tests/test_payloads.py`):

```python
from unittest.mock import patch
import json
import xml.etree.ElementTree as ET
from kas_sdk import KasClient

@patch('kas_sdk.client.requests.post')
def test_dns_add_record_payload(mock_post):
    mock_post.return_value.content = (
        b'<root><return><item><key>ReturnString</key><value>TRUE</value></item></return></root>'
    )
    KasClient('user', 'pass').dns.add_dns_settings(
        zone_host='example.com', record_type='A', record_name='test', record_data='1.2.3.4'
    )
    body = mock_post.call_args[1]['data']
    request = ET.fromstring(body).find(
        './/{http://schemas.xmlsoap.org/soap/envelope/}Body//{urn:xmethods-delayed-quotes}KasApi/KasRequest'
    ).text
    params = json.loads(request)['KasRequestParams']
    assert params['zone_host'] == 'example.com.'
```

---

## 4. Mock-Pattern: HTTP-Transport und Logs

- **Transport:** `@patch('kas_sdk.client.requests.post')` — `return_value.content` mit SOAP-XML belegen;
  Netzwerkfehler über `side_effect = requests.exceptions.ConnectionError(...)`.
- **HTTP-Status:** `raise_for_status` ist am `MagicMock` ein No-op; für Status-Tests explizit
  `mock_post.return_value.raise_for_status.side_effect = requests.HTTPError(...)` setzen.
- **Logs auf Secrets prüfen** (für I2): pytest-`caplog` auf `DEBUG` und ein Sentinel-Passwort, das im Log nicht
  vorkommen darf:

```python
import logging
from kas_sdk import KasClient

def test_dry_run_does_not_log_password(caplog):
    caplog.set_level(logging.DEBUG, logger="kas_sdk.client")
    KasClient("w0000000", "PW-SENTINEL", dry_run=True).statistic.get_space()
    assert "PW-SENTINEL" not in caplog.text
```

- **Flood-Schutz:** Tests mit mehreren Requests auf einem Client warten sonst je 2 s — `flood_protection_delay=0`
  übergeben.

### Optionale Abhängigkeiten: `pytest.importorskip()`

Tests für `scripts/generate_source_of_truth.py` brauchen `beautifulsoup4` (Extra `dev`):

```python
bs4 = pytest.importorskip("bs4")  # überspringt den Test, wenn das Extra nicht installiert ist
```

---

## 5. Was wird getestet

- **Request-Aufbau:** Werte als Strings, `None`-Werte weggelassen, Trailing Dot bei `add_dns_settings`, kein
  `zone_host` bei `update_dns_settings`
- **Antwort-Parsing:** `item/key/value` → `dict`, Schlüssel `0..N` → `list`, Namespace-Präfixe, `Response`-Unwrapping
- **Fehlerpfade:** SOAP-Fault → `KasApiError`, kaputtes XML → `KasApiError`, Netzwerkfehler → `KasConnectionError`,
  fehlender Login → `KasAuthError`
- **Validierung der Services:** ungültige Enum-/Bereichswerte → `ValueError` (heute nur `AccountService` abgedeckt)
- **Dry-Run:** kein `requests.post`, Aktivierung per Argument und Umgebungsvariable
- **Edge Cases:** leere Antworten, einzelner Datensatz statt Liste, Sonderzeichen in Werten (`&`, `<`)
- **Lücken (Stand Init):** keine Tests für Skripte (`scripts/`, `debug/`), für `kas_sdk/utils.py` und für 20 der
  21 Services außer Payload-Stichproben

---

## 6. Ausführung

```bash
# Alle Tests (= Gate 4, offline)
pytest tests/

# Einzelne Datei
pytest tests/test_integration.py -v

# Ohne Cache-Verzeichnis im Repo (z. B. in Agenten-Läufen)
pytest -p no:cacheprovider tests/
```

Coverage wird noch nicht gemessen (`pytest-cov` nicht in den dev-Abhängigkeiten). Marker sind nicht registriert,
weil es keine Tests mit Netz/echten Diensten gibt; kommen Live-Tests hinzu, bekommen sie den Marker `live` und
werden in `pyproject.toml` unter `[tool.pytest.ini_options].markers` registriert. Kommt Coverage hinzu, gilt
≥ 80 % der Business-Logik-Funktionen als Richtwert — ein Hinweis auf ungetesteten Code, kein Qualitätsziel.

### Testgüte (Regel: `docs/principles/TEST_EFFECTIVENESS.md`)

- **Mutationsprüfung:** `mutmut run`, danach `mutmut results` bzw. `mutmut browse`. Die zu mutierenden Pfade stehen in
  `pyproject.toml` unter `[tool.mutmut]`; der Schlüsselname hat sich zwischen mutmut-Versionen geändert — die Doku der
  eingesetzten Version nehmen. Unter Windows vor dem ersten Lauf prüfen, ob die Version nativ läuft (sonst WSL).
  Überlebende Mutanten zeigen typischerweise Tests, die nur prüfen, *dass* ein Ergebnis bzw. Befund entsteht, nicht
  *welcher* (Code, Feldpfad, Grenzwert wie 0/1/Maximum) — dort zuerst nachschärfen. Fallen von `mutmut` 3: Es sucht
  den Code unter `./src` des Aufrufverzeichnisses (in einem Workspace aus dem Paketordner starten); geänderte Tests
  bei unverändertem Code bewertet es nicht neu (nach Teständerungen frisch laufen lassen); Tests laufen in der Kopie
  `mutants/`, feste `Path(__file__).parents[n]`-Pfade brechen dort — die Projektwurzel über eine Marker-Datei suchen.
  Projektbezug: flaches Layout ohne `src/` — die Pfade (`kas_sdk/`) deshalb ausdrücklich unter `[tool.mutmut]`
  eintragen.
- **Eigenschaftstests:** Hypothesis. Gefundene Gegenbeispiele zusätzlich mit `@example(...)` festschreiben.
  ```python
  from hypothesis import example, given, strategies as st

  @given(st.text())
  @example("")
  def test_roundtrip(text: str) -> None:
      assert parse(serialisiere(text)) == text
  ```

**Stand:** Weder `mutmut` noch `hypothesis` stehen in den dev-Abhängigkeiten; Mutationsprüfung bisher nur von Hand
(`docs/KICKOFF.md` Phase 2, Charakterisierungstests).

Stand bei Init (2026-10-11, lokal, Python 3.13): `31 passed`.
