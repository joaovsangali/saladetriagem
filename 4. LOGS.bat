@echo off
echo ========================================
echo  SALA DE TRIAGEM - LOGS EM TEMPO REAL
echo ========================================
echo.
echo Pressione Ctrl+C para sair
echo.
echo ========================================
echo.

docker-compose logs -f --tail=50