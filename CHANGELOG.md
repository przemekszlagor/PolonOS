# Dziennik Zmian PolonOS (CHANGELOG)
Wszystkie istotne zmiany wprowadzone w dystrybucji PolonOS od wydania wersji **v1.1**.

---

## [Wersja v1.2] – Wydanie Stabilne (2026-07-31)

### Nowe Aplikacje
* **PolonOS Kalendarz**
  - Przemianowano aplikację z "PolonOS Calendar" na "PolonOS Kalendarz" w całym systemie (nazwy folderów, plików `.desktop`, skrótów oraz zmiennych konfiguracyjnych `~/.config/polonos-kalendarz`), aby uniknąć błędów niespójności nazw.
  - Zaktualizowano opis w pakiecie instalacyjnym `.deb` na: *"Prosta i czytelna aplikacja do obsługi Kalendarza Google"*.
  - Dodano nową, systemową aplikację kalendarza napisaną w Pythonie przy użyciu biblioteki PyQt.
  - Implementacja lokalnej bazy danych SQLite (`database.py`) do bezpiecznego przechowywania terminów i zdarzeń offline.
  - Wdrożenie dwukierunkowej, bezpiecznej synchronizacji z Google Calendar API (`google_sync.py`) z domyślnie wbudowanymi kluczami aplikacji.
  - Stworzenie nowoczesnego, ciemnego interfejsu użytkownika w stylu premium (`ui/styles.py`) z przełącznikiem motywów (Red Carbon / Ciemny / Jasny / Systemowy), opcją Autostartu oraz widokami tygodniowymi, miesięcznymi i rocznymi.
  - Integracja z zasobnikiem systemowym (Systray) oraz wyskakującymi powiadomieniami o nadchodzących wydarzeniach (`ui/systray_popup.py`).
  - Przygotowanie automatycznego skryptu budującego pakiet instalacyjny Debian (`build_deb.sh`) i wdrożenie gotowej paczki `polonos-kalendarz.deb`.

### Obsługa Drukowania (CUPS & Polkit)
* **Automatyzacja i konfiguracja obsługi drukarek**
  - Stworzono skrypt `setup-cups-polonos.sh` automatyzujący kompletną konfigurację usług druku zarówno bezpośrednio w systemie, jak i w chroocie Cubic ISO.
  - Wdrożono reguły Polkit (`rules.d/60-printing.rules`) umożliwiające bezproblemowe dodawanie, usuwanie i modyfikowanie drukarek bez konieczności wpisywania hasła administratora dla użytkowników z grup `lpadmin` oraz `sudo`.
  - Skonfigurowano `/etc/adduser.conf`, aby automatycznie przypisywać nowo zakładane konta użytkowników do systemowej grupy `lpadmin` zarządzającej drukarkami.
  - Dodano pełen pakiet oprogramowania obsługi druku: `cups`, `cups-daemon`, `cups-filters`, `cups-pk-helper`, `printer-driver-all` (kompletny zestaw sterowników), `hplip` (dedykowana obsługa urządzeń HP), `avahi-daemon` (automatyczne sieciowe wykrywanie urządzeń), `ipp-usb` (obsługa nowoczesnych drukarek IPP-over-USB) oraz interfejsy zarządzania (`print-manager` i `system-config-printer`).
  - Włączono domyślne usługi systemd: `cups`, `cups.socket`, `avahi-daemon` i `ipp-usb`.

### Unifikacja Kolorystyczna (Styl Premium Red Carbon)
* **Spójny wygląd aplikacji systemowych**
  - Przeniesiono kolorystykę aplikacji `polonos-welcome` oraz `PolonOS Net Monitor` na spójny motyw ciemny (Red Carbon), bazując na oficjalnym ciemnym motywie graficznym programu `PolonOS Kalendarz`.
  - W `polonos-welcome`: Zaktualizowano globalne style QSS, okna dialogowe (`ProgressDialog`, `NvidiaDriverDialog`) oraz systemową paletę kolorów aplikacji (`QPalette`). Wprowadzono antracytowe/grafitowe tła `#161616` / `#242424` / `#1e1e1e` oraz karminowy akcent `#c22e45`.
  - W `PolonOS Net Monitor`: Zmodyfikowano zmienne w pliku `style.css` (`--bg-dark`, `--card-bg`, `--color-down`, `--border-accent`), zastępując stary motyw fioletowy schematem antracytowo-karminowym. Zaktualizowano również zasoby graficzne logo na oficjalną systemową wersję PolonOS oraz zaimplementowano wczytywanie ikony okna w kodzie aplikacji.

