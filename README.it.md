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

> **Questa pagina è un breve riepilogo.** Il [README inglese](README.md) è
> quello di riferimento e viene mantenuto aggiornato; le pagine tradotte erano
> in origine copie complete e sono rimaste indietro di mesi senza che nessuno se
> ne accorgesse, perciò ora sono volutamente brevi. Per la tabella di stato
> marca per marca, le limitazioni note, ogni opzione e ogni chiamata di
> servizio, leggi la pagina inglese.

> 📛 In precedenza pubblicato come **`vag-connect-ha`**. Entità, chiamate di servizio
> (compreso l'uovo di Pasqua `vag_connect.show_vag`), automazioni e l'installazione
> tramite HACS restano tutte invariate: è cambiato solo il nome visualizzato. Grazie a
> **Si Gregory**, **Ben Johnson**, **Evets David** e **Jordan Waeles**, che hanno
> dato lo spunto; la storia completa è in [`MIGRATION.md`](MIGRATION.md).

## Cosa fa

Porta la tua auto del Gruppo Volkswagen in [Home Assistant](https://www.home-assistant.io):
stato della batteria e della ricarica, autonomia, contachilometri,
climatizzazione, porte e finestrini, posizione GPS e altro ancora, per
Volkswagen, Audi, Škoda, SEAT, CUPRA, Porsche, Bentley e per gli account
nordamericani di VW e Audi, da un'unica voce di configurazione.

I comandi remoti come blocco, climatizzazione e controllo della ricarica
esistono **dove il backend della marca li consente ancora**, e questo cambia da
marca a marca e da modello a modello. La tabella di stato nel README inglese
indica con precisione quale marca può fare cosa: controllala prima di fare
affidamento su un comando.

Non richiede **nessun add-on, broker o container middleware** e funziona
insieme a [evcc](https://evcc.io).

## Installazione

1. Apri **HACS** in Home Assistant.
2. Cerca **VW Group Connect** e installalo.
3. Riavvia Home Assistant.
4. Vai su **Impostazioni → Dispositivi e servizi → Aggiungi integrazione → VW Group Connect**
   e segui la procedura di accesso.

La versione minima di Home Assistant è quella indicata dal badge qui sopra:
viene letta da questo repository ed è lo stesso requisito che HACS applica
quando installi.

## Volkswagen EU: accedere non basta

Per le auto Volkswagen EU, i dati iniziano ad arrivare solo dopo che **tu** hai
attivato la condivisione dei dati sul portale di Volkswagen. Se l'auto compare
senza dati, quasi sempre il motivo è questo e non una password sbagliata: apri
una volta il portale dati VW, completa ogni richiesta una tantum (termini,
consenso, onboarding) e imposta **use of non-personal data** su concesso. Dopo
di che i valori possono comunque comparire solo alla successiva guida o al
successivo risveglio dell'auto.

La guida completa si trova nel [README inglese](README.md).

## Aiuto e segnalazione di problemi

- Domande e aiuto per la configurazione → [GitHub Discussions](https://github.com/its-me-prash/vwgroup-connect-ha/discussions)
- Un bug o un campo API sconosciuto → [apri una issue](https://github.com/its-me-prash/vwgroup-connect-ha/issues/new/choose).
  Il **Vehicle Data Scout** integrato precompila per te la maggior parte della
  segnalazione.
- Una vulnerabilità di sicurezza → non aprire una issue pubblica, usa
  [GitHub Security Advisories](https://github.com/its-me-prash/vwgroup-connect-ha/security/advisories/new).

Segnalazioni e risposte nella tua lingua sono benvenute: i modelli di issue sono
in inglese, ma non sei obbligato a scrivere in inglese.

## Sostieni questo progetto

Questo è un progetto portato avanti da una sola persona, e ogni modifica al
backend di Volkswagen significa giorni di lavoro per trovare di nuovo una strada
che funzioni. Se per te ha valore, puoi sostenerne la manutenzione continua
tramite [GitHub Sponsors](https://github.com/sponsors/its-me-prash). Grazie.

## Licenza

[GNU AGPL v3.0-or-later](LICENSE). Per l'attribuzione e i termini relativi a
nome e marchio in caso di uso o fork: vedi [`ATTRIBUTION.md`](ATTRIBUTION.md).
