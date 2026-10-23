# TODO – all-inkl-kas-sdk

Einzige Quelle des Inkrementplans (KICKOFF verweist nur hierher). Pro Inkrement: Aufgaben und — falls über die
Standard-DoD hinaus nötig — zusätzliche Kriterien. Ein Inkrement gilt erst als erledigt, wenn die Standard-DoD
**und** seine eigenen Kriterien erfüllt sind.

Parkplatz für noch unspezifizierte Ideen: `BACKLOG.md`.
Bekannte Bugs ohne aktiven Fix: `KNOWN_ISSUES.md`.

Priorisierung beim Init (2026-10-11): erst Secret-Lecks (Schaden am Schutzgut KAS-Passwort), dann
Request-Korrektheit, dann Datenverlustrisiko im DNS-Skript, dann Prozess-/Lieferkette, zuletzt Doku-Abgleich und
Konsistenz. Alle Code-Inkremente arbeiten offline (gemocktes `requests.post`, Fixtures) — **keine** Aufrufe gegen die
echte KAS-API durch Agenten.

---

## Standard-Definition of Done (gilt für jedes Inkrement — nicht abhaken, sie bleibt stehen)

- Code-Änderungen abgeschlossen, kein TODO-/FIXME-Kommentar offen
- Quality Gates grün (`CONVENTIONS_COMMON.md` §5; Befehle in `CONVENTIONS.md`)
- Integration-Tests grün, falls relevant
- Security-Checkliste aus `CONVENTIONS.md` durchgegangen (falls der Stack eine liefert)
- Trigger-Matrix in `KICKOFF.md` Phase 3a geprüft → alle relevanten Docs aktualisiert
  (`architecture/OVERVIEW.md`, `features/`, `architecture/`, `security/`, `GLOSSARY.md`, `KNOWN_ISSUES.md`, `LESSONS_LEARNED.md`)
- `STATE.md`: Tabellenzeile + „Nächster Schritt"-Abschnitt aktualisiert
- `CHANGELOG.md`: neuer Abschnitt mit Datum + Inkrement-Titel + Sections
  (Added / Changed / Fixed / Removed / Security / Confidence / Ungeprüft / Lessons Learned)
- KICKOFF Phase 3b vollständig (Struktur-Check, TODO-Verschiebung, Advocatus-Diaboli-Gate)
- Commit erstellt (`<type>(<scope>): <desc>`); Commit-Hash in `STATE.md` eingetragen

Projektzusatz bis I5: Gate 1–3 sind noch nicht eingerichtet (`CONVENTIONS.md` §8) — verbindlich ist Gate 4; das
Fehlen von Gate 1–3 steht im Confidence-Block.

---

## Aktuell (Hohe Priorität)

### I2: Secrets aus Dry-Run-Log, Export und Debug-Ausgaben fernhalten

Behebt `KNOWN_ISSUES.md` K1–K3 (`security/THREAT_MODEL.md` Bedrohungen 1 und 2). Geschätzt 5 Dateien.

**Aufgaben:**

- [ ] Test zuerst: Dry-Run mit Sentinel-Werten für `kas_auth_data` und `mail_password`, Logger `kas_sdk.client` auf
      `DEBUG` (`caplog`) → kein Sentinel im Log; Test muss vor dem Fix an der `assert`-Zeile rot sein
- [ ] Eine öffentliche Maskierungsfunktion in `kas_sdk/client.py` (Schlüssel mit `password`, `passwort`, `passwd`,
      `auth_data`, `secret`, `token`, `_key`, `_crt`, `_csr`, `private`; rekursiv für verschachtelte Werte)
- [ ] `KasClient.request`: Dry-Run loggt nur maskierte Parameter, den SOAP-Body gar nicht mehr
- [ ] `scripts/export_account.py`: dieselbe Maskierung statt eigener `SENSITIVE_KEYWORDS`, auch für verschachtelte Werte;
      `--show-passwords` lässt private Schlüssel trotzdem maskiert
- [ ] `debug/ssl_inspect_host.py`, `debug/ssl_inspect_verbose.py`: Ausgabe über die Maskierung
- [ ] Docs: K1–K3 nach „Behobene Probleme", Restrisiken in `security/THREAT_MODEL.md`, `principles/LOGGING.md`
      Projektabschnitt, `operations/SECRETS_MANAGEMENT.md` Projektstand

**Zusätzliche DoD:**

