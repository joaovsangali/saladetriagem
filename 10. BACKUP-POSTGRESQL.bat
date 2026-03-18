@echo off
echo ========================================
echo  SALA DE TRIAGEM - BACKUP DO BANCO
echo ========================================
echo.

REM Criar pasta de backups se não existir
if not exist "backups" mkdir backups

REM Nome do arquivo com timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set BACKUP_FILE=backups\saladetriagem_%datetime:~0,8%_%datetime:~8,6%.sql

echo [INFO] Criando backup em: %BACKUP_FILE%
echo.

docker-compose exec -T db pg_dump -U postgres saladetriagem > "%BACKUP_FILE%"

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao criar backup!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  BACKUP CONCLUIDO!
echo ========================================
echo.
echo Arquivo: %BACKUP_FILE%
echo Tamanho: 
dir "%BACKUP_FILE%" | find "%BACKUP_FILE%"
echo.
pause