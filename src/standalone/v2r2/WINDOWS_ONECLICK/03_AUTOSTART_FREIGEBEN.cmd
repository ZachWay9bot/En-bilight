@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
set "SSH=ssh"
set "SCP=scp"
echo === Standalone dauerhaft aktivieren ===
echo Erst aktivieren, wenn Farben, FPS und Bedienung am Receiver getestet sind.
choice /c JN /m "Alten VU-Ambilight-Autostart deaktivieren und Standalone aktivieren"
if errorlevel 2 exit /b 0
%SSH% root@%IP% "if [ -f /home/elight-addons/vu_ambilight_r10r2/service.sh ];then sh /home/elight-addons/vu_ambilight_r10r2/service.sh stop && sh /home/elight-addons/vu_ambilight_r10r2/service.sh disable || exit 2;fi; sh /home/en-bilight/service.sh enable && sh /home/en-bilight/service.sh start && sh /home/en-bilight/service.sh status"
pause
