# Eigenständige Architektur

Der Broadcom-Sampler in `fast_bcm73625_r10.py` nutzt den nur lesenden
`/dev/mem`-Zugriff auf Video-Puffer und BCM73625-Register. Kein
`/usr/bin/enigmalight`, kein EnigmaLight-Paket, keine EnigmaLight-Konfig
und kein `aio-grab`-Prozess werden zur Laufzeit verwendet. Die weiteren
Teile (`effects_r10.py`, `web_r10.py`, `supervisor.sh`) sind unabhängig.

Pipeline: Broadcom YUV/BT.601 → 314 RGB-Abtastpunkte → Anti-Bounce →
Gain/Gamma/Sättigung → zeitliche Glättung/Delay → 942 RGB-Bytes → DDP/4048.
WLED bekommt die Helligkeit über seine lokale HTTP-API, der DDP-Datenstrom
bleibt RAW-RGB (Kalibrierung nur falls eingestellt).

## Fremdcode / Lizenz

Der Videoformat-/Register-Ansatz wurde im En-bilight-Projekt aus der
OpenPLi-aio-grab-Technik adaptiert; die Python-Portierung wurde im
Projekt iterativ experimentell erarbeitet. Hinweise und Originalquellen:
https://github.com/OpenPLi/aio-grab
https://github.com/ZachWay9bot/En-bilight
Die Quelltexte behalten vorhandene GPL-2.0-only-Kennzeichnungen.
EnigmaLight ist nicht Teil des Standalone-Pakets.
