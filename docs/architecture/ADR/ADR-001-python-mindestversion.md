# ADR-001: Python-Mindestversion 3.11, Zielversion 3.15

**Status:** Accepted
**Datum:** 2026-11-02

## 1. Kontext & Problem

`requires-python` stand auf `>=3.9`, die CI testete 3.9/3.11/3.13. Python 3.9 bekommt seit 2025-10-31 keine
Sicherheitsupdates mehr, 3.10 seit 2026-10-31. Die Fix-Versionen `urllib3` 2.8.0 und `python-dotenv` 1.2.2
verlangen Python ≥ 3.10; deshalb brauchten die Sicherheits-Floors aus I11 Marker, und unter 3.9 blieben die
`urllib3`-Lücken offen. Seit der Umstellung von `ubuntu-latest` auf Ubuntu 26.04 bietet `actions/setup-python`
dort kein Python 3.9 mehr an: der CI-Lauf vom 2026-11-02 scheiterte, ein Übergangs-Fix legte den Runner auf
`ubuntu-24.04` fest (`b1e5ee5`).

Stand 2026-11 werden 3.11 (bis 2027-10), 3.12, 3.13, 3.14 und 3.15 (stabil seit 2026-10, Updates bis 2031-10)
unterstützt.

## 2. Betrachtete Alternativen

* `>=3.9` lassen, Runner dauerhaft auf `ubuntu-24.04` festlegen
* `>=3.11`: älteste noch unterstützte Version als Untergrenze, 3.15 als Zielversion
* `>=3.15`: nur die neueste Version

## 3. Entscheidung

`requires-python = ">=3.11"`. Die CI testet 3.11 (Untergrenze), 3.13 und 3.15 (Zielversion) auf `ubuntu-26.04`.
Empfohlen wird 3.15. Die Marker `python_version` an den Abhängigkeiten entfallen.

## 4. Begründung

* Jede zulässige Laufzeit bekommt noch Sicherheitsupdates, und unter jeder greifen alle Sicherheits-Floors.
* `>=3.15` würde Nutzer mit dem Systempython von Debian/Ubuntu (3.11–3.14) ausschließen, ohne dass das SDK ein
  Sprachmerkmal von 3.15 braucht.
* `>=3.9` hielte EOL-Laufzeiten und die Marker-Sonderfälle am Leben und hängt die CI an ein altes Runner-Image.
* Das SDK nutzt keine Sprachmerkmale jenseits 3.9; die Anhebung erzwingt keine Codeänderung.

## 5. Konsequenzen

* **Positiv:** keine Marker mehr in `pyproject.toml`/`requirements.txt`; `tomllib` aus der Standardbibliothek
  statt `tomli`; `X | None` in Annotationen erlaubt; CI wieder auf dem aktuellen Runner-Image.
* **Negativ/Risiken:** Nutzer mit Python 3.9/3.10 können neue Versionen nicht mehr installieren (inkompatible
  Änderung, beim nächsten Release nennen). 3.11 endet 2027-10; die Untergrenze dann erneut anheben (Kadenz-Sweep).
