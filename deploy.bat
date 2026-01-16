@echo off
echo ========================================
echo  Network Mapper - Deploy to Server
echo ========================================
echo.

set SERVER=edcv-utl-idd1
set IIS_PATH=\\%SERVER%\c$\inetpub\wwwroot\NetworkMapper
set API_PATH=\\%SERVER%\e$\Apps\NetworkMapper

echo Deploying frontend to IIS...
copy /Y "frontend\index.html" "%IIS_PATH%\index.html"
if %errorlevel%==0 (echo   ✓ index.html deployed) else (echo   ✗ Failed to deploy index.html)

echo.
echo Deploying backend to API server...
copy /Y "backend\api_server.py" "%API_PATH%\api_server.py"
if %errorlevel%==0 (echo   ✓ api_server.py deployed) else (echo   ✗ Failed to deploy api_server.py)

copy /Y "backend\requirements.txt" "%API_PATH%\requirements.txt"
if %errorlevel%==0 (echo   ✓ requirements.txt deployed) else (echo   ✗ Failed to deploy requirements.txt)

echo.
echo ========================================
echo  Deployment complete!
echo ========================================
echo.
echo NOTE: If you changed api_server.py, restart Flask on the server:
echo   1. Ctrl+C in the Flask console
echo   2. python api_server.py
echo.
pause