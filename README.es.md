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

> **Esta página es un resumen breve.** El [README en inglés](README.md) es la
> versión de referencia y se mantiene al día; las páginas traducidas eran antes
> copias completas y se fueron quedando atrás sin que nadie lo notara, por eso
> ahora se mantienen cortas a propósito. Para la tabla de estado por marca, las
> limitaciones conocidas, todas las opciones y todas las llamadas a servicios,
> consulta la página en inglés.

> 📛 Publicado anteriormente como **`vag-connect-ha`**. Las entidades, las llamadas a servicios
> (incluido el huevo de Pascua `vag_connect.show_vag`), las automatizaciones y la instalación
> de HACS siguen exactamente igual; solo ha cambiado el nombre visible. Gracias a
> **Si Gregory**, **Ben Johnson**, **Evets David** y **Jordan Waeles**, que lo
> impulsaron; la historia completa está en [`MIGRATION.md`](MIGRATION.md).

## Qué hace

Lleva tu coche del Grupo Volkswagen a [Home Assistant](https://www.home-assistant.io):
estado de la batería y de la carga, autonomía, cuentakilómetros, climatización,
puertas y ventanillas, posición GPS y más, para Volkswagen, Audi, Škoda, SEAT,
CUPRA, Porsche, Bentley y las cuentas norteamericanas de VW y Audi, todo desde
una única entrada de configuración.

Los comandos remotos, como el cierre centralizado, la climatización y el control
de la carga, existen **allí donde el backend de la marca todavía los permite**, lo
cual varía según la marca y el modelo. La tabla de estado del README en inglés
indica con exactitud qué marca puede hacer qué: consúltala antes de contar con un
comando.

No necesita **ningún add-on, broker ni contenedor de middleware**, y funciona
junto con [evcc](https://evcc.io).

## Instalación

1. Abre **HACS** en Home Assistant.
2. Busca **VW Group Connect** e instálalo.
3. Reinicia Home Assistant.
4. Ve a **Ajustes → Dispositivos y servicios → Añadir integración → VW Group Connect**
   y sigue el proceso de inicio de sesión.

La versión mínima de Home Assistant es la que indica la insignia de arriba; se lee
de este repositorio y es el mismo requisito que HACS aplica al instalar.

## Volkswagen UE: iniciar sesión no basta

En los coches Volkswagen de la UE, los datos solo empiezan a llegar cuando **tú**
has activado el uso compartido de datos en el portal propio de Volkswagen. Si el
coche aparece sin datos, casi siempre es esta la razón y no una contraseña
incorrecta: abre una vez el portal de datos de VW, completa allí cualquier aviso
que aparezca una sola vez (condiciones, consentimiento, alta inicial) y pon el
**uso de datos no personales** en concedido. Después, todavía puede pasar hasta
el siguiente trayecto o el siguiente despertar del coche antes de que aparezcan
valores.

La guía completa paso a paso está en el [README en inglés](README.md).

## Ayuda y notificación de problemas

- Preguntas y ayuda con la configuración → [GitHub Discussions](https://github.com/its-me-prash/vwgroup-connect-ha/discussions)
- Un error o un campo desconocido de la API → [abre una incidencia](https://github.com/its-me-prash/vwgroup-connect-ha/issues/new/choose).
  El **Vehicle Data Scout** integrado rellena de antemano la mayor parte del
  informe por ti.
- Una vulnerabilidad de seguridad → por favor, no abras una incidencia pública;
  usa [GitHub Security Advisories](https://github.com/its-me-prash/vwgroup-connect-ha/security/advisories/new).

Los informes y las respuestas en tu propio idioma son bienvenidos: las plantillas
de incidencias están en inglés, pero tú no tienes por qué escribir en inglés.

## Apoya este proyecto

Este es un proyecto de una sola persona, y cada cambio de backend que hace
Volkswagen supone días de trabajo para volver a encontrar un camino que funcione.
Si te resulta valioso, puedes apoyar su mantenimiento continuo a través de
[GitHub Sponsors](https://github.com/sponsors/its-me-prash). Gracias.

## Licencia

[GNU AGPL v3.0-or-later](LICENSE). Atribución y condiciones de nombre y marca al
usarlo o hacer un fork: consulta [`ATTRIBUTION.md`](ATTRIBUTION.md).
