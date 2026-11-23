## Standalone V2R2 - 2026-11-23

- CPU-Auslastung der VU+ oben rechts, systemweite CPU-Zeit-Differenzen aus /proc/stat
- RAM gesamt/belegt aus /proc/meminfo, aelterer Kernel-Fallback
- Refresh jede Sekunde auf bereits geschuetztem /api/status (kein zweiter HTTP-Port)
- Responsive Header-Anzeige mit zwei Balken fuer Desktop und Handy
- OneClick-Update/OneClick-Rollback mit bytegetreuer Sicherung der zwei bisherigen Webdateien
- Grabber, DDP, LED-Zonen und Kalibrierung unveraendert
- Offline-Tests inkl. Browser, Socket-API und simuliertem Dienstbetrieb bestanden

## Standalone V2R1 (2026-11-22)

- Neues responsives Web-Dashboard mit vier Tabs: Übersicht, LED-Anordnung, Farben und Erweitert.
- Feste Speicherleiste mit Erkennung ungespeicherter Einstellungen.
- Live-Status, FPS, LED-Zahl und Capture-Zeit prominent zusammengefasst.
- Keine Änderung an Grabber, WLED-DDP, Konfiguration, LED-Layout oder Autostart.
- UI-only-OneClick-Update und Rollback auf vorheriges V2-HTML.
- Das Layout ist nur für Standalone V2, nicht für den bisherigen VU-Ambilight-Dienst.

# Changelog

## Standalone V1 (Testzweig)

- Laufzeit vollständig unabhängig von EnigmaLight.
- Installation nach `/home/en-bilight` statt `/home/elight-addons/...`.
- Eigenständiger SysV-Startdienst; kein Autostart ohne ausdrücklichen Befehl.
- Migration der vorhandenen V1R10R2-Settings und WLED-Zieladresse auf dem Receiver.
- Vierseitige Abtasttiefe, Anti-Bounce, Kalibrierbereich 300, Webserver 8095.
- Keine Änderung am unveränderten V1R8/V1R10R2-Freeze.

## Grundlage

- V1R8 Freeze: 24,38 FPS am Gerät.
- V1R9 Test: bis 24,97 FPS mit DDP.
- V1R10R2 Freeze: Webinterface und Dauerbetrieb.
- V1R10R3-5: Abtasttiefe, Anti-Bounce, Kalibrierregler (experimentell).

## Standalone V2 (LED-Konfigurationsdialog, Testzweig)

- Web-Dialog für physische LED-Anzahlen je TV-Kante und interaktive Zuordnungsvorschau.
- Start in einer von vier Ecken, Uhrzeigersinn oder Gegenuhrzeigersinn, konfigurierbarer Umlaufversatz.
- Gesamtlänge 1–480 LEDs, RAW-YUV-Sampler, Effekt-Engine, FlashGuard und DDP-Pakete dynamisch angepasst.
- Integrierter 8-Sekunden-LED-Test über den vorhandenen Sender: Einzel-LED und farbige Kanten.
- Originale 314er-Geometrie bleibt pixelgenau erhalten, solange das Layout auf Standard steht.
- Atomare separate Konfiguration unter `/home/en-bilight/led_layout.cfg`, Code-Backup für Update und Rollback.
- Kein neuer automatischer Dienststart; unveränderter Web-Token und Autostart.
