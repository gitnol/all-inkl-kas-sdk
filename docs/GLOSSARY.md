# Glossar – all-inkl-kas-sdk

Ubiquitous Language für dieses Projekt. Jeder Begriff hat genau eine Bedeutung.
Synonyme oder doppelt belegte Begriffe schaffen Drift und werden vermieden.

LLM-Agenten konsultieren dieses Glossar, **bevor** sie Begriffe im Code, in
Commit-Messages oder in Doku verwenden.

---

## Begriffe

| Begriff | Bedeutung | Wo verwendet | Nicht zu verwechseln mit |
|---|---|---|---|
| KAS | Kundenadministrationssystem des Hosters All-Inkl; verwaltet Webhosting-Accounts | gesamtes Projekt | KAS-API (die Schnittstelle dazu) |
| KAS-API | SOAP-Schnittstelle des KAS unter `kasapi.kasserver.com`, nimmt einen JSON-String im Element `KasRequest` entgegen | `kas_sdk/client.py` | REST-API (die KAS-API ist kein REST) |
| KAS-Login | Benutzerkennung eines Accounts, Form `w` + Ziffern (Beispiel fiktiv: `w0123456`) | `kas_login`, `KAS_LOGIN` | Postfach-Login (`m…`), FTP-Login (`f…`), DB-Login (`d…`) |
| Unter-Account | KAS-Account, der unter einem Haupt-Account angelegt ist und eigene Limits (`max_*`) hat | `AccountService` | Postfach, FTP-Nutzer |
| Aktion | Eine Funktion der KAS-API, identifiziert durch `kas_action` (z. B. `get_dns_settings`) | `KasClient.request(action, …)` | SDK-Methode (die Python-Methode, die eine Aktion aufruft) |
| Paket | Fachliche Gruppe von Aktionen in der KAS-Doku (z. B. `dns`, `mailaccount`); 21 Pakete | `readme_KAS_API_SOURCE_OF_TRUTH.md` | Python-Paket (`kas_sdk`) |
| Service | Python-Klasse, die ein Paket kapselt (`DnsService` …), erreichbar als `client.<paket>` | `kas_sdk/services/*.py` | Dienst/Daemon (das SDK hat keinen) |
| Source of Truth (SOT) | Aus der Hoster-Doku generierte Liste aller Aktionen mit Pflicht-/optionalen Parametern und Fehlercodes; Orakel für Parameternamen | `readme_KAS_API_SOURCE_OF_TRUTH.md`, `scripts/generate_source_of_truth.py` | README (Nutzer-Doku) |
| Flood-Schutz | Mindestabstand zwischen zwei Requests eines Clients (`flood_protection_delay`, Default 2 s) | `KasClient.request` | Retry/Backoff (gibt es nicht) |
| SDK-Dry-Run | Modus von `KasClient`, in dem **kein** Request gesendet wird; Antwort ist ein Mock | `dry_run`, `KAS_DRY_RUN` | Skript-Probelauf |
| Skript-Probelauf | Modus eines Wartungsskripts, das echt liest, aber Änderungen nur anzeigt (`dns_remove_wildcards.py` ohne `--execute`, `ssl_enforce_hsts.py` mit `KAS_DRY_RUN`) | `scripts/` | SDK-Dry-Run |
| `ReturnString` / `ReturnInfo` | Felder der KAS-Antwort: Erfolgskennzeichen (`TRUE`) bzw. Nutzdaten (Liste, ID, Dict) | Services | `Response`-Wrapper (wird vom Client entfernt) |
| Fault | SOAP-Fehlerantwort mit `faultstring` (KAS-Fehlercode wie `missing_parameter`) | `_parse_soap_map` → `KasApiError` | Netzwerkfehler (`KasConnectionError`) |
| `zone_host` | DNS-Zone (Domain) einer DNS-Aktion; beim Anlegen mit abschließendem Punkt (`example.com.`) | `DnsService` | `record_name` (Name innerhalb der Zone) |
| Wildcard-Record | DNS-Record mit `record_name == "*"` (A/AAAA), der alle nicht explizit definierten Namen auflöst | `scripts/dns_remove_wildcards.py` | Wildcard-Subdomain im KAS |
| HSTS | HTTP Strict Transport Security; hier gesetzt über `ssl_certificate_hsts_max_age` (Sekunden, `-1` = aus) | `SslService`, `scripts/ssl_*` | Force-HTTPS (`ssl_certificate_force_https`, 301-Umleitung) |
| SNI-Zertifikat | Eigenes TLS-Zertifikat eines Hosts (`ssl_certificate_sni_*`: `key`, `crt`, `bundle`, `csr`) | `SslService`, HSTS-Skripte | IP-basiertes Zertifikat (`ssl_certificate_ip`) |
| Export | Markdown-Bericht der Account-Konfiguration unter `scripts/output/` | `scripts/export_account.py` | Source of Truth |

---

## Verbotene Synonyme

Begriffe, die im Projekt-Kontext **nicht** mehr verwendet werden dürfen,
auch wenn sie umgangssprachlich gleichbedeutend wirken:

| Verbotener Begriff | Korrekt | Grund |
|---|---|---|
| „Dry-Run" ohne Zusatz | SDK-Dry-Run bzw. Skript-Probelauf | zwei Modi mit gegensätzlichem Leseverhalten (`docs/KNOWN_ISSUES.md` K11) |
| „Endpoint" / „Methode" für eine KAS-Funktion | Aktion | die API hat genau einen Endpunkt; „Methode" ist die Python-Seite |
| „Sub-Account", „Subaccount" (in deutscher Doku) | Unter-Account | einheitliche Schreibweise; im englischen Bestand bleibt „sub-account" |
| „Kunde" für einen KAS-Account | Account bzw. Unter-Account | „Kunde" ist der Vertragspartner des Hosters, nicht das technische Objekt |

---

## Pflege

- Neuer Domänenbegriff im Code → **vor dem Commit** hier ergänzen.
- Begriff wird umbenannt → alter Eintrag bleibt mit Vermerk „ersetzt durch <neuer Begriff>"
  stehen (mindestens eine Inkrement-Generation als Übergangsphase).
- Begriff entfällt → Eintrag mit „deprecated <Datum>" markieren, nicht löschen.
- Diese Datei steht in der Trigger-Matrix in `KICKOFF.md` Phase 3a.
