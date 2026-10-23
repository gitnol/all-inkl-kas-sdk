# Threat Model & Mitigationen – all-inkl-kas-sdk

---

Leitfragen zum Finden von Bedrohungen: `security/THREAT_MODEL_GUIDE.md` (vom Template gepflegt).
Öffentliches oder potenziell öffentliches Repo: keine internen Hosts, Versionen oder Betroffenheiten konkreter Systeme —
die gehören nach `docs/local/` (`CONVENTIONS_COMMON.md` 3.1).

**Schutzgut:** Das KAS-Passwort ist der Generalschlüssel eines Webhosting-Accounts (Domains, DNS, Mailpostfächer,
Datenbanken, FTP, Unter-Accounts). Wer es kennt, kann Domains umziehen, DNS umbiegen und Postfächer übernehmen.
Weitere Secrets im Datenfluss: Passwörter von Postfächern/FTP/Datenbanken/Unter-Accounts (als API-Parameter oder in
API-Antworten), private TLS-Schlüssel (`ssl_certificate_sni_key`), SSO-Session-Tokens (`add_session`).

Stand der Analyse: 2026-10-11 (Init, Code-Stand `412a2ff`). Status-Werte: **belegt** = per Lauf/Code nachgewiesen,
**Annahme** = plausibel, ohne echten API-Aufruf nicht prüfbar.

## 1. Secrets im Log beim Dry-Run (belegt)

**Gefahr:** `KasClient.request` loggt im Dry-Run alle Request-Parameter auf `INFO` (`kas_sdk/client.py:163`) und den
kompletten SOAP-Body auf `DEBUG` (`kas_sdk/client.py:164`). Der Body enthält `kas_auth_data` (KAS-Passwort), die
Parameter enthalten je nach Aktion `mail_password`, `ftp_password`, `database_password`, `account_kas_password`,
`ssl_certificate_sni_key`. Lokaler Lauf am 2026-10-11 mit Sentinel-Werten: beide Passwörter erscheinen im Log.
Dry-Run ist genau der Modus, den Nutzer zum gefahrlosen Ausprobieren und Debuggen mit erhöhtem Log-Level nutzen —
Logs landen dann in Terminal-Historie, CI-Logs oder Log-Dateien (`*.log` ist zwar gitignored, aber nicht geschützt).

**Mitigation:**
- Parameter vor dem Logging maskieren (Schlüssel mit `password`/`passwort`/`auth_data`/`key`/`secret`/`token`),
  den SOAP-Body nie loggen — geplant in `docs/TODO.md` I2.
- Regressionstest mit Sentinel-Passwort, der das Log auf Abwesenheit prüft.
- Bis dahin: Dry-Run nicht mit `DEBUG`-Logging in geteilten Umgebungen (CI) betreiben (`docs/KNOWN_ISSUES.md` K1).

**Restrisiko:** Hoch – bis I2 umgesetzt ist; danach Gering.

---

## 2. Private TLS-Schlüssel und Passwörter in Exporten und Diagnoseausgaben (Annahme/belegt)

**Gefahr:** `scripts/export_account.py` maskiert nur Felder, deren Name `password`, `passwort`, `passwd`,
`auth_data`, `secret` oder `token` enthält (`scripts/export_account.py:41`). Ein Feld `ssl_certificate_sni_key`
(privater Schlüssel) wird nicht maskiert; verschachtelte Werte werden zudem ungekürzt ausgegeben
(`scripts/export_account.py:121`). Ob `get_domains()`/`get_subdomains()` den Schlüssel in der Massenabfrage liefern,
ist eine **Annahme** — `scripts/ssl_enforce_hsts.py` liest ihn aus genau diesen Antworten. Die Debug-Skripte geben
alle `ssl*`-Felder inklusive Schlüssel ungefiltert aus (`debug/ssl_inspect_host.py:30`,
`debug/ssl_inspect_verbose.py:72`; **belegt** durch Code). Mit `--show-passwords` enthält der Export bewusst
Klartext-Passwörter; die Datei wird mit Standard-Dateirechten geschrieben.

**Mitigation:**
- Maskierungsliste um `key`, `private`, `crt`/`csr` erweitern bzw. Positivliste für Ausgabefelder; verschachtelte
  Werte ebenfalls maskieren — I2.
- Debug-Skripte filtern Schlüsselmaterial vor der Ausgabe — I2.
- Exportverzeichnis `scripts/output/` ist gitignored (`output/`); Hinweis in `docs/security/DATA_HANDLING.md`.

**Restrisiko:** Mittel – Exporte liegen lokal beim Betreiber; Leck entsteht erst durch Weitergabe der Datei.

---

## 3. XML-Injection und kaputte Requests durch unescapte Werte im SOAP-Envelope (belegt)

