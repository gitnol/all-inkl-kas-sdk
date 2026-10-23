# Dependency-Audit – all-inkl-kas-sdk

Wann und wie Abhängigkeiten auf bekannte Schwachstellen geprüft werden.
Verbindet sich mit `architecture/DEPENDENCIES.md` (Was ist drin?) und
`security/THREAT_MODEL.md` (Bedrohung: Vulnerable Dependencies).

---

## Wann auditieren

| Auslöser | Pflicht? |
|---|---|
| Vor jedem Release | Ja |
| Bei neuer oder aktualisierter Dependency | Ja, die betroffene + Transitive |
| Nach Sicherheitsmeldung (CVE) für eine genutzte Dep | Ja, sofort |
| Kadenz-Sweep (Scanner **und** Web-Advisory-/Best-Practice-Recherche für Base+Stack) | Default 14 Tage, Marker `**Nächster Security-Sweep:**` im `STATE.md`-Kopf — `principles/SECURITY_CURRENCY.md` |

---

## Audit-Befehle pro Stack

| Stack | Befehl | Output | Bemerkung |
|---|---|---|---|
| Python | `pip-audit -r requirements.txt` | CVE-Liste mit Fix-Version | Alternativ: `safety check` |
| Python (pyproject) | `pip-audit` (im aktivierten venv) | Wie oben | Erfasst auch lock-File |
| .NET | `dotnet list package --vulnerable --include-transitive` | Pakete + Severity | NuGet-Audit-API |
| PowerShell | `Get-Module ... | Find-Module -AllowPrerelease` + manueller Abgleich gegen `MSRC` | begrenzt | PSGallery hat keine integrierte CVE-DB — manuell prüfen |
| Node | `npm audit` / `yarn audit` | CVE-Bericht | `npm audit fix` zum Patchen |
| Rust | `cargo deny check advisories` (bzw. `cargo audit`) | RustSec-Advisories mit Fix-Version | `cargo deny check` prüft zusätzlich Lizenzen/Quellen; liest `Cargo.lock` |

> Ergebnis als Artefakt sichern (`docs/audits/<JJJJ-MM-TT>-deps.txt` oder
> CI-Artefakt), damit Historie nachvollziehbar bleibt.

---

## Schweregrad-Politik

| Severity | Reaktion |
|---|---|
| Critical | Sofort patchen (innerhalb 24h) oder Mitigation (Feature deaktivieren); blockiert das Inkrement |
| High | Blockiert das aktuelle Inkrement, bis gepatcht oder mitigiert (`principles/SECURITY_CURRENCY.md`) |
| Medium | Im nächsten regulären Inkrement |
| Low | Backlog; bei nächstem Major-Upgrade mitziehen |

Mitigation kann auch sein: Nutzung der verwundbaren Funktion entfernen,
falls Update nicht möglich ist.

---

## Befunde (datiert)

Ablage für Scanner- und Recherche-Ergebnisse (`principles/SECURITY_CURRENCY.md` → Artefakt). Neueste oben.
Öffentliches oder potenziell öffentliches Repo: die Betroffenheit **konkreter interner Hosts** nur in `docs/local/`,
hier nur generisch (`CONVENTIONS_COMMON.md` 3.1).

### 2026-10-23 – Kadenz-Sweep (vorgezogen, fällig 2026-10-25)

Zeitraum seit dem Init-Sweep 2026-10-11; Advisories mit früherem Datum, die dort fehlten, sind nachgetragen.
Bestand (kein Lockfile; Untergrenzen aus `pyproject.toml`/`requirements.txt`, lokal installierte Versionen als
Stichprobe): `requests` 2.34.2, transitiv `urllib3` 2.8.0, `certifi` 2026.7.22, `idna` 3.20,
`charset-normalizer` 3.5.2; `keyring` 25.7.0 (mit `jaraco.*`, `pywin32-ctypes`, `more-itertools`), `tabulate`
0.10.0, `python-dotenv` 1.2.4; dev `pytest` 9.1.1, `beautifulsoup4` 4.15.0 (`soupsieve` 2.10); Laufzeit lokal
CPython 3.13.14 mit Expat 2.8.1 und OpenSSL 3.0.21; CI `actions/checkout@v4`, `actions/setup-python@v5`
(Python 3.9/3.11/3.13, jeweils neuester Patch).

