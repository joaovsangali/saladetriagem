@echo off
echo ========================================
echo  SALA DE TRIAGEM - STATUS
echo ========================================
echo.

docker-compose ps

echo.
echo ========================================
echo  ESTATISTICAS DE USO
echo ========================================
echo.

docker stats --no-stream saladetriagem-web-1 saladetriagem-worker-1 saladetriagem-beat-1 saladetriagem-db-1 saladetriagem-redis-1 2>nul

if errorlevel 1 (
    echo [INFO] Containers nao estao rodando ou nomes diferentes.
    echo Use "docker ps" para ver containers ativos.
)

echo.
pause