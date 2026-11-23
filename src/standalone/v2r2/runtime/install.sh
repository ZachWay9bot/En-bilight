#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
set -eu
STAGE=/tmp/en-bilight-stage
DIR=/home/en-bilight
OLDDIR=/home/elight-addons/vu_ambilight_r10r2
echo '=== En-bilight Standalone V2R2 Installation (ohne Autostart/Start) ==='
CHIP=`cat /proc/stb/info/chipset 2>/dev/null || true`
case "$CHIP" in *73625*) :;; *) echo "ABBRUCH: BCM73625 erwartet, gefunden: $CHIP";exit 12;; esac
python3 -c 'import os,sys,socket,time,mmap' || exit 13
for F in effects_r10.py fast_bcm73625_r10.py web_r10.py index.html led_regions.txt led_layout.py service.sh supervisor.sh doctor.sh rollback_led_dialog.sh update_sysmon_v2r2.sh rollback_sysmon_v2r2.sh;do
  [ -f "$STAGE/$F" ] || { echo "FEHLER: $F fehlt";exit 14; }
done
# Preflight from staging before mutating the installation.
(cd "$STAGE" && python3 -B fast_bcm73625_r10.py --r10-selftest) || { echo 'FEHLER: Staging-Selbsttest';exit 16; }
if [ -r "$DIR/service.sh" ] && sh "$DIR/service.sh" status | grep -q '^STANDALONE_RUNNING';then
  echo 'FEHLER: Standalone laeuft; vor einem Update stoppen';exit 15
fi
mkdir -p "$DIR" /tmp/en-bilight
chmod 700 "$DIR"
# No auto-configuration that erases an already working setup.
if [ -f "$DIR/fast_bcm73625_r10.py" ];then
  mkdir -p "$DIR/code_backup"
  for F in effects_r10.py fast_bcm73625_r10.py web_r10.py index.html led_regions.txt led_layout.py service.sh supervisor.sh doctor.sh rollback_led_dialog.sh update_sysmon_v2r2.sh rollback_sysmon_v2r2.sh;do
    [ ! -f "$DIR/$F" ] || cp "$DIR/$F" "$DIR/code_backup/$F"
  done
fi
for F in effects_r10.py fast_bcm73625_r10.py web_r10.py index.html led_regions.txt led_layout.py service.sh supervisor.sh doctor.sh rollback_led_dialog.sh update_sysmon_v2r2.sh rollback_sysmon_v2r2.sh;do
  cp "$STAGE/$F" "$DIR/$F"
done
chmod 755 "$DIR/service.sh" "$DIR/supervisor.sh" "$DIR/doctor.sh" "$DIR/update_sysmon_v2r2.sh" "$DIR/rollback_sysmon_v2r2.sh"
if [ ! -e "$DIR/settings.cfg" ] && [ -f "$OLDDIR/settings.cfg" ];then
  cp "$OLDDIR/settings.cfg" "$DIR/settings.cfg"
  echo 'Vorhandene Kalibrierung lokal uebernommen.'
fi
if [ ! -e "$DIR/wled_host.txt" ];then
  if [ -s /home/elight-addons/vu_ambilight/wled_host.txt ];then
    cp /home/elight-addons/vu_ambilight/wled_host.txt "$DIR/wled_host.txt"
    echo 'Vorhandenen WLED-Host lokal uebernommen.'
  elif [ -s "$OLDDIR/wled_host.txt" ];then
    cp "$OLDDIR/wled_host.txt" "$DIR/wled_host.txt"
  else
    echo 'HINWEIS: WLED-Ziel fehlt. WLED-IP in /home/en-bilight/wled_host.txt eintragen.'
  fi
fi
# Existing web token is only copied locally on the same box, never uploaded to GitHub.
if [ ! -e "$DIR/web_token.txt" ] && [ -f "$OLDDIR/web_token.txt" ];then
  cp "$OLDDIR/web_token.txt" "$DIR/web_token.txt"
fi
for F in settings.cfg wled_host.txt web_token.txt;do
  [ ! -f "$DIR/$F" ] || chmod 600 "$DIR/$F"
done
cd "$DIR"
python3 -B fast_bcm73625_r10.py --r10-selftest
echo 'INSTALLATION_OK V2R2 CPU/RAM-DASHBOARD ohne EnigmaLight | Kein Start, kein Autostart | Alt bleibt unveraendert.'
