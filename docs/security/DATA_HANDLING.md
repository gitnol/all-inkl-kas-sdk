# Datenschutz & Compliance – all-inkl-kas-sdk

Kein formaler Compliance-Rahmen: öffentliches Community-Projekt (MIT-Lizenz), nicht vom Hoster autorisiert oder
betreut. Wer das SDK in einer Organisation mit Rahmenwerk (DSGVO-Verarbeitungsverzeichnis, ISO 27001, TISAX)
einsetzt, bewertet die Exporte und Logs dort selbst; das Overlay `compliance-tisax` ist für dieses öffentliche Repo
bewusst nicht kopiert.

---

## Datenklassen (kanonisch)

Alle Overlays (`llm-integration`, `document-intelligence`, `compliance-tisax`) verwenden diese vier Klassen und
ergänzen nur ihre Erlaubnis-Matrix bzw. das TISAX-Mapping.

| Klasse | EN | Beispiele | An externe Dienste / Cloud-Modelle |
|---|---|---|---|
| Öffentlich | public | veröffentlichte Texte, Demo-Daten | erlaubt |
| Intern | internal | allgemeine Geschäftskommunikation, interne Prozessdokumente | nach Prüfung des Dienstes (Checkliste unten) |
| Vertraulich | confidential | Kunden- und Lieferantendaten, Verträge, Preise, Strategie | **nur mit dokumentierter Freigabe und Auftragsverarbeitungsvertrag (AVV)** |
| Streng vertraulich | restricted | Personalakten, besondere Kategorien personenbezogener Daten, Konstruktions-/Tarifgeheimnisse | **nein** — nur lokal/On-Prem; Ausnahme nur mit ausdrücklichem DSGVO-/TISAX-Sign-off |

Projektzuordnung:

| Daten im SDK | Klasse | Begründung |
|---|---|---|
| KAS-Passwort, Passwörter von Postfächern/FTP/DB/Unter-Accounts, private TLS-Schlüssel, Session-Tokens | Streng vertraulich | Generalschlüssel bzw. Identitätsübernahme möglich |
| Account-Konfiguration (Domains, DNS-Zonen, Postfachnamen, Weiterleitungsziele, Cronjob-URLs, Server-IPs) | Vertraulich | enthält personenbezogene Daten (E-Mail-Adressen) und Angriffsfläche des Betreibers |
| Statistikwerte (Speicher, Traffic), Liste verfügbarer TLDs/Software | Intern | keine Personenbezüge, aber betreiberspezifisch |
| Code, Doku, Testfixtures (fiktive Werte wie `example.com`, `w0123456`) | Öffentlich | Repo ist öffentlich |

---

## 1. Lokale Verarbeitung / Datenisolation

- Verarbeitung erfolgt lokal im Prozess des Aufrufers; einziger externer Empfänger ist die KAS-API des Hosters
  (`kasapi.kasserver.com`, HTTPS). Der Hoster ist ohnehin Verarbeiter der Account-Daten.
- Zugriff auf die Daten haben: der lokale Benutzer, der Skripte ausführt, und alle, die Lesezugriff auf seine
  Logs, Exporte und den System-Keyring haben.
- Keine Air-Gap-Anforderung (das SDK braucht Internetzugang zur API).

---

## 2. Minimalprinzip (Data Minimization)

- An die KAS-API gehen nur die Parameter der jeweiligen Aktion plus Login und Passwort (bei jedem Request).
- Nicht weitergegeben werden: Daten an Dritte, Telemetrie, Fehlerberichte — das SDK hat keinen weiteren Empfänger.
- Begrenzung sensibler Felder: Der Export kürzt flache Werte auf 80 Zeichen und maskiert Passwortfelder; private
  Schlüssel werden **nicht** maskiert (`docs/KNOWN_ISSUES.md` K2, Mitigation in `docs/TODO.md` I2).

---

## 3. Output-Dateien und Speicherorte

| Datei | Inhalt | Sensitivität |
|-------|--------|-------------|
| `scripts/output/kas_export_YYYY-MM-DD_HHMM.md` | Vollständige Account-Konfiguration (Accounts, Domains, DNS-Zonen, Postfächer, Weiterleitungen, DBs, FTP, Cronjobs, DKIM); Passwörter maskiert | Vertraulich |
| dieselbe Datei mit `--show-passwords` | wie oben, **mit Klartext-Passwörtern** | Streng vertraulich |
| Konsolen-/Log-Ausgabe im Dry-Run | Request-Parameter, auf `DEBUG` der SOAP-Body mit KAS-Passwort (K1) | Streng vertraulich |
| Konsolenausgabe `debug/*.py` | alle `ssl*`-Felder eines Hosts inkl. privatem Schlüssel (K3) | Streng vertraulich |
| `readme_KAS_API_SOURCE_OF_TRUTH.md` | Funktionsliste der API (Parameternamen, Fehlercodes) | Öffentlich |
| `API Funktionen.html` (lokal, gitignored) | Kopie der Hoster-Dokumentation, Eingabe des SOT-Generators | Intern (Urheberrecht des Hosters) |

- Exporte bleiben lokal unter `scripts/output/` (gitignored über `output/` und `kas_export_*.md`); nicht in
  Tickets, Chats oder Repos kopieren.
- `.gitignore` enthält zusätzlich `.env`, `*.log`, `*.pem`, `*.key`, `*.pfx`, `/docs/local/`, `/.internal-terms`.

---

## 4. Zugriffsschutz

- Zugriff hat, wer das KAS-Passwort kennt; das SDK selbst kennt keine Rollen. Least Privilege bedeutet hier: für
  Automatisierung einen **Unter-Account** mit eingeschränkten Rechten (`max_*`-Limits, `kas_access_forbidden`)
  statt des Haupt-Accounts verwenden, wo die Aufgabe das zulässt.
- Das Passwort liegt bevorzugt im System-Keyring (Dienst `kas_api`), nicht in `.env`.
- Secret-Speicherung und Rotation: siehe `docs/operations/SECRETS_MANAGEMENT.md`

---

## 5. Datenhaltung / Retention

- Exporte akkumulieren: jede Ausführung erzeugt eine neue Datei mit Zeitstempel, nichts wird überschrieben.
- Das SDK löscht nichts automatisch; Aufräumen ist Aufgabe des Betreibers, der die Exporte erzeugt.
- Empfehlung: Exporte nach Gebrauch löschen bzw. nur so lange aufbewahren wie für Vergleich/Wiederherstellung nötig;
  Klartext-Exporte (`--show-passwords`) sofort nach Gebrauch löschen.

---

## 6. Compliance-Checkliste für neue Features

- [ ] Keine neuen persistenten Speicher ohne Retention-Konzept
- [ ] Kein Logging von sensiblen Inhalten (Passwörter, Nutzdaten, PII)
- [ ] Externe Services nur nach Compliance-Prüfung einführen
- [ ] Neue API-Antwortfelder mit Secret-Charakter (Passwort, Schlüssel, Token) in die Maskierung des Exports aufnehmen
- [ ] Neue Skripte mit Schreibzugriff haben einen Dry-Run als Default (`--execute` zum Ausführen)
- [ ] Beispielwerte in Doku/Tests sind eindeutig fiktiv (`example.com`, `w0123456`)
