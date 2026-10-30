@echo off
title StudyBuddy AI - Public Internet Host
echo ========================================================================
echo        StudyBuddy AI - Collaborative Study Hub (Public Host)
echo ========================================================================
echo.
echo [*] Launching Cloudflare Public Tunnel for StudyBuddy AI...
echo [*] Local backend must be running on http://localhost:8000
echo.
echo ------------------------------------------------------------------------
echo Look below for your unique public https://xxxx.trycloudflare.com link:
echo ------------------------------------------------------------------------
echo.
.\cloudflared.exe tunnel --url http://localhost:8000
pause

