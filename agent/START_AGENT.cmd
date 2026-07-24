@echo off
title Infrastructure Monitoring Agent
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-agent.ps1" -PauseOnExit %*
