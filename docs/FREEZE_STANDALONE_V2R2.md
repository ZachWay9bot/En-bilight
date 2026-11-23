# Freeze: En-bilight Standalone V2R2 – CPU/RAM Live

**Datum:** 2026-11-23

**Quellartefakt:** `EN_BILIGHT_STANDALONE_V2R2_CPU_RAM_LIVE_2026-11-23.zip`

**Freeze-Artefakt:** `EN_BILIGHT_STANDALONE_V2R2_CPU_RAM_LIVE_FREEZE_2026-11-23.zip`

**SHA256, beide ZIPs (byteidentisch):** `b37d1d44e393113ef778a24be4046bfd4ba020e2005b7ef868453f20d78414cb`

**Hardware:** VU+ Zero, BCM73625, OpenPLi 9.2; WLED/DDP 4048.

**Stand:** Eigenständiger Grabber ohne EnigmaLight zur Laufzeit, Dashboard-Tabs, 1–480 konfigurierbare LEDs (Standard 314 in 100/57/100/57), CPU- und RAM-Anzeige im Webinterface Port 8095. Einstellungen, Token und WLED-Ziel werden lokal gespeichert.

**Prüfung zum Freeze:** Python-Kompilierung, Shell-Syntax sowie `tests/offline_regression.py`, `tests/test_dashboard_browser.py`, `tests/test_system_monitor.py` und `tests/test_update_rollback.py` bestanden. Die Tests verwenden Simulation und Browser-Testtreiber; sie sind keine VU+-Live-FPS-Messung. Die reale V2R2-Laufzeit auf der Zielhardware ist damit noch nicht neu validiert.

**Wichtig:** Die älteren V1R8- und V1R10R2-Freeze-Branches bleiben unberührt. Dieser Freeze schreibt nichts auf die VU+. Die zugehörigen Windows-Skripte im öffentlichen Repository verwenden aus Datenschutzgründen die Beispiel-IP `192.168.1.10`; die ZIP-Archivdateien bleiben byteidentisch und unverändert. In der Firmware/Runtime wurde keine Einstellung verändert.

**Bekannte Einschränkung:** Der Schwarz-Weiß-Vorblitz wird weiterhin untersucht; eine erneute hardwarebasierte FPS-Messung steht aus. Das Web-Token darf nicht öffentlich gespeichert werden.
