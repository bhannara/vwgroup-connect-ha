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

> **Tämä sivu on lyhyt yhteenveto.** [Englanninkielinen README](README.md) on
> ensisijainen lähde, ja sitä pidetään ajan tasalla. Käännetyt sivut olivat
> aiemmin täydellisiä kopioita ja jäivät huomaamatta kuukausia jälkeen, joten ne
> pidetään nyt tarkoituksella lyhyinä. Automerkkikohtaisen tilataulukon, tunnetut
> rajoitukset, kaikki asetukset ja jokaisen palvelukutsun löydät
> englanninkieliseltä sivulta.

> 📛 Aiemmin julkaistu nimellä **`vag-connect-ha`**. Entiteetit, palvelukutsut
> (mukaan lukien pääsiäismuna `vag_connect.show_vag`), automaatiot ja
> HACS-asennus pysyvät kaikki ennallaan. Vain näyttönimi on muuttunut. Kiitos aloitteesta:
> **Si Gregory**, **Ben Johnson**, **Evets David** ja **Jordan Waeles**.
> Koko tarina on tiedostossa [`MIGRATION.md`](MIGRATION.md).

## Mitä se tekee

Tuo Volkswagen-konsernin autosi järjestelmään
[Home Assistant](https://www.home-assistant.io): akun ja latauksen tila,
toimintamatka, matkamittari, ilmastointi, ovet ja ikkunat, GPS-sijainti ja paljon
muuta — automerkeille Volkswagen, Audi, Škoda, SEAT, CUPRA, Porsche ja Bentley
sekä Pohjois-Amerikan VW- ja Audi-tileille, yhdellä määrityksellä.

Etäkomennot, kuten lukitus sekä ilmastoinnin ja latauksen ohjaus, ovat käytössä
**vain siellä, missä automerkin taustajärjestelmä ne yhä sallii**, ja tämä vaihtelee
automerkeittäin ja malleittain. Englanninkielisen README-tiedoston tilataulukosta
näet tarkasti, mikä automerkki osaa mitä — tarkista se, ennen kuin luotat
johonkin komentoon.

Se ei tarvitse **lisäosaa, välittäjää eikä välikerroskonttia**, ja se toimii
rinnakkain [evcc](https://evcc.io)-järjestelmän kanssa.

## Asennus

1. Avaa Home Assistantissa **HACS**.
2. Hae **VW Group Connect** ja asenna se.
3. Käynnistä Home Assistant uudelleen.
4. Siirry kohtaan **Asetukset → Laitteet ja palvelut → Lisää integraatio → VW Group Connect**
   ja seuraa kirjautumisen ohjeita.

Pienin tuettu Home Assistant -versio on ilmoitettu yllä olevassa kuvakkeessa. Se
luetaan tästä repositoriosta, ja se on sama vaatimus, jonka HACS tarkistaa
asennuksen yhteydessä.

## Volkswagen EU: pelkkä kirjautuminen ei riitä

EU:n Volkswagen-autoissa tiedot alkavat virrata vasta, kun **sinä itse** olet
ottanut tiedonjaon käyttöön Volkswagenin omassa portaalissa. Jos auto näkyy ilman
tietoja, syy on lähes aina tämä eikä väärä salasana: avaa VW:n tietoportaali
kerran, suorita siellä mahdollinen kertaluonteinen kehote (ehdot, suostumus,
käyttöönotto) ja aseta **ei-henkilötietojen käyttö** tilaan myönnetty. Sen
jälkeenkin arvojen ilmestymiseen voi mennä auton seuraavaan ajoon tai
heräämiseen asti.

Täydellinen ohje löytyy [englanninkielisestä README-tiedostosta](README.md).

## Apua ja ongelmien ilmoittaminen

- Kysymykset ja asennusapu → [GitHub Discussions](https://github.com/its-me-prash/vwgroup-connect-ha/discussions)
- Virhe tai tuntematon API-kenttä → [avaa ongelmailmoitus](https://github.com/its-me-prash/vwgroup-connect-ha/issues/new/choose).
  Sisäänrakennettu **Vehicle Data Scout** täyttää suurimman osan ilmoituksesta
  puolestasi.
- Tietoturvahaavoittuvuus → älä avaa julkista ongelmailmoitusta, vaan käytä
  [GitHub Security Advisories](https://github.com/its-me-prash/vwgroup-connect-ha/security/advisories/new) -palvelua.

Ilmoitukset ja vastaukset omalla kielelläsi ovat tervetulleita — ongelmailmoitusten
pohjat ovat englanniksi, mutta sinun ei tarvitse kirjoittaa englanniksi.

## Tue tätä projektia

Tämä on yhden ihmisen projekti, ja jokainen Volkswagenin taustajärjestelmään
tekemä muutos tarkoittaa päiväkausien työtä, ennen kuin toimiva reitti löytyy
uudelleen. Jos tästä on sinulle hyötyä, voit tukea jatkuvaa ylläpitoa
[GitHub Sponsors](https://github.com/sponsors/its-me-prash) -palvelun kautta.
Kiitos.

## Lisenssi

[GNU AGPL v3.0-or-later](LICENSE). Tekijän mainitsemista sekä nimeä ja
tavaramerkkiä koskevat ehdot käytön tai haarauttamisen yhteydessä: katso
[`ATTRIBUTION.md`](ATTRIBUTION.md).
