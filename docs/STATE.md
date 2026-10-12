# Aktueller Projektstatus – all-inkl-kas-sdk

Zuletzt aktualisiert: 2026-10-11
**Initialisiert mit:** docs_template v27@5ce0f84
**Stack / Overlays:** python-cli / keine
**Letztes abgeschlossenes Inkrement:** I1 docs_template-Baseline eingeführt (Bestand übernommen) (2026-10-11)
**Nächster Schritt:** I2 Secrets aus Dry-Run-Log, Export und Debug-Ausgaben fernhalten
**Nächste Reflexion:** bei Abschluss von I3 (siehe `KICKOFF.md` Phase 1c → `docs/REFLECTION.md` — `docs/`-Drift prüfen + Template-Backport prüfen; danach Marker um 3 erhöhen)
**Nächster Security-Sweep:** 2026-10-25 (Intervall 14 Tage; siehe `KICKOFF.md` Phase 1 Punkt 4a → `docs/principles/SECURITY_CURRENCY.md` — fällig, sobald heute ≥ diesem Datum; nach dem Sweep Marker = Sweep-Datum + Intervall)

---

## Nächster Schritt

I2 aus `docs/TODO.md`: Das Dry-Run-Log enthält heute das KAS-Passwort und alle Passwort-Parameter (K1, lokal
belegt); Export und Debug-Skripte geben private TLS-Schlüssel aus (K2, K3). Zuerst den Sentinel-Test schreiben, der
an der `assert`-Zeile rot ist, dann eine gemeinsame Maskierung einführen. Kein Aufruf der echten KAS-API.

---

## Abgeschlossene Inkremente

| # | Titel | Datum | Commit |
|---|-------|-------|--------|
| I1 | docs_template-Baseline eingeführt (Bestand übernommen) | 2026-10-11 | a134265 |

---

## Offene Punkte

| # | Beschreibung | Priorität |
|---|-------------|-----------|
| I2 | Secrets aus Dry-Run-Log, Export und Debug-Ausgaben fernhalten | Hoch |
| I3 | SOAP-Envelope korrekt escapen und Faults vor dem HTTP-Status auswerten | Hoch |
| I4 | Wildcard-Skript verifiziert Name und Typ | Mittel |
| I5 | Quality Gates 1–3 einführen | Mittel |
| I6 | Lieferkette und Laufzeit-Baseline | Mittel |
| I7 | API-Referenz, README und `.env.example` an den Code angleichen | Mittel |
| I8 | Source of Truth als Ratchet-Test und nicht existierende Aktionen bereinigen | Niedrig |
| I9 | Reihenfolge der Zugangsdatenquellen vereinheitlichen | Niedrig |

---

## Kennzahlen (gemessen)

Nur gemessene Werte; Schätzungen gehören nicht in diese Tabelle. Floor = Wert, unter den der
automatische Check nicht fallen darf (nur anheben, Senken nur mit Begründung/ADR).

Orakel: `readme_KAS_API_SOURCE_OF_TRUTH.md` (aus der Hoster-Doku generiert) für Aktionsnamen und Parameter.

| Kennzahl | Wert | Floor | Gemessen am | Messbefehl / Check |
|---|---|---|---|---|
| Offline-Tests bestanden | 31 / 31 | alle grün | 2026-10-11 | `pytest -p no:cacheprovider tests/` (Python 3.13) |
| KAS-Aktionen der SOT, die das SDK aufruft | 75 / 76 (ohne die veraltete `get_accountressources`; fehlt: `move_subdomain`) | noch kein automatischer Check (kommt mit I8) | 2026-10-11 | Aktionsnamen aus den `self.client.request(…)`-Aufrufen in `kas_sdk/services/` gegen die Aktionsüberschriften der SOT abgleichen (`grep` + `comm`) |
| SDK-Aktionen ohne SOT-Eintrag | 2 (`delete_symlink`, `delete_softwareinstall`) | Ziel 0, Check mit I8 | 2026-10-11 | wie oben, Gegenrichtung |
| Signatur-Abweichungen in den Codebeispielen der API-Referenz | 14 | Ziel 0, Check mit I7 | 2026-10-11 | AST-Abgleich `client.<svc>.<methode>(…)` gegen Signaturen (`LESSONS_LEARNED.md` L1) |

---

## Risiken & Blocker

Eintragen, **sobald** ein Punkt erkannt ist — nicht erst, wenn er eskaliert.
Wenn keine Risiken bekannt: Zeile „(noch keine Einträge)" einsetzen, Tabelle nicht leer lassen (`CONVENTIONS_COMMON.md` §3).

| Risiko / Blocker | Auswirkung | Mitigation / Nächster Schritt | Owner | Status |
|---|---|---|---|---|
| KAS-Passwort im Dry-Run-Log (K1) | Generalschlüssel des Accounts kann über Logs abfließen | I2; bis dahin kein `DEBUG`-Logging im Dry-Run | Maintainer | offen |
| Keine Testumgebung beim Hoster; Agenten dürfen die echte API nicht aufrufen | Annahmen über API-Verhalten (K7, Auth-Typen) bleiben ungeprüft | Orakel = Hoster-Doku + von Menschen aufgezeichnete Antworten; Annahmen im Confidence-Block kennzeichnen | Maintainer | offen |
| Quality Gates 1–3 fehlen | Lint-/Typfehler bleiben bis I5 unbemerkt | I5; bis dahin Vermerk im Confidence-Block | Maintainer | offen |
| Python 3.10 EOL am 2026-10-31, 3.9 bereits EOL | Nutzer auf alten Laufzeiten ohne Sicherheitsupdates | I6 (ADR-001) | Maintainer | offen |
| Advocatus-Diaboli-Hook (`.claude/settings.json`) beim Init nicht angelegt | Gate vor dem Commit nur von Hand | Entscheidung des Maintainers (öffentliches Repo), `BACKLOG.md`; bis dahin KICKOFF Phase 3b Punkt 5 manuell | Maintainer | offen |
