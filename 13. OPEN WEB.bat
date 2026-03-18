@echo off
echo ========================================
echo  SALA DE TRIAGEM - ABRIR NAVEGADOR
echo ========================================
echo.

REM Aguardar alguns segundos para garantir que containers estão prontos
echo [INFO] Aguardando containers ficarem prontos...
timeout /t 5 /nobreak >nul

echo [INFO] Abrindo navegador...
start http://localhost:8000

echo.
echo ========================================
echo  NAVEGADOR ABERTO!
echo ========================================
echo.
pause