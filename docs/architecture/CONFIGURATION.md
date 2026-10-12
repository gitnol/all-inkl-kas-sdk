# Konfiguration – all-inkl-kas-sdk

Wo Werte herkommen, in welcher Reihenfolge sie überschreiben, und wie sie
validiert werden. Verbindet sich mit den Prinzipien [[EXPLICIT_OVER_IMPLICIT]]
und [[FAIL_FAST]].

Das SDK hat **kein** Konfigurationsobjekt und keine Konfigurationsdatei außer einer optionalen `.env`. Die Werte
werden im Konstruktor von `KasClient` aufgelöst und als Attribute gehalten; Skripte lösen Zugangsdaten zusätzlich
über `kas_sdk/utils.py` auf — **mit abweichender Reihenfolge** (siehe unten, `docs/KNOWN_ISSUES.md` K10).

---

## Quellen-Hierarchie (Präzedenz, höchste zuerst)

**`KasClient` (Bibliothek, `kas_sdk/client.py`):**

1. **Konstruktor-Argumente** (`KasClient(kas_login=…, kas_auth_data=…, dry_run=…)`)
2. **Umgebungsvariablen** (`KAS_LOGIN`, `KAS_PASS`, `KAS_DRY_RUN`)
3. **`.env` im Arbeitsverzeichnis** — wird beim *Import* von `kas_sdk.client` per `python-dotenv` in die
   Umgebung geladen (überschreibt bereits gesetzte Umgebungsvariablen nicht)
4. **System-Keyring** — nur für das Passwort: Dienst `kas_api`, Benutzer = aufgelöster Login
5. **Code-Defaults** (`kas_auth_type="plain"`, `flood_protection_delay=2.0`, `api_url=SOAP_URL`)

**Skripte über `kas_sdk.utils.get_kas_credentials()`:**

1. `KAS_LOGIN` aus der Umgebung, sonst Default-Login aus dem Keyring (`kas_api` / `default_kas_login`)
2. Passwort zuerst aus dem **Keyring**, erst danach aus `KAS_PASS`
3. Interaktive Eingabe (`input`/`getpass`) mit Angebot, beides im Keyring zu speichern

Niedrigere Quelle wird durch höhere **überschrieben**, nicht ergänzt.

> Die beiden Reihenfolgen widersprechen sich beim Passwort (Client: Env vor Keyring; Skripte: Keyring vor Env).
> Bis zur Angleichung gilt: Wer in Skripten ein anderes Passwort per `KAS_PASS` erzwingen will, muss den
> Keyring-Eintrag entfernen. Bewusst nicht still korrigiert — Entscheidung als ADR-Kandidat in `docs/TODO.md`.

---

## Validierung beim Laden

- Fehlt der Login aus allen Quellen → `KasAuthError` im Konstruktor (Fail Fast).
- Fehlt das Passwort → nur eine Warnung im Log; der erste API-Aufruf scheitert dann an der KAS-API.
- `KAS_DRY_RUN` wird als Wahrheitswert gelesen (`true`/`1`/`yes`, Groß-/Kleinschreibung egal).
- `kas_auth_type`, `api_url` und `flood_protection_delay` werden **nicht** validiert.
- Parameter der einzelnen API-Aktionen validieren die Services beim Aufruf (`ValueError` bei ungültigen
  Enum-/Bereichswerten), nicht beim Laden.

---

## Secrets gehören NICHT in normale Konfigurationsdateien

- Secrets immer über eine sichere Quelle: Env-Variablen, Secrets-Manager,
  Credential Store, DPAPI, KeyVault. In diesem Projekt: System-Keyring (bevorzugt) oder `KAS_PASS`.
- Details: `docs/operations/SECRETS_MANAGEMENT.md`.
- Versionierte Konfigurationsdateien enthalten **nie** Secrets. Einzige Datei-Quelle für Secrets ist die lokale,
  ignorierte `.env` für dev/test (`docs/operations/SECRETS_MANAGEMENT.md`, Präzedenz Punkt 4); sie steht in
  `.gitignore` (siehe `docs/BOOTSTRAP.md`). Versioniert ist nur `.env.example` mit Platzhalterwerten.

