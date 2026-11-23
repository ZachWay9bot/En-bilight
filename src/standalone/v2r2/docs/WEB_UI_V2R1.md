# En-bilight Standalone V2R1: Übersichtliches Web-Dashboard

Dieses Update betrifft ausschließlich die Weboberfläche (`index.html`) der **Standalone-V2**-Installation.

## Vier Bereiche

- **Übersicht:** Aktuelle FPS, Live-Status, Auswertungszeit, LED-Gesamtzahl, WLED-Helligkeit, Delay, Glättung und Diagnose.
- **LED-Anordnung:** Vorhandener LED-Konfigurationsdialog mit 1..480 LEDs, Laufrichtung, DIN-Start, Startversatz und Live-Test sowie vier Abtasttiefen.
- **Farben:** RGB-Kalibrierung, Sättigung und Gamma mit den bisherigen Wertebereichen.
- **Erweitert:** Flackerschwelle, Anti-Bounce und Hinweise zur Latenz.

Die Speichern-Leiste bleibt im Browser sichtbar und markiert ungespeicherte Änderungen. Der LED-Konfigurationsdialog speichert sein Layout separat, genau wie in V2.

## Installation auf bestehender Standalone V2

1. V2R1-ZIP auspacken.
2. `WINDOWS_ONECLICK/12_DASHBOARD_UI_UPDATE.cmd` ausführen.
3. `WINDOWS_ONECLICK/07_WEB_OEFFNEN.cmd` öffnen, `Strg+F5` drücken.

Das Skript legt bei der ersten Aktualisierung eine Sicherung unter `/home/en-bilight/index.before_dashboard_v2r1.html` an. Es verändert **keine** Konfigurationsdateien, keine Web-Tokens, keine DDP-Ausgabe und keine Autostart-Einstellungen. Der laufende Dienst muss nicht neu gestartet werden, da das HTML für jeden GET neu eingelesen wird.

## Rücksetzung

`WINDOWS_ONECLICK/13_DASHBOARD_UI_ZURUECK.cmd` benutzen. Nur die HTML-Datei wird restauriert.

## Noch den alten VU-Ambilight-Dienst aktiv?

Dann hat das Update keine sichtbare Wirkung. Es aktualisiert ausschließlich `/home/en-bilight/index.html`, nicht die alte `/home/elight-addons/...`-Installation. Zum Test zuerst über `02_TESTWECHSEL.cmd` auf Standalone V2 wechseln. Vorher Pi-Hyperion ausschalten, damit nicht mehrere DDP-Sender aktiv sind.

## Tests

HTML-IDs erhalten, Javascript-Syntax geprüft, Tabwechsel, Speichern und LED-Dialog mit Browser-Test geprüft. Kein Hardware-FPS-Test nach der Umgestaltung; Grabber und Video-/DDP-Ausgabepfad bleiben unverändert.

**Hinweis:** Der ab V2R2 verfuegbare CPU/RAM-Monitor ist unter `CPU_RAM_MONITOR_V2R2.md` beschrieben.
