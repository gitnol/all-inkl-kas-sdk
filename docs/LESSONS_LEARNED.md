# Lessons Learned – all-inkl-kas-sdk

Strukturierter Index für gelernte Patterns. Jeder Eintrag benennt Scope und
Backport-Ziel, damit die Reflexions-Phase (REFLECTION.md Schritt 3) offene
generische Patterns als Backport-Vorschlag melden kann; eingespielt wird erst nach Freigabe
des Prompters (REFLECTION.md Schritt 3, Freigabe-Disziplin).

Neue Einträge entstehen aus dem „Lessons Learned"-Abschnitt der `CHANGELOG.md` —
dort kurze Beschreibung, hier der strukturierte Steckbrief.

---

## L1: Bestandsdoku-Codebeispiele maschinell gegen Signaturen prüfen
- Inkrement: I1
- Scope: generisch-stack
- Backport-Ziel: `stacks/python-cli/testing/UNIT_TESTS.md` (bzw. NEUES 3d als Prüfschritt für übernommene Doku)
- Status: offen

Handgeschriebene API-Doku driftet still vom Code weg. Ein kleiner AST-Abgleich (Aufrufe `client.<svc>.<methode>(…)`
in den ```` ```python ````-Blöcken gegen die echten Funktionssignaturen) fand beim Init 14 Abweichungen in vier Dateien —
billiger und belastbarer als Lesen, und als Test wiederverwendbar (Ratchet: Anzahl Abweichungen darf nur sinken).

---

## L2: Sicherheits-Floor gegen die Laufzeit-Untergrenze der Fix-Version prüfen
- Inkrement: I11
- Scope: generisch-base
- Backport-Ziel: `base/principles/SECURITY_CURRENCY.md` (Abschnitt „Durchführung", neuer Punkt zur Maßnahme)
- Status: offen

Ein Advisory nennt die Fix-Version, aber nicht, welche Laufzeit sie verlangt. `urllib3` 2.8.0 und `python-dotenv`
1.2.2 setzen Python ≥ 3.10 voraus, das Projekt erlaubt 3.9: ein schlichtes `urllib3>=2.8.0` hätte die Installation
unter 3.9 (CI-Matrix) unauflösbar gemacht. Vorher die Metadaten der Fix-Version lesen (PyPI JSON
`requires_python`, npm `engines`, NuGet-Zielframeworks); passt sie nicht, den Floor per Umgebungsmarker auf die
passenden Laufzeiten beschränken und die Lücke auf der alten Laufzeit als Restrisiko führen — oder die
Mindestversion anheben (ADR).

---

## Pflege

- Neuer „Lessons Learned"-Block im `CHANGELOG.md` → Eintrag `## L<N>:` hier anlegen.
- Mehrere Patterns aus einem Inkrement → mehrere `## L<N>:`-Einträge.
- Scope-Werte:
  - `projekt-spezifisch` — nur für dieses Projekt relevant, kein Backport nötig.
  - `generisch-stack` — gehört in `docs_template/stacks/<stack>/CONVENTIONS.md` o.ä.
  - `generisch-base` — gehört in `docs_template/base/` (Prinzip, Basis-Convention, MANIFEST).
- Status `offen` → wird bei der nächsten Reflexion (REFLECTION.md Schritt 3) als Backport-Vorschlag gemeldet;
  bleibt `offen` bis zur Freigabe.
- Status `backported vN@<commit>` → Backport-Commit ins Template-Repo durchgeführt (Template-Stand
  Version + Commit, z. B. `v26@0a4c8f1`); der Tag `vN` folgt erst nach dem Pre-Tag-Gate (REFLECTION.md Schritt 3b).
- Status `projekt-intern` → Endzustand für `Scope: projekt-spezifisch` (kein Backport vorgesehen; die Lesson gilt
  im Projekt weiter). Wird in der Reflexion nicht als Backport-Kandidat gemeldet.
- Niemals Patterns löschen, auch wenn überholt — `Status: verworfen (<grund>)` setzen.
- Diese Datei steht in der Trigger-Matrix in `KICKOFF.md` Phase 3a.
