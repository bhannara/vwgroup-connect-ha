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

> **Denne siden er et kort sammendrag.** Den [engelske README-en](README.md) er den
> gjeldende og holdes oppdatert. Oversatte sider var tidligere fulle kopier og
> havnet i det stille måneder på etterskudd, så de holdes nå bevisst korte.
> For statustabellen per merke, de kjente begrensningene, alle alternativer og
> alle tjenestekall, se den engelske siden.

> 📛 Tidligere utgitt som **`vag-connect-ha`**. Entiteter, tjenestekall
> (inkludert påskeegget `vag_connect.show_vag`), automatiseringer og
> HACS-installasjonen er alle uendret. Det er bare visningsnavnet som er endret. Takk til
> **Si Gregory**, **Ben Johnson**, **Evets David** og **Jordan Waeles**, som
> tok initiativet til det; hele historien står i [`MIGRATION.md`](MIGRATION.md).

## Hva den gjør

Henter Volkswagen-konsernbilen din inn i [Home Assistant](https://www.home-assistant.io):
batteri- og ladestatus, rekkevidde, kilometerstand, klima, dører og vinduer,
GPS-posisjon og mer, for Volkswagen, Audi, Škoda, SEAT, CUPRA, Porsche, Bentley
og de nordamerikanske VW- og Audi-kontoene, fra én enkelt konfigurasjonsoppføring.

Fjernkommandoer som lås, klima og ladestyring finnes **der merkets backend
fortsatt tillater dem**, og det er ulikt fra merke til merke og fra modell til
modell. Statustabellen i den engelske README-en forteller nøyaktig hvilket merke
som kan hva. Sjekk den før du stoler på en kommando.

Den trenger **ingen tillegg, broker eller mellomvarecontainer**, og den kjører
side om side med [evcc](https://evcc.io).

## Installasjon

1. Åpne **HACS** i Home Assistant.
2. Søk etter **VW Group Connect** og installer den.
3. Start Home Assistant på nytt.
4. Gå til **Settings → Devices & Services → Add Integration → VW Group Connect**
   og følg påloggingsforløpet.

Minimumsversjonen av Home Assistant er den som vises i merket ovenfor. Den leses
fra dette repositoriet og er det samme kravet som HACS håndhever når du
installerer.

## Volkswagen EU: det er ikke nok å logge inn

For Volkswagen EU-biler begynner data først å strømme når **du** har slått på
datadeling i Volkswagens egen portal. Hvis bilen vises uten data, er dette nesten
alltid årsaken, snarere enn feil passord: åpne VW-dataportalen én gang, fullfør
eventuelle engangsspørsmål der (vilkår, samtykke, onboarding) og sett **bruk av
ikke-personlige data** til innvilget. Etter det kan det fortsatt ta til bilens
neste kjøretur eller oppvåkning før verdiene dukker opp.

Den fullstendige gjennomgangen står i den [engelske README-en](README.md).

## Hjelp og rapportering av problemer

- Spørsmål og hjelp med oppsett → [GitHub Discussions](https://github.com/its-me-prash/vwgroup-connect-ha/discussions)
- En feil eller et ukjent API-felt → [opprett et issue](https://github.com/its-me-prash/vwgroup-connect-ha/issues/new/choose).
  Den innebygde **Vehicle Data Scout** fyller ut det meste av rapporten for deg.
- En sikkerhetssårbarhet → ikke opprett et offentlig issue, bruk
  [GitHub Security Advisories](https://github.com/its-me-prash/vwgroup-connect-ha/security/advisories/new).

Rapporter og svar på ditt eget språk er velkomne. Issue-malene er på engelsk, men
du trenger ikke å skrive på engelsk.

## Støtt dette prosjektet

Dette er et enmannsprosjekt, og hver endring Volkswagen gjør i backend betyr
dagevis med arbeid for å finne en fungerende vei igjen. Hvis det er verdt noe for
deg, kan du støtte det videre vedlikeholdet gjennom
[GitHub Sponsors](https://github.com/sponsors/its-me-prash). Takk.

## Lisens

[GNU AGPL v3.0-or-later](LICENSE). Kreditering og vilkår for navn og varemerke
ved bruk eller fork: se [`ATTRIBUTION.md`](ATTRIBUTION.md).
