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

> **Tato stránka je jen stručné shrnutí.** [Anglické README](README.md) je
> závazné a udržuje se aktuální; přeložené stránky byly dříve úplnými kopiemi
> a nenápadně zaostávaly o měsíce, proto jsou nyní záměrně krátké. Tabulku
> stavu podle značek, známá omezení, všechny volby a všechna volání služeb
> najdete na anglické stránce.

> 📛 Dříve zveřejněno jako **`vag-connect-ha`**. Entity, volání služeb
> (včetně velikonočního vajíčka `vag_connect.show_vag`), automatizace i instalace
> přes HACS zůstávají beze změny. Změnil se jen zobrazovaný název. Poděkování
> za podnět patří těmto lidem: **Si Gregory**, **Ben Johnson**, **Evets David** a **Jordan Waeles**.
> Celý příběh je v [`MIGRATION.md`](MIGRATION.md).

## Co umí

Přenese váš vůz koncernu Volkswagen do systému [Home Assistant](https://www.home-assistant.io):
stav baterie a nabíjení, dojezd, najeté kilometry, klimatizaci, dveře a okna,
polohu GPS a další, a to pro Volkswagen, Audi, Škoda, SEAT, CUPRA, Porsche,
Bentley i severoamerické účty VW a Audi, z jediného konfiguračního záznamu.

Vzdálené příkazy, například zamknutí, klimatizace a řízení nabíjení, existují
**tam, kde to backend dané značky stále umožňuje**, což se liší podle značky
i modelu. Tabulka stavu v anglickém README přesně uvádí, která značka co umí,
proto si ji prosím zkontrolujte dříve, než se na nějaký příkaz spolehnete.

Nepotřebuje **žádný doplněk, broker ani kontejner s middlewarem** a funguje
souběžně s [evcc](https://evcc.io).

## Instalace

1. V Home Assistantu otevřete **HACS**.
2. Vyhledejte **VW Group Connect** a nainstalujte ho.
3. Restartujte Home Assistant.
4. Přejděte do **Nastavení → Zařízení a služby → Přidat integraci → VW Group Connect**
   a postupujte podle přihlašovacího průvodce.

Minimální verze Home Assistantu je uvedena na odznaku výše; načítá se z tohoto
repozitáře a je to stejný požadavek, který HACS vynucuje při instalaci.

## Volkswagen EU: samotné přihlášení nestačí

U vozů Volkswagen pro EU začnou data proudit teprve tehdy, když **vy sami**
zapnete sdílení dat na vlastním portálu společnosti Volkswagen. Pokud se vůz
zobrazí bez dat, je to téměř vždy tímto důvodem, a ne špatným heslem: jednou
otevřete datový portál VW, dokončete tam každou jednorázovou výzvu (podmínky,
souhlas, úvodní nastavení) a nastavte **využití neosobních údajů** na uděleno.
Poté ještě může trvat až do další jízdy nebo probuzení vozu, než se hodnoty
objeví.

Celý postup najdete v [anglickém README](README.md).

## Pomoc a hlášení problémů

- Dotazy a pomoc s nastavením → [GitHub Discussions](https://github.com/its-me-prash/vwgroup-connect-ha/discussions)
- Chyba nebo neznámé pole API → [založte issue](https://github.com/its-me-prash/vwgroup-connect-ha/issues/new/choose).
  Integrovaný **Vehicle Data Scout** předvyplní většinu hlášení za vás.
- Bezpečnostní zranitelnost → prosím nezakládejte veřejné issue, použijte
  [GitHub Security Advisories](https://github.com/its-me-prash/vwgroup-connect-ha/security/advisories/new).

Hlášení i odpovědi ve vašem vlastním jazyce jsou vítány: šablony issue jsou
anglicky, ale vy anglicky psát nemusíte.

## Podpořte tento projekt

Jde o projekt jednoho člověka a každá změna backendu, kterou Volkswagen provede,
znamená dny práce, než se znovu najde funkční cesta. Pokud pro vás něco znamená,
můžete další údržbu podpořit přes
[GitHub Sponsors](https://github.com/sponsors/its-me-prash). Děkuji.

## Licence

[GNU AGPL v3.0-or-later](LICENSE). Uvedení původu a podmínky týkající se názvu
a ochranné známky při použití nebo forku: viz [`ATTRIBUTION.md`](ATTRIBUTION.md).
