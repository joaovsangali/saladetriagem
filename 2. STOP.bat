@echo off
echo ========================================
echo  SALA DE TRIAGEM - PARAR SISTEMA
echo ========================================
echo.

docker-compose down

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao parar containers!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  SISTEMA PARADO COM SUCESSO!
echo ========================================
echo.
echo Todos os containers foram parados.
echo Os dados persistem nos volumes Docker.
echo.
pause