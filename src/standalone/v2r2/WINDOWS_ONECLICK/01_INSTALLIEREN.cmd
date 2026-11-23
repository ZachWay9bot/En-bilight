@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
set "SSH=ssh"
set "SCP=scp"
cd /d "%~dp0"
echo === EN-BILIGHT STANDALONE INSTALLATION ===
echo Diese Aktion installiert nichts von EnigmaLight und stoppt keinen Dienst.
%SSH% root@%IP% "mkdir -p /tmp/en-bilight-stage" || goto :error
%SCP% "..\en-bilight-runtime.tar.gz" root@%IP%:/tmp/en-bilight-runtime.tar.gz || goto :error
%SSH% root@%IP% "tar -xzf /tmp/en-bilight-runtime.tar.gz -C /tmp/en-bilight-stage && sh /tmp/en-bilight-stage/install.sh" || goto :error
echo Installation abgeschlossen. Erst Testwechsel via 02_TESTWECHSEL.cmd.
pause
exit /b 0
:error
echo FEHLER: Installation nicht fertig, Logs oben lesen.
pause
exit /b 1
