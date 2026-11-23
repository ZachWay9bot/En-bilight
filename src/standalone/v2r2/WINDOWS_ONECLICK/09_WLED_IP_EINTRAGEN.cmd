@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
set "SSH=ssh"
set "SCP=scp"
set /p WLEDIP=WLED-IP eingeben (z.B. 192.168.1.50): 
if not defined WLEDIP exit /b 1
echo %WLEDIP% | findstr /r "^[0-9][0-9.]*$" >nul || (echo Bitte IPv4-Adresse eingeben.& pause & exit /b 2)
echo %WLEDIP%>"%TEMP%\en_bilight_wled_host.txt"
%SCP% "%TEMP%\en_bilight_wled_host.txt" root@%IP%:/home/en-bilight/wled_host.txt
if errorlevel 1 (echo IP-Uebertragung fehlgeschlagen& pause& exit /b 3)
%SSH% root@%IP% "chmod 600 /home/en-bilight/wled_host.txt"
echo WLED Host aktualisiert; laufenden Dienst ggf. neustarten.
pause
