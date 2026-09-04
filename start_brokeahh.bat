@echo off
title BrokeAhh - Stock & Mutual Fund Broker Platform
echo =======================================================
echo          Starting BrokeAhh Platform...
echo =======================================================
py run.py
if %ERRORLEVEL% NEQ 0 (
    python run.py
)
pause
