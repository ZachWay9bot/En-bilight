@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
cd /d "%~dp0"
echo =========================================================
echo  EN-BILIGHT V2 LED KONFIGURATION - ONECLICK UPDATE
 echo =========================================================
echo Dieses Update bewahrt Settings, WLED-IP, Web-Token und Autostart.
echo Nur der eigene Standalone-Dienst wird gegebenenfalls kurz gestoppt.
echo EnigmaLight und die bisherigen Freeze-Staende bleiben unberuehrt.
choice /c JN /m "LED-Konfigurationsdialog installieren"
if errorlevel 2 exit /b 0
ssh root@%IP% "mkdir -p /tmp/en-bilight-stage" || goto :error
scp "..\en-bilight-runtime.tar.gz" root@%IP%:/tmp/en-bilight-runtime.tar.gz || goto :error
ssh root@%IP% "tar -xzf /tmp/en-bilight-runtime.tar.gz -C /tmp/en-bilight-stage && sh /tmp/en-bilight-stage/update.sh && sh /home/en-bilight/service.sh status" || goto :error
echo.
echo V2 installiert. Webbrowser per 07_WEB_OEFFNEN.cmd oeffnen, STRG+F5.
pause
exit /b 0
:error
echo FEHLER: Ausgabe oben pruefen. Update-Rollback ist in update.sh integriert.
pause
exit /b 1