### Usprawnienia Asystenta Instalacji Sterowników (`polonos-welcome`)
* **Poprawki dla architektur NVIDIA Pascal / Maxwell**
  - **Dopasowanie do architektury**: Dodano automatyczne sugerowanie i zaznaczanie **Wersji stabilnej (550.x)** dla starszych kart graficznych NVIDIA Pascal (seria GTX 10xx, np. GTX 1050 Ti Mobile) i Maxwell (seria GTX 9xx).
  - **Rozwiązanie problemu wymuszania wersji deweloperskiej (610.x)**: Instalator automatycznie oczyszcza system z pozostałości repozytoriów CUDA i NVIDIA (usuwa pliki `cuda*.list` oraz `nvidia*.list` z `/etc/apt/sources.list.d/` oraz odinstalowuje pakiet `cuda-keyring`) przed przystąpieniem do instalacji wersji stabilnej. Zapobiega to konfliktom i błędom komunikacji ze starszymi GPU.
  - **Uproszczenie interfejsu wyboru**: Usunięto wadliwą i niedziałającą w practical opcję `legacy_580`. Zamiast tego zaoferowano dwie czytelne opcje:
    1. *Wersja stabilna (z repozytoriów dystrybucji, 550.x)* – zalecana dla starszych kart oraz dla maksymalnej stabilności.
    2. *Najnowsza wersja deweloperska (z repozytorium NVIDIA CUDA, obecnie 610.x)* – zalecana dla nowoczesnych kart RTX i obliczeń AI.
  - **Kompletny zestaw sterowników**: Skrypt instalatora został rozbudowany o jawną instalację brakujących pakietów, w tym nagłówków jądra (`linux-headers-amd64`), oprogramowania firmware (`firmware-misc-nonfree`), jądra dkms (`nvidia-kernel-dkms`) oraz narzędzi `nvidia-smi` i `nvidia-settings`.
  - **Poprawa rozmiaru okna**: Zwiększono szerokość okna dialogowego wyboru sterownika (`NvidiaDriverDialog`) z 500 do 650 pikseli, aby zapobiec ucinaniu długich nazw wersji sterowników (np. przy pobieraniu wersji z repozytorium CUDA online).
  - **Monit o restarcie komputera**: Po pomyślnej instalacji zalecanych sterowników asystent wyświetla dedykowane okno informacyjne (modalny `QMessageBox`) o potrzebie restartu z przyciskiem "ROZUMIEM", po czym sterowanie powraca do użytkownika (brak automatycznego restartu).
  - **Automatyczne czyszczenie pakietów (autoremove)**: Skrypt aktualizacji systemowych uruchamiany z poziomu asystenta powitalnego został rozbudowany o automatyczne wywoływanie `apt-get autoremove -y`. Dzięki temu po instalacji aktualizacji system samoczynnie oczyszcza się ze zbędnych, osieroconych pakietów i zależności, co eliminuje konieczność ręcznego sprzątania systemu w konsoli.

### Usprawnienia Menedżera Oprogramowania (`polonos-welcome`)
* **Rozszerzenie oferty i poprawki zgodności**
  - **Przeglądarka Opera**: Dodano przeglądarkę internetową Opera (jako pakiet Flatpak z Flathub) do kategorii "Internet".
  - **Instalator Wine**: Wdrożono niezawodną instalację pakietów Wine (`winehq-staging` || `winehq-stable` || `wine`) wraz z automatyczną aktywacją architektury 32-bitowej (`i386`). Rozwiązuje to błędy pakietów wirtualnych w Debianie Testing (Trixie), zapewniając bezproblemową instalację i działanie warstwy kompatybilności z aplikacjami Windows.
  - **Zintegrowane zasoby ikon**: Pobrano i zintegrowano dedykowane ikony wektorowe (SVG/PNG) dla Opery, Steam, Heroic oraz Wine. Zaimplementowano w asystencie powitalnym mechanizm lokalnego fallbacku poszukujący plików ikon w `/usr/share/pixmaps` oraz w katalogu deweloperskim `icons/`, eliminując wyświetlanie generycznych awatarów tekstowych.
  - **Instalator SageMath (Conda)**: Wprowadzono opcjonalną, w pełni zautomatyzowaną instalację zaawansowanego oprogramowania matematycznego **SageMath** w kategorii "Edukacja & Narzędzia". Ze względu na usunięcie pakietu z oficjalnych repozytoriów Debiana testowego, instalacja odbywa się w izolowanym, bezpiecznym środowisku **Conda**, co chroni zależności systemowe przed konfliktami, a na koniec tworzy skróty w menu aplikacji do interfejsu Jupyter Notebook i konsoli tekstowej.
  - **Domyślna aktywacja Flathub**: Repozytorium **Flathub** zostało wdrożone i włączone jako standardowe źródło pakietów na poziomie systemowym w chroocie dystrybucji. Zapewnia to użytkownikowi natychmiastowy i bezproblemowy dostęp do bazy tysięcy aplikacji Flatpak w graficznym menedżerze oprogramowania (np. Discover lub GNOME Software) bezpośrednio po instalacji systemu.
  - **Reorganizacja kategorii oprogramowania**: Rozdzielono sekcję „Edukacja & Narzędzia" na dwie osobne: **Edukacja** (SageMath, Kate, Pakiet Edukacyjny KDE Edu) oraz **Narzędzia** (NVIDIA CUDA Toolkit, Wine). Przeniesiono Wine z kategorii „Rozrywka" do „Narzędzia".

