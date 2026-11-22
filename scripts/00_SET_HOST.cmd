@echo off
setlocal
set /p VU_HOST=VU+ IP-Adresse eingeben: 
if "%VU_HOST%"=="" exit /b 1
echo Dein Benutzer: root@%VU_HOST%
echo Start mit: ssh root@%VU_HOST%
pause
