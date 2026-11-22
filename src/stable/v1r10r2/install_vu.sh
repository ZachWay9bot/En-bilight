#!/bin/sh
set -eu
STAGE=/tmp/vu_ambilight_r10r2_stage
DIR=/home/elight-addons/vu_ambilight_r10r2
RUN=/tmp/vu_ambilight_r10r2
for F in effects_r10.py fast_bcm73625_r10.py web_r10.py index.html led_regions.txt service.sh supervisor.sh brightness_selftest.py; do
  [ -f "$STAGE/$F" ] || { echo "FEHLER: $F fehlt"; exit 2; }
done
if [ -f "$RUN/supervisor.pid" ]; then
  P=`cat "$RUN/supervisor.pid"`
  if [ -r "/proc/$P/cmdline" ] && tr '\000' ' ' < "/proc/$P/cmdline" | grep -q 'vu_ambilight_r10r2/supervisor.sh'; then
    echo 'FEHLER: R10R2 laeuft. Erst Stoppen, dann aktualisieren.'; exit 3
  fi
fi
mkdir -p "$DIR" "$RUN"
# Keep existing persistent settings and token. Migrate prior temporary user settings if available.
if [ ! -f "$DIR/settings.cfg" ] && [ -f /tmp/vu_ambilight_r10/settings.cfg ]; then
  cp /tmp/vu_ambilight_r10/settings.cfg "$DIR/settings.cfg"
  echo 'Vorhandene V1R10R1-Einstellungen uebernommen.'
fi
if [ ! -f "$DIR/web_token.txt" ] && [ -f /tmp/vu_ambilight_r10/web_token.txt ]; then
  cp /tmp/vu_ambilight_r10/web_token.txt "$DIR/web_token.txt"
fi
# Backup updated code only, keep original files available.
if [ -f "$DIR/fast_bcm73625_r10.py" ]; then
  mkdir -p "$DIR/previous_update"
  for F in effects_r10.py fast_bcm73625_r10.py web_r10.py index.html led_regions.txt service.sh supervisor.sh brightness_selftest.py; do
    [ ! -f "$DIR/$F" ] || cp "$DIR/$F" "$DIR/previous_update/$F"
  done
fi
for F in effects_r10.py fast_bcm73625_r10.py web_r10.py index.html led_regions.txt service.sh supervisor.sh brightness_selftest.py; do
  cp "$STAGE/$F" "$DIR/$F"
done
chmod 755 "$DIR/service.sh" "$DIR/supervisor.sh"
chmod 700 "$DIR"
[ ! -f "$DIR/settings.cfg" ] || chmod 600 "$DIR/settings.cfg"
[ ! -f "$DIR/web_token.txt" ] || chmod 600 "$DIR/web_token.txt"
cd "$DIR"
python3 -B fast_bcm73625_r10.py --r10-selftest
python3 -B "$STAGE/brightness_selftest.py"
# Do not enable autostart from installer.
echo 'INSTALLATION PASS: R10R2 dauerhaft abgelegt. Autostart NOCH AUS.'
