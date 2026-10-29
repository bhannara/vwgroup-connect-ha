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

> **Den här sidan är en kort sammanfattning.** Den [engelska README-filen](README.md)
> är den som gäller och hålls aktuell; de översatta sidorna var tidigare
> fullständiga kopior som i tysthet hamnade månader efter, och därför hålls de
> medvetet korta nu. För statustabellen per märke, de kända begränsningarna,
> alla alternativ och alla tjänsteanrop, läs den engelska sidan.

> 📛 Tidigare publicerad som **`vag-connect-ha`**. Entiteter, tjänsteanrop
> (inklusive påskägget `vag_connect.show_vag`), automatiseringar och
> HACS-installationen är alla oförändrade. Det är bara visningsnamnet som har ändrats. Tack till
> **Si Gregory**, **Ben Johnson**, **Evets David** och **Jordan Waeles**, som
> tog initiativet till det; hela historien finns i [`MIGRATION.md`](MIGRATION.md).

## Vad den gör

Hämtar in din bil från Volkswagen-koncernen i [Home Assistant](https://www.home-assistant.io):
batteri- och laddstatus, räckvidd, vägmätare, klimat, dörrar och fönster,
GPS-position och mer, för Volkswagen, Audi, Škoda, SEAT, CUPRA, Porsche, Bentley
och de nordamerikanska VW- och Audi-kontona, från en enda konfigurationspost.

Fjärrkommandon som låsning, klimat- och laddstyrning finns **där märkets backend
fortfarande tillåter dem**, vilket skiljer sig mellan märken och modeller.
Statustabellen i den engelska README-filen anger exakt vilket märke som kan vad.
Kontrollera den innan du förlitar dig på ett kommando.

Den kräver **inget tillägg, ingen broker och ingen middleware-container**, och
den fungerar sida vid sida med [evcc](https://evcc.io).

## Installation

1. Öppna **HACS** i Home Assistant.
2. Sök efter **VW Group Connect** och installera det.
3. Starta om Home Assistant.
4. Gå till **Settings → Devices & Services → Add Integration → VW Group Connect**
   och följ inloggningsflödet.

Den lägsta Home Assistant-versionen anges av badgen ovan. Den läses från detta
repository och är samma krav som HACS tillämpar när du installerar.

## Volkswagen EU: att logga in räcker inte

För Volkswagen-bilar i EU börjar data flöda först när **du** har aktiverat
datadelning på Volkswagens eget portal. Om bilen dyker upp utan data är det
nästan alltid orsaken, snarare än ett felaktigt lösenord: öppna VW:s dataportal
en gång, slutför eventuella engångssteg där (villkor, samtycke, introduktion) och
sätt **användning av icke-personliga data** till medgiven. Därefter kan det
fortfarande dröja tills bilens nästa körning eller uppvaknande innan värden
visas.

Hela genomgången finns i den [engelska README-filen](README.md).

## Hjälp och felrapportering

- Frågor och installationshjälp → [GitHub Discussions](https://github.com/its-me-prash/vwgroup-connect-ha/discussions)
- Ett fel eller ett okänt API-fält → [öppna ett ärende](https://github.com/its-me-prash/vwgroup-connect-ha/issues/new/choose).
  Den inbyggda **Vehicle Data Scout** fyller i det mesta av rapporten åt dig.
- En säkerhetsbrist → öppna inget offentligt ärende, utan använd
  [GitHub Security Advisories](https://github.com/its-me-prash/vwgroup-connect-ha/security/advisories/new).

Rapporter och svar på ditt eget språk är välkomna. Ärendemallarna är på
engelska, men du behöver inte skriva på engelska.

## Stöd projektet

Det här är ett enmansprojekt, och varje ändring som Volkswagen gör i sin backend
innebär flera dagars arbete för att hitta en fungerande väg igen. Om det är värt
något för dig kan du stödja det fortsatta underhållet via
[GitHub Sponsors](https://github.com/sponsors/its-me-prash). Tack.

## Licens

[GNU AGPL v3.0-or-later](LICENSE). Attribution samt villkor för namn och
varumärke vid användning eller fork: se [`ATTRIBUTION.md`](ATTRIBUTION.md).
