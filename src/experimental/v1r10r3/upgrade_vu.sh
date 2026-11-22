#!/bin/sh
# V1R10R3 update for installed R10R2. No changes to SysV autostart links.
set -eu
DIR=/home/elight-addons/vu_ambilight_r10r2
RUN=/tmp/vu_ambilight_r10r2
STAGE=/tmp/vu_ambilight_r10r3_stage
BACKUP=$DIR/rollback_v1r10r2_pre_depth
FILES='effects_r10.py fast_bcm73625_r10.py web_r10.py index.html'
SERVICE="$DIR/service.sh"

[ -f "$SERVICE" ] || { echo 'FEHLER: V1R10R2 nicht installiert. Erst das urspruengliche Paket installieren.'; exit 2; }
for F in $FILES led_regions.txt rollback_vu.sh; do
 [ -f "$STAGE/$F" ] || { echo "FEHLER: $F fehlt im Upload"; exit 2; }
done

# Test complete new engine offline before touching running service.
cd "$STAGE"
VU_AMBILIGHT_HOME="$DIR" VU_AMBILIGHT_RUNTIME="$RUN" python3 -B fast_bcm73625_r10.py --r10-selftest || { echo 'FEHLER: Selbsttest vor Installation'; exit 3; }

WAS_RUNNING=0
if [ -f "$RUN/supervisor.pid" ]; then
 P=`cat "$RUN/supervisor.pid"`
 case "$P" in ''|*[!0-9]*) ;; *)
  if [ -r "/proc/$P/cmdline" ] && tr '\000' ' ' < "/proc/$P/cmdline" | grep -q 'vu_ambilight_r10r2/supervisor.sh'; then WAS_RUNNING=1; fi
 esac
fi

# Create first rollback snapshot only; never overwrite on repeated updates.
if [ ! -d "$BACKUP" ]; then
 mkdir -p "$BACKUP"
 for F in $FILES; do
  [ -f "$DIR/$F" ] || { echo "FEHLER: installierte Datei fehlt: $F"; exit 4; }
  cp -p "$DIR/$F" "$BACKUP/$F"
 done
 echo 'FREEZE_BACKUP_CREATED'
else
 for F in $FILES; do [ -f "$BACKUP/$F" ] || { echo "FEHLER: Backup unvollstaendig: $F"; exit 4; }; done
 echo 'FREEZE_BACKUP_PRESERVED'
fi

if [ "$WAS_RUNNING" -eq 1 ]; then
 echo 'STOP_RUNNING_SERVICE'
 sh "$SERVICE" stop || { echo 'FEHLER: Dienst nicht sauber gestoppt. Keine Codeaenderung.'; exit 5; }
fi

# Fail-safe recovery: restoration can be called after partial update.
recover() {
 echo 'REVERT_CODE_FROM_SNAPSHOT'
 for F in $FILES; do cp "$BACKUP/$F" "$DIR/$F" || true; done
 if [ "$WAS_RUNNING" -eq 1 ]; then sh "$SERVICE" start || true; fi
}

cp "$STAGE/rollback_vu.sh" "$DIR/rollback_vu.sh" || { echo 'FEHLER: Rollback-Skript nicht kopiert'; recover; exit 6; }
chmod 700 "$DIR/rollback_vu.sh"
for F in $FILES; do
 if ! cp "$STAGE/$F" "$DIR/$F"; then
  echo "FEHLER: Kopie $F fehlgeschlagen";recover;exit 6
 fi
done
cd "$DIR"
if ! python3 -B fast_bcm73625_r10.py --r10-selftest; then
 echo 'FEHLER: neuer Code auf Zielsystem nicht lauffaehig';recover;exit 7
fi
if [ "$WAS_RUNNING" -eq 1 ]; then
 if ! sh "$SERVICE" start; then
  echo 'FEHLER: Dienststart; Rolle auf V1R10R2 zurueck';recover;exit 8
 fi
fi
# Keep original settings.cfg and web_token.txt untouched.
echo 'UPDATE_PASS V1R10R3: 4 Abtasttiefen 1..50%, Autostart und Einstellungen erhalten'
if [ "$WAS_RUNNING" -eq 1 ]; then echo 'SERVICE_RESTARTED';else echo 'SERVICE_WAS_STOPPED';fi
sh "$SERVICE" status
