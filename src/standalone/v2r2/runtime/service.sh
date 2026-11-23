#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Standalone En-bilight service; does not need EnigmaLight.
DIR=/home/en-bilight
RUN=/tmp/en-bilight
SERVICE=/etc/init.d/en-bilight
LINK=/etc/rc3.d/S98en-bilight
OLDSERVICE=/home/elight-addons/vu_ambilight_r10r2/service.sh
mkdir -p "$RUN"
ispid() {
  case "$1" in ''|*[!0-9]*) return 1;; esac
  [ -r "/proc/$1/cmdline" ] || return 1
  tr '\000' ' ' < "/proc/$1/cmdline" | grep -q '/home/en-bilight/supervisor.sh'
}
pid() { [ ! -f "$RUN/supervisor.pid" ] || cat "$RUN/supervisor.pid"; }
oldrunning() {
  [ -f "$OLDSERVICE" ] || return 1
  sh "$OLDSERVICE" status 2>/dev/null | grep -q '^SERVICE_RUNNING'
}
case "${1:-}" in
  start)
    P=`pid`
    if ispid "$P"; then echo "ALREADY_RUNNING pid=$P";exit 0;fi
    if oldrunning; then echo 'BLOCKIERT: Alter VU-Ambilight-Dienst laeuft. Erst kontrolliert stoppen.';exit 20;fi
    if ps | grep -E '[e]nigmalight (-m|$)' >/dev/null;then
      echo 'BLOCKIERT: EnigmaLight-Prozess laeuft. Erst beenden.';exit 21
    fi
    if ps | grep -E '[f]ast_bcm73625_r10.py.*--r10-(daemon-live|live)' >/dev/null;then
      echo 'BLOCKIERT: Ein anderer Ambilight-Capture-Prozess laeuft.';exit 22
    fi
    [ -s "$DIR/wled_host.txt" ] || { echo 'BLOCKIERT: WLED-Ziel fehlt';exit 23; }
    rm -f "$RUN/supervisor.pid"
    sh "$DIR/supervisor.sh" >> "$RUN/supervisor.log" 2>&1 < /dev/null &
    P=$!;echo "$P" > "$RUN/supervisor.pid"
    sleep 2
    if ! ispid "$P"; then echo 'START FEHLGESCHLAGEN'; tail -n 20 "$RUN/supervisor.log";exit 24;fi
    echo "STANDALONE_RUNNING pid=$P";;
  stop)
    P=`pid`
    if ispid "$P";then
      kill -TERM "$P" 2>/dev/null || true
      i=0
      while ispid "$P" && [ "$i" -lt 12 ];do sleep 1;i=$((i+1));done
      if ispid "$P";then echo 'STOP_TIMEOUT: nicht hart beendet';exit 25;fi
    fi
    rm -f "$RUN/supervisor.pid"
    echo STANDALONE_STOPPED;;
  status)
    P=`pid`;if ispid "$P";then echo "STANDALONE_RUNNING pid=$P";else echo STANDALONE_STOPPED;fi
    if [ -L "$LINK" ] && [ "`readlink "$LINK"`" = '../init.d/en-bilight' ];then echo AUTOSTART_ENABLED;else echo AUTOSTART_DISABLED;fi
    [ ! -f "$RUN/live_status.txt" ] || cat "$RUN/live_status.txt";;
  enable)
    [ -d /etc/init.d ] && [ -d /etc/rc3.d ] || { echo 'OpenPLi Runlevel 3 fehlt';exit 26; }
    if [ -e "$SERVICE" ] && ! grep -q '/home/en-bilight/service.sh' "$SERVICE";then
      echo 'Fremder Dienstname existiert';exit 27
    fi
    printf '#!/bin/sh\nexec /bin/sh /home/en-bilight/service.sh "$1"\n' > "$SERVICE"
    chmod 755 "$SERVICE"
    if [ -L "$LINK" ];then
      [ "`readlink "$LINK"`" = '../init.d/en-bilight' ] || { echo 'Fremder Symlink vorhanden';exit 28; }
    elif [ -e "$LINK" ];then echo 'Fremde Runlevel-Datei vorhanden';exit 29
    else ln -s ../init.d/en-bilight "$LINK";fi
    echo AUTOSTART_ENABLED;;
  disable)
    if [ -L "$LINK" ] && [ "`readlink "$LINK"`" = '../init.d/en-bilight' ];then rm -f "$LINK";fi
    echo AUTOSTART_DISABLED;;
  restart) "$0" stop && "$0" start;;
  *) echo 'Usage: service.sh start|stop|status|enable|disable|restart';exit 2;;
esac
