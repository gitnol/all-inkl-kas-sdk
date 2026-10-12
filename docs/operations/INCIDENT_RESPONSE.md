# Incident Response – all-inkl-kas-sdk

Was zu tun ist, wenn ein Sicherheitsvorfall, ein kritischer Bug oder ein
Datenverlust eintritt. Vor Eskalation lesen, nicht erst während der Krise.

Verbindet sich mit `security/THREAT_MODEL.md`, `operations/SECRETS_MANAGEMENT.md`
und `operations/RUNBOOK.md` (Stack-spezifisch).

---

## Klassifizierung

| Stufe | Definition | Beispiele | Reaktionsfenster |
|---|---|---|---|
| **P0 – Kritisch** | Datenverlust, Datenleck, Produktion komplett offline | Credentials in git, kompromittierter API-Key, DB-Korruption | sofort |
| **P1 – Hoch** | Kernfunktion ausgefallen, sensible Daten gefährdet aber nicht abgeflossen | Auth-Service unten, Logging-Bug exponiert PII | < 2 Stunden |
| **P2 – Mittel** | Funktion eingeschränkt, kein Daten-/Sicherheitsrisiko | Performance-Einbruch, einzelner Endpoint kaputt | < 24 Stunden |
| **P3 – Niedrig** | Kosmetischer / nicht-blockierender Defekt | UI-Bug, falsche Fehlermeldung | Backlog |

---

## Vorgehen (5 Phasen)

### 1. Eindämmen (Contain)

Ziel: weiteren Schaden verhindern, Beweise sichern. Erst danach analysieren.

- Bei Credential-Leak: betroffenes Secret **sofort** invalidieren (siehe
  `SECRETS_MANAGEMENT.md` → Rotation).
- Bei aktivem Angriff: betroffene Komponente isolieren (Service stoppen,
  Netzwerk-Zugriff sperren).
- Logs und betroffene Artefakte sichern, **bevor** etwas verändert wird
  (Forensik-Pfad).
- Bei P0: weitere Personen benachrichtigen (siehe Eskalationspfad unten).

### 2. Bewerten (Assess)

- **Was ist betroffen?** Welche Daten, welche Nutzer, welche Systeme?
- **Wann hat es begonnen?** Logs prüfen → Zeitfenster eingrenzen.
- **Welcher Vektor?** Welche Schwachstelle / welches Versagen hat es ermöglicht?
- **Wer muss informiert werden?** Intern (Stakeholder), extern (Kunden,
  Auditor, Datenschutzbehörde bei DSGVO-Relevanz).

Output: kurzer Status (1 Absatz), an Eskalationsstelle übergeben.

### 3. Kommunizieren (Communicate)

- **Intern zuerst.** Stakeholder informieren, bevor sie es von außerhalb hören.
- **Faktentreu.** Was wir wissen, was wir nicht wissen, was wir gerade tun.
  Keine Spekulation.
- **Extern nur abgestimmt.** Bei DSGVO-Verstoss: Meldepflicht 72h
  (Datenschutzbehörde); Compliance-Rahmen siehe `security/DATA_HANDLING.md`.

### 4. Beheben (Eradicate & Recover)

- Wurzelursache fixen, nicht nur Symptom (Code-Fix, Konfigurations-Härtung,
  Patch-Update).
- Verifikation: Reproduziert sich der Vorfall im fix-validierten Stand? Nein.
- Wiederherstellung: Service wieder hochfahren, Datenintegrität prüfen.
- Monitoring intensivieren für 24–72h.

### 5. Post-Mortem

Innerhalb von 5 Werktagen nach P0/P1-Vorfall:

- **Zeitleiste:** wer hat wann was bemerkt / getan.
- **Wurzelursache:** technisch + prozessual (5-Why-Analyse).
- **Lessons Learned:** was schief lief, was gut lief. Einträge in
  `LESSONS_LEARNED.md` und `CHANGELOG.md`.
- **Maßnahmen:** konkrete TODO-Punkte oder ADRs, um Wiederholung zu verhindern.
- **Update Threat Model:** falls die Bedrohung neu ist → Eintrag in
  `security/THREAT_MODEL.md`.

---

## Eskalationspfad

| Vorfall-Stufe | Wer wird wann benachrichtigt |
|---|---|
| P0 | Betreiber des betroffenen KAS-Accounts sofort (er allein kann das Passwort ändern); Maintainer des Repos über ein privates GitHub-Security-Advisory, wenn die Ursache im SDK liegt |
| P1 | Maintainer des Repos (Repo-Owner) innerhalb 1 Stunde über ein privates Security-Advisory; betroffene Nutzer über Release-Notiz/README-Hinweis |
| P2 | GitHub-Issue im nächsten regulären Durchgang |
| P3 | Backlog-Eintrag, keine Sonder-Eskalation |

Das Projekt ist ein Community-SDK ohne Betriebsteam: Die Verantwortung für einen konkreten Account liegt beim
jeweiligen Betreiber, die Verantwortung für den Code beim Maintainer.

---

## Projektspezifische Erstmaßnahmen

| Vorfall | Eindämmen | Prüfen |
|---|---|---|
| KAS-Passwort geleakt (Log, Export, Commit, CI-Ausgabe) | Passwort im KAS sofort ändern, Keyring/`KAS_PASS` aktualisieren; Fundstelle (Log/Export) löschen; bei Commit: History bereinigen **und** trotzdem rotieren | KAS: Unter-Accounts, Domains (Umzug), DNS-Zonen, Mail-Weiterleitungen, Cronjobs, FTP-Nutzer auf fremde Änderungen |
| Privater TLS-Schlüssel offengelegt (Debug-Ausgabe, Export) | Zertifikat widerrufen bzw. neu ausstellen, neuen Schlüssel per `update_ssl` setzen | betroffene Hosts per `get_domains`/`get_subdomains` |
| Wildcard-Skript hat DNS falsch geändert (`--execute`) | fehlende Records manuell per `add_dns_settings` anlegen bzw. Wildcard wiederherstellen; Ausgabe des Laufs sichern | Auflösung von `www` und allen Subdomains (A **und** AAAA) |
| SDK sendet fehlerhafte Requests (z. B. kaputter Envelope) | betroffene Skripte stoppen, im Dry-Run reproduzieren | Antwort-Fault-Text, `docs/KNOWN_ISSUES.md` |

---

## Checkliste für die ersten 15 Minuten bei P0/P1

- [ ] Schaden eingedämmt (Service / Secret / Netzwerk-Pfad)?
- [ ] Logs gesichert?
- [ ] Eskalation losgeschickt?
- [ ] Zeitstempel des Beginns notiert?
- [ ] Aktuell aktive Personen kennen jeweils ihren Teil-Auftrag?

---

## Pflege

Trigger: nach jedem P0/P1-Vorfall: Post-Mortem-Hinweis hier integrieren falls
generalisierbar (z.B. Eskalationsweg ändert sich). Sonst nur projektspezifische
Anpassung der Eskalations-Tabelle.
