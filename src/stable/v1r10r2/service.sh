#!/bin/sh
# OpenPLi SysV-style service manager. Does not touch Enigma2 itself.
DIR=/home/elight-addons/vu_ambilight_r10r2
RUN=/tmp/vu_ambilight_r10r2
SERVICE=/etc/init.d/vuambilight-r10r2
LINK=/etc/rc3.d/S98vuambilight-r10r2
mkdir -p "$RUN"
ispid() { case "$1" in ''|*[!0-9]*) return 1;; esac; [ -r "/proc/$1/cmdline" ] || return 1; tr '\000' ' ' < "/proc/$1/cmdline" | grep -q 'vu_ambilight_r10r2/supervisor.sh'; }
pid() { if [ -f "$RUN/supervisor.pid" ]; then cat "$RUN/supervisor.pid"; fi; }
case "$1" in
  start)
    P=`pid`
    if ispid "$P"; then echo "ALREADY_RUNNING pid=$P"; exit 0; fi
    rm -f "$RUN/supervisor.pid"
    # Fail safe: don't start while old test branch is still using port 8095.
    if [ -f /tmp/vu_ambilight_r10/web.pid ]; then
      OLD=`cat /tmp/vu_ambilight_r10/web.pid`
      if [ -r "/proc/$OLD/cmdline" ] && tr '\000' ' ' < "/proc/$OLD/cmdline" | grep -q 'web_r10.py'; then
        echo 'FEHLER: Alte V1R10-Weboberflaeche laeuft. Erst 05_STOP_WEB.cmd aus R10R1 verwenden.';exit 3
      fi
    fi
    if ps | grep -E '[f]ast_bcm73625_r10.py.*--r10-(live|probe)' >/dev/null; then
      echo 'FEHLER: ein alter R10-Livetest laeuft. Erst Strg+C.';exit 4
    fi
    sh "$DIR/supervisor.sh" >> "$RUN/supervisor.log" 2>&1 < /dev/null &
    P=$!
    echo "$P" > "$RUN/supervisor.pid"
    sleep 2
    if ! ispid "$P"; then
      echo 'FEHLER: Dienststart fehlgeschlagen.';cat "$RUN/supervisor.log";exit 5
    fi
    echo "SERVICE_STARTED pid=$P (Web und TV werden nach Bereitschaft gestartet)";;
  stop)
    P=`pid`
    if ispid "$P"; then
      kill -TERM "$P" 2>/dev/null || true
      N=0
      while ispid "$P" && [ "$N" -lt 10 ]; do sleep 1; N=$((N+1)); done
      if ispid "$P"; then echo 'WARNUNG: Supervisor reagiert nicht; kein gewaltsames Beenden.';exit 6;fi
      echo 'SERVICE_STOPPED'
    else echo 'SERVICE_ALREADY_STOPPED';fi
    rm -f "$RUN/supervisor.pid";;
  status)
    P=`pid`
    if ispid "$P"; then echo "SERVICE_RUNNING pid=$P";else echo 'SERVICE_STOPPED';fi
    if [ -L "$LINK" ]; then echo 'AUTOSTART_ENABLED';else echo 'AUTOSTART_DISABLED';fi
    [ ! -f "$RUN/live_status.txt" ] || cat "$RUN/live_status.txt"
    ;;
  enable)
    [ -d /etc/rc3.d ] && [ -d /etc/init.d ] || { echo 'FEHLER: OpenPLi SysV rc3.d nicht vorhanden. Autostart nicht aktiviert.';exit 7; }
    if [ -e "$SERVICE" ] && [ ! -f "$DIR/service_installed.marker" ]; then
      echo 'FEHLER: Gleichnamiger fremder Init-Dienst existiert.';exit 8
    fi
    # Only our own script is installed at the known path.
    printf '#!/bin/sh\nexec /bin/sh /home/elight-addons/vu_ambilight_r10r2/service.sh "$1"\n' > "$SERVICE" || exit 9
    chmod 755 "$SERVICE"
    touch "$DIR/service_installed.marker"
    if [ -L "$LINK" ]; then
      [ "`readlink "$LINK"`" = '../init.d/vuambilight-r10r2' ] || { echo 'FEHLER: Runlevel-Link bereits anderweitig belegt.';exit 10; }
    elif [ -e "$LINK" ]; then echo 'FEHLER: Runlevel-Link ist fremde Datei.';exit 11
    else ln -s ../init.d/vuambilight-r10r2 "$LINK";fi
    echo 'AUTOSTART_ENABLED (Boot Runlevel 3)';;
  disable)
    if [ -L "$LINK" ] && [ "`readlink "$LINK"`" = '../init.d/vuambilight-r10r2' ]; then rm -f "$LINK";fi
    echo 'AUTOSTART_DISABLED (laufender Dienst bleibt aktiv)';;
  restart) "$0" stop && "$0" start;;
  *) echo 'Usage: service.sh start|stop|status|enable|disable|restart';exit 2;;
esac