- [ ] Sentinel-Tests für Dry-Run-Log, Export-Formatierung (`format_section` mit `ssl_certificate_sni_key`) und
      verschachtelte Werte grün; RED-Beweis im Iterations-Log zitiert

### I3: SOAP-Envelope korrekt escapen und Faults vor dem HTTP-Status auswerten

Behebt K4 und K7, Code-Teil von K9 (`security/THREAT_MODEL.md` Bedrohungen 3 und 6). Geschätzt 2–3 Dateien.

**Aufgaben:**

- [ ] Test zuerst: Passwort und Parameter mit `&`, `<`, `]]>` → gesendeter Body ist wohlgeformtes XML und der
      JSON-Payload kommt unverändert an (heute: `ParseError`)
- [ ] Envelope mit XML-Escaping erzeugen (`xml.sax.saxutils.escape` oder `ElementTree`)
- [ ] Bei HTTP-Fehlerstatus zuerst den Body auf `faultstring` prüfen; nur ohne Fault `KasConnectionError`
- [ ] Auth-Faults auf `KasAuthError` abbilden — die Codes für falschen Login/falsches Passwort stehen **nicht** in
      `readme_KAS_API_SOURCE_OF_TRUTH.md` (der Generator blendet die Auth-Parameter aus; dort nur z. B.
      `kas_login_syntax_incorrect`, `kas_login_not_found`); Codes vorher in der offiziellen Hoster-Doku belegen,
      sonst als Annahme kennzeichnen
- [ ] Docs: `architecture/ERROR_HANDLING.md` (Hierarchie, Konvertierungstabelle), `security/AUTHENTICATION.md`

**Zusätzliche DoD:**

- [ ] Annahme „Faults kommen mit HTTP 500" ist entweder belegt (Hoster-Doku, von einem Menschen aufgezeichnete
      Antwort) oder der Code behandelt beide Fälle (Fault mit 200 und mit 500) und der Confidence-Block nennt die
      offene Annahme

---

## Mittlere Priorität

### I4: Wildcard-Skript verifiziert Name und Typ

Behebt K5 (`security/THREAT_MODEL.md` Bedrohung 4). Geschätzt 2 Dateien.

**Aufgaben:**

- [ ] Planungslogik aus `main()` in eine reine Funktion ziehen (Eingabe: Records, Subdomains, Domain; Ausgabe:
      anzulegende Records, löschbare Wildcards)
- [ ] Tests: `www` nur als A + Wildcards A/AAAA → AAAA-Record für `www` wird angelegt bzw. AAAA-Wildcard bleibt;
      Name nur als TXT/MX → A-Record wird angelegt; zweiter Lauf ohne Wildcard ändert nichts
- [ ] Verifikation nach dem Anlegen auf (Name, Typ) umstellen
- [ ] Docs: `architecture/CLI.md`, K5 nach „Behobene Probleme"

### I5: Quality Gates 1–3 einführen

Stellt die Standard-DoD her (`CONVENTIONS_COMMON.md` §5). Geschätzt 4 Dateien plus ein reiner Formatierungs-Commit.

**Aufgaben:**

- [ ] `ruff` und `mypy` in `[project.optional-dependencies].dev`, Konfiguration in `pyproject.toml`
- [ ] Formatierung des Bestands als eigener, reiner `style`-/`chore`-Commit (keine Verhaltensänderung, Tests grün)
- [ ] `mypy` zunächst für `kas_sdk/client.py` und `kas_sdk/exceptions.py`; Ausweitung auf `kas_sdk/services/`
      (implizites `Optional`) als Folge-Inkrement in `TODO.md` einplanen, wenn > ~400 LOC Diff
- [ ] Gates in CI (`.github/workflows/ci.yml`) und lokal in `tools/git-hooks/pre-commit.local`
- [ ] Docs: `CONVENTIONS.md` §8 (Übergangsregel entfernen), `architecture/DEPENDENCIES.md`

### I6: Lieferkette und Laufzeit-Baseline

Behebt `security/THREAT_MODEL.md` Bedrohung 5; Befunde in `security/DEPENDENCY_AUDIT.md`. Geschätzt 5 Dateien.

**Aufgaben:**

