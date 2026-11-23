@echo off
setlocal EnableExtensions
set "IP=192.168.1.10"
set "SSH=ssh"
set "SCP=scp"
%SSH% root@%IP% "sh /home/en-bilight/service.sh stop"
pause
