#!/bin/sh
echo '=== En-bilight Standalone Diagnose ==='
cat /etc/issue 2>/dev/null
python3 --version || exit 1
if [ -r /proc/stb/info/chipset ];then
  CHIP=`cat /proc/stb/info/chipset`;echo "CHIPSET=$CHIP"
  case "$CHIP" in *73625*) :;; *) echo 'FEHLER: Nur BCM73625 getestet';exit 2;; esac
else echo 'FEHLER: /proc/stb/info/chipset fehlt';exit 2;fi
[ -r /dev/mem ] || { echo '/dev/mem fehlt/kein Leserecht';exit 3; }
python3 -c 'import os,sys,socket,time,mmap' || exit 4
echo 'PYTHON_CORE_OK; EnigmaLight wird nicht benoetigt.'
cd /home/en-bilight || exit 5
python3 -B fast_bcm73625_r10.py --r10-selftest || exit 6
echo '--- Host ---'
[ ! -s wled_host.txt ] || echo 'WLED_HOST_CONFIGURED'
echo '--- Dienst ---'
sh ./service.sh status
