# Installation unter OpenPLi 9.2 (VU+ Zero)

**Voraussetzungen:** VU+ Zero mit BCM73625, OpenPLi 9.2, Python 3.9 mit `mmap`, WLED über DDP UDP/4048, Netzteil für LED-Streifen, lokale SSH-Verbindung. Unterstützt werden 314 LEDs und die im Projekt enthaltenen LED-Zonen.

> Achtung: Die native Bildaufnahme liest `/dev/mem`. Nur auf exakt geprüfter BCM73625-Hardware verwenden. Die im Repository bereitgestellten Versionen sind Quellcode-Snapshots, keine allgemein unterstützte Installationslösung. Vor einer Installation auf anderen Receivern zuerst CPU, Chipsatz und Speicherzugriffe prüfen.

## V1R10R2 (Dauerbetrieb, Referenz)

1. Originalquellen aus `src/stable/v1r10r2/` lokal bereitstellen.
2. Über SSH den Receiver erreichen.
3. WLED-Host **auf dem Receiver** in `/home/elight-addons/vu_ambilight/wled_host.txt` konfigurieren. Diese Datei wird **nicht** in Git veröffentlicht.
4. Bestehende Installation und `/etc/init.d` sichern.
5. Die Dateien aus `src/stable/v1r10r2/` nach `/tmp/vu_ambilight_r10r2_stage/` kopieren und dort `install_vu.sh` ausführen.
6. Den Dienst manuell mit `sh /home/elight-addons/vu_ambilight_r10r2/service.sh start` starten, Log und Weboberfläche prüfen.
7. Nur nach erfolgreichem Test Autostart mit `sh /home/elight-addons/vu_ambilight_r10r2/service.sh enable` einschalten, falls der Befehl von der enthaltenen Service-Version unterstützt wird.

**Keine zwei Sender:** Während der Testphase Hyperion auf dem Raspberry Pi stoppen.

**Sicherheitscheck:** Zugangstoken steht ausschließlich unter `/home/elight-addons/vu_ambilight_r10r2/web_token.txt` auf dem Receiver. Weboberfläche Port 8095 nur im vertrauenswürdigen LAN betreiben, niemals ins Internet freigeben.

## Weiterentwicklung

`src/experimental/v1r10r3` ergänzt die vier Abtasttiefen. `src/experimental/v1r10r4` ergänzt einen Anti-Bounce-Test. `src/experimental/v1r10r5-patch` erweitert die Kalibrierregler. Änderungen einzeln testen. Nur V1R8 und V1R10R2 sind als Freeze archiviert, keine Freigabe für eine beliebige Kombination der Experimente.
