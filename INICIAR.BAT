@echo off
title Sala de Triagem - Servidor

REM Ir para a pasta do projeto
cd /d C:\Users\jvsan\Desktop\dev\Projetos\saladetriagem

REM Ativar virtualenv
call .venv\Scripts\activate.bat

REM Definir variáveis de ambiente
set SECRET_KEY=uma_chave_segura_aqui
set FLASK_DEBUG=0

REM Iniciar servidor
python run.py

pause