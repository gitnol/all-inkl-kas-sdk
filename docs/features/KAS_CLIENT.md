# Feature: KAS-API-Client (KasClient + Services)

---

## Zweck

Python-Entwickler:innen und die Wartungsskripte des Projekts steuern einen All-Inkl-Webhosting-Account per Code:
`KasClient` übernimmt Anmeldung, SOAP-Transport und Antwort-Parsing, die 21 Services bilden die KAS-Pakete
(Account, Domain, DNS, Mail, SSL, …) als Python-Methoden ab.

---

## Technologie / Abhängigkeiten

- `requests` — HTTPS-POST an `https://kasapi.kasserver.com/soap/KasApi.php` (Timeout 30 s)
- `xml.etree.ElementTree` (stdlib) — Parsing der SOAP-Antwort; `json` (stdlib) — Request-Payload
- `keyring` (optional zur Laufzeit) — Passwort aus dem System-Keyring; `python-dotenv` (optional) — `.env` beim Import
- Keine externen Binaries

---

## Datenstrukturen

Es gibt keine Datenklassen; Ein- und Ausgaben sind Python-Grundtypen.

```python
# Request (gebaut in KasClient.request, als JSON im Element <KasRequest>)
kas_login: str               # KAS-Login, z. B. "w0123456" (fiktiv)
kas_auth_type: str           # "plain" (Default) oder "sha1"
kas_auth_data: str           # Passwort bzw. Hash — Secret, nie loggen
kas_action: str              # Aktionsname laut Source of Truth, z. B. "get_dns_settings"
KasRequestParams: dict[str, str]  # alle Werte per str(), None-Werte entfernt

# Antwort (nach _parse_soap_map, "Response"-Wrapper entfernt)
ReturnString: str            # "TRUE" bei Erfolg
ReturnInfo: list | dict | str  # Nutzdaten: Listen bei Schlüsseln "0".."N", sonst dict bzw. Text/ID
```

---

## Konfigurierbare Parameter (Konstruktor)

| Argument | Default | Validierungsregel | Beschreibung |
|-------------|---------|------------------|-------------|
| `kas_login` | `KAS_LOGIN` | Pflicht (sonst `KasAuthError`) | KAS-Login |
| `kas_auth_data` | `KAS_PASS`, dann Keyring | fehlt → nur Warnung | Passwort |
| `kas_auth_type` | `"plain"` | keine | Auth-Typ |
| `api_url` | offizieller Endpunkt | keine | SOAP-Endpunkt |
| `flood_protection_delay` | `2.0` | keine | Sekunden zwischen zwei Requests |
| `dry_run` | `KAS_DRY_RUN` | Wahrheitswert-String | keine Requests, Mock-Antwort |

Die Skripte haben eigene CLI-Argumente: `docs/architecture/CLI.md`.

---

## Kritische Patterns

- Services rufen nur `self.client.request(action, params)` auf und übergeben optionale Parameter nur, wenn sie
  gesetzt sind; Enum-Werte vorher gegen Klassenkonstanten prüfen (`ValueError`).
- Parameternamen exakt wie in `readme_KAS_API_SOURCE_OF_TRUTH.md`; Abweichungen in der Doku sind Fehler der Doku
  (`docs/KNOWN_ISSUES.md` K8), nicht der API.
- DNS: `zone_host` beim Anlegen mit Punkt am Ende, beim Ändern nicht senden (`DnsService`).
- Rückgabewert-Konvention: Lese-Aktionen liefern `ReturnInfo` (oder `[]`/`{}`), Schreib-Aktionen `bool`
  (`ReturnString == "TRUE"`), Anlege-Aktionen teils die neue ID.
- Neue Services in `KasClient._SERVICE_MAP` **und** `kas_sdk/services/__init__.py` eintragen.

---

## Bekannte Einschränkungen

| Einschränkung | Ursache | Status |
|---------------|---------|--------|
| Dry-Run loggt Parameter und Passwort (K1) | Debug-Komfort ohne Maskierung | Geplant in I2 |
| `&`/`<` in Werten ergeben ungültige Requests (K4) | Envelope per f-String ohne Escaping | Geplant in I3 |
| API-Fehler mit HTTP 500 verlieren den Fault-Text (K7, Annahme) | `raise_for_status()` vor dem Parsing | Geplant in I3 |
| `delete_symlink`, `delete_softwareinstall` ohne Gegenstück in der API (K6) | Aktionen nicht in der Hoster-Doku | Geplant in I8 |
| `move_subdomain` fehlt im SDK | nicht implementiert | Geplant in I8 |
| Kein Retry/Backoff | bewusst (nicht idempotente Schreibaktionen) | Akzeptiert |
| Rückgaben untypisiert (`dict`/`list`/`str`) | generischer Parser | Akzeptiert |

---

## Bekannte Fallstricke

- SDK-Dry-Run unterdrückt auch Lesezugriffe — Skripte, die echt lesen und nur Schreiben simulieren wollen, dürfen
  den SDK-Dry-Run nicht nutzen (`scripts/ssl_enforce_hsts.py` entfernt dafür `KAS_DRY_RUN` aus der Umgebung).
- `import kas_sdk.client` lädt eine `.env` aus dem aktuellen Arbeitsverzeichnis — überraschende Werte in Tests oder
  fremden Verzeichnissen.
- Mehrere Requests auf einem Client warten je bis zu 2 s (Flood-Schutz); in Tests `flood_protection_delay=0`.
- Liste-vs.-Dict-Heuristik: Der Parser macht aus lückenlosen Schlüsseln `0..N` eine Liste (auch bei genau einem
  Datensatz). Liefert die API einen Datensatz ohne Index-Wrapper, käme ein `dict` — ob das vorkommt, ist ungeprüft;
  `example_usage.py` prüft den Typ deshalb defensiv.

---

## Teststrategie

- Zugehörige Testdateien: `tests/test_payloads.py` (Request-Aufbau), `tests/test_integration.py` (Parsing, Fehler,
  Dry-Run, Account-Validierung)
- Kritische Testfälle: Werte als Strings; Trailing Dot bei `add_dns_settings`; Fault → `KasApiError`; Namespace-Präfixe;
  Netzwerkfehler → `KasConnectionError`; Dry-Run ohne `requests.post`
- Was nicht automatisiert getestet wird: echtes API-Verhalten (keine Testumgebung) — Orakel ist die Source of Truth;
  Live-Prüfung nur manuell mit eigenem Unter-Account (`docs/testing/INTEGRATION_TESTS.md`)
