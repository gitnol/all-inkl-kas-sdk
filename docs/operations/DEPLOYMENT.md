# Deployment – all-inkl-kas-sdk

Default-Template; derzeit liefert kein Stack eine eigene Variante. Beschreibt die
Mindest-Inhalte, die jedes Projekt dokumentiert haben muss; stack-spezifische Setup- und
Betriebsdetails stehen in `operations/SETUP.md` und `operations/RUNBOOK.md`.

Verbindet sich mit `operations/SETUP.md` (Erst-Setup), `operations/RUNBOOK.md`
(Betrieb) und `operations/SECRETS_MANAGEMENT.md`.

Das Projekt wird **nicht deployt**: Es ist eine Bibliothek plus Skripte, die Nutzer aus dem Git-Repository
installieren (`pip install -e .`). Es gibt keinen Server, keine Paketveröffentlichung (kein PyPI-Upload) und keine
Release-Tags. Abschnitte zu Staging, Health-Endpoints und Datenbank-Migrationen entfallen.

---

## Umgebungen

| Umgebung | Zweck | Datenquelle | Wer darf deployen |
|---|---|---|---|
| dev | Lokale Entwicklung und Offline-Tests | XML-Fixtures in `tests/`, Dry-Run | Entwickler:in |
| CI | `pytest` auf Python 3.9 / 3.11 / 3.13 bei Push und Pull Request auf `main` | Fixtures, kein Netz, keine Secrets | GitHub Actions |
| Nutzer-Installation | Einsatz gegen einen echten KAS-Account | Live-API des Hosters | jede:r Nutzer:in für den eigenen Account |

Unterschiede zwischen Umgebungen werden ausschließlich über Konfiguration
gesteuert (siehe `architecture/CONFIGURATION.md`), nicht über Code-Branches
oder Feature-Flags ohne Default.

---

## Build

```
pip install -e ".[dev]"      # Entwicklung (wie CI)
python -m build              # optional: Wheel/Sdist bauen — nicht Teil des aktuellen Ablaufs
```

Build-Artefakt: keines im aktuellen Ablauf; bei Bedarf `dist/kas_sdk-<version>-py3-none-any.whl` (gitignored über
`dist/`).

**Reproduzierbar:**
- [ ] Dependency-Lock-File committet — fehlt (nur Untergrenzen in `pyproject.toml`/`requirements.txt`); offen in
  `docs/TODO.md` I6
- [x] Build wird in sauberer Umgebung getestet (CI: frische Runner, `pip install -e ".[dev]"`)

---

## Release

| Schritt | Verantwortung | Verifikation |
|---|---|---|
| Dependency-Audit + Security-Currency-Abgleich (Pflicht vor jedem Release) | Maintainer | datierter Eintrag in `security/DEPENDENCY_AUDIT.md` → Befunde (`principles/SECURITY_CURRENCY.md`) |
| Version in `pyproject.toml` anheben (`version = "1.0.0"`), Eintrag in `docs/CHANGELOG.md` | Maintainer | Diff im Release-Commit |
| CI grün auf `main` | GitHub Actions | Workflow-Lauf |
| Optional: Git-Tag `vX.Y.Z` | Maintainer | Tag zeigt auf den grünen Commit |

---

## Rollback

**Bedingung:** Ein Commit auf `main` bricht Nutzer-Skripte oder sendet fehlerhafte Requests, und ein Fix ist
nicht kurzfristig möglich.

| Schritt | Befehl / Aktion |
|---|---|
| 1. Letzte stabile Version identifizieren | `git log --oneline` (CI-Status je Commit) |
| 2. Rollback ausführen | `git revert <commit>` auf `main` (kein Force-Push); Nutzer: `git checkout <commit>` + `pip install -e .` |
| 3. Verifikation | `pytest tests/` grün; betroffenes Skript im Dry-Run |

> Änderungen am KAS-Account selbst (DNS, Postfächer) rollt kein Git-Revert zurück — dafür
> `docs/operations/INCIDENT_RESPONSE.md` → Projektspezifische Erstmaßnahmen.

---

## Post-Deploy-Verifikation

- [ ] CI-Lauf grün auf allen Python-Versionen der Matrix
- [ ] `pytest tests/` lokal grün nach `pip install -e .`
- [ ] Ein lesender Aufruf (`client.statistic.get_space()`) gegen den eigenen Account funktioniert — nur durch
      Nutzer:innen mit eigenem Account, nie in CI

---

## Pflege

Trigger: neue Umgebung / geänderter Build-Befehl / geänderter Rollback-Pfad →
hier eintragen. Vor jedem nicht-trivialen Architektur-Change prüfen, ob diese
Datei betroffen ist.
