@echo off
echo ========================================
echo  SALA DE TRIAGEM - INICIO LIMPO
echo ========================================
echo.
echo [AVISO] Este script vai:
echo   - Limpar containers e volumes
echo   - Rebuildar todas as imagens
echo   - Iniciar sistema do zero
echo   - TODOS OS DADOS SERAO PERDIDOS!
echo.
echo Tem certeza? Pressione Ctrl+C para cancelar.
pause
echo.

echo [1/4] Parando containers...
docker-compose down -v

echo.
echo [2/4] Limpando build cache...
docker-compose build --no-cache

if errorlevel 1 (
    echo.
    echo [ERRO] Falha no build!
    echo.
    pause
    exit /b 1
)

echo.
echo [3/4] Iniciando containers...
docker-compose up -d

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao iniciar!
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Aguardando containers ficarem prontos...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo  SISTEMA INICIADO DO ZERO!
echo ========================================
echo.
echo Acesse: http://localhost:8000
echo.
echo Status dos containers:
docker-compose ps
echo.
pause