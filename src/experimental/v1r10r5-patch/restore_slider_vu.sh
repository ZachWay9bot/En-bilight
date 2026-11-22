#!/bin/sh
# Only rollback gamma and saturation slider edits.
set -eu
DIR=/home/elight-addons/vu_ambilight_r10r2
BACKUP=$DIR/rollback_pre_v1r10r5_regler
SERVICE=$DIR/service.sh
PATCH=/tmp/vu_ambilight_slider_r5_stage/patch_slider_ranges.py
[ -f "$SERVICE" ] || { echo 'FEHLER: Dienst fehlt';exit 2; }
[ -f "$PATCH" ] || { echo 'FEHLER: Patch-Pruefdatei fehlt';exit 2; }
for F in index.html effects_r10.py;do [ -f "$BACKUP/$F" ] || { echo "FEHLER: Snapshot fehlt: $F";exit 2; };done
# Do not overwrite an upgraded version unrelated to the original snapshot.
python3 -B "$PATCH" compatible "$DIR" "$BACKUP" || exit 3
# The old version rejects values >180; refuse rollback instead of corrupting a live service.
python3 -B - "$DIR/settings.cfg" <<'PY_CHECK'
import sys
try:
    with open(sys.argv[1]) as f:
        for line in f:
            k,sep,v=line.strip().partition('=')
            if sep and k in ('saturation_pct','gamma_red','gamma_green','gamma_blue') and int(v)>180:
                print('ROLLBACK_BLOCKED: '+k+'='+v+' > 180. Zuerst im Webinterface auf 180 oder weniger stellen.')
                sys.exit(3)
except FileNotFoundError:
    pass
PY_CHECK
WAS_RUNNING=0
if sh "$SERVICE" status | grep -q '^SERVICE_RUNNING';then WAS_RUNNING=1;fi
if [ "$WAS_RUNNING" -eq 1 ];then sh "$SERVICE" stop || exit 4;fi
cp -p "$BACKUP/index.html" "$BACKUP/effects_r10.py" "$DIR/" || exit 5
if [ "$WAS_RUNNING" -eq 1 ];then sh "$SERVICE" start || exit 6;fi
echo 'RESTORE_PASS: Nur Reglerdateien wiederhergestellt. Settings/Autostart unveraendert.'
sh "$SERVICE" status