---

## Konfigurationsobjekt — Verwendung

- Es gibt kein separates Konfigurationsobjekt; die aufgelöste Konfiguration lebt in der `KasClient`-Instanz und
  wird den Services als Konstruktor-Argument (`BaseService(client)`) übergeben.
- Services lesen **keine** Umgebungsvariablen; nur `KasClient.__init__` und die Skripte tun das.
- Skripte bauen den Client **einmal** in `main()` (Composition Root) und reichen ihn weiter.

---

## Konfigurations-Tabelle (Pflicht ausfüllen)

| Schlüssel | Typ | Default | Quelle(n) | Beschreibung |
|---|---|---|---|---|
| `kas_login` / `KAS_LOGIN` | `str` | kein (Pflicht) | Argument / ENV / `.env` / Keyring (`default_kas_login`, nur Skripte) | KAS-Login des Accounts, z. B. `w0123456` (fiktiv) |
| `kas_auth_data` / `KAS_PASS` | `str` (Secret) | kein | Argument / ENV / `.env` / Keyring (`kas_api`, Login) | KAS-Passwort; geht bei jedem Request im Body mit |
| `kas_auth_type` | `str` | `plain` | Argument; `KAS_AUTH_TYPE` nur in `scripts/ssl_enforce_hsts.py` und `debug/*.py` | Authentifizierungstyp der KAS-API (`plain`, `sha1`) |
| `dry_run` / `KAS_DRY_RUN` | `bool` | `False` | Argument / ENV / `.env`; Skripte zusätzlich Keyring (`config_dry_run`) bzw. Rückfrage | Keine Requests senden, Mock-Antwort zurückgeben (gilt auch für lesende Aufrufe) |
| `flood_protection_delay` | `float` (s) | `2.0` | Argument | Mindestabstand zwischen zwei Requests |
| `api_url` | `str` | `https://kasapi.kasserver.com/soap/KasApi.php` | Argument | SOAP-Endpunkt |
| HTTP-Timeout | `int` (s) | `30` | fest im Code (`client.py`) | Timeout je Request, nicht konfigurierbar |
| `--show-passwords` | Flag | aus | CLI (`scripts/export_account.py`) | Passwortmaskierung im Export abschalten |
| `--execute` / `--domain` | Flag / `str` | aus / alle | CLI (`scripts/dns_remove_wildcards.py`) | Änderungen wirklich ausführen / auf eine Domain begrenzen |
| `--html` / `--output` | Pfad | `API Funktionen.html` / `readme_KAS_API_SOURCE_OF_TRUTH.md` im Repo-Root | CLI (`scripts/generate_source_of_truth.py`) | Eingabe-HTML und Ausgabedatei des SOT-Generators |

---

## Anti-Pattern

- **Werte direkt aus `os.environ` / `Environment.GetEnvironmentVariable` /
  `$env:VAR` mitten in der Geschäftslogik lesen.** Versteckte Abhängigkeit. Im Bestand: `scripts/ssl_enforce_hsts.py`
  löscht `KAS_DRY_RUN` aus der Umgebung, damit der Client lesende Aufrufe wirklich ausführt.
- **Konfiguration zur Laufzeit mutieren** (z.B. `config.timeout = 30` in
  einem Service). Immutabilität bricht. Test-Setup ist die Ausnahme — dort
  über DI/Override-Mechanismus, nicht durch Mutation.
- **Magic Defaults im Code** (`timeout=30` in jeder Funktion neu) statt
  zentralem Wert im Konfigurationsobjekt.

---

## Pflege

Trigger (siehe `KICKOFF.md` Phase 3a): neue Konfig-Quelle / neuer Schlüssel /
geänderte Präzedenz → diese Datei eintragen, Validierung implementieren,
Tabelle aktualisieren.
