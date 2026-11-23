@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
echo EN-BILIGHT - CPU/RAM-MONITOR ZURUECKNEHMEN
 echo Es werden NUR Webserver und Dashboard zurueckgesetzt.
choice /c JN /m "Vorherige V2R1-Oberflaeche und Webserver wiederherstellen"
if errorlevel 2 exit /b 0
ssh root@%IP% "sh /home/en-bilight/rollback_sysmon_v2r2.sh && sh /home/en-bilight/service.sh status" || goto :error
echo Ruecksetzung abgeschlossen. Browser Strg+F5.
pause
exit /b 0
:error
echo Ruecksetzung fehlgeschlagen. Siehe Ausgabe oben.
pause
exit /b 1
