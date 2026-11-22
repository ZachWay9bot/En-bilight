#!/bin/sh
# VU-Ambilight R10R5 slider-only patch. Only two files modified, no config/autostart changes.
set -eu
DIR=/home/elight-addons/vu_ambilight_r10r2
RUN=/tmp/vu_ambilight_r10r2
STAGE=/tmp/vu_ambilight_slider_r5_stage
BACKUP=$DIR/rollback_pre_v1r10r5_regler
SERVICE=$DIR/service.sh
[ -f "$SERVICE" ] || { echo 'FEHLER: V1R10R2-Dienst nicht installiert';exit 2; }
[ -f "$STAGE/patch_slider_ranges.py" ] || { echo 'FEHLER: Patch-Datei fehlt';exit 2; }
[ -f "$DIR/settings.cfg" ] || echo 'HINWEIS: settings.cfg noch nicht vorhanden, keine Aenderung an Einstellungen'
STATE=$(python3 -B "$STAGE/patch_slider_ranges.py" state "$DIR") || exit 3
if [ "$STATE" = new ]; then
 echo 'ALREADY_PATCHED. Die Bereiche sind bereits erweitert; kein Neustart erforderlich.'
 sh "$SERVICE" status
 exit 0
fi
[ "$STATE" = old ] || { echo 'FEHLER: Unbekannter Patch-Zustand';exit 3; }
python3 -B "$STAGE/patch_slider_ranges.py" selftest "$DIR" || exit 3
# Preserve unmodified originals, never overwrite an existing snapshot.
if [ -d "$BACKUP" ]; then
 for F in index.html effects_r10.py;do [ -f "$BACKUP/$F" ] || { echo 'FEHLER: Backup unvollstaendig';exit 4; };done
 python3 -B "$STAGE/patch_slider_ranges.py" compatible "$DIR" "$BACKUP" || { echo 'Snapshot stammt von anderer Version';exit 4; }
 echo 'SNAPSHOT_ALREADY_PRESENT'
else
 TMP="$BACKUP.tmp.$$"
 mkdir -p "$TMP"
 cp -p "$DIR/index.html" "$DIR/effects_r10.py" "$TMP/" || { rm -rf "$TMP";exit 4; }
 mv "$TMP" "$BACKUP"
 echo 'SNAPSHOT_CREATED'
fi
WAS_RUNNING=0
if sh "$SERVICE" status | grep -q '^SERVICE_RUNNING';then WAS_RUNNING=1;fi
if [ "$WAS_RUNNING" -eq 1 ];then
 echo 'STOP_SERVICE_FOR_CODE_CHANGE'
 sh "$SERVICE" stop || { echo 'FEHLER: Dienst liess sich nicht stoppen';exit 5; }
fi
recover() {
 echo 'RECOVER_PREVIOUS_SLIDER_FILES'
 cp -p "$BACKUP/index.html" "$BACKUP/effects_r10.py" "$DIR/" || true
 if [ "$WAS_RUNNING" -eq 1 ];then sh "$SERVICE" start || true;fi
}
if ! python3 -B "$STAGE/patch_slider_ranges.py" apply "$DIR";then recover;exit 6;fi
if ! python3 -B "$STAGE/patch_slider_ranges.py" verify "$DIR";then recover;exit 7;fi
if [ "$WAS_RUNNING" -eq 1 ];then
 if ! sh "$SERVICE" start;then recover;exit 8;fi
 echo 'SERVICE_RESTARTED'
else
 echo 'SERVICE_WAS_STOPPED; ist absichtlich gestoppt geblieben'
fi
echo 'REGELUPDATE_PASS: Sat 50..300, Gamma 60..300, bestehende Werte gespeichert'
echo 'Unveraendert: settings.cfg / Token / Autostart / Abtasttiefen / Flashguard / DDP'
sh "$SERVICE" status
