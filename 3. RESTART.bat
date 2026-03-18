@echo off
echo ========================================
echo  SALA DE TRIAGEM - REINICIAR SISTEMA
echo ========================================
echo.

echo [INFO] Parando containers...
docker-compose down

echo.
echo [INFO] Iniciando containers...
docker-compose up -d

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao reiniciar!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  SISTEMA REINICIADO COM SUCESSO!
echo ========================================
echo.
echo Acesse: http://localhost:8000
echo.
pause