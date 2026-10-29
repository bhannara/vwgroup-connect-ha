<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vwgroup-connect-ha/main/custom_components/vag_connect/logo.png" alt="VW Group Connect" width="180">
</p>

<h1 align="center">VW Group Connect</h1>

<p align="center">
  <strong>One Home Assistant integration for Volkswagen Group cars: Audi · Volkswagen · Škoda · SEAT · CUPRA · Porsche · Bentley · VW and Audi US/Canada</strong>
</p>

<p align="center">
  <a href="https://github.com/sponsors/its-me-prash"><img src="https://img.shields.io/badge/%E2%9D%A4%20Sponsor-ec6cb9?logo=github-sponsors&logoColor=white" alt="Sponsor this project"></a>
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Default-41BDF5.svg" alt="HACS Default"></a>
  <a href="https://github.com/its-me-prash/vwgroup-connect-ha/releases"><img src="https://img.shields.io/github/v/release/its-me-prash/vwgroup-connect-ha?include_prereleases" alt="Release"></a>
  <a href="https://www.home-assistant.io"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fits-me-prash%2Fvwgroup-connect-ha%2Fmain%2Fhacs.json&query=%24.homeassistant&label=Home%20Assistant&prefix=%E2%89%A5&color=blue" alt="Minimum Home Assistant version"></a>
</p>

<p align="center">
  🌍 <a href="README.md">English</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.it.md">Italiano</a> · <a href="README.nl.md">Nederlands</a> · <a href="README.pl.md">Polski</a> · <a href="README.cs.md">Čeština</a> · <a href="README.sv.md">Svenska</a> · <a href="README.da.md">Dansk</a> · <a href="README.nb.md">Norsk</a> · <a href="README.fi.md">Suomi</a>
</p>

---

> **Diese Seite ist eine Kurzfassung.** Die [englische README](README.md) ist die
> maßgebliche Fassung und wird aktuell gehalten; übersetzte Seiten waren früher
> vollständige Kopien und sind unbemerkt monatelang zurückgefallen, deshalb werden
> sie jetzt bewusst kurz gehalten. Für die Statustabelle je Marke, die bekannten
> Einschränkungen, jede Option und jeden Service-Aufruf die englische Seite lesen.

> 📛 Früher veröffentlicht als **`vag-connect-ha`**. Entitäten, Dienstaufrufe
> (auch das Osterei `vag_connect.show_vag`), Automatisierungen und die
> HACS-Installation bleiben alle unverändert. Nur der Anzeigename hat sich geändert.
> Danke an **Si Gregory**, **Ben Johnson**, **Evets David** und **Jordan Waeles**,
> die den Anstoß dazu gegeben haben; die ganze Geschichte steht in [`MIGRATION.md`](MIGRATION.md).

## Was es macht

Bindet ein Fahrzeug des Volkswagen-Konzerns in [Home Assistant](https://www.home-assistant.io)
ein: Batterie- und Ladestatus, Reichweite, Kilometerstand, Klima, Türen und
Fenster, GPS-Position und mehr, für Volkswagen, Audi, Škoda, SEAT, CUPRA,
Porsche, Bentley sowie die nordamerikanischen VW- und Audi-Konten, aus einem
einzigen Konfigurationseintrag.

Fernbefehle wie Verriegeln, Klimatisierung und Ladesteuerung gibt es **dort, wo
das Backend der Marke sie noch zulässt**; das unterscheidet sich je nach Marke
und Modell. Die Statustabelle in der englischen README zeigt genau, welche Marke
was kann. Vor dem Einsatz eines Befehls bitte dort nachsehen.

Es braucht **kein Add-on, keinen Broker und keinen Middleware-Container** und
läuft parallel zu [evcc](https://evcc.io).

## Installation

1. **HACS** in Home Assistant öffnen.
2. Nach **VW Group Connect** suchen und installieren.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → VW Group Connect**
   öffnen und dem Anmeldeablauf folgen.

Die Mindestversion von Home Assistant steht im Badge oben; sie wird aus diesem
Repository gelesen und ist dieselbe Anforderung, die HACS bei der Installation
durchsetzt.

## Volkswagen EU: Anmelden allein reicht nicht

Bei Volkswagen-EU-Fahrzeugen fließen Daten erst, wenn die Datenfreigabe im
eigenen Portal von Volkswagen **selbst** eingeschaltet wurde. Erscheint das
Fahrzeug ohne Daten, ist das fast immer der Grund und kein falsches Passwort:
das VW-Datenportal einmal öffnen, dort jede einmalige Abfrage abschließen
(Bedingungen, Einwilligung, Onboarding) und die **Nutzung nicht
personenbezogener Daten** auf erteilt setzen. Danach kann es noch bis zur
nächsten Fahrt oder zum nächsten Aufwachen des Fahrzeugs dauern, bis Werte
erscheinen.

Die vollständige Anleitung steht in der [englischen README](README.md).

## Hilfe und Probleme melden

- Fragen und Hilfe bei der Einrichtung → [GitHub Discussions](https://github.com/its-me-prash/vwgroup-connect-ha/discussions)
- Ein Fehler oder ein unbekanntes API-Feld → [Issue eröffnen](https://github.com/its-me-prash/vwgroup-connect-ha/issues/new/choose).
  Der integrierte **Vehicle Data Scout** füllt den Großteil der Meldung vor.
- Eine Sicherheitslücke → bitte kein öffentliches Issue eröffnen, sondern
  [GitHub Security Advisories](https://github.com/its-me-prash/vwgroup-connect-ha/security/advisories/new) nutzen.

Meldungen und Antworten in der eigenen Sprache sind willkommen: Die Issue-Vorlagen
sind auf Englisch, das ist aber keine Pflicht.

## Dieses Projekt unterstützen

Dies ist ein Ein-Personen-Projekt, und jede Backend-Änderung von Volkswagen
bedeutet Tage an Arbeit, um wieder einen funktionierenden Weg zu finden. Wenn es
von Nutzen ist, lässt sich die laufende Pflege über
[GitHub Sponsors](https://github.com/sponsors/its-me-prash) unterstützen. Danke.

## Lizenz

[GNU AGPL v3.0-or-later](LICENSE). Namensnennung sowie Bedingungen zu Name und
Marke bei Nutzung oder Fork: siehe [`ATTRIBUTION.md`](ATTRIBUTION.md).
