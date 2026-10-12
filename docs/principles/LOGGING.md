# Logging Strategy

## Regel

Logs sind das einzige Fenster in den Systemzustand eines laufenden Prozesses.
Jeder Log-Eintrag muss ohne Kontextwissen verständlich und filterbar sein.

## Konkrete Vorgaben

- **Level DEBUG:** Detaillierter Datenfluss (z.B. "Datei X gelesen, Hash: Y")
- **Level INFO:** Fachliche Meilensteine (z.B. "Dokument X erfolgreich verarbeitet")
- **Level WARNING:** Erwartete, aber behandelte Probleme (z.B. "Service Timeout, Versuch 1/3")
- **Level ERROR:** Unerwartete Fehler – muss zwingend den Stacktrace enthalten (z. B. Python `exc_info=True`,
  .NET `LogError(ex, …)`)
- **Kontext:** Jeder Eintrag muss IDs, Dateinamen oder Bezeichner enthalten.
  "Verarbeitung fehlgeschlagen" ist verboten.
  "Verarbeitung für Datei 'X.pdf' fehlgeschlagen" ist korrekt.
- Konsolenausgaben über `print()` sind für interaktive CLI-Tools akzeptabel.
  Bei automatisiertem Betrieb (Scheduler, Service) muss das Logging-Framework verwendet werden.

## Verwandt

- [[FAIL_FAST]]
- [[UNTRUSTED_DOCUMENT_CONTENT]]

## Projektspezifisch

<!-- Hier beim Befüllen ersetzen. Maßgeblich für die Update-Klassifizierung ist
     der Vergleich gegen die alte Template-Version (ALTES_PROJECT_AKTUALISIEREN.md,
     Schritt 2c/3): LOGGING.md ist konstruktionsbedingt immer Kategorie C. -->


- **Bibliothek:** `kas_sdk/client.py` nutzt `logging.getLogger("kas_sdk.client")` und konfiguriert keine Handler —
  der Aufrufer entscheidet über Level und Ziel (Bibliotheks-Konvention). Inhalte: Keyring-Treffer (`INFO`),
  fehlendes Passwort / Dry-Run aktiv (`WARNING`), Keyring nicht installiert (`DEBUG`).
- **Skripte:** `scripts/*.py`, `debug/*.py`, `kas_sdk/utils.py` geben Fortschritt und Fehler per `print()` auf der
  Konsole aus (bewusst, interaktive Werkzeuge); kein Logging-Setup.
- **Debug-/Dry-Run-Modus:** `KasClient(dry_run=True)` bzw. `KAS_DRY_RUN=1`; zusätzliche Details nur, wenn der
  Aufrufer den Logger auf `DEBUG` setzt.
- **Nie loggen:** `kas_auth_data`, Request-Bodys, Parameter-Dicts (enthalten `*_password`, `ssl_certificate_sni_key`),
  Session-Tokens, private Schlüssel. **Heute verletzt** im Dry-Run (`kas_sdk/client.py:163-164`,
  `docs/KNOWN_ISSUES.md` K1, Fix `docs/TODO.md` I2). Login-Namen (`w…`) und Domainnamen sind erlaubt.
- **Ziel:** nur Konsole bzw. was der Aufrufer konfiguriert; das Projekt schreibt keine Log-Dateien (`*.log` ist
  gitignored für umgeleitete Ausgaben).
