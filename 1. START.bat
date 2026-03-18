@echo off
echo ========================================
echo  SALA DE TRIAGEM - INICIAR SISTEMA
echo ========================================
echo.

REM Verificar se Docker Desktop está rodando
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Docker Desktop nao esta rodando!
    echo.
    echo Por favor, inicie o Docker Desktop e aguarde ate que esteja pronto.
    echo.
    pause
    exit /b 1
)

echo [INFO] Docker Desktop detectado.
echo [INFO] Iniciando containers...
echo.

docker-compose up -d

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao iniciar containers!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  SISTEMA INICIADO COM SUCESSO!
echo ========================================
echo.
echo Acesse: http://localhost:8000
echo.
echo Containers ativos:
docker-compose ps
echo.
echo Pressione qualquer tecla para sair...
pause >nul