- [ ] ADR-001: Python-Mindestversion (3.9 EOL 2025-10-31, 3.10 EOL 2026-10-31) — Optionen, Folgen für Nutzer
- [ ] `requires-python` und CI-Matrix gemäß ADR; Untergrenze `requests>=2.32.4` in `pyproject.toml` und `requirements.txt`
- [ ] Rest aus I11: Fällt Python 3.9 weg, die Marker `python_version >= "3.10"` an den Floors für `urllib3` und
      `python-dotenv` entfernen (beide Dateien; `tests/test_dependency_floors.py` prüft den Gleichlauf) — bis dahin
      fehlen unter 3.9 die `urllib3`-Fixes aus 2.8.0
- [ ] `pip-audit` lokal ausführen, Ergebnis datiert in `security/DEPENDENCY_AUDIT.md`; Schritt in CI
- [ ] CI härten: `permissions: contents: read`, Actions per Commit-SHA mit Versionskommentar
- [ ] Docs: `architecture/DEPENDENCIES.md`, `operations/DEPLOYMENT.md` (Lockfile-Entscheidung)

### I7: API-Referenz, README und `.env.example` an den Code angleichen

Behebt K8, Doku-Teil von K9, K11. Geschätzt 5 Dateien (`docs/01_account.md`, `docs/03_email.md`,
`docs/04_system.md`, `README.md`, `.env.example`).

**Aufgaben:**

- [ ] Alle 14 Signatur-Abweichungen und die Wertfehler aus K8 korrigieren (Code ist maßgeblich; englisch bleiben)
- [ ] README: Exception-Tabelle (`KasAuthError`) passend zum Stand nach I3
- [ ] `.env.example`: `KAS_AUTH_TYPE`-Hinweis und Dry-Run-Beschreibung korrigieren
- [ ] Abgleich wiederholbar machen: AST-Prüfung der Doku-Beispiele (`LESSONS_LEARNED.md` L1) als Test oder Skript

**Zusätzliche DoD:**

- [ ] Doku-Beispiel-Abgleich meldet 0 Abweichungen (Befehl und Ausgabe im CHANGELOG)

---

## Niedrige Priorität

### I8: Source of Truth als Ratchet-Test und nicht existierende Aktionen bereinigen

Behebt K6. Geschätzt 4–5 Dateien.

**Aufgaben:**

- [ ] Test: Jede vom SDK aufgerufene Aktion existiert in `readme_KAS_API_SOURCE_OF_TRUTH.md`; Abdeckung (heute 75/76)
      als Floor in `STATE.md` → Kennzahlen und im Test
- [ ] `delete_symlink` / `delete_softwareinstall`: entfernen oder mit `DeprecationWarning` als „nicht in der API"
      markieren (öffentliche API — Entscheidung im CHANGELOG begründen)
- [ ] `move_subdomain` ergänzen (einzige SOT-Aktion ohne SDK-Methode) oder bewusst ausschließen
- [ ] Docs: `docs/04_system.md`, `docs/02_domains_dns.md`, `README.md`-Servicetabelle

### I9: Reihenfolge der Zugangsdatenquellen vereinheitlichen

Behebt K10. Geschätzt 4 Dateien.

**Aufgaben:**

- [ ] ADR-002: eine verbindliche Reihenfolge für Client und Skripte (Argument → Env → Keyring → interaktiv?)
- [ ] `kas_sdk/utils.get_kas_credentials` bzw. `KasClient` angleichen, Tests mit gepatchtem `keyring`
- [ ] Docs: `architecture/CONFIGURATION.md`, `README.md` (Credential Management)

### I10: mypy auf `strict = true` anheben

Neue Regel aus docs_template v28 (`CONVENTIONS.md` §2 „mypy streng"); das Projekt nutzt mypy noch gar nicht, I5 führt
es schrittweise ein. Setzt I5 voraus. Geschätzt 3–5 Dateien je Paketteil; bei > ~400 LOC Diff aufteilen.

**Aufgaben:**

- [ ] `pyproject.toml` → `[tool.mypy]` mit `strict = true`; Lockerungen nur per `[[tool.mypy.overrides]]` je
      benanntem Modul mit Begründungskommentar (z. B. `keyring`, `tabulate` ohne Typen)
- [ ] Baseline-Befunde beheben (fehlende Annotationen, implizites `Optional`, `Any`-Rückgaben);
      `# type: ignore` nur mit Fehlercode
- [ ] Gate 3 in CI und `tools/git-hooks/pre-commit.local` auf den strikten Lauf umstellen
- [ ] Docs: `CONVENTIONS.md` §2 (Stand-Hinweis entfernen) und §8

---

## Abgeschlossen

- I1 docs_template-Baseline eingeführt (Bestand übernommen) — [ABGESCHLOSSEN 2026-10-11]
