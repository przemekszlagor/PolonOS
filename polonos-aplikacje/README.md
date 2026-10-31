# PolonOS Aplikacje

**PolonOS Aplikacje** to prosty program graficzny do zarządzania oprogramowaniem i aktualizacjami w systemie **PolonOS** (oraz innych systemach opartych na Debianie). Został stworzony po to, aby użytkownik mógł zaktualizować system lub zainstalować programy kilkoma kliknięciami myszki, bez używania terminala.

---

## Do czego służy ten program?

Program podzielony jest na 3 czytelne zakładki:

1. **Aktualizacje systemowe**
   - Sprawdza dostępne aktualizacje pakietów systemowych (**APT**) oraz zainstalowanych aplikacji **Flatpak**.
   - Pokazuje łączną liczbę pakietów do zaktualizowania oraz rozmiar danych do pobrania.
   - Przycisk **„Aktualizuj system”** instaluje wszystkie aktualizacje za jednym razem.

2. **Menedżer programów**
   - Zawiera listę najpopularniejszych programów podzielonych na kategorie (Biuro, Internet, Grafika, Multimedia, Narzędzia, Edukacja, Gry, Programowanie) z opisami w języku polskim.
   - Pozwala wyszukać dowolny pakiet z repozytorium APT.
   - Umożliwia zaznaczenie wielu programów jednocześnie (checkboxy) i zainstalowanie lub odinstalowanie ich jednym przyciskiem.
   - Rozpoznaje programy zainstalowane zarówno przez APT, jak i Flatpak.

3. **Aktualizacja PolonOS**
   - Sprawdza, czy pojawiła się nowsza wersja całego systemu PolonOS (np. przejście z wersji 1.3 na 1.4).
   - Pozwala zaktualizować cały system jednym kliknięciem, bez konieczności instalowania go od nowa z płyty/pendrive'a ISO.
   - Przypomina o wykonaniu kopii zapasowej w programie **Timeshift** i pozwala go szybko otworzyć.

---

## Dodatkowe funkcje

- **Instalator plików `.deb`** — po powiązaniu programu z plikami `.deb` (w oknie *Ustawienia*), dwukrotne kliknięcie dowolnego pobranego pliku `.deb` otwiera okno instalatora i instaluje program wraz z wymaganymi zależnościami.
- **Ikona w zasobniku systemowym (obok zegara)** — program może uruchamiać się wraz ze startem systemu, sprawdzać w tle co 6 godzin dostępność aktualizacji i sygnalizować nowe aktualizacje czerwoną kropką z wykrzyknikiem.

---

## Jak zainstalować program?

### Sposób 1: Z gotowego pliku `.deb` (najprostszy)
Pobierz plik `polonos-aplikacje.deb` (lub `polonos-aplikacje_1.4.0_amd64.deb`) i zainstaluj go poleceniem:
```bash
sudo apt install ./polonos-aplikacje.deb
```

### Sposób 2: Samodzielne zbudowanie paczki `.deb` ze źródeł
W katalogu projektu uruchom skrypt:
```bash
chmod +x build_deb.sh
./build_deb.sh
```
Skrypt utworzy gotowy plik `polonos-aplikacje_1.4.0_amd64.deb`.

---

## Struktura plików projektu

- `src/main.py` — plik startowy uruchamiający aplikację.
- `src/ui/main_window.py` — główne okno programu, pasek zakładek, obsługa ikony w zasobniku systemowym i autostartu.
- `src/ui/tab_updates.py` — pierwsza zakładka (aktualizacje pakietów APT i Flatpak).
- `src/ui/tab_store.py` — druga zakładka (wyszukiwarka, lista programów, instalacja i deinstalacja).
- `src/ui/tab_upgrade.py` — trzecia zakładka (aktualizacja wydania systemu PolonOS).
- `src/ui/deb_installer_dialog.py` — okno *Ustawienia* oraz okno instalatora pojedynczych plików `.deb`.
- `src/ui/about_dialog.py` — okno *O programie*.
- `src/ui/styles.py` i `src/ui/assets_helper.py` — wygląd ciemnego motywu PolonOS oraz obsługa ikon.
- `src/backend/apt_manager.py` — obsługa menedżera pakietów APT, bazy dpkg oraz Flatpak.
- `src/backend/dist_upgrader.py` — sprawdzanie i pobieranie nowych wersji systemu PolonOS.
- `build_deb.sh` — skrypt budujący instalator `.deb`.

---

## Licencja i podziękowania

Program jest udostępniany na wolnej licencji **GNU General Public License v2.0 (GPL-2.0)** i czerpie inspirację z klasycznego menedżera pakietów **Synaptic**.

- **Strona projektu:** [https://polonos.org](https://polonos.org)
- **Kontakt:** `kontakt@polonos.org`
