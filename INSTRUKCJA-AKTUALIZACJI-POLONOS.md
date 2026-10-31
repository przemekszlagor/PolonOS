# System Aktualizacji Wydań Dystrybucji PolonOS (Wariant Hybrydowy 1+3)

Ten dokument opisuje wdrożony w **PolonOS Aplikacje** mechanizm aktualizacji całego systemu do nowszej wersji jednym kliknięciem (bez konieczności ponownej instalacji z pliku ISO) oraz obsługę użytkowników starszych wersji (**1.0, 1.1, 1.2, 1.3**).

---

## 1. Jak działa ten mechanizm?

1. **Plik manifestu (`polonos-release.json`)** w głównym katalogu repozytorium `PolonOS-Repo` (dostępny pod adresem `https://raw.githubusercontent.com/przemekszlagor/PolonOS/main/polonos-release.json`) przechowuje informację o aktualnie opublikowanej wersji systemu.
   - Obecnie jest tam ustawiona wersja **`1.3`**, więc dopóki pracujesz nad wersją **1.4**, użytkownicy widzą komunikat: *„✓ Posiadasz najnowszą wersję PolonOS”*.
2. **Aplikacja PolonOS Aplikacje** (moduł `src/backend/dist_upgrader.py` oraz `src/ui/tab_upgrade.py`) jest już w 100% przygotowana:
   - Odczytuje wersję zainstalowanego systemu z `/etc/os-release` (`VERSION_ID`).
   - Porównuje ją z `latest_version` w pliku `polonos-release.json`.
   - Gdy `latest_version` w internecie jest wyższe niż lokalna wersja (np. `1.4 > 1.3` lub `1.4 > 1.0`), odblokowuje przycisk **„Aktualizuj do PolonOS 1.4-KDE”**.
   - Po kliknięciu otwiera okno postępu, prosi o hasło administratora (`pkexec`), pobiera paczkę `polonos-upgrade-1.4.tar.gz`, uruchamia zawarty w niej skrypt `upgrade.sh`, aktualizuje pakiety i podnosi wersję systemu do `1.4`.

---

## 2. Co z użytkownikami wersji 1.0, 1.1 oraz 1.2? (Aktualizacje Kumulatywne)

Zastosowaliśmy model **Kumulatywnej Paczki Aktualizacyjnej (Cumulative Rollup Upgrade)**:
- Paczka aktualizacyjna do wersji docelowej (np. `1.4`) zawiera **wszystkie aktualne pliki `.deb`** Twoich aplikacji oraz **pełny zestaw konfiguracji docelowych**.
- Dzięki temu użytkownik **nie musi** aktualizować systemu po kolei (`1.0 -> 1.1 -> 1.2 -> 1.3 -> 1.4`).
- Niezależnie od tego, czy ktoś ma zainstalowany **PolonOS 1.0, 1.1, 1.2 czy 1.3**, kliknięcie przycisku **„Aktualizuj”** od razu przeniesie go bezpośrednio do najnowszej wersji (**1.4**).
- *Uwaga dla wersji 1.0–1.2:* Ponieważ w wersjach 1.0–1.2 nie było jeszcze programu `PolonOS Aplikacje`, użytkownicy tych starszych wydań muszą najpierw jednorazowo zainstalować plik `polonos-aplikacje.deb` (np. pobrany z Twojej strony lub repozytorium), a po jego uruchomieniu od razu zobaczą przycisk aktualizacji całego systemu do najnowszej wersji.

---

## 3. Co musisz zrobić, gdy skończysz pracę nad PolonOS 1.4 i wydasz nowe ISO?

Gdy wersja **1.4** będzie gotowa do publikacji, wykonujesz tylko **3 proste kroki**:

1. W folderze `PolonOS-Repo` uruchom przygotowany skrypt:
   ```bash
   chmod +x przygotuj-aktualizacje.sh
   ./przygotuj-aktualizacje.sh 1.4 "Opis nowości w PolonOS 1.4-KDE"
   ```
   *(Skrypt automatycznie zbierze wszystkie najnowsze paczki `.deb`, wygeneruje skrypt migracyjny `upgrade.sh`, stworzy plik `polonos-upgrade-1.4.tar.gz` oraz zaktualizuje `polonos-release.json` do wersji `1.4`)*.

2. Na swoim GitHubie (`https://github.com/przemekszlagor/PolonOS/releases`) utwórz wydanie (Release) z tagiem **`v1.4`** i wrzuć tam wygenerowany plik **`polonos-upgrade-1.4.tar.gz`**.

3. Wyślij zaktualizowany plik `polonos-release.json` na GitHuba:
   ```bash
   git add polonos-release.json
   git commit -m "Wydanie PolonOS 1.4"
   git push
   ```

Od tej sekundy u każdego użytkownika PolonOS (1.0, 1.1, 1.2, 1.3) w programie **PolonOS Aplikacje** zaświeci się przycisk **„Aktualizuj do PolonOS 1.4-KDE”**.
