@echo off
echo ========================================
echo  SALA DE TRIAGEM - SHELL WEB
echo ========================================
echo.
echo Abrindo shell no container web...
echo Digite "exit" para sair
echo.

docker-compose exec web /bin/bash

if errorlevel 1 (
    echo.
    echo [ERRO] Nao foi possivel conectar ao container.
    echo Verifique se o sistema esta rodando com "status.bat"
    echo.
    pause
)