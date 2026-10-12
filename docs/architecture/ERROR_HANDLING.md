# Fehlerbehandlung – all-inkl-kas-sdk

Wo und wie Fehler erkannt, propagiert, behandelt und gemeldet werden.
Konsolidiert Regeln, die sonst in `CONVENTIONS.md`, `principles/FAIL_FAST.md`,
`principles/CONTRACTS.md` und `principles/LOGGING.md` verstreut sind.

---

## Exception-/Fehler-Hierarchie

Ist-Zustand (`kas_sdk/exceptions.py`, öffentlich über `kas_sdk.__init__`):

```
Exception
└── KasApiError            # Basis aller SDK-Fehler: SOAP-Fault, unlesbares XML
    ├── KasAuthError       # Login fehlt beim Konstruktor
    └── KasConnectionError # HTTP-/Netzwerkfehler (inkl. HTTP-Status ≥ 400)
ValueError                 # Services: ungültige Enum-/Bereichswerte, fehlende Pflicht-Kombinationen
```

- **Niemals nackte `Exception` / `Error` werfen.** Neue Fehlerursachen bekommen eine Unterklasse von `KasApiError`.
- `ValueError` aus den Services ist bewusst **keine** `KasApiError`: Es ist ein Aufruferfehler, der vor dem
  Request erkannt wird (Fail Fast), kein API-Fehler.
- Bekannte Lücke: Ungültige Zugangsdaten kommen als SOAP-Fault zurück und werden zu `KasApiError`, nicht zu
  `KasAuthError` (`docs/KNOWN_ISSUES.md` K9).

---

## Boundary vs. interne Fehler

| Ebene | Verhalten |
|---|---|
| **Boundary Bibliothek** (`KasClient.request`) | Alle Fehler außer `KasApiError` werden in `KasConnectionError` gewickelt (`raise … from e`); kein Traceback-Verlust. |
| **Boundary Skripte** (`main()` in `scripts/*.py`) | Fangen `Exception` pro Host/Domain, geben `ERROR: …` auf der Konsole aus und machen mit dem nächsten Element weiter; Exit-Code ist dann meist 0 (Ausnahmen in der Konvertierungstabelle). |
| **Anwendung** (Services) | Werfen `ValueError` bei ungültigen Parametern; geben API-Fehler unverändert weiter. Rückgabe `False` bei `ReturnString != TRUE`. |
| **Infrastruktur** (`_parse_soap_map`) | `ET.ParseError` → `KasApiError`; `faultstring` im XML → `KasApiError("KAS API Fault: …")`. |

---

## Was geloggt und was gerethrowt wird

- **Boundary** fängt → loggt → konvertiert in Antwortformat. Das Level richtet sich nach der Art des Fehlers
  (Level-Semantik: `docs/principles/LOGGING.md`):
  - **unerwartet** (Programmierfehler, Sicherheitsnetz, Infrastruktur ausgefallen) → `ERROR` mit vollem Stacktrace
    (`exc_info=True`);
  - **erwartet, fachlich** (ungültige Eingabe, Ressource nicht gefunden, Rechte fehlen) → `WARNING` ohne
    Stacktrace — sonst erzeugt jeder Robustheitstest ein `ERROR`.
- Die Bibliothek selbst loggt **keine** Fehler, sie wirft sie (der Aufrufer entscheidet). Sie loggt nur
  Zustandsinformationen (Keyring-Treffer, Dry-Run-Modus) über den Logger `kas_sdk.client`.
- **Mittelschichten** lassen Fehler durch — **kein doppeltes Logging** desselben Fehlers.
- **Niemals `except: pass` / leeres `catch {}` ohne Logging.** Im Bestand verletzt: `scripts/ssl_update_hsts_manual.py`
  (`except Exception: pass` bei der Schlüsselsuche) — Kandidat für das nächste Skript-Inkrement.
- **Fehlermeldungen enthalten nie Secrets.** `KasConnectionError` übernimmt den Text der `requests`-Exception
  (enthält URL, nicht den Body); Request-Bodys dürfen nie in Fehlertexte oder Logs (`docs/security/THREAT_MODEL.md`).

---

## Retry-Strategien

- Das SDK retryt **nicht**. Begründung: Schreibende KAS-Aktionen (`add_*`) sind nicht idempotent; ein Retry nach
  Timeout könnte Objekte doppelt anlegen.
