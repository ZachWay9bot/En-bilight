# LED-Konfigurationsdialog: Standalone V2

Im Browser: `http://<RECEIVER-IP>:8095/?key=<WEB_TOKEN>` → **LED-Konfiguration öffnen**.

## Einstellmöglichkeiten

- **Oben / Rechts / Unten / Links:** Anzahl physisch verbauter LEDs je TV-Kante, 0 erlaubt.
- **Gesamtzahl:** automatisch aus den vier Kanten, **1–480 LEDs** pro DDP-Paket. 480 ist die Grenze dieses Testzweigs: 1440 RGB-Bytes + 10 DDP-Headerbytes ohne IP-Fragmentierung.
- **Start-Ecke:** oben links (TL), oben rechts (TR), unten rechts (BR), unten links (BL), vom Betrachter vor dem TV aus gesehen.
- **Richtung:** im Uhrzeigersinn (CW) oder gegen den Uhrzeigersinn (CCW), jeweils vom Bildschirm aus betrachtet.
- **Startversatz:** 0 bis Gesamtzahl minus 1, rotiert die Zuordnung von LED 1 entlang des virtuellen Umfangs. Für gewöhnliche durchgehende Streifen 0 lassen.
- **Vorschau:** rote Punkte für oben, grüne für rechts, blaue für unten, orange für links; Marker „LED 1“ und „LED N“.

## Original bleibt exakt erhalten

Solange keine andere Anordnung gespeichert wird, greift **die ursprüngliche Hyperion-Zuordnung 100 / 57 / 100 / 57**. Die Abtastpunkte werden über die unveränderte `led_regions.txt` aufgebaut. Selbst bei Standalone V2 sind die ursprünglichen Capture-Koordinaten **pixelgenau identisch**.

Die neue Konfiguration wird **separat** in `/home/en-bilight/led_layout.cfg` gespeichert. `settings.cfg`, `web_token.txt` und `wled_host.txt` werden nicht verändert.

## LED-Zuordnung testen

Nach dem Speichern kann der bereits aktive En-bilight-Liveprozess für 8 Sekunden eigene Testdaten ausgeben:

- **Eine LED rot:** die gewählte physische Nummer, beginnend mit LED 1 am DIN-Ende.
- **Vier Kantenfarben:** oben Rot, rechts Grün, unten Blau, links Orange.
- **Test beenden:** beendet den Test sofort (bis zum nächsten Capture-Frame).

Die Tests verwenden denselben DDP-Ausgang und starten **keinen zweiten UDP-Sender**. Der WLED-Helligkeitswert bleibt unverändert. Die Testanfrage liegt nur kurz in `/tmp/en-bilight/led_test.cfg` und läuft automatisch ab. Ohne aktiven Standalone-Dienst lehnt die Web-API den Test ab.

**Hinweis:** Der Controller muss in WLED auf eine LED-Anzahl eingestellt sein, die mindestens der hier gewählten Gesamtzahl entspricht. Für 480 LEDs kann die Bildrate auf der VU+ Zero wegen der zusätzlichen Abtastpunkte unter die bisherigen ~25 FPS fallen; das ist nicht auf Hardware verifiziert.

## Aktualisieren / Rückweg

- Beim bereits laufenden Standalone V1 die Windows-CMD `10_LED_DIALOG_UPDATE_ONECLICK.cmd` verwenden. Einstellungen und Autostart bleiben.
- Für Neuinstallation `01_INSTALLIEREN.cmd`, dann bewusst `02_TESTWECHSEL.cmd`.
- Für Rollback zum V1-Code `11_ZURUECK_ZU_V1.cmd` (nach einem erfolgreichen V2-Update).
- Für Rückweg zum alten VU-Ambilight `04_ZURUECK_ZUM_ALTEN.cmd`.

Der V1R8- und V1R10R2-Freeze wird nicht verändert. Alle neuen Funktionen sind derzeit **experimentell**.
