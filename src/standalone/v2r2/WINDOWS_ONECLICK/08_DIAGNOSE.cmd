@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
set "SSH=ssh"
set "SCP=scp"
%SSH% root@%IP% "sh /home/en-bilight/doctor.sh; echo === SERVICE LOG ===; tail -n 20 /tmp/en-bilight/supervisor.log 2>/dev/null; echo === LIVE LOG ===; tail -n 20 /tmp/en-bilight/live.log 2>/dev/null"
pause
