#!/bin/sh
set -eu
DIR=/home/elight-addons/vu_ambilight_r10r2
RUN=/tmp/vu_ambilight_r10r2
BACKUP=$DIR/rollback_v1r10r2_pre_depth
FILES='effects_r10.py fast_bcm73625_r10.py web_r10.py index.html'
SERVICE="$DIR/service.sh"
[ -f "$SERVICE" ] || { echo 'FEHLER: Alter Service fehlt';exit 2; }
for F in $FILES; do [ -f "$BACKUP/$F" ] || { echo "FEHLER: Keine Sicherung $F";exit 3; };done
WAS_RUNNING=0
if [ -f "$RUN/supervisor.pid" ]; then
 P=`cat "$RUN/supervisor.pid"`
 case "$P" in ''|*[!0-9]*) ;; *)
  if [ -r "/proc/$P/cmdline" ] && tr '\000' ' ' < "/proc/$P/cmdline" | grep -q 'vu_ambilight_r10r2/supervisor.sh'; then WAS_RUNNING=1; fi
 esac
fi
if [ "$WAS_RUNNING" -eq 1 ]; then sh "$SERVICE" stop || exit 4;fi
for F in $FILES;do cp "$BACKUP/$F" "$DIR/$F" || exit 5;done
cd "$DIR"
python3 -B fast_bcm73625_r10.py --r10-selftest || { echo 'WARNUNG: wiederhergestellter Selbsttest fehlgeschlagen';exit 6; }
if [ "$WAS_RUNNING" -eq 1 ]; then sh "$SERVICE" start || exit 7;fi
echo 'RESTORE_PASS V1R10R2-Code wiederhergestellt; Einstellungen/Autostart unveraendert.'
sh "$SERVICE" status