### Poprawki Sterowników i Jądra Systemowego
* **Stabilność kart sieciowych Realtek (rtw88)**
  - **Eliminacja błędów startu Wi-Fi**: Dodano fabryczną konfigurację systemową w `/etc/modprobe.d/rtw88.conf` wyłączającą głębokie uśpienie (`disable_lps_deep=y`) oraz zarządzanie energią magistrali PCIe (`disable_aspm=y`) dla sterownika Realtek `rtw88`. Rozwiązuje to błędy zawieszania modułu `rtw88_8822ce` przy starcie systemu na fizycznym sprzęcie.
* **Naprawa parametrów startowych GRUB**
  - **Eliminacja wpisu 'noefi'**: Usunięto wadliwą i błędną opcję rozruchu jądra `noefi` z `/etc/default/grub`, która blokowała jądru dostęp do zmiennych EFI i uniemożliwiała poprawne montowanie `efivars` w zainstalowanym systemie.
  - **Uporządkowanie logów startowych**: Zastąpiono zbędną opcję `splash` (PolonOS nie korzysta z ekranów Plymouth) flagą `loglevel=3` w celu zachowania cichego i czystego rozruchu.
* **Uprawnienia magistrali i2c**
  - **Rozwiązanie błędów startowych i2c**: Poprawiono regułę udev w `/usr/lib/udev/rules.d/60-i2c-tools.rules` zmieniając maskę uprawnień na `MODE="0666"`. Zapobiega to błędom uprawnień dla aplikacji bez uprawnień roota chcących korzystać z magistrali i2c.
* **Uzupełnienie brakujących pakietów systemowych**
  - **Integracja kont i kalendarza**: Zainstalowano brakujący pakiet **`evolution-data-server`** w chroocie dystrybucji, co eliminuje błędy synchronizacji kont online i systemowego kalendarza pulpitu.
* **Bezpieczny rozruch bez shim (Secure Boot)**
  - **Eliminacja błędów Ventoy na maszynach Dell**: Odinstalowano z chroota pakiety `shim-signed` oraz `grub-efi-amd64-signed` na rzecz standardowego, stabilnego `grub-efi-amd64`. Zapobiega to rejestrowaniu nieprawidłowych wpisów rozruchu z shim przy instalacjach z nośników Ventoy (które emulują Secure Boot w locie) na sprzęcie, gdzie Secure Boot jest wyłączony.
* **Polityka bezpieczeństwa haseł**
  - **Całkowity brak obostrzeń haseł**: Zmodyfikowano plik konfiguracyjny PAM (`/etc/pam.d/common-password`), zastępując moduł `obscure` opcją `minlen=1` w `pam_unix.so`. W połączeniu z ustawieniami instalatora Calamares, użytkownik może teraz ustawić dowolnie krótkie i proste hasło (np. jednoliterowe) zarówno podczas instalacji, jak i przy zmianie hasła w działającym systemie.
* **Wsparcie dla kart graficznych NVIDIA**
  - **Opcjonalny instalator CUDA**: Do menu „Edukacja & Narzędzia” w asystencie `polonos-welcome` dodano możliwość opcjonalnej instalacji pakietu `nvidia-cuda-toolkit` (wymaganego do sprzętowego kodowania NVENC w OBS lub renderowania GPU). Pozwala to zaoszczędzić ok. 7 GB na obrazie ISO dla użytkowników bez kart NVIDIA.
  - **Wbudowane wsparcie OptiX**: Zainstalowano na stałe pakiet `libnvoptix1` w chroocie dystrybucji, co zapewnia natychmiastowe działanie akceleracji renderowania OPTIX na kartach RTX (np. w programie Blender) bezpośrednio po wgraniu sterowników graficznych.
  - **Ostrzeżenie Nouveau na Pulpicie**: Utworzono plik informacyjny `NVIDIA_PRZECZYTAJ_MNIE.txt` na Pulpicie w wersji Live oraz po instalacji. Ostrzega on o niestabilności otwartych sterowników Nouveau w sesji Wayland i instruuje o przełączeniu sesji Live na X11, a po instalacji o wgraniu sterowników zamkniętych.

