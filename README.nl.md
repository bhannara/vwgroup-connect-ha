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

> **Deze pagina is een korte samenvatting.** De [Engelse README](README.md) is
> de leidende versie en wordt bijgehouden; vertaalde pagina's waren eerder
> volledige kopieën en liepen ongemerkt maanden achter, daarom worden ze nu
> bewust kort gehouden. Voor de statustabel per merk, de bekende beperkingen,
> alle opties en alle service-aanroepen: lees de Engelse pagina.

> 📛 Eerder gepubliceerd als **`vag-connect-ha`**. Entiteiten, serviceaanroepen
> (inclusief het paasei `vag_connect.show_vag`), automatiseringen en de installatie
> via HACS blijven allemaal ongewijzigd: alleen de weergavenaam is veranderd. Dank aan
> **Si Gregory**, **Ben Johnson**, **Evets David** en **Jordan Waeles**, die hiervoor
> de aanzet gaven; het hele verhaal staat in [`MIGRATION.md`](MIGRATION.md).

## Wat het doet

Brengt je auto uit de Volkswagen Group naar [Home Assistant](https://www.home-assistant.io):
accu- en laadstatus, actieradius, kilometerstand, klimaat, deuren en ramen,
gps-positie en meer — voor Volkswagen, Audi, Škoda, SEAT, CUPRA, Porsche, Bentley
en de Noord-Amerikaanse VW- en Audi-accounts, met één enkele configuratie.

Commando's op afstand, zoals vergrendelen, klimaat- en laadbesturing, bestaan
**waar de backend van het merk ze nog toestaat**, en dat verschilt per merk en
per model. De statustabel in de Engelse README laat precies zien welk merk wat
kan — controleer die voordat je op een commando vertrouwt.

Er is **geen add-on, broker of middleware-container** nodig, en de integratie
draait naast [evcc](https://evcc.io).

## Installeren

1. Open **HACS** in Home Assistant.
2. Zoek naar **VW Group Connect** en installeer het.
3. Herstart Home Assistant.
4. Ga naar **Settings → Devices & Services → Add Integration → VW Group Connect**
   en volg de inlogstappen.

De minimaal vereiste Home Assistant-versie staat in de badge hierboven; die wordt
uit deze repository gelezen en is dezelfde eis die HACS bij de installatie
afdwingt.

## Volkswagen EU: inloggen is niet genoeg

Bij Volkswagen-auto's in de EU beginnen er pas gegevens binnen te komen nadat
**jij** het delen van gegevens hebt ingeschakeld op het eigen portaal van
Volkswagen. Verschijnt de auto zonder gegevens, dan is dit bijna altijd de
oorzaak en niet een verkeerd wachtwoord: open het VW-dataportaal één keer, rond
daar elke eenmalige melding af (voorwaarden, toestemming, onboarding) en zet
**gebruik van niet-persoonlijke gegevens** op toegestaan. Daarna kan het nog
duren tot de volgende rit of het volgende ontwaken van de auto voordat er
waarden verschijnen.

De volledige handleiding staat in de [Engelse README](README.md).

## Hulp en problemen melden

- Vragen en hulp bij de installatie → [GitHub Discussions](https://github.com/its-me-prash/vwgroup-connect-ha/discussions)
- Een bug of een onbekend API-veld → [open een issue](https://github.com/its-me-prash/vwgroup-connect-ha/issues/new/choose).
  De ingebouwde **Vehicle Data Scout** vult het grootste deel van de melding al
  voor je in.
- Een beveiligingslek → open alsjeblieft geen openbaar issue; gebruik
  [GitHub Security Advisories](https://github.com/its-me-prash/vwgroup-connect-ha/security/advisories/new).

Meldingen en reacties in je eigen taal zijn welkom — de issuesjablonen zijn in het
Engels, maar jij hoeft niet in het Engels te schrijven.

## Dit project steunen

Dit is een project van één persoon, en elke wijziging die Volkswagen in de
backend doorvoert, betekent dagen werk om weer een werkend pad te vinden. Als het
je iets waard is, kun je het voortdurende onderhoud steunen via
[GitHub Sponsors](https://github.com/sponsors/its-me-prash). Bedankt.

## Licentie

[GNU AGPL v3.0-or-later](LICENSE). Naamsvermelding en voorwaarden voor naam en
handelsmerk bij gebruik of fork: zie [`ATTRIBUTION.md`](ATTRIBUTION.md).
