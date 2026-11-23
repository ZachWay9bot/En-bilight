# En-bilight Standalone V2R2: Live CPU & RAM

Im Kopfbereich rechts sind zwei kleine Live-Kacheln integriert:

- **CPU:** gesamte Prozessorauslastung der VU+ Zero in Prozent (aus der Differenz zweier `/proc/stat`-Messungen). **Nicht** nur die CPU-Auslastung des Grabbers.
- **RAM:** verwendeter RAM in Prozent und MiB, ermittelt aus `/proc/meminfo` (`MemTotal - MemAvailable`; bei älteren Kernelversionen Fallback aus Free, Buffers, Cache etc.). MiB werden in der UI vereinfacht als MB angezeigt.

Eine Messung pro Sekunde über den bereits authentifizierten Endpunkt `/api/status`. Keine neuen Abhängigkeiten oder zweiten HTTP-Server; die Python-Reads aus `/proc` sind sehr kurz. Bei fehlenden Werten zeigt die Anzeige `--` an statt Phantasiezahlen.

## Installation auf Standalone V2 oder V2R1

1. ZIP entpacken.
2. `WINDOWS_ONECLICK/14_CPU_RAM_LIVE_INSTALLIEREN.cmd` starten.
3. `WINDOWS_ONECLICK/07_WEB_OEFFNEN.cmd` starten und `Strg+F5` drücken.

Die Installation sichert die bis dahin vorhandenen `web_r10.py` und `index.html` unter `/home/en-bilight/rollback_before_sysmon_v2r2/`. Falls der Standalone-Dienst läuft, wird er zum Austausch des Webservers **einmal kontrolliert angehalten und wieder gestartet**. Die Ausgabe kann kurz unterbrochen sein. Ein zweiter DDP-Sender wird nicht gestartet.

- Es werden keine Konfigurations- oder Token-Dateien geschrieben.
- Für Rücksetzung: `WINDOWS_ONECLICK/15_CPU_RAM_ZURUECK.cmd`.
- Die älteren Freezes V1R8 und V1R10R2 bleiben unangetastet.

## Vorbedingungen

Das Update benötigt eine bestehende **En-bilight Standalone V2/V2R1** Installation unter `/home/en-bilight`. Es hat keine Wirkung auf den älteren VU-Ambilight-Dienst unter `/home/elight-addons/...`. Falls du aktuell noch den alten Dienst verwendest, zuerst auf Standalone wechseln.

Die Systemmessung ist von der Bildaufnahme und dem DDP-Sender entkoppelt; daher sollte die Änderung keinen merklichen Einfluss auf die FPS haben. **Auf echter VU+-Hardware wurde der Liveverbrauch dieses V2R2-Patches noch nicht gemessen.**
