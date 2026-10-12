# Authentication und Authorization – all-inkl-kas-sdk

> Herkunft: Die `python-cli`-Vorlage beschreibt ein Tool ohne Netzwerk und ohne Credentials. Dieses Projekt
> authentifiziert sich bei einer externen API; deshalb folgt die Gliederung der Vorlage
> `stacks/python-api/security/AUTHENTICATION.md` (Template v27, `NEUES_PROJECT_INITIALISIEREN.md` Schritt 2 Punkt 3),
> befüllt für die KAS-API. Abschnitte zu `subprocess` und Dateisystem-Workspaces entfallen (keine externen Binaries).

---

## Auth-Stack

- **KAS-Login + Passwort pro Request:** Jeder SOAP-Request trägt `kas_login`, `kas_auth_type` und `kas_auth_data`
  im JSON-Payload (`kas_sdk/client.py`, `request`). Default `kas_auth_type="plain"` → `kas_auth_data` ist das
  Klartext-Passwort; `sha1` (Passwort-Hash) wird vom Client durchgereicht, aber nicht berechnet.
- Kein Token-Caching: Das SDK holt kein Session-Token für API-Aufrufe; `SessionService.add_session` erzeugt nur ein
  SSO-Token für die KAS-Weboberfläche (2FA-PIN optional über `session_2fa`).
- Transport ausschließlich HTTPS (`https://kasapi.kasserver.com/soap/KasApi.php`), Zertifikatsprüfung über
  `requests`-Default (`verify=True`, nicht abschaltbar über die SDK-API).
- Kein User-Login / kein interaktiver Flow: Ja für die Bibliothek; die Skripte fragen fehlende Zugangsdaten
  interaktiv ab (`kas_sdk/utils.py`, `getpass`).

---

## Flow-Beschreibung

```
1. Aufrufer erzeugt KasClient → Login aus Argument | KAS_LOGIN | .env; fehlt er → KasAuthError
2. Passwort aus Argument | KAS_PASS | .env | Keyring (Dienst kas_api, Benutzer = Login); fehlt es → nur Warnung
3. Erster Zugriff auf client.<service> lädt die Service-Klasse (Lazy-Loading)
4. Service ruft client.request(action, params) → Flood-Schutz-Wartezeit → JSON mit Login/Auth-Typ/Passwort
   → SOAP-Envelope → HTTPS POST (Timeout 30 s)
5. Antwort: SOAP-Fault (z. B. falsches Passwort) → KasApiError mit Fault-Text;
   HTTP-Fehlerstatus → KasConnectionError (siehe docs/KNOWN_ISSUES.md K7)
6. Kein Wiederholungsversuch — der Aufrufer entscheidet
```

> **Achtung:** Das Passwort steht in jedem Request-Body. Jede Stelle, die Bodys oder Parameter loggt, ist ein
> Secret-Leck (`docs/security/THREAT_MODEL.md` Bedrohung 1).

Welche Werte `kas_auth_type` außer `plain` heute offiziell unterstützt (`sha1`, Session-basiert), ist in der
öffentlichen KAS-Dokumentation nicht aufgelistet (Recherche 2026-10-11) — offen im Backlog.

---

## Rollenstruktur

```
Haupt-Account (w…):  voller Zugriff auf alle Pakete, inkl. Unter-Accounts anlegen/löschen und Domains umziehen
Unter-Account:       Zugriff auf die eigenen Ressourcen innerhalb der beim Anlegen gesetzten max_*-Limits;
                     kas_access_forbidden="Y" sperrt laut Parametername den KAS-Zugang des Unter-Accounts
                     (Wirkung nicht geprüft)
```

Minimalprinzip: Automatisierte Skripte (Export, HSTS, DNS) wenn möglich mit einem Unter-Account betreiben, der
nur die betroffenen Domains enthält. Das SDK selbst kennt keine Rollen; die Rechte setzt die KAS-API durch.

---

## Retry- und Fehlerbehandlung

- Kein Retry im SDK (siehe `docs/architecture/ERROR_HANDLING.md` → Retry-Strategien).
- Fehlgeschlagene Anmeldung **nie** automatisch wiederholen — wiederholte Fehlversuche können zur Sperre durch
  den Hoster führen. Skripte, die pro Host einen Request schicken, sollten nach einem Auth-Fehler abbrechen statt
  mit dem nächsten Host weiterzumachen (heute: weitermachen, siehe Backlog).

---

## Zugriffsschutz

Durchgesetzt von der KAS-API (Account-Rechte). Lokal schützt nur das Betriebssystem: Wer den Benutzer-Keyring
oder die Umgebung des Prozesses lesen kann, kann das Passwort lesen. `.env` enthält das Passwort im Klartext und
gehört nur auf Einzelplatz-Entwicklungsrechner.

---

## Security-Checkliste

- [x] Keine Hardcoded-Secrets im Repo – Credentials nur aus den Quellen laut `docs/operations/SECRETS_MANAGEMENT.md`
      (geprüft 2026-10-11: Arbeitsbaum und History enthalten nur Platzhalterwerte)
- [x] `.env` in `.gitignore` eingetragen
- [ ] API-Client hat nur Minimalberechtigung (Least Privilege) — Empfehlung Unter-Account, nicht technisch erzwungen
- [ ] Passwort wird nicht geloggt — **verletzt** im Dry-Run (`docs/KNOWN_ISSUES.md` K1, Fix in `docs/TODO.md` I2)
- [x] Passwort wird nicht persistiert, außer bewusst im System-Keyring (Rückfrage in `get_kas_credentials`)
- [x] Passwort geht nur per HTTPS an den offiziellen Endpunkt
- [ ] Ungültige Zugangsdaten werden als `KasAuthError` gemeldet — heute `KasApiError` (K9, `docs/TODO.md` I3)
- [ ] Bei Passwort-Rotation: neues Passwort im KAS setzen, Keyring/Umgebung aktualisieren (bei Leak: zuerst ändern,
      `docs/operations/SECRETS_MANAGEMENT.md` → Rotation)
