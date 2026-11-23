#!/bin/sh
# OneClick Update from Standalone V1 to V2. Preserve all persistent configurations.
# SPDX-License-Identifier: GPL-2.0-only
set -eu
STAGE=/tmp/en-bilight-stage
DIR=/home/en-bilight
BACKUP=$DIR/rollback_before_led_dialog
FILES='effects_r10.py fast_bcm73625_r10.py web_r10.py index.html led_regions.txt led_layout.py service.sh supervisor.sh doctor.sh update_sysmon_v2r2.sh rollback_sysmon_v2r2.sh'
RUNNING=0
if [ -r "$DIR/service.sh" ] && sh "$DIR/service.sh" status | grep -q '^STANDALONE_RUNNING';then
  RUNNING=1
  echo 'Standalone laeuft: wird fuer das Update kontrolliert gestoppt.'
  sh "$DIR/service.sh" stop || exit 21
fi
if [ -d "$DIR" ];then
  mkdir -p "$BACKUP"
  rm -f "$BACKUP"/*.absent
  for f in $FILES;do
    if [ -f "$DIR/$f" ];then cp -p "$DIR/$f" "$BACKUP/$f";else : > "$BACKUP/$f.absent";fi
  done
fi
if ! sh "$STAGE/install.sh";then
  echo 'INSTALLATION FEHLGESCHLAGEN - vorherige Standalone-Dateien wiederherstellen.'
  if [ -d "$BACKUP" ];then
    for f in $FILES;do
      if [ -f "$BACKUP/$f" ];then cp -p "$BACKUP/$f" "$DIR/$f";
      elif [ -f "$BACKUP/$f.absent" ];then rm -f "$DIR/$f";fi
    done
  fi
  if [ "$RUNNING" -eq 1 ];then sh "$DIR/service.sh" start || true;fi
  exit 22
fi
if [ "$RUNNING" -eq 1 ];then
  echo 'Standalone war aktiv: starte wieder.'
  sh "$DIR/service.sh" start || exit 23
else
  echo 'Standalone war aus: bleibt aus. Kein unerwuenschter Start.'
fi
echo 'EN_BILIGHT_V2_LED_DIALOG_UPDATE_OK'
