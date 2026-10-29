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

> **Ta strona to krótkie podsumowanie.** [Angielski plik README](README.md) jest
> wiążący i na bieżąco aktualizowany; strony w innych językach były wcześniej
> pełnymi kopiami i po cichu zostawały o całe miesiące w tyle, dlatego celowo są
> teraz krótkie. Tabelę stanu poszczególnych marek, znane ograniczenia, wszystkie
> opcje i każde wywołanie usługi znajdziesz na stronie angielskiej.

> 📛 Wcześniej opublikowane jako **`vag-connect-ha`**. Encje, wywołania usług
> (w tym pisanka `vag_connect.show_vag`), automatyzacje i instalacja przez
> HACS pozostają bez zmian. Zmieniła się tylko wyświetlana nazwa. Podziękowania
> dla osób, które dały impuls: **Si Gregory**, **Ben Johnson**, **Evets David** i **Jordan Waeles**.
> Pełna historia znajduje się w [`MIGRATION.md`](MIGRATION.md).

## Co to robi

Wprowadza Twój samochód z koncernu Volkswagen Group do [Home Assistant](https://www.home-assistant.io):
stan akumulatora i ładowania, zasięg, przebieg, klimatyzację, drzwi i okna, pozycję GPS
i więcej — dla marek Volkswagen, Audi, Škoda, SEAT, CUPRA, Porsche, Bentley
oraz północnoamerykańskich kont VW i Audi, z jednego wpisu konfiguracji.

Polecenia zdalne, takie jak blokowanie zamków, klimatyzacja i sterowanie ładowaniem,
istnieją **tam, gdzie backend danej marki nadal na to pozwala**, a to różni się
w zależności od marki i modelu. Tabela stanu w angielskim README dokładnie podaje,
która marka co potrafi — sprawdź ją, zanim zaczniesz polegać na jakimś poleceniu.

Nie wymaga **żadnego dodatku, brokera ani kontenera pośredniczącego** i działa
równolegle z [evcc](https://evcc.io).

## Instalacja

1. Otwórz **HACS** w Home Assistant.
2. Wyszukaj **VW Group Connect** i zainstaluj go.
3. Uruchom ponownie Home Assistant.
4. Przejdź do **Ustawienia → Urządzenia i usługi → Dodaj integrację → VW Group Connect**
   i postępuj zgodnie z procesem logowania.

Minimalną wersję Home Assistant podaje powyższa plakietka; jest odczytywana z tego
repozytorium i jest tym samym wymaganiem, które HACS egzekwuje podczas instalacji.

## Volkswagen EU: samo zalogowanie nie wystarcza

W samochodach Volkswagen EU dane zaczynają płynąć dopiero wtedy, gdy **Ty** włączysz
udostępnianie danych na własnym portalu firmy Volkswagen. Jeśli samochód pojawia się
bez danych, prawie zawsze jest to przyczyną, a nie błędne hasło: otwórz raz portal
danych VW, zakończ tam każdy jednorazowy monit (regulamin, zgoda, wdrożenie) i ustaw
**korzystanie z danych nieosobowych** jako udzielone. Potem może jeszcze potrwać do
następnej jazdy lub wybudzenia samochodu, zanim pojawią się wartości.

Pełną instrukcję znajdziesz w [angielskim README](README.md).

## Pomoc i zgłaszanie problemów

- Pytania i pomoc przy konfiguracji → [GitHub Discussions](https://github.com/its-me-prash/vwgroup-connect-ha/discussions)
- Błąd lub nieznane pole API → [otwórz zgłoszenie](https://github.com/its-me-prash/vwgroup-connect-ha/issues/new/choose).
  Wbudowany **Vehicle Data Scout** wypełnia za Ciebie większość zgłoszenia.
- Luka bezpieczeństwa → nie otwieraj publicznego zgłoszenia; użyj
  [GitHub Security Advisories](https://github.com/its-me-prash/vwgroup-connect-ha/security/advisories/new).

Zgłoszenia i odpowiedzi w Twoim własnym języku są mile widziane — szablony zgłoszeń
są po angielsku, ale Ty nie musisz pisać po angielsku.

## Wesprzyj projekt

To projekt prowadzony przez jedną osobę, a każda zmiana backendu po stronie Volkswagena
oznacza dni pracy, zanim uda się znów znaleźć działającą ścieżkę. Jeśli ma on dla Ciebie
wartość, możesz wesprzeć dalsze utrzymanie przez
[GitHub Sponsors](https://github.com/sponsors/its-me-prash). Dziękuję.

## Licencja

[GNU AGPL v3.0-or-later](LICENSE). Informacje o uznaniu autorstwa oraz warunki dotyczące
nazwy i znaku towarowego przy użyciu lub forku: zob. [`ATTRIBUTION.md`](ATTRIBUTION.md).
