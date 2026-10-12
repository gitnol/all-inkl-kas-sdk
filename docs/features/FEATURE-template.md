# Feature: [Feature-Name]

---

## Zweck

[Was macht dieses Feature? Wer nutzt es? Ein Satz reicht.]

---

## Technologie / Abhängigkeiten

- [Bibliothek/Framework — z.B. `imagehash` für pHash, `sqlite3` für Persistenz]
- [Externe Binary — z.B. `ffmpeg` (optional, PATH)]

---

## Datenstrukturen

[Welche Modelle / Dataclasses sind beteiligt? Welche Felder sind für dieses Feature relevant?]

```python
# Beispiel: relevante Felder aus dem zentralen Domänenmodell
[feld_a]: [Typ]  # [Bedeutung]
[feld_b]: [Typ]  # [Bedeutung]
```

---

## Konfigurierbare Parameter (CLI)

| CLI-Argument | Default | Validierungsregel | Beschreibung |
|-------------|---------|------------------|-------------|
| `--[arg]` | [Default] | [Min ≤ N ≤ Max] | [Beschreibung] |

<!-- VORLAGEN-HINWEIS: Nur Argumente eintragen, die dieses Feature direkt steuern.
Validierungsregeln aus build_config() ableiten.
Abschnitt löschen wenn Feature kein eigenes CLI-Argument hat.
-->

---

## Kritische Patterns

[Was muss beim Arbeiten an diesem Feature IMMER beachtet werden?]

- [Pattern 1 — z.B. "choose_best_file() immer verwenden, nie inline"]
- [Pattern 2 — z.B. "pHash-Strings nie manuell parsen außer in den dafür vorgesehenen Funktionen"]

---

## Bekannte Einschränkungen

| Einschränkung | Ursache | Status |
|---------------|---------|--------|
| [Einschränkung] | [Technische Ursache] | [Geplant in I# / Akzeptiert (V2-Scope) / Offen] |

---

## Bekannte Fallstricke

[Was ist in der Vergangenheit schiefgelaufen? Was darf NICHT gemacht werden?]

- [Fallstrick 1 — mit Verweis auf betroffene Datei/Zeile wenn möglich]

---

## Teststrategie

- Zugehörige Testdatei: `tests/test_[modul].py`
- Kritische Testfälle: [z.B. "Hamming-Distanz 0 für identische Hashes; Union-Find Transitivität"]
- Was nicht automatisiert getestet wird: [z.B. "echte Video-pHash mit ffmpeg — @pytest.mark.live"]
