#!/bin/sh
# Restore exactly the web backend and UI that were present before V2R2.
# SPDX-License-Identifier: GPL-2.0-only
set -eu
DIR=/home/en-bilight
BACK=$DIR/rollback_before_sysmon_v2r2
RUNNING=0
[ -s "$BACK/index.html" ] && [ -s "$BACK/web_r10.py" ] || {
 echo 'ABBRUCH: Kein V2R2-Ruecksetzpunkt vorhanden.';exit 41;
}
if sh "$DIR/service.sh" status 2>/dev/null | grep -q '^STANDALONE_RUNNING';then
 RUNNING=1
 sh "$DIR/service.sh" stop || exit 42
fi
cp -p "$BACK/index.html" "$DIR/.sysmon-rollback-index.tmp"
cp -p "$BACK/web_r10.py" "$DIR/.sysmon-rollback-web.tmp"
chmod 644 "$DIR/.sysmon-rollback-index.tmp" "$DIR/.sysmon-rollback-web.tmp"
mv -f "$DIR/.sysmon-rollback-index.tmp" "$DIR/index.html"
mv -f "$DIR/.sysmon-rollback-web.tmp" "$DIR/web_r10.py"
if [ "$RUNNING" -eq 1 ];then sh "$DIR/service.sh" start || exit 43;fi
echo 'EN_BILIGHT_SYSMON_V2R2_ZURUECK - alter Webstand wiederhergestellt.'