- Einziger Zeitmechanismus ist der Flood-Schutz (`flood_protection_delay`) vor jedem Request.
- Wer retryen will, tut das im Aufrufer und nur für lesende Aktionen (`get_*`).
- Authentifizierungsfehler **niemals retryen**.

---

## Feindliche Eingaben — kein Absturz an Systemgrenzen

Alles, was von außen kommt, ist feindlich: Dateien und Fremdformate, CLI-Parameter,
Konfiguration, API- und DB-Antworten, Aufrufe durch Agenten/Tools. Ergebnis ist **immer
ein behandelbarer Fehler** (projektspezifische Exception → Boundary-Konvertierung), nie
ein Prozessabsturz, ein hängender Prozess oder verlorene Nutzerdaten.

> Abgrenzung zu [[FAIL_FAST]]: Fail Fast bricht die **Operation** früh und laut ab.
> Diese Regel sorgt dafür, dass dabei nicht der **Prozess** oder die Arbeit des Nutzers
> mitgerissen wird. Abgrenzung zu [[UNTRUSTED_DOCUMENT_CONTENT]]: dort geht es um fremden
> Inhalt im LLM-Prompt (Injection/Fälschung), hier um die Robustheit des Prozesses.

Projektbezug:

- **API-Antworten:** Das XML der KAS-API wird mit `xml.etree.ElementTree` geparst; Parse-Fehler werden zu
  `KasApiError`. Rekursion im Parser (`_parse_element`) ist nicht begrenzt — tief verschachtelte Antworten sind
  theoretisch möglich, aber von der KAS-API nicht zu erwarten.
- **Aufruferdaten im Request:** Werte landen über `json.dumps` im SOAP-Envelope, der per f-String gebaut wird;
  `&` und `<` erzeugen ungültiges XML (`docs/KNOWN_ISSUES.md` K4). Ergebnis ist heute ein Serverfehler statt
  einer klaren Exception.
- **Schreiben atomar:** `scripts/export_account.py` schreibt den Export direkt (nicht atomar); bei Abbruch bleibt
  eine unvollständige Datei — akzeptiert, da jede Datei einen Zeitstempel trägt und nichts überschrieben wird.
- **Jeder Crash-Fix bringt einen kleinen synthetischen Regressionstest mit**, der vor dem
  Fix nachweislich abgestürzt ist (behaviorales Rot, `KICKOFF.md` Phase 2).

---

## Konvertierungstabelle (Pflicht ausfüllen)

| Interne Exception | CLI Exit-Code | HTTP-Status | Log-Level | Bemerkung |
|---|---|---|---|---|
| `ValueError` (Service-Validierung) | `0` (Skript fängt, gibt `ERROR:` aus) | — | Konsole | Aufruferfehler, Request wird nicht gesendet |
| `KasAuthError` | `0` bzw. Traceback, wenn außerhalb eines `try` | — | — | Login fehlt beim Konstruktor |
| `KasConnectionError` | `0` (pro Host gefangen) | — | Konsole | Netzwerk/HTTP-Fehler, auch HTTP 500 |
| `KasApiError` (Basis, Fault/XML) | `0` (pro Host gefangen) | — | Konsole | Fault-Text aus der API in der Meldung |
| Fehlende Zugangsdaten in `ssl_enforce_hsts.py` | `1` | — | Konsole | einziger Skript-Pfad mit Exit-Code ≠ 0 |
| `generate_source_of_truth.py`: HTML fehlt | `1` | — | Konsole | `return 1` aus `main()` |

> Die Spalte HTTP-Status entfällt (kein HTTP-Server). Dass Skripte trotz Fehlern mit `0` enden, ist ein bekanntes
> Defizit für automatisierte Läufe (Cron/CI) — als Backlog-Punkt erfasst.

---

## Anti-Pattern

- **`raise Exception("...")`** statt einer spezifischen Klasse.
- **Catch-and-rethrow ohne Mehrwert** (`except Foo: raise Foo`) — entfernen. (`except KasApiError: raise` in
  `KasClient.request` ist gewollt: Es verhindert, dass ein Fault in `KasConnectionError` gewickelt wird.)
- **Stilles Wegfangen** in der Mitte des Aufruf-Stacks (`except: pass`) —
  Fail-Fast wird ausgehebelt.

---

## Pflege

Trigger (siehe `KICKOFF.md` Phase 3a): neue Exception-Klasse / neue Boundary
/ neue Retry-Stelle → diese Datei + Konvertierungstabelle aktualisieren.
