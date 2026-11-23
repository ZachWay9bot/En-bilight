#!/bin/sh
# Restore previous standalone code, keeping settings, token and physical LED layout file.
# SPDX-License-Identifier: GPL-2.0-only
set -eu
DIR=/home/en-bilight
BACKUP=$DIR/rollback_before_led_dialog
FILES='effects_r10.py fast_bcm73625_r10.py web_r10.py index.html led_regions.txt led_layout.py service.sh supervisor.sh doctor.sh'
[ -d "$BACKUP" ] || { echo 'KEIN VORHERIGER CODE-BACKUP VORHANDEN';exit 30; }
RUNNING=0
if sh "$DIR/service.sh" status | grep -q '^STANDALONE_RUNNING';then RUNNING=1; sh "$DIR/service.sh" stop || exit 31;fi
for f in $FILES;do
  if [ -f "$BACKUP/$f" ];then cp -p "$BACKUP/$f" "$DIR/$f";
  elif [ -f "$BACKUP/$f.absent" ];then rm -f "$DIR/$f";fi
done
if [ "$RUNNING" -eq 1 ];then sh "$DIR/service.sh" start || exit 32;fi
echo 'VORHERIGER STANDALONE-CODE WIEDERHERGESTELLT'
