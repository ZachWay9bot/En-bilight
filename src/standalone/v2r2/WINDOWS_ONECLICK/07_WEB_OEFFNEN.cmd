@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
set "SSH=ssh"
set "SCP=scp"
set "KEY="
for /f "usebackq delims=" %%T in (`%SSH% root@%IP% "cat /home/en-bilight/web_token.txt"`) do set "KEY=%%T"
if not defined KEY (echo Kein Web-Token gefunden. Erst Standalone starten.& pause & exit /b 1)
start "" "http://%IP%:8095/?key=%KEY%"
echo Browser geoeffnet.
