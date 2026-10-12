# Integration Tests – all-inkl-kas-sdk

Begriffsklärung: `tests/test_integration.py` heißt „Integration", testet aber **offline** die Kette
SOAP-XML → Parser → Service-Rückgabe mit realistischen Fixtures und gemocktem Transport. Das ist hier der
„Pipeline-Test" der Vorlage. Echte Integrationstests gegen die KAS-API gibt es nicht und darf ein Agent nicht
ausführen (kein Testsystem beim Hoster, jeder Aufruf wirkt auf einen produktiven Account).

---

## 1. Trennung von Offline-Kettentests und Live-Tests

- **Standard (= Gate 4):** Kein Netz, keine Zugangsdaten — `requests.post` gepatcht, XML-Fixtures, Dry-Run.
- **Live-Tests:** gibt es nicht. Falls eingeführt, nur **lesende** Aktionen (`get_*`), nur mit Marker `live`, nur
  manuell durch Menschen mit eigenem (Unter-)Account:

```bash
# Standard (offline, = Gate 4)
pytest tests/

# Live-Tests (noch nicht vorhanden; erfordert KAS_LOGIN/KAS_PASS eines Test-Unter-Accounts)
pytest tests/ -m live
```

---

## 2. Kettentest: Antwort-XML bis Service-Rückgabe

Muster aus `tests/test_integration.py` (`TestDnsServiceIntegration`):

```python
from unittest.mock import patch
from kas_sdk import KasClient

@patch('kas_sdk.client.requests.post')
def test_get_dns_settings_returns_list(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.content = XML_DNS_RECORDS      # realistische KAS-Antwort mit 2 Records

    records = KasClient('user', 'pass').dns.get_dns_settings('example.com.')

    assert isinstance(records, list)
    assert records[0]['record_name'] == 'www'
```

Neue Fixtures sollen aus **dokumentierten oder von Menschen aufgezeichneten** Antworten stammen (Secrets vorher
entfernen, Werte fiktiv machen) und im Kommentar ihre Herkunft nennen.

---

## 3. Dry-Run-Test

```python
from unittest.mock import patch
from kas_sdk import KasClient

def test_dry_run_does_not_call_requests():
    with patch('kas_sdk.client.requests.post') as mock_post:
        KasClient('user', 'pass', dry_run=True).dns.get_dns_settings('example.com.')
        mock_post.assert_not_called()
```

Für die Skripte (eigener Dry-Run, echte Lesezugriffe) fehlen Tests; Kandidat zuerst
`scripts/dns_remove_wildcards.py` (`docs/TODO.md` I4): Verifikationslogik als Funktion herauslösen und mit
Record-Listen testen, ohne `KasClient`.

---

## 4. Wiederholbarkeit (Idempotenz der Skripte)

Die Wartungsskripte prüfen den Ist-Zustand vor jeder Änderung (HSTS bereits gesetzt → überspringen; keine
Wildcard → überspringen). Ein Test dafür braucht zwei aufeinanderfolgende gemockte Antworten (vorher/nachher):

```python
from unittest.mock import MagicMock

def test_second_run_changes_nothing():
    client = MagicMock()
    client.dns.get_dns_settings.return_value = [
        {"record_name": "www", "record_type": "A", "record_data": "192.0.2.1", "record_id": "1"},
    ]
    # Erwartung: ohne Wildcard kein add_dns_settings / delete_dns_settings
    ...
    client.dns.delete_dns_settings.assert_not_called()
```

(Skizze für I4 — die Skriptlogik ist heute in `main()` eingebettet und so nicht direkt aufrufbar.)

---

## 5. Was nicht automatisiert getestet wird

| Bereich | Grund | Alternative |
|---------|-------|-------------|
| Echtes Verhalten der KAS-API (Fault-Codes, HTTP-Status bei Faults, Antwortfelder) | keine Testumgebung, Aufrufe wirken produktiv | Hoster-Doku + `readme_KAS_API_SOURCE_OF_TRUTH.md` als Orakel; manuelle Stichprobe mit Unter-Account |
| Interaktive Eingaben (`kas_sdk/utils.py`: `input`, `getpass`) | Tastatureingabe | Zugangsdaten über Umgebung in Tests |
| System-Keyring | Backend plattformabhängig | `keyring` patchen |
| Flood-Schutz-Wartezeit | verlangsamt Tests | `flood_protection_delay=0` |
| DNS-Auflösung nach Skriptläufen | externes System | manueller Check (`docs/operations/MONITORING.md`) |
