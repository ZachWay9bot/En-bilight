#!/bin/sh
# En-bilight Standalone V2R2: CPU/RAM top-right; update ONLY UI and LAN web server.
# SPDX-License-Identifier: GPL-2.0-only
set -eu
DIR=/home/en-bilight
STAGE=/tmp/en-bilight-sysmon-v2r2
BACK=$DIR/rollback_before_sysmon_v2r2
RUNNING=0

[ -f "$DIR/service.sh" ] && [ -f "$DIR/led_layout.py" ] && [ -s "$DIR/web_r10.py" ] && [ -s "$DIR/index.html" ] || {
  echo 'ABBRUCH: En-bilight Standalone V2/V2R1 nicht vorhanden. Erst Standalone installieren.';exit 31;
}
[ -s "$STAGE/index.html" ] && [ -s "$STAGE/web_r10.py" ] && [ -s "$STAGE/rollback_sysmon_v2r2.sh" ] || {
  echo 'ABBRUCH: Updatepaket unvollstaendig.';exit 32;
}
# Parse before touching the running program. No bytecode created on receiver.
python3 - "$STAGE" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
s=(p/'web_r10.py').read_text()
compile(s,'web_r10.py','exec')
h=(p/'index.html').read_text()
for word in ('Standalone V2R2','id="sys-cpu"','id="sys-ram"','id="sys-ram-bar"','renderSystem(s)'):
    assert word in h, 'UI fehlt: '+word
assert 'SYSTEM_METRICS.snapshot()' in s
PY

if cmp -s "$STAGE/index.html" "$DIR/index.html" && cmp -s "$STAGE/web_r10.py" "$DIR/web_r10.py";then
  echo 'EN_BILIGHT_SYSMON_V2R2_BEREITS_INSTALLIERT';exit 0
fi
mkdir -p "$BACK"
# Never destroy the original rollback snapshot during repeated update runs.
if [ ! -f "$BACK/index.html" ] && [ ! -f "$BACK/web_r10.py" ];then
  cp -p "$DIR/index.html" "$BACK/index.html"
  cp -p "$DIR/web_r10.py" "$BACK/web_r10.py"
  chmod 600 "$BACK/index.html" "$BACK/web_r10.py"
fi
[ -s "$BACK/index.html" ] && [ -s "$BACK/web_r10.py" ] || {
  echo 'ABBRUCH: Ruecksetz-Dateien fehlen.';exit 33;
}
cp "$STAGE/rollback_sysmon_v2r2.sh" "$DIR/rollback_sysmon_v2r2.sh"
chmod 700 "$DIR/rollback_sysmon_v2r2.sh"

if sh "$DIR/service.sh" status 2>/dev/null | grep -q '^STANDALONE_RUNNING';then
  RUNNING=1
  echo 'Standalone ist aktiv. Kontrollierter kurzer Neustart, kein zweiter LED-Sender.'
  sh "$DIR/service.sh" stop || { echo 'ABBRUCH: Standalone konnte nicht beendet werden.';exit 34; }
fi
restore() {
  echo 'FEHLER: Stelle bisheriges Dashboard und Webserver wieder her.'
  cp -p "$BACK/index.html" "$DIR/index.html" || true
  cp -p "$BACK/web_r10.py" "$DIR/web_r10.py" || true
  if [ "$RUNNING" -eq 1 ];then sh "$DIR/service.sh" start || true;fi
}
if ! cp "$STAGE/index.html" "$DIR/.sysmon-index.tmp" || ! cp "$STAGE/web_r10.py" "$DIR/.sysmon-web.tmp";then
  restore;exit 35
fi
chmod 644 "$DIR/.sysmon-index.tmp" "$DIR/.sysmon-web.tmp"
if ! mv -f "$DIR/.sysmon-index.tmp" "$DIR/index.html" || ! mv -f "$DIR/.sysmon-web.tmp" "$DIR/web_r10.py";then
  restore;exit 36
fi
if ! cmp -s "$STAGE/index.html" "$DIR/index.html" || ! cmp -s "$STAGE/web_r10.py" "$DIR/web_r10.py";then
  restore;exit 37
fi
if [ "$RUNNING" -eq 1 ];then
  if ! sh "$DIR/service.sh" start;then restore;exit 38;fi
else
  echo 'Standalone war gestoppt und bleibt gestoppt.'
fi
echo 'EN_BILIGHT_SYSMON_V2R2_OK | CPU/RAM jede Sekunde | Config, WLED, Autostart unveraendert.'
