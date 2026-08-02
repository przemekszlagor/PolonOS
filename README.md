# PolonOS LTS (KDE Plasma)

PolonOS to polska, stabilna i bezpieczna dystrybucja systemu operacyjnego oparta na gałęzi testowej Debiana (Testing/Trixie) ze środowiskiem graficznym KDE Plasma. System został zoptymalizowany pod kątem wysokiej wydajności oraz łatwości użytkowania.

---

## Pobieranie (ISO)

Najnowszy obraz instalacyjny ISO systemu PolonOS możesz pobrać z różnych źródeł, w zależności od preferencji dotyczących szybkości transferu:

### Szybkie pobieranie bezpośrednie (CDN)

*   **[Główny Mirror (Cloudflare R2 CDN)](https://pub-fdfbdf6f7a81492aaf39366393d73ad6.r2.dev/iso/polonos-1.2-amd64.iso)** – Zalecane, najszybsze pobieranie z globalnej sieci dostarczania treści bez limitów prędkości.
*   **[SourceForge](https://sourceforge.net/projects/polonos/files/latest/download)** – Tradycyjna sieć serwerów lustrzanych.

### Pobieranie P2P (BitTorrent)

Dla osób chcących zminimalizować zużycie łączy serwera lub pobierać w niesprzyjających warunkach sieciowych rekomendujemy protokół P2P:

*   **[Plik .torrent](https://pub-fdfbdf6f7a81492aaf39366393d73ad6.r2.dev/torrents/polonos-1.2-amd64.iso.torrent)** – Oficjalny plik torrent.
*   **[Link Magnet](magnet:?xt=urn:btih:b158e4d3a0eb43b2315dc535b65290490ee3c44ebc196440df0a21a144f7132a&dn=polonos-1.2-amd64.iso)** – Bezpośrednie otwarcie pobierania w klincie torrent.

### Weryfikacja integralności obrazu

Przed nagraniem ISO na nośnik USB (np. programem Rufus lub Ventoy), upewnij się, że plik nie uległ uszkodzeniu podczas transferu:

*   **Suma kontrolna SHA256:** `b158e4d3a0eb43b2315dc535b65290490ee3c44ebc196440df0a21a144f7132a`

---

## Kluczowe Funkcje

*   **Asystent PolonOS Welcome:** Dedykowana aplikacja startowa pomagająca w pierwszej konfiguracji systemu bezpośrednio po instalacji.
*   **Sterowniki i aktualizacje:** Wbudowany moduł wykrywania sprzętu oferujący instalację własnościowych sterowników (w tym stabilnych oraz najnowszych wersji sterowników NVIDIA bezpośrednio z oficjalnych repozytoriów producenta oraz sterowników Broadcom).
*   **Instalator aplikacji:** Szybka instalacja najpopularniejszych programów (przeglądarki, pakiety biurowe, multimedia, Steam) zintegrowana z Flatpak (Flathub) oraz APT.
*   **Środowisko KDE Plasma:** Piękny, responsywny i wysoce konfigurowalny pulpit dopasowany do nowoczesnych standardów.

---

## Wymagania systemowe

Aby zapewnić komfortowe działanie systemu, zalecana jest następująca konfiguracja sprzętowa:

| Komponent | Wymagania minimalne | Wymagania zalecane |
| :--- | :--- | :--- |
| **Procesor** | Dwurdzeniowy 2.0 GHz | Czterordzeniowy 2.5 GHz lub lepszy |
| **Pamięć RAM** | 4 GB RAM | 8 GB RAM lub więcej |
| **Miejsce na dysku** | 25 GB wolnego miejsca | 50 GB (SSD zalecane) |
| **Karta graficzna** | Zintegrowana z obsługą OpenGL | Dedykowana NVIDIA / AMD |

---

## Zgłaszanie problemów i rozwój

Jeśli napotkasz błąd lub masz sugestie dotyczące rozwoju systemu, skorzystaj z zakładki [Issues](https://github.com/przemekszlagor/PolonOS/issues) w tym repozytorium.
