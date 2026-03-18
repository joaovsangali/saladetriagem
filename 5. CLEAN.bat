@echo off
echo ========================================
echo  SALA DE TRIAGEM - LIMPEZA COMPLETA
echo ========================================
echo.
echo [AVISO] Este script vai:
echo   - Parar todos os containers
echo   - Remover containers
echo   - Remover volumes (DADOS SERAO PERDIDOS!)
echo   - Remover networks
echo.
echo Tem certeza? Pressione Ctrl+C para cancelar.
pause
echo.

echo [INFO] Parando e removendo containers...
docker-compose down -v

if errorlevel 1 (
    echo.
    echo [ERRO] Falha na limpeza!
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Removendo imagens antigas...
docker image prune -f

echo.
echo ========================================
echo  LIMPEZA CONCLUIDA!
echo ========================================
echo.
echo Todos os containers, volumes e dados foram removidos.
echo Use "fresh-start.bat" para iniciar do zero.
echo.
pause