#!/bin/sh
# V1R10R4 optional flash-guard patch. Requires currently installed R10R3.
set -eu
DIR=/home/elight-addons/vu_ambilight_r10r2
RUN=/tmp/vu_ambilight_r10r2
STAGE=/tmp/vu_ambilight_r10r4_stage
BACKUP=$DIR/rollback_v1r10r3_pre_guard
FILES='effects_r10.py fast_bcm73625_r10.py web_r10.py index.html'
SERVICE="$DIR/service.sh"
[ -f "$SERVICE" ] || { echo 'FEHLER: V1R10R2 Basisservice fehlt.';exit 2; }
grep -q 'V1R10R3' "$DIR/fast_bcm73625_r10.py" || { echo 'FEHLER: V1R10R3 ist nicht installiert. Kein Update.'; exit 2; }
for F in $FILES rollback_r10r4.sh; do [ -f "$STAGE/$F" ] || { echo "FEHLER: Stage $F fehlt";exit 2; }; done
cd "$STAGE"
VU_AMBILIGHT_HOME="$DIR" VU_AMBILIGHT_RUNTIME="$RUN" python3 -B fast_bcm73625_r10.py --r10-selftest || { echo 'SELFTEST_BEFORE_INSTALL_FAILED';exit 3; }
if [ -d "$BACKUP" ]; then
 for F in $FILES; do [ -f "$BACKUP/$F" ] || { echo "FEHLER: Backup unvollstaendig $F";exit 4; }; done
 echo 'R10R3_SNAPSHOT_ALREADY_EXISTS'
else
 mkdir -p "$BACKUP"
 for F in $FILES; do
  [ -f "$DIR/$F" ] || { echo "FEHLER: Installierte $F fehlt";exit 4; }
  cp -p "$DIR/$F" "$BACKUP/$F" || exit 4
 done
 echo 'R10R3_SNAPSHOT_CREATED'
fi
WAS_RUNNING=0
if [ -f "$RUN/supervisor.pid" ]; then
 P=`cat "$RUN/supervisor.pid"`
 case "$P" in ''|*[!0-9]*) ;; *)
  if [ -r "/proc/$P/cmdline" ] && tr '\000' ' ' < "/proc/$P/cmdline" | grep -q 'vu_ambilight_r10r2/supervisor.sh'; then WAS_RUNNING=1;fi
 esac
fi
if [ "$WAS_RUNNING" -eq 1 ]; then
 sh "$SERVICE" stop || { echo 'SERVICE_STOP_FAILED';exit 5; }
fi
recover() {
 echo 'R10R3_RESTORE_AFTER_ERROR'
 for F in $FILES; do cp "$BACKUP/$F" "$DIR/$F" || true; done
 if [ "$WAS_RUNNING" -eq 1 ]; then sh "$SERVICE" start || true;fi
}
if ! cp "$STAGE/rollback_r10r4.sh" "$DIR/rollback_r10r4.sh";then recover;exit 6;fi
chmod 700 "$DIR/rollback_r10r4.sh"
for F in $FILES; do
 if ! cp "$STAGE/$F" "$DIR/$F"; then recover;exit 6;fi
done
cd "$DIR"
if ! python3 -B fast_bcm73625_r10.py --r10-selftest;then recover;exit 7;fi
if [ "$WAS_RUNNING" -eq 1 ]; then
 if ! sh "$SERVICE" start;then recover;exit 8;fi
fi
echo 'UPDATE_PASS V1R10R4 FLASHGUARD; Standard AUS (1 Frame)'
echo 'GESPERRT: Keine Aenderung an Settings, Originalen, Autostart, LED-Zonen.'
sh "$SERVICE" status
