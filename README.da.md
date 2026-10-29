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

> **Denne side er et kort resumé.** Den [engelske README](README.md) er den, der
> gælder, og den holdes ajour; de oversatte sider var tidligere fulde kopier og
> kom stille og roligt måneder bagud, så de holdes nu bevidst korte. Den
> engelske side har tabellen med status for hvert mærke, de kendte begrænsninger,
> alle indstillinger og alle tjenestekald.

> 📛 Tidligere udgivet som **`vag-connect-ha`**. Entiteter, tjenestekald
> (herunder påskægget `vag_connect.show_vag`), automatiseringer og
> HACS-installationen er alle uændrede. Det er kun visningsnavnet, der er ændret. Tak til
> **Si Gregory**, **Ben Johnson**, **Evets David** og **Jordan Waeles**, som
> tog initiativ til det; hele historien står i [`MIGRATION.md`](MIGRATION.md).

## Hvad den gør

Henter din Volkswagen Group-bil ind i [Home Assistant](https://www.home-assistant.io):
batteri- og ladestatus, rækkevidde, kilometertæller, klima, døre og vinduer,
GPS-position og meget mere — for Volkswagen, Audi, Škoda, SEAT, CUPRA, Porsche,
Bentley og de nordamerikanske VW- og Audi-konti, fra én konfigurationspost.

Fjernkommandoer som låsning, klima- og ladestyring findes **hvor mærkets backend
stadig tillader dem**, og det varierer fra mærke til mærke og fra model til
model. Statustabellen i den engelske README viser præcis, hvilket mærke der kan
hvad — tjek den, før du stoler på en kommando.

Den kræver **ingen add-on, broker eller middleware-container**, og den kører side
om side med [evcc](https://evcc.io).

## Installation

1. Åbn **HACS** i Home Assistant.
2. Søg efter **VW Group Connect**, og installér den.
3. Genstart Home Assistant.
4. Gå til **Settings → Devices & Services → Add Integration → VW Group Connect**
   og følg login-forløbet.

Den mindste Home Assistant-version er den, badget ovenfor viser; den læses fra
dette repository og er det samme krav, som HACS håndhæver, når du installerer.

## Volkswagen EU: det er ikke nok at logge ind

For Volkswagen EU-biler begynder data først at flyde, når **du** har aktiveret
datadeling på Volkswagens eget portal. Hvis bilen dukker op uden data, er det
næsten altid forklaringen og ikke en forkert adgangskode: åbn VW-dataportalen én
gang, gennemfør en eventuel engangsprompt dér (vilkår, samtykke, onboarding) og
sæt **brug af ikke-personlige data** til givet. Derefter kan der stadig gå til
bilens næste kørsel eller opvågning, før værdierne dukker op.

Den fulde gennemgang findes i den [engelske README](README.md).

## Hjælp og rapportering af problemer

- Spørgsmål og hjælp til opsætning → [GitHub Discussions](https://github.com/its-me-prash/vwgroup-connect-ha/discussions)
- En fejl eller et ukendt API-felt → [opret et issue](https://github.com/its-me-prash/vwgroup-connect-ha/issues/new/choose).
  Den indbyggede **Vehicle Data Scout** forudfylder det meste af rapporten for dig.
- En sikkerhedssårbarhed → åbn venligst ikke et offentligt issue; brug
  [GitHub Security Advisories](https://github.com/its-me-prash/vwgroup-connect-ha/security/advisories/new).

Rapporter og svar på dit eget sprog er velkomne — issue-skabelonerne er på
engelsk, men det behøver du ikke selv at være.

## Støt dette projekt

Dette er et enmandsprojekt, og hver gang Volkswagen ændrer sin backend, betyder
det dages arbejde at finde en fungerende vej igen. Hvis den er noget værd for
dig, kan du støtte den fortsatte vedligeholdelse via
[GitHub Sponsors](https://github.com/sponsors/its-me-prash). Tak.

## Licens

[GNU AGPL v3.0-or-later](LICENSE). Kildeangivelse samt vilkår for navn og
varemærke ved brug eller fork: se [`ATTRIBUTION.md`](ATTRIBUTION.md).
