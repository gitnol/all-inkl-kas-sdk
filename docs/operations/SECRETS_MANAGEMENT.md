# Secrets-Management – all-inkl-kas-sdk

Wo Secrets leben dürfen, wie sie rotiert werden, und wie sie nicht in Logs
oder Repositories landen. Konsolidiert Hinweise aus den `CONVENTIONS.md`-Checklisten,
`security/AUTHENTICATION.md` (falls der Stack sie liefert) und `security/DATA_HANDLING.md`.

Verbindet sich mit `architecture/CONFIGURATION.md` (Konfiguration vs. Secret-Quellen)
und `security/THREAT_MODEL.md` (Bedrohung: Secret-Exposition).

---

## Erlaubte Speicherorte pro Secret-Typ

| Secret-Typ | Erlaubter Speicherort | NICHT erlaubt |
|---|---|---|
| API-Token / OAuth2 client_secret | `.env` (gitignored), Secrets-Manager, Vault | Quellcode, Logs, README, ADR |
| DB-Passwort | Env-Variable, Secrets-Manager | Connection-String im Code/Doku |
| Service-Account-Password | Windows Credential Store / DPAPI / Vault | Klartext-Datei, Task-Scheduler-Parameter |
| Signier-/Verschlüsselungs-Key | KeyVault, HSM, DPAPI | Repo, S3 ohne SSE, lokale Datei ohne ACL |
| SSH-Key (privat) | `~/.ssh/` mit 600/Service-Account-Profil | Repo, Shared-Drive |
| Webhook-Secret | Env-Variable, Secrets-Manager | Quellcode |

**Projektbezug — Secrets, die dieses SDK berührt:**

| Secret | Erlaubter Speicherort | NICHT erlaubt |
|---|---|---|
| KAS-Passwort (`kas_auth_data`) | System-Keyring (Dienst `kas_api`, Benutzer = Login), `KAS_PASS` in CI/Container, lokale `.env` nur dev | Quellcode, Skript-Konstanten, CLI-Argumente, Logs (auch Dry-Run), Exporte |
| Passwörter für Postfächer, FTP, DB, Samba, DynDNS, Verzeichnisschutz, Unter-Accounts (API-Parameter `*_password`) | nur transient als Funktionsargument; dauerhaft im Passwortmanager des Betreibers | Logs, Exporte ohne Maskierung, Doku-Beispiele mit echten Werten |
| Privater TLS-Schlüssel (`ssl_certificate_sni_key`) | Schlüsseldatei mit restriktiven Rechten außerhalb des Repos (`*.key`/`*.pem` sind gitignored) | Konsolenausgabe (`debug/*.py`, K3), Export (K2), Logs |
| SSO-Session-Token (`add_session`) | nur im Speicher, kurze Lebensdauer (`session_lifetime`) | Logs, URLs in geteilten Kanälen |

---

## Quellen-Präzedenz für Secrets (nicht für Konfiguration)

Anders als bei normalen Konfigurationswerten (siehe
`architecture/CONFIGURATION.md`) gilt für Secrets eine **engere** Hierarchie:

1. **Secrets-Manager** (Vault, AWS Secrets Manager, Azure KeyVault)
2. **Credential Store des Betriebssystems** (Windows Credential Store, DPAPI, Keychain)
3. **Umgebungsvariable** (CI/CD, Container)
4. **`.env`-Datei lokal** (nur dev/test, **niemals** in git)

CLI-Argumente und **versionierte** Konfigurationsdateien sind als Secret-Quelle **ausgeschlossen** — sie sind
sichtbar in Prozesslisten, History und Repositories. Die einzige erlaubte Datei-Quelle ist die lokale, ignorierte
`.env` für dev/test (Punkt 4); eine Vorlage ohne echte Werte (`.env.example`) darf versioniert sein.

---

## Rotation

| Secret-Typ | Empfohlenes Rotations-Intervall | Auslöser einer außerplanmäßigen Rotation |
|---|---|---|
| API-Token / OAuth2 | 90 Tage | Token-Leak, Mitarbeiterwechsel, Provider-Empfehlung |
| Service-Account-Password | jährlich (oder Policy) | Verdacht auf Kompromittierung |
| Signier-Key | Policy-abhängig | Hardware-Kompromittierung |
| SSH-Key | 6–12 Monate | Compute-Wechsel, Personalwechsel |

**Rotations-Schritte (generisch):**

1. Neues Secret im Manager / Store anlegen.
2. Zielsystem mit neuem Secret konfigurieren (Env, KeyVault-Referenz).
3. Anwendung neu starten / Token-Cache invalidieren.
4. Funktion mit neuem Secret verifizieren.
5. Altes Secret deaktivieren (nicht direkt löschen — erst nach 24h Beobachtung).

**Bei Leak oder Verdacht** gilt die umgekehrte Reihenfolge (`operations/INCIDENT_RESPONSE.md` → Eindämmen): altes
Secret **zuerst** sperren bzw. widerrufen, dann neues anlegen und verteilen — eine kurze Ausfallzeit ist in Kauf zu
nehmen.

---

## Was niemals in Logs landen darf

- Token-Werte, Passwörter, Keys (auch nicht „nur die ersten 8 Zeichen")
- Connection-Strings mit eingebettetem Passwort (`postgres://user:pw@host`) — vor Logging maskieren
- Request-Bodies, die Credentials enthalten (Login-Endpunkte, Webhook-Payloads)
- Stack-Traces, die Credentials in lokalen Variablen sichtbar machen könnten

**Pattern:** Logging-Schicht maskiert sensible Felder automatisch
(`***`, `[REDACTED]`). Wenn das nicht möglich ist, das betreffende Feld
explizit aus Log-Payloads filtern.

**Projektstand:** Verletzt im Dry-Run von `KasClient.request` (Parameter auf `INFO`, SOAP-Body mit KAS-Passwort auf
`DEBUG`) — `docs/KNOWN_ISSUES.md` K1, Behebung `docs/TODO.md` I2. Rotation des KAS-Passworts: im KAS unter den
Account-Einstellungen bzw. per `client.account.update_accountsettings(account_password=…)`, danach Keyring-Eintrag
(`keyring set kas_api <login>`) bzw. `KAS_PASS` aktualisieren.

---

## Was niemals committet werden darf

- `.env` mit echten Werten (Template `.env.example` ist erlaubt)
- `config.ps1`, `appsettings.Production.json`, `*.pfx`, `*.pem`, `*.key`
- Backup-Dumps, die Secrets enthalten können

`.gitignore` muss diese Pfade erfassen — siehe `BOOTSTRAP.md`.

---

## Pflege

Trigger (siehe `KICKOFF.md` Phase 3a): neues Secret eingeführt, rotiert, Speicherort
geändert oder Logging-Pfad ergänzt → diese Datei eintragen.
