# Dziennik zmian PolonOS (CHANGELOG)

Wszystkie istotne zmiany wprowadzone w dystrybucji PolonOS.

---

## [Wersja v1.3] – Wydanie Stabilne (2026-08-18)

### Nowy Motyw Graficzny (PolonOS Dark Suite)
* **Zintegrowany autorski motyw PolonOS Dark**
  - Domyślny ciemny motyw graficzny włączony fabrycznie w trybie LIVE ISO oraz w zainstalowanym systemie.
  - Wdrożono spójny schemat kolorów `PolonOSDark`, obramowania okien Aurorae (`PolonOS-Dark`), autorski pakiet ikon `PolonOS-Icons` z dedykowanym logotypem PolonOS, tapetę `PolonOS20.png` oraz ekran powitalny KSplash (`org.polonos.dark`).
  - Natywne logo PolonOS zaimplementowane w menu Start KDE (Kickoff) we wszystkich zestawach ikon i rozdzielczościach.

### Ekran Logowania SDDM (Qt6 / Plasma 6)
* **Zaktualizowany motyw SDDM (`polonos-sddm`)**
  - Wdrożono dedykowaną obsługę silnika Qt6 i środowiska Plasma 6 w pliku `metadata.desktop` (`QtVersion=6`).
  - Utworzono automatyczne dowiązanie `/usr/bin/sddm-greeter` do `/usr/bin/sddm-greeter-qt6`, co wyeliminowało przełączanie się ekranu logowania do awaryjnego białego widoku.

### Typografia Google Roboto
* **Powszechna integracja czcionki Roboto**
  - Zainstalowano fabryczny pakiet `fonts-roboto` w systemie.
  - Wykonano pełną integrację typografii Google Roboto we wszystkich natywnych aplikacjach PySide6 (`PolonOS Welcome`, `PolonOS Kalendarz`, `PolonOS NetMonitor`) oraz w konfiguracji interfejsów GTK i Qt.

### Zaktualizowany Pakiet Aplikacji PolonOS (v1.3)
* **PolonOS Welcome 1.3**
  - Przearanżowano układ okna głównego: ustawiono czcionkę 12px na panelu bocznym, ukryto zbędne paski przewijania, włączono automatyczne wielowierszowe zwijanie etykiet w prawym panelu oraz poprawiono tekstury dialogów.
* **PolonOS Kalendarz 1.3**
  - Zaktualizowano wersję aplikacji do 1.3, zaimplementowano typografię Roboto oraz odświeżono stylizację nagłówka.
* **PolonOS NetMonitor 1.3**
  - Zaktualizowano wersję aplikacji do 1.3, wdrożono nagłówek GTK oraz dopasowano stylistykę CSS.

### Sterowniki i Kompatybilność Sprzętowa
* **Wsparcie dla kart NVIDIA serii RTX 50xx oraz układy hybrydowe**
  - Wdrożono pakiet sterowników `firmware-nvidia-gsp`, `nvidia-open`, `nvidia-kernel-open-dkms` oraz `nvidia-driver` dla obsługi nowoczesnych układów graficznych NVIDIA (RTX 50xx / Blackwell).
  - Skonfigurowano bezkonfliktową obsługę układów hybrydowych AMD Ryzen + NVIDIA (PRIME Offload) poprzez obligatoryjną aktywację modułu `nvidia-drm.modeset=1`.

### Instalator Calamares
* **Automatyzacja poinstalacyjna**
  - Stworzono wykonywalny skrypt poinstalacyjny `/usr/sbin/polonos-postinstall.sh`, eliminując błędy interpretacji zmiennych powłoki w module `shellprocess.conf`.
  - Ustawiono UID 999 dla konta użytkownika Live (`user`), co gwarantuje, że instalator Calamares wyświetla wyłącznie konto utworzone przez użytkownika podczas instalacji.

---

## [Wersja v1.2] – Wydanie Stabilne (2026-08-02)

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
* **Obsługa modułów jądra NVIDIA Open Kernel Modules oraz wsparcie architektury Blackwell (RTX 5060/50xx)**
  - **Wdrożenie modułów otwartych**: Wprowadzono instalację pakietu `nvidia-open-kernel-dkms` dla nowożytnych kart graficznych NVIDIA (architektury Blackwell, Ada Lovelace, Ampere oraz Turing, w tym RTX 50xx, 40xx, 30xx i 20xx) z automatycznym wycofaniem (fallback) do `nvidia-kernel-dkms` dla generacji starszych.
  - **Kolejność i układ opcji**: Uporządkowano chronologicznie listę dostępnych wersji sterowników NVIDIA w oknie dialogowym:
    1. *1. Sterowniki NVIDIA 550.xx (Wersja stabilna z repozytorium dystrybucji)* – wersja domyślna, zalecana dla większości kart.
    2. *2. Sterowniki NVIDIA 580.xx (Dedykowana wersja LTS)* – wersja przeznaczona dla kart z architektury Pascal (seria GTX 10xx) oraz Maxwell (seria 9xx).
    3. *3. Sterowniki NVIDIA 610.xx (Najnowsza wersja z repozytorium CUDA)* – wersja pobierana online z serwerów NVIDIA.
  - **Przejrzyste zaznaczanie bez dopisków**: Wyeliminowano zbędne tekstowe wyróżnienia i dopiski. Wybrana przez algorytm lub użytkownika opcja wskazywana jest wyłącznie standardową czerwoną kropką wyboru.
  - **Poszerzenie okna dialogowego**: Powiększono szerokość okna `NvidiaDriverDialog` do 740 pikseli, eliminując ucinanie długich opisów i numerów podwersji online (np. `610.42`).
  - **Automatyczne czyszczenie pakietów (autoremove)**: Skrypt aktualizacji systemowych uruchamiany z poziomu asystenta powitalnego został rozbudowany o automatyczne wywoływanie `apt-get autoremove -y`. Dzięki temu po instalacji aktualizacji system samoczynnie oczyszcza się ze zbędnych, osieroconych pakietów i zależności.

---

## [Wersja v1.1] – Wydanie Stabilne (2026-07-22)

### Nowości i Zmiany
* **Wstępne wsparcie dla nowszego jądra**: Przeniesienie dystrybucji na jądro `7.1.3` oraz bazę pakietów Debian 13 (Testing).
* **Aktualizacje przeglądarki**: Poprawki stabilności i integracji dla przeglądarki internetowej Brave.
* **PolonOS Net Monitor (Wersja v1.1)**
  - Optymalizacja bibliotek WebKit2GTK pod kątem sesji Wayland (zapobieganie błędom renderowania na GPU NVIDIA poprzez wymuszenie flag `WEBKIT_DISABLE_COMPOSITING_MODE` i `WEBKIT_DISABLE_DMABUF_RENDERER`).
