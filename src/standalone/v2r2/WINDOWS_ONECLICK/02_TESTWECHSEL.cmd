@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
set "SSH=ssh"
set "SCP=scp"
echo === Kontrollierter Testwechsel auf eigenstaendiges En-bilight ===
echo Alte Software wird nur GESTOPPT. Alter Autostart bleibt bis zur Freigabe bestehen.
echo Pi-Hyperion muss ebenfalls gestoppt sein.
choice /c JN /m "Pi-Hyperion gestoppt, alten Dienst stoppen und Standalone starten"
if errorlevel 2 exit /b 0
%SSH% root@%IP% "if [ -f /home/elight-addons/vu_ambilight_r10r2/service.sh ]; then sh /home/elight-addons/vu_ambilight_r10r2/service.sh stop || exit 2; fi; sh /home/en-bilight/service.sh start; sh /home/en-bilight/service.sh status" 
pause
