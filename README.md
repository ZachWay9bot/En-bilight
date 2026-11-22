# En-bilight

Ambilight direkt auf der **VU+ Zero (OpenPLi 9.2 / BCM73625)**: 314 adressierbare LEDs, Bildfarb-Sampling aus dem Broadcom-Videopuffer, Ausgabe über **WLED/DDP**, Weboberfläche und optionaler Enigma2-Autostart.

## Projektstand

- **V1R8:** Eingefrorener, hardwaregetesteter 1-Punkt-Sampler: **24,38 FPS** mit DDP im 20-Sekunden-Test.
- **V1R10R2:** Eingefrorener Dauerbetriebsstand mit Weboberfläche (Port 8095), Helligkeit, Delay, Smooth, Deadband und RGB-Kalibrierung.
- **V1R10R3–R5:** Experimentelle Abtasttiefen, Anti-Bounce und erweiterte Farbregler; *nicht* als neue stabile Version freigegeben.

Die ursprünglichen Freeze-Archive werden nicht verändert. Das öffentliche Repository enthält die Quellen als nachprüfbare Snapshots, jedoch keine privaten Konfigurationen.

## Schnellstart

Siehe [Installation für OpenPLi 9.2](docs/INSTALL_OPENPLI92.md) und [Versionen](docs/VERSIONS.md). Kein Autostart ohne manuellen Test aktivieren; beim Test den bisherigen Hyperion-Sender stoppen.

## Verzeichnisstruktur

- `src/stable/v1r8/`: Direkt-Sampler (Referenz) und Native-C-Entwurf
- `src/stable/v1r10r2/`: Persistenter Dienst mit Webserver
- `src/experimental/v1r10r3/`: Vierseitige Abtasttiefe
- `src/experimental/v1r10r4/`: Anti-Bounce-Test
- `src/experimental/v1r10r5-patch/`: Regler-Patch
- `config/`: unverfängliche Beispielkonfigurationen
- `docs/`: Installation, Sicherheit und Versionshistorie

## Sicherheit und Lizenz

Webinterface ausschließlich im LAN verwenden; niemals den Web-Token veröffentlichen. Der Grabber verwendet `/dev/mem` und ist **nur für den geprüften Chipsatz** gedacht. Einige Quellmodule tragen `SPDX-License-Identifier: GPL-2.0-only` und stammen aus/lehnen sich an OpenPLi-/EnigmaLight-Technik an; Lizenz- und Herkunftshinweise müssen bei Weiterverwendung beachtet werden. Siehe [Sicherheit](docs/SECURITY.md).

## Status

Dieses Projekt ist ein experimenteller Hardware-Port. Mit 25 FPS wird eine lokale Messung beschrieben, keine allgemeine Leistungszusage. Der bekannte Vorblitz bei schnellen Schwarz-Weiß-Wechseln ist noch in Untersuchung.
