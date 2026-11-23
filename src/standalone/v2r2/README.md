# En-bilight Standalone V2R2 (Quellcode-Freeze)

Dieser Ordner enthält eine **öffentlich bereinigte Quellcodekopie** des Standalone-V2R2-Pakets. Die eigenständige Runtime benötigt kein installiertes EnigmaLight.

- Runtime: `runtime/`
- Windows-One-Click-Skripte: `WINDOWS_ONECLICK/`
- Hardware-/Installationsdokumentation: `docs/`
- Offline-Tests: `tests/`
- Gebündelte VU+-Runtime: `en-bilight-runtime.tar.gz`

**Herkunft, unveränderliche Archivfassung:** Siehe [Freeze-Dokumentation](../../../docs/FREEZE_STANDALONE_V2R2.md), SHA256 `b37d1d44e393113ef778a24be4046bfd4ba020e2005b7ef868453f20d78414cb`.

Die CMD-Dateien im öffentlichen Repository besitzen statt der privaten Receiver-Adresse den Beispielwert `192.168.1.10`; passe ihn auf deinen Receiver an. Diese öffentliche Bereinigung hat keine Änderung am byteidentischen Freeze-ZIP vorgenommen.

**Hardwarestatus:** Alle Offline-Tests bestanden. Standalone-V2R2-Live-FPS und CPU/RAM-Verbrauch auf VU+-Hardware sind noch nicht bestätigt.

**Sicherheitsstand:** Für offene Internetzugriffe ungeeignet. Den Webserver nur im LAN mit geräteindividuellem Token betreiben. Keine persönlichen `settings.cfg`, `wled_host.txt` oder `web_token.txt` committen.
