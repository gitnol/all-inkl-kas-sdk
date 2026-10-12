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
