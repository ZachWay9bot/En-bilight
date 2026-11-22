# Versionen und Messwerte

| Version | Status | Messung / Eigenschaft |
|---|---|---|
| V1R6 RAW | älterer Freeze | 0,97 FPS, korrekte rohe RGB-Farben |
| V1R8 1P | Freeze | 24,38 FPS bei 20,02 s WLED-Live-Test |
| V1R9 FastPath | Testzweig | 24,97 FPS bei 25,03 s WLED-Live-Test, keine Langzeitfreigabe |
| V1R10R2 | Dauerbetrieb-Freeze | Webkonfiguration, Helligkeit 1..255, Delay 0..500 ms, Smooth 0..95 %, Deadband 0..64 |
| V1R10R3 | Experiment | Vier Abtasttiefen 1..50 %, gleiche 314 LED-Positionen |
| V1R10R4 | Experiment | Anti-Bounce-Filter bei harten Helligkeitswechseln |
| V1R10R5 | Patch | Kalibrierregler auf 300 % erweitert |

Messwerte stammen aus einzelnen Nutzertests auf VU+ Zero / OpenPLi 9.2 und sind keine Benchmarks auf anderen Geräten.

Die Hardware-Freeze-ZIPs wurden **nicht** ungeprüft ins öffentliche Repository übertragen, da sie gerätespezifische Einstellungen enthalten. Die Quell-Snapshots sind daraus extrahiert, originale lokale Freeze-ZIPs bleiben privat.