**Gefahr:** Der JSON-Payload wird per f-String ohne XML-Escaping in `<KasRequest>` eingesetzt
(`kas_sdk/client.py:149,156`). Enthält ein Passwort oder ein Parameter `&` oder `<`, ist der Envelope kein
wohlgeformtes XML (lokaler Lauf 2026-10-11: `ParseError: not well-formed`). Stammen Parameter aus fremder Quelle
(z. B. DNS-Record-Daten aus einem Webformular des Aufrufers), kann ein Angreifer mit `</KasRequest>` den Envelope
verändern. Folgen: fehlschlagende Requests mit irreführender Fehlermeldung; im schlechtesten Fall abweichend
interpretierte Requests.

**Mitigation:**
- Payload mit `xml.sax.saxutils.escape` (bzw. Envelope per `ElementTree`) erzeugen — I3.
- Test mit `&`, `<`, `]]>` im Passwort und in Parametern.

**Restrisiko:** Mittel – Angriffsfläche nur, wenn Aufrufer fremde Daten durchreichen; der Funktionsfehler trifft
aber jeden Nutzer mit Sonderzeichen im Passwort.

---

## 4. Ungewollte DNS-Änderungen durch das Wildcard-Skript (belegt)

**Gefahr:** `scripts/dns_remove_wildcards.py --execute` löscht Wildcard-A/AAAA-Records, nachdem es explizite
Records angelegt und „verifiziert" hat. Die Verifikation vergleicht nur Record-**Namen** (`existing_dns_names`,
`scripts/dns_remove_wildcards.py:93,130`), nicht Name **und Typ**: Existiert `www` nur als A-Record, wird die
AAAA-Wildcard trotzdem gelöscht (IPv6 für `www` fällt weg); existiert ein Name nur als TXT/MX-Record, wird kein
A-Record angelegt und die Auflösung bricht nach dem Löschen. Integritäts-/Verfügbarkeitsschaden an Produktiv-DNS.

**Mitigation:**
- Default ist Dry-Run (`--execute` nötig) — vorhanden.
- Verifikation auf (Name, Typ) umstellen, Logik als testbare Funktion herauslösen — I4.
- Bis dahin: Ausgabe im Dry-Run manuell prüfen, `--domain` für Einzelläufe nutzen (`docs/KNOWN_ISSUES.md` K5).

**Restrisiko:** Mittel – nur bei `--execute`; Schaden ist reversibel, aber sichtbar (Ausfall von Subdomains).

---

## 5. Abhängigkeiten und Laufzeit ohne Untergrenzen für Sicherheitsfixes (belegt)

**Gefahr:** `pyproject.toml`/`requirements.txt` erlauben `requests>=2.0.0` — damit auch Versionen mit
CVE-2023-32681 (Proxy-Authorization-Leck, behoben 2.31.0) und CVE-2024-47081 (`.netrc`-Credential-Leck, behoben
2.32.4). Kein Lockfile, kein `pip-audit`-Lauf in CI. `requires-python >=3.9`: Python 3.9 ist seit 2025-10-31 ohne
Sicherheitsupdates, 3.10 endet am 2026-10-31. CI nutzt Actions per Tag (`@v4`, `@v5`) ohne `permissions:`-Block
(`.github/workflows/ci.yml`) — Tag-Umschreibung wie beim `tj-actions`-Vorfall 2025 würde fremden Code in CI ausführen;
CI hat aber keine Secrets.
Transitive Pakete ohne Untergrenze (Sweep 2026-10-23): `certifi` < 2026.10.19 vertraut emSign-Wurzeln mit
kompromittierten Zwischen-CA-Schlüsseln (GHSA-6q48-6c7w-9gw2, Critical) — ein damit ausgestelltes Zertifikat für den
API-Host würde akzeptiert, ein Angreifer im Netzpfad läse den SOAP-Body samt KAS-Passwort; `urllib3` < 2.8.0
ignoriert unter Umständen die TLS-Konfiguration eines HTTPS-Proxys (CVE-2026-97687).

**Mitigation:**
- Untergrenze `requests>=2.32.4`, `pip-audit` in CI, Python-Mindestversion anheben (ADR), Actions per SHA pinnen,
  `permissions: contents: read` — I6.
- Untergrenzen `certifi>=2026.10.19` und — nur Python ≥ 3.10 — `urllib3>=2.8.0`, `python-dotenv>=1.2.2`,
  geprüft von `tests/test_dependency_floors.py` — umgesetzt in I11 (2026-10-23).
- Details und Quellen: `docs/security/DEPENDENCY_AUDIT.md`.

**Restrisiko:** Gering – lokal installiert ist `requests` 2.34.2 (nicht betroffen); das Risiko trifft Nutzer mit
alten Umgebungen. Neuinstallationen ziehen seit I11 `certifi` ≥ 2026.10.19; eine bestehende Umgebung bleibt auf dem
alten Bündel, bis sie neu installiert oder `pip install -U certifi` ausgeführt wird. Unter Python 3.9 gibt es keine
`urllib3`-Version mit den Fixes von 2.8.0 (verlangt Python ≥ 3.10) — erledigt sich mit der Mindestversion aus I6.

---

