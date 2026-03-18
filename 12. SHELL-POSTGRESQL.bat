@echo off
echo ========================================
echo  SALA DE TRIAGEM - SHELL POSTGRESQL
echo ========================================
echo.
echo Abrindo psql no banco de dados...
echo Digite "\q" para sair
echo.

docker-compose exec db psql -U postgres -d saladetriagem

if errorlevel 1 (
    echo.
    echo [ERRO] Nao foi possivel conectar ao banco.
    echo Verifique se o sistema esta rodando com "status.bat"
    echo.
    pause
)