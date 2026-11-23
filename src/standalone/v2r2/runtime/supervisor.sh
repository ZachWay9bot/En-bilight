#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
DIR=/home/en-bilight
RUN=/tmp/en-bilight
mkdir -p "$RUN"
LIVE_PID=
WEB_PID=
STOP=0
safe_kill() {
  P="$1";MATCH="$2"
  case "$P" in ''|*[!0-9]*) return;; esac
  if [ -r "/proc/$P/cmdline" ] && tr '\000' ' ' < "/proc/$P/cmdline" | grep -q "$MATCH";then
    kill -TERM "$P" 2>/dev/null || true
  fi
}
cleanup() {
  STOP=1
  safe_kill "$LIVE_PID" '/home/en-bilight/fast_bcm73625_r10.py'
  safe_kill "$WEB_PID" '/home/en-bilight/web_r10.py'
  [ -z "$LIVE_PID" ] || wait "$LIVE_PID" 2>/dev/null || true
  [ -z "$WEB_PID" ] || wait "$WEB_PID" 2>/dev/null || true
  rm -f "$RUN/live.pid" "$RUN/web.pid"
  echo 'SUPERVISOR_STOPPED'
}
trap 'cleanup; exit 0' TERM INT HUP
start_web() {
  cd "$DIR" || exit 1
  python3 -B -u "$DIR/web_r10.py" > "$RUN/web.log" 2>&1 < /dev/null &
  WEB_PID=$!;echo "$WEB_PID" > "$RUN/web.pid"
  sleep 1
  if ! kill -0 "$WEB_PID" 2>/dev/null;then
    echo 'WEB_START_FAILED';cat "$RUN/web.log";WEB_PID=;return 1
  fi
  echo "WEB_STARTED pid=$WEB_PID"
}
start_web || true
sleep 4
while [ "$STOP" -eq 0 ];do
  if [ -z "$WEB_PID" ] || ! kill -0 "$WEB_PID" 2>/dev/null;then start_web || true;fi
  cd "$DIR" || exit 1
  python3 -B -u "$DIR/fast_bcm73625_r10.py" --r10-daemon-live --ack-wled > "$RUN/live.log" 2>&1 < /dev/null &
  LIVE_PID=$!;echo "$LIVE_PID" > "$RUN/live.pid"
  wait "$LIVE_PID"
  RC=$?
  echo "LIVE_EXIT rc=$RC" >> "$RUN/supervisor.log"
  rm -f "$RUN/live.pid";LIVE_PID=
  sleep 7
done
cleanup