## 6. Fehlerdiagnose verdeckt Auth-Probleme (Annahme)

**Gefahr:** `response.raise_for_status()` läuft vor dem Fault-Parsing (`kas_sdk/client.py:182`). PHP-SOAP-Server
liefern Faults üblicherweise mit HTTP 500; dann würde jeder API-Fehler (auch ein Passwortfehler) als
`KasConnectionError` ohne Fault-Text gemeldet. Folge: Nutzer suchen Netzwerkprobleme statt falscher Zugangsdaten,
Skripte wiederholen fehlgeschlagene Anmeldungen — Risiko von Kontosperren durch den Hoster. **Annahme**, weil
gegen die echte API nicht geprüft werden darf.

**Mitigation:**
- Bei HTTP-Fehlerstatus zuerst den Body auf `faultstring` prüfen; Auth-Faults auf `KasAuthError` abbilden — I3
  (mit aufgezeichnetem bzw. dokumentiertem Fault-Fixture als Orakel).

**Restrisiko:** Mittel – bis zur Prüfung unklar.

---

## Security-Currency-Abgleich (Init, 2026-10-11)

Bestand (Quelle: `pyproject.toml`, `requirements.txt`, `.github/workflows/ci.yml`; lokal installierte Versionen
nur als Stichprobe, kein Lockfile): `requests>=2.0.0` (lokal 2.34.2), `keyring>=25.0.0` (25.7.0),
`tabulate>=0.9.0` (0.10.0), `python-dotenv>=1.0.0` (1.2.4), dev: `pytest>=7.0` (9.1.1),
`beautifulsoup4>=4.12.0` (4.15.0); Laufzeit Python 3.9–3.13, Expat 2.8.1 (lokal); `actions/checkout@v4`,
`actions/setup-python@v5`.

| Thema | Quelle (abgerufen 2026-10-11) | Bewertung für dieses Projekt |
|---|---|---|
| `requests` CVE-2024-47081 (`.netrc`-Leck, Fix 2.32.4) | ManageEngine-CVE-Datenbank, GitLab-MR „requests to v2.32.4 [security]" | betrifft Nutzer mit `requests` < 2.32.4 und `.netrc`; Untergrenze anheben (I6) |
| `requests` CVE-2023-32681 (Proxy-Authorization, Fix 2.31.0), CVE-2024-35195 (`verify=False` im Session-Pool, Fix 2.32.0) | Debian Security Tracker, Tenable | 32681 betrifft Nutzer mit Proxy-Credentials in der URL; 35195 betrifft uns nicht (kein `Session`, kein `verify=False`) |
| Python-Lebenszyklus: 3.9 EOL 2025-10-31, 3.10 EOL 2026-10-31 | Python Developer's Guide (via herodevs.com, endoflife-Zusammenfassungen) | betrifft uns: Mindestversion und CI-Matrix anpassen (I6, ADR) |
| Stdlib-XML-Parser für nicht vertrauenswürdige Daten; Expat ≥ 2.4.1 schützt vor „billion laughs" | docs.python.org „XML Processing Modules", discuss.python.org (defusedxml-Status) | Antworten kommen per TLS vom Hoster (halb vertrauenswürdig); kein Handlungsbedarf außer Expat-Version aktuell halten; `defusedxml` als Backlog-Option |
| GitHub-Actions-Härtung (SHA-Pinning, `permissions: contents: read`, Vorfall `tj-actions` 2025) | orca.security, pydevtools.com-Handbuch | betrifft uns: Workflow per Tag gepinnt, keine `permissions` (I6) |
| KAS-API-Authentifizierung (`plain`/`sha1`/Session) | offizielle KAS-API-Doku (kasapi.kasserver.com/dokumentation/phpdoc) | Doku nennt nur `kas_auth_type` ohne Werteliste; Status von `sha1` und Session-Auth **ungeklärt** → Confidence-Block, Backlog |
| KAS-Aktionen `delete_symlink`, `delete_softwareinstall` | offizielle KAS-API-Doku | existieren dort nicht → `docs/KNOWN_ISSUES.md` K6 |

Nicht durchgeführt: `pip-audit` (nicht installiert; Installation aus dem Netz im Init-Lauf bewusst unterlassen) →
Aufgabe in I6. Nächster Sweep laut `docs/STATE.md`-Kopf.

---

## Hinweise

- Dieses Dokument wird bei jeder neuen Funktion geprüft, die externe Eingaben verarbeitet
  oder auf sensible Ressourcen zugreift — anhand der Leitfragen in `security/THREAT_MODEL_GUIDE.md`.
- Neue Bedrohungen als ADR dokumentieren wenn sie eine Architekturentscheidung auslösen.
- Prompt-Injection (Leitfrage „fremder Inhalt im LLM-Prompt") ist nicht anwendbar: Das Projekt ruft kein LLM auf.
  Im analysierten Code und README wurden keine an Agenten gerichteten Anweisungstexte gefunden (Init 2026-10-11).
