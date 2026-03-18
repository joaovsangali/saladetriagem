@echo off
echo ========================================
echo  SALA DE TRIAGEM - REBUILD
echo ========================================
echo.
echo Este script vai:
echo   - Parar containers
echo   - Rebuildar imagens
echo   - Iniciar containers
echo   - DADOS SAO PRESERVADOS (volumes nao sao apagados)
echo.
pause
echo.

echo [1/3] Parando containers...
docker-compose down

echo.
echo [2/3] Rebuilding imagens...
docker-compose build

if errorlevel 1 (
    echo.
    echo [ERRO] Falha no build!
    echo.
    pause
    exit /b 1
)

echo.
echo [3/3] Iniciando containers...
docker-compose up -d

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao iniciar!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  REBUILD CONCLUIDO!
echo ========================================
echo.
echo Acesse: http://localhost:8000
echo.
pause