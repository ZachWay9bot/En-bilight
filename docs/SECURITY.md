# Sicherheit und private Einstellungen

- Niemals `web_token.txt`, `settings.cfg`, originale Hyperion-Backups, reale SSH-Schlüssel oder Geräte-Dumps committen.
- WLED-IP, VU+-IP, WLAN und Zugangstoken in nicht versionierten lokalen Dateien bzw. Umgebungsvariablen belassen.
- Der eingebettete HTTP-Server auf Port 8095 unterstützt einen Token, aber **kein TLS**. Nur im vertrauenswürdigen lokalen Netz verwenden.
- Die Originalimplementierung prüft im Servercode auf ein hartcodiertes LAN-Präfix. Bei anderen Heimnetzen muss diese Prüfung bewusst angepasst werden.
- `/dev/mem` erfordert root und greift direkt auf Chipregister zu. Experimente nicht auf anderen Chipsätzen ausführen.
- Ein Github-Repository ist keine Garantie für sichere Installation auf unbekannter Hardware.
