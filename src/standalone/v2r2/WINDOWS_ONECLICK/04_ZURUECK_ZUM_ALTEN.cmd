@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
set "SSH=ssh"
set "SCP=scp"
echo === Standalone stoppen und alten VU-Ambilight-Dienst zurueckholen ===
choice /c JN /m "Altes Ambilight und dessen Autostart wieder aktivieren"
if errorlevel 2 exit /b 0
%SSH% root@%IP% "sh /home/en-bilight/service.sh stop && sh /home/en-bilight/service.sh disable && if [ -f /home/elight-addons/vu_ambilight_r10r2/service.sh ]; then sh /home/elight-addons/vu_ambilight_r10r2/service.sh enable && sh /home/elight-addons/vu_ambilight_r10r2/service.sh start; else echo 'Kein alter Dienst vorhanden'; fi"
pause
