@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
cd /d "%~dp0"
echo =============================================================
echo EN-BILIGHT STANDALONE V2R2 - LIVE CPU / RAM IM DASHBOARD
echo =============================================================
echo CPU und RAM in der Kopfzeile: echte Werte der VU+ jede 1 s.
echo Aendert NUR das Dashboard und den Webserver.
echo Standalone-Livebetrieb wird fuer das Update kontrolliert
 echo neu gestartet, falls er gerade laeuft.
echo RGB, 314 LED-Konfiguration, WLED-IP, Token und Autostart
 echo bleiben unveraendert. Keine Aenderung an EnigmaLight.
echo.
choice /c JN /m "CPU/RAM-Update installieren"
if errorlevel 2 exit /b 0
ssh root@%IP% "mkdir -p /tmp/en-bilight-sysmon-v2r2" || goto :error
scp "..\runtime\index.html" "..\runtime\web_r10.py" "..\runtime\rollback_sysmon_v2r2.sh" "..\runtime\update_sysmon_v2r2.sh" root@%IP%:/tmp/en-bilight-sysmon-v2r2/ || goto :error
ssh root@%IP% "sh /tmp/en-bilight-sysmon-v2r2/update_sysmon_v2r2.sh && sh /home/en-bilight/service.sh status" || goto :error
echo.
echo Update installiert. 07_WEB_OEFFNEN.cmd, dann Strg+F5.
pause
exit /b 0
:error
echo FEHLER: Ausgabe oben pruefen. Bei vorher erfolgreicher
 echo Installation mit 15_CPU_RAM_ZURUECK.cmd zurueckwechseln.
pause
exit /b 1