### Usprawnienia Monitora Sieci (`PolonOS Net Monitor`)
* **Stabilniejsze wykrywanie połączenia**
  - Zaimplementowano priorytetowe odpytywanie NetworkManagera za pomocą polecenia `nmcli device` w celu szybkiego i precyzyjnego znalezienia fizycznie połączonego interfejsu sieciowego (Wi-Fi lub Ethernet).
  - Zapobiega to sytuacjom, w których monitor wybierał nieaktywny interfejs Ethernet (np. ze względu na zgromadzone bajty w `/proc/net/dev` podczas startu) zamiast aktywnego połączenia Wi-Fi.
  - Zachowano dotychczasowe mechanizmy (odczyt `/proc/net/route` i `/proc/net/dev`) jako fallback na wypadek braku lub wyłączenia usługi NetworkManager.
* **Poprawki stabilności komunikacji**
  - Przeniesiono kanał komunikacyjny z Pythona do JavaScript na bezpieczną, pełną transmisję Base64 (`atob()`), co całkowicie rozwiązało błędy parsowania znaków specjalnych i cudzysłowów w nazwach Wi-Fi (SSID).
  - Usunięto błędy asynchronicznego startu wyścigu wątków (`AttributeError` dla zmiennej `was_connected`) oraz błędy lokalnego zakresu importów w wątku pobierania IP (`UnboundLocalError`).
  - Rozwiązano błędy komunikacji z JS poprzez obsłużenie typu `WebKit2.JavascriptResult` za pomocą `message.get_js_value().to_string()`.
  - Wprowadzono pełną kompatybilność camelCase w JS, obsługując dynamicznie zarówno `window.webkit.messageHandlers` jak i `window.webkit.message_handlers`.
  - Dodano 500ms opóźnienie wczytywania (`setTimeout`) przy starcie, pozwalając silnikowi WebKita na prawidłowe zainicjalizowanie i wstrzyknięcie obiektów komunikacyjnych.
  - Wdrożono bezwarunkowe ignorowanie weryfikacji certyfikatów SSL za pomocą `ssl._create_unverified_context()` dla zapytań o publiczne IP oraz dla testów prędkości, eliminując awarie w środowiskach bez zaktualizowanych urzędów certyfikacji (np. Conda).
* **Zintegrowany moduł Speedtest (Test prędkości)**
  - Zaimplementowano asynchroniczny test prędkości pobierania (Download) i wysyłania (Upload) oparty na oficjalnej infrastrukturze Cloudflare (ograniczenie próbki do 10 MB w celu uniknięcia blokad firewalla 403, spersonalizowany User-Agent).
  - Dodano nowoczesny moduł graficzny testu prędkości z dynamicznym paskiem postępu i wynikami, wkomponowany w schemat graficzny **Red Carbon**.

### Konfiguracja instalatora systemowego (Calamares)
* **Automatyczne odblokowanie pełnych repozytoriów w nowym systemie**
  - Zmodyfikowano skrypt pomocniczy `calamares-sources-final` w chroocie dystrybucji, tak aby generowany plik `/etc/apt/sources.list` nowej instalacji automatycznie zawierał sekcje własnościowe (`main contrib non-free non-free-firmware`) dla wszystkich repozytoriów. Zapobiega to potrzebie ręcznej modyfikacji źródeł APT w celu instalacji własnościowych sterowników Wi-Fi, kart graficznych NVIDIA i innych komercyjnych programów zaraz po wgraniu systemu.

---

## [Wersja v1.1] – Wydanie Stabilne

### Nowości i Zmiany
* **Wstępne wsparcie dla nowszego jądra**: Przeniesienie dystrybucji na jądro `7.1.3` oraz bazę pakietów Debian 13 (Testing).
* **Aktualizacje przeglądarki**: Poprawki stabilności i integracji dla przeglądarki internetowej Brave.
* **PolonOS Net Monitor (Wersja v1.1)**
  - Optymalizacja bibliotek WebKit2GTK pod kątem sesji Wayland (zapobieganie błędom renderowania na GPU NVIDIA poprzez wymuszenie flag `WEBKIT_DISABLE_COMPOSITING_MODE` i `WEBKIT_DISABLE_DMABUF_RENDERER`).
  - Wdrożenie pierwszych funkcji monitorowania ruchu sieciowego w czasie rzeczywistym zintegrowanych z interfejsem HTML5.
