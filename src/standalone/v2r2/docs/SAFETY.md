# Sicherheit und bekannte Grenzen

- **Nur für BCM73625 / OpenPLi 9.2** getestet, root und `/dev/mem` nötig.
- Keine Register-Schreibzugriffe; trotzdem kann direkter Hardwarezugriff problematisch sein.
- Webserver Port 8095 nur im LAN, Zugriff mit geräteeigenem Token. Kein Port-Forwarding.
- Vor dem Start **alten VU-Ambilight-Dienst und Pi-Hyperion stoppen**.
- Nicht die LED-Stromversorgung über VU-USB betreiben; Streifen braucht eigenes Netzteil.
- Früherer Anti-Bounce-Filter ist experimentell, reproduzierter TV-Vorblitz noch nicht endgültig behoben.
- 25 FPS stammen aus kurzen Hardwaretests des älteren Codezweigs; Standalone muss erneut gemessen werden.
- Dieses Paket installiert **nicht** EnigmaLight und entfernt bestehendes EnigmaLight **nicht**.
- Einmalig manuell testen, erst danach eigenen Autostart aktivieren.
- Ein OpenPLi-Update kann den Speicher-/Registerzugriff ändern.
