@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
echo === STANDALONE V2 LED-DIALOG: CODE-ROLLBACK ===
echo Settings, WLED-IP, Web-Token, AutoStart werden nicht veraendert.
choice /c JN /m "Vorherigen Standalone-Code wiederherstellen"
if errorlevel 2 exit /b 0
ssh root@%IP% "sh /home/en-bilight/rollback_led_dialog.sh && sh /home/en-bilight/service.sh status"
pause