| Prüfgegenstand | Ergebnis | Bewertung (betrifft uns / nicht, Begründung) | Quelle |
|---|---|---|---|
| `certifi` (transitiv über `requests`; lokal 2026.7.22) | GHSA-6q48-6c7w-9gw2 / PYSEC-2026-4320, **Critical**, 2026-10-20: emSign-Wurzelzertifikate entfernt, deren Zwischen-CAs wegen Schlüsselkompromittierung widerrufen sind (MITM möglich). Betroffen ≥ 2019.03.09; Fix laut GHSA 2026.10.18, laut OSV 2026.10.19 (beide auf PyPI) | **betrifft uns** — `requests` prüft die TLS-Verbindung zur KAS-API gegen das `certifi`-Bündel; der SOAP-Body trägt das KAS-Passwort. Ein mit kompromittiertem CA-Schlüssel ausgestelltes Zertifikat würde akzeptiert. Lokal installierte Version ist betroffen; das SDK setzt keine Untergrenze | `gh api repos/certifi/python-certifi/security-advisories`; OSV `querybatch` + `/v1/vulns/PYSEC-2026-4320`; PyPI JSON (Release-Liste) |
| `urllib3` (transitiv; lokal 2.8.0) | GHSA-8988-9cw3-xx77 / CVE-2026-97687 (High, HTTPS-Proxy-TLS-Konfiguration ignoriert), GHSA-vxq7-64xx-v4gw / CVE-2026-97689 (High, unbegrenzte Chunk-Size-Zeile im Speicher), GHSA-gh4c-6fx4-qh6g / CVE-2026-97688 (Medium, Endlosschleife bei Deflate-Streaming); alle 2026-09-15, Fix 2.8.0 — im Init-Sweep nicht erfasst | lokal **nicht** betroffen (2.8.0). Für Nutzer **ja**, da `requests` 2.34.2 `urllib3` < 2.8.0 zulässt: 97687 bei HTTPS-Proxy aus der Umgebung (`requests` übernimmt `HTTPS_PROXY`), 97689 als Speicher-DoS durch den Server (Hoster, per TLS — gering); 97688 nicht (SDK streamt nicht) | `gh api repos/urllib3/urllib3/security-advisories`; `gh release list -R urllib3/urllib3` |
| `python-dotenv` (lokal 1.2.4) | GHSA-mf9w-mj56-hr94 / CVE-2026-28684 (Medium, 2026-04-19): `set_key()`/`unset_key()` folgen Symlinks, Fix 1.2.2 — im Init-Sweep nicht erfasst | **nicht** betroffen — das SDK ruft nur `load_dotenv()` auf (`kas_sdk/client.py`), nie `set_key`/`unset_key`; Untergrenze `>=1.0.0` erlaubt die Versionen trotzdem | `gh api repos/theskumar/python-dotenv/security-advisories`; OSV `/v1/vulns/CVE-2026-28684`; Websuche (vulert.com, osv.dev) |
| `requests`, `keyring`, `tabulate`, `idna`, `charset-normalizer`, `jaraco.*`, `pywin32-ctypes`, `more-itertools`, `pytest`, `beautifulsoup4`, `soupsieve` (jeweils lokale Version) | OSV-Abfrage je Version: 0 Treffer; GitHub-Advisories seit 2026-09-01: keine; neueste Releases: `requests` 2.34.2 (2026-05), `keyring` 25.7.0, `python-dotenv` 1.2.4 (2026-10-01) | nicht betroffen (keine Meldung zur verbauten Version) | OSV `querybatch`; `gh api …/security-advisories` (psf/requests, jaraco/keyring, astanin/python-tabulate, pytest-dev/pytest, kjd/idna, jawah/charset_normalizer); PyPI JSON; Websuche versionsspezifisch ohne Treffer |
| CPython (lokal 3.13.14; CI neuester Patch) | 3.13.15 (2026-08-05), 3.13.16 (2026-09-30), 3.13.17 (2026-10-21) mit Security-Abschnitten: Expat-Bündel auf 2.8.2 bzw. 2.8.5, `http.client` begrenzt Trailer-/1xx-Zeilen (GHSA-w4q2-g22w-6fr4), `xml.etree`-XPath-Indexprädikate ohne quadratischen Aufwand, `tarfile`-Filter-Bypässe, `ssl.wrap_bio`/`asyncio.start_tls`-Hostnamenprüfung, `ensurepip` mit pip 26.2.2 | lokale Laufzeit **gering** betroffen: Expat parst die API-Antworten (`ET.fromstring`), `urllib3` baut auf `http.client` auf; Quelle ist der Hoster per TLS. `tarfile`, `asyncio`, `ssl.wrap_bio`, `findall`/`iterfind` nutzt das SDK nicht. CI nicht betroffen (zieht den neuesten Patch) | `gh api repos/python/cpython/contents/Misc/NEWS.d/3.13.1{5,6,7}.rst` (je Tag), Tag-Daten per `gh api …/git/tags` |
| libexpat (Upstream) | 2.9.0 (2026-10-05): CVE-2026-102633 (Integer-Overflow nur 32-Bit), CVE-2026-77214 (`len` in `XML_ParseBuffer`); CPython 3.13.17 bündelt noch 2.8.5; Upstream-Hinweis auf weiterhin ungefixte Sicherheitsprobleme (Issue #1160) | nicht abschließend bewertet: 64-Bit-Laufzeit, ob CPythons `pyexpat` `XML_ParseBuffer` nutzt, ist nicht geprüft; Antworten vom Hoster per TLS → Restrisiko gering, beobachten | `gh api repos/libexpat/libexpat/releases`; `expat/Changes` (Tag `R_2_9_0`); `Modules/expat/expat.h` (Tag `v3.13.17`) |
| GitHub Actions `actions/checkout`, `actions/setup-python` | keine Advisories | nicht betroffen; SHA-Pinning bleibt offen (I6) | `gh api repos/actions/{checkout,setup-python}/security-advisories` |
| PowerShell 7 / .NET | — | nicht anwendbar: das Projekt enthält weder PowerShell- noch .NET-Bestandteile (Git-Hooks sind `sh`) | `git ls-files` |
| Scanner `pip-audit` | **nicht gelaufen** — lokal nicht installiert, Installation im Sweep unterlassen; ersatzweise OSV-Abfrage je installierter Version | unbekannt für Pakete außerhalb der Stichprobe | — |

Offen aus diesem Sweep: `certifi`-Untergrenze `>=2026.10.19` und `urllib3`-Untergrenze `>=2.8.0` (Critical bzw.
High, `docs/TODO.md` I11 — laut Schweregrad-Politik vor dem nächsten Code-Inkrement); `python-dotenv>=1.2.2`
mitziehen (Low, I11); lokale Entwicklungsumgebung: `certifi` und CPython (3.13.17) aktualisieren (Maintainer,
außerhalb des Repos); `pip-audit` weiterhin offen (I6); libexpat 2.9.0 bzw. `XML_ParseBuffer`-Nutzung in CPython
beim nächsten Sweep nachprüfen.

**Umgesetzt 2026-10-23 (I11):** Untergrenzen `certifi>=2026.10.19` (alle Python-Versionen),
`urllib3>=2.8.0` und `python-dotenv>=1.2.2` (beide nur Python ≥ 3.10) in `pyproject.toml` und `requirements.txt`;
Test `tests/test_dependency_floors.py`. Frische venv (Python 3.13) installiert `certifi` 2026.10.19 und `urllib3`
2.8.0. **Rest:** Die Fix-Versionen von `urllib3` und `python-dotenv` verlangen Python ≥ 3.10 (PyPI
`requires_python`); unter Python 3.9 werden `urllib3` 2.6.3 und `python-dotenv` 1.2.1 aufgelöst (`uv pip compile`) — die drei
`urllib3`-Advisories bleiben dort offen, bis I6 (ADR-001) die Mindestversion anhebt. `certifi` wirkt auch unter 3.9.

### 2026-10-11 – Init-Sweep

| Datum | Quelle (Scanner / URL) | Paket / Version | Befund | betrifft uns? (Begründung) | Maßnahme / Restrisiko |
|---|---|---|---|---|---|
| 2026-10-11 | Web: ManageEngine-CVE-DB, GitLab-MR „requests to v2.32.4 [security]" | `requests>=2.0.0` (lokal 2.34.2) | CVE-2024-47081: `.netrc`-Credentials können bei präparierter URL an Dritte gehen, Fix 2.32.4 (Moderate) | ja, für Nutzer mit `requests` < 2.32.4 und `.netrc` — die Untergrenze erlaubt solche Versionen | Untergrenze `requests>=2.32.4` (`docs/TODO.md` I6); Restrisiko gering |
| 2026-10-11 | Web: Debian Security Tracker, Tenable | `requests>=2.0.0` | CVE-2023-32681: Proxy-Authorization-Header nach Redirect an Ziel, Fix 2.31.0 | ja, nur bei Proxy-Credentials in der Proxy-URL | durch Untergrenze 2.32.4 abgedeckt (I6) |
| 2026-10-11 | Web: Debian Security Tracker, Tenable | `requests>=2.0.0` | CVE-2024-35195: `verify=False` bleibt im Session-Pool aktiv, Fix 2.32.0 | nein — SDK nutzt keine `Session` und setzt nie `verify=False` | keine |
| 2026-10-11 | Web: Python Developer's Guide (Status), via herodevs.com | Python `>=3.9`, CI 3.9/3.11/3.13 | 3.9 EOL 2025-10-31, 3.10 EOL 2026-10-31 — keine Sicherheitsupdates mehr | ja — Mindestversion und CI-Matrix | Mindestversion anheben, ADR (I6); Restrisiko gering (Laufzeit wählt der Nutzer) |
| 2026-10-11 | Web: docs.python.org „XML Processing Modules" | stdlib `xml.etree` + Expat (lokal 2.8.1) | Stdlib-Parser nicht gegen bösartiges XML gehärtet; Expat ≥ 2.4.1 schützt vor „billion laughs" | gering — Antworten kommen per TLS vom Hoster | keine Sofortmaßnahme; `defusedxml` im Backlog |
| 2026-10-11 | Web: orca.security, pydevtools.com | `actions/checkout@v4`, `actions/setup-python@v5` | Tag-Pinning ist umschreibbar (Vorfall `tj-actions/changed-files`, 2025); fehlender `permissions:`-Block | ja (Härtung) — CI hat keine Secrets, Schaden begrenzt | SHA-Pinning + `permissions: contents: read` (I6) |
| 2026-10-11 | Scanner | alle | `pip-audit` **nicht gelaufen** (nicht installiert; Installation im Init bewusst unterlassen) | unbekannt | `pip-audit` lokal und in CI einführen (I6) |

---

## SBOM (optional)

Software Bill of Materials für regulierte Projekte:

- Python: `cyclonedx-py` / `pip-licenses`
- .NET: `dotnet CycloneDX`
- Node: `npm sbom --sbom-format cyclonedx` (npm ≥ 9.5) bzw. `@cyclonedx/cyclonedx-npm`
- Rust: `cargo cyclonedx` (cargo-cyclonedx)
- Format: CycloneDX oder SPDX

SBOM gehört in `docs/audits/` oder als Build-Artefakt — nicht in den
Quellbaum als rotierende Datei.

---

## Was nicht ausreicht

- **„Wir nutzen nur populäre Bibliotheken"** — populär ≠ sicher (siehe
  `event-stream`, `colors.js`, `xz-utils`).
- **GitHub Dependabot allein** — gut für externe Repos, nicht ausreichend
  für private/interne Deps oder Binaries.
- **Einmaliger Audit beim Projektstart** — Audits müssen wiederholt werden,
  weil neue CVEs ständig erscheinen.
- **Scanner-Lauf allein** — `pip-audit`/`dotnet --vulnerable`/`npm audit` finden
  bekannte CVEs der Deps, aber keine Härtungs-Best-Practices und keine Advisories
  ohne CVE-Eintrag. Web-Recherche nach `principles/SECURITY_CURRENCY.md` ergänzt
  den Scanner, ersetzt ihn nicht (und umgekehrt).

---

## Pflege

Trigger (siehe `KICKOFF.md` Phase 3a): neue Dependency hinzugefügt /
CVE-Meldung erhalten / Audit-Tool geändert → diese Datei + Audit-Artefakt
aktualisieren.
