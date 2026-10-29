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

> **Cette page est un court résumé.** Le [README anglais](README.md) fait foi et
> est tenu à jour ; les pages traduites étaient auparavant des copies complètes
> et ont discrètement pris des mois de retard, c’est pourquoi elles sont
> désormais volontairement courtes. Pour le tableau d’état marque par marque,
> les limitations connues, chaque option et chaque appel de service, consultez
> la page anglaise.

> 📛 Auparavant publié sous le nom **`vag-connect-ha`**. Les entités, les appels de service
> (y compris l'œuf de Pâques `vag_connect.show_vag`), les automatisations et l'installation
> HACS restent tous inchangés : seul le nom affiché a changé. Merci à
> **Si Gregory**, **Ben Johnson**, **Evets David** et **Jordan Waeles**, qui en sont
> à l'origine ; toute l'histoire se trouve dans [`MIGRATION.md`](MIGRATION.md).

## Ce que fait l’intégration

Intègre votre véhicule du groupe Volkswagen à
[Home Assistant](https://www.home-assistant.io) : état de la batterie et de la
charge, autonomie, compteur kilométrique, climatisation, portes et fenêtres,
position GPS et plus encore, pour Volkswagen, Audi, Škoda, SEAT, CUPRA,
Porsche, Bentley ainsi que les comptes nord-américains de VW et Audi, à partir
d’une seule entrée de configuration.

Les commandes à distance, comme le verrouillage, la climatisation et le
contrôle de la charge, existent **là où le backend de la marque les autorise
encore**, ce qui varie selon la marque et le modèle. Le tableau d’état du README
anglais indique précisément ce que chaque marque peut faire ; consultez-le avant
de vous fier à une commande.

Elle n’exige **aucun module complémentaire, broker ni conteneur middleware**, et
fonctionne aux côtés d’[evcc](https://evcc.io).

## Installation

1. Ouvrez **HACS** dans Home Assistant.
2. Recherchez **VW Group Connect** et installez-le.
3. Redémarrez Home Assistant.
4. Allez dans **Paramètres → Appareils et services → Ajouter une intégration →
   VW Group Connect** et suivez la procédure de connexion.

La version minimale de Home Assistant est celle indiquée par le badge
ci-dessus ; elle est lue depuis ce dépôt et correspond à l’exigence que HACS
applique lors de l’installation.

## Volkswagen UE : se connecter ne suffit pas

Pour les véhicules Volkswagen UE, les données ne commencent à arriver qu’une
fois que **vous** avez activé le partage des données sur le portail propre à
Volkswagen. Si le véhicule apparaît sans données, c’est presque toujours la
raison, plutôt qu’un mauvais mot de passe : ouvrez une fois le portail de
données VW, terminez toute étape unique qui s’y présente (conditions,
consentement, première configuration) et réglez **l’utilisation de données non
personnelles** sur accordée. Ensuite, il peut encore s’écouler jusqu’au
prochain trajet ou réveil du véhicule avant que des valeurs n’apparaissent.

Le guide complet pas à pas se trouve dans le [README anglais](README.md).

## Aide et signalement de problèmes

- Questions et aide à la configuration → [GitHub Discussions](https://github.com/its-me-prash/vwgroup-connect-ha/discussions)
- Un bug ou un champ d’API inconnu → [ouvrir un ticket](https://github.com/its-me-prash/vwgroup-connect-ha/issues/new/choose).
  Le **Vehicle Data Scout** intégré préremplit la majeure partie du signalement
  pour vous.
- Une faille de sécurité → merci de ne pas ouvrir de ticket public ; utilisez
  plutôt les [GitHub Security Advisories](https://github.com/its-me-prash/vwgroup-connect-ha/security/advisories/new).

Les signalements et réponses dans votre propre langue sont les bienvenus : les
modèles de ticket sont en anglais, mais rien ne vous oblige à écrire en anglais.

## Soutenir ce projet

Ce projet est mené par une seule personne, et chaque modification du backend
par Volkswagen représente des jours de travail pour retrouver un chemin qui
fonctionne. Si ce projet a de la valeur pour vous, vous pouvez soutenir sa
maintenance continue via
[GitHub Sponsors](https://github.com/sponsors/its-me-prash). Merci.

## Licence

[GNU AGPL v3.0-or-later](LICENSE). Conditions d’attribution, de nom et de marque
en cas d’utilisation ou de fork : voir [`ATTRIBUTION.md`](ATTRIBUTION.md).
