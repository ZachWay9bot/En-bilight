EN-BILIGHT STANDALONE V2R2 - CPU/RAM LIVE OBEN RECHTS
=====================================================
OpenPLi 9.2 | VU+ Zero BCM73625 | WLED DDP | 1..480 LEDs

NEU: CPU-Auslastung + RAM-Nutzung der VU+ rechts oben im Dashboard.
- Aktualisierung jede Sekunde; Prozent-Balken, RAM benutzt/gesamt.
- Daten direkt aus /proc/stat und /proc/meminfo.
- Keine Zusatzprozesse, keine Pakete, keine Eingriffe in Grabber/DDP.

BESTEHENDE STANDALONE V2/V2R1 INSTALLATION:
  WINDOWS_ONECLICK\14_CPU_RAM_LIVE_INSTALLIEREN.cmd
  Danach 07_WEB_OEFFNEN.cmd, Browser STRG+F5.
  Rueckweg: 15_CPU_RAM_ZURUECK.cmd
  Achtung: Kontrollierter kurzer Neustart des Standalone-Diensts.

NEUINSTALLATION OHNE ENIGMALIGHT:
  01_INSTALLIEREN.cmd (legt Dateien ab, startet noch nichts)
  02_TESTWECHSEL.cmd (alter Sender wird kontrolliert gestoppt)
  07_WEB_OEFFNEN.cmd (Webinterface mit Token)
  03_AUTOSTART_FREIGEBEN.cmd erst nach erfolgreichem Hardwaretest

VORHANDENE FEATURES:
  Dashboard-Tabs: Uebersicht | LED-Anordnung | Farben | Erweitert.
  LED-Layout mit Startecke, Laufrichtung, Startversatz, Test.
  Smoothing, Delay, Anti-Bounce, RGB-Saettigung und Gamma.

SICHERHEIT:
  Alter Webstand wird vor dem CPU/RAM-Update bytegenau gesichert.
  RGB, Settings, WLED-IP, Token, LED-Zahlen und Autostart unveraendert.
  Kein zweiter DDP-Sender.
  Freeze V1R8 und V1R10R2 bleiben unangetastet.

Tests: Python + Web-API + Browser/Desktop/Mobil + Shell-Rollback +
      simulierte DDP-LED-Layout-Regression. Keine VU+-Live-FPS-Messung.
Dokumentation: docs\CPU_RAM_MONITOR_V2R2.md
