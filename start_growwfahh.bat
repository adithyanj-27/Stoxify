@echo off
title GrowwFAHH - Stock & Mutual Fund Trading Platform
echo =======================================================
echo          Starting GrowwFAHH Platform...
echo =======================================================
py run.py
if %ERRORLEVEL% NEQ 0 (
    python run.py
)
pause
