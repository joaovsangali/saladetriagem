@echo off
echo ========================================
echo  SALA DE TRIAGEM - SHELL REDIS
echo ========================================
echo.
echo Abrindo redis-cli...
echo Digite "exit" para sair
echo.

REM Ler senha do .env se existir
set REDIS_PASSWORD=
for /f "tokens=1,2 delims==" %%a in ('type .env 2^>nul ^| findstr /i "REDIS_PASSWORD"') do set REDIS_PASSWORD=%%b

if defined REDIS_PASSWORD (
    echo [INFO] Usando senha do .env
    docker-compose exec redis redis-cli -a %REDIS_PASSWORD%
) else (
    echo [AVISO] REDIS_PASSWORD nao encontrado no .env
    docker-compose exec redis redis-cli
)

if errorlevel 1 (
    echo.
    echo [ERRO] Nao foi possivel conectar ao Redis.
    echo Verifique se o sistema esta rodando com "status.bat"
    echo.
    pause
)