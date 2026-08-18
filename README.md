# PolonOS LTS (KDE Plasma)

PolonOS to polska, stabilna i bezpieczna dystrybucja systemu operacyjnego oparta na gałęzi testowej Debiana (Testing/Trixie) ze środowiskiem graficznym KDE Plasma. System został zoptymalizowany pod kątem wysokiej wydajności oraz łatwości użytkowania.

---

## Pobieranie (ISO)

Najnowszy obraz instalacyjny ISO systemu PolonOS możesz pobrać z różnych źródeł, w zależności od preferencji dotyczących szybkości transferu:

### Szybkie pobieranie bezpośrednie (CDN)

*   **[Główny mirror (Cloudflare R2 CDN)](https://pub-fdfbdf6f7a81492aaf39366393d73ad6.r2.dev/iso/polonos-1.3-amd64.iso)** – Zalecane, najszybsze pobieranie z globalnej sieci dostarczania treści bez limitów prędkości.
*   **[SourceForge](https://sourceforge.net/projects/polonos/files/latest/download)** – Tradycyjna sieć serwerów lustrzanych.

### Pobieranie P2P (BitTorrent)

Dla osób chcących zminimalizować zużycie łączy serwera lub pobierać w niesprzyjających warunkach sieciowych rekomendujemy protokół P2P:

*   **[Plik .torrent](https://pub-fdfbdf6f7a81492aaf39366393d73ad6.r2.dev/torrents/polonos-1.3-amd64.iso.torrent)** – Oficjalny plik torrent.
*   **[Link magnet](magnet:?xt=urn:btih:d09131338a240914ed67336e89aaa17fad3132fe&dn=polonos-1.3-amd64.iso)** – Bezpośrednie otwarcie pobierania w kliencie torrent.

### Weryfikacja integralności obrazu

Przed nagraniem ISO na nośnik USB (np. programem Rufus lub Ventoy), upewnij się, że plik nie uległ uszkodzeniu podczas transferu:

*   **Suma kontrolna SHA256:** `9001372f134a98b1265fc735531901227b657990f55ca8d1b3faffeb07bd38be`
*   **Suma kontrolna MD5:** `a8d9475a0794c674887e8af853f42299`

---

## Kluczowe funkcje

*   **Autorski motyw PolonOS Dark:** Elegancka, spójna ciemna oprawa graficzna dostępna natywnie w trybie LIVE oraz po instalacji.
*   **Domyślna typografia Google Roboto:** Wbudowana czcionka Google Roboto używana we wszystkich natywnych aplikacjach PolonOS oraz w środowisku pulpitu.
*   **Asystent PolonOS Welcome 1.3:** Dedykowana aplikacja startowa pomagająca w pierwszej konfiguracji systemu bezpośrednio po instalacji.
*   **Sterowniki i aktualizacje:** Wbudowany moduł wykrywania sprzętu oferujący instalację własnościowych sterowników NVIDIA (w tym pełne wsparcie dla architektury Blackwell / RTX 50xx).
*   **Instalator oprogramowania:** Szybka instalacja popularnych programów zintegrowana z repozytoriami Flatpak (Flathub) oraz APT.
*   **Środowisko KDE Plasma 6:** Piękny, responsywny pulpit dopasowany do nowoczesnych standardów ze wsparciem sesji Wayland oraz X11.

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
