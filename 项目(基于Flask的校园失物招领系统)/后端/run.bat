@echo off
chcp 65001 >nul
echo ============================================
echo 校园失物招领系统 - 启动脚本
echo ============================================
echo.

cd /d "%~dp0"

REM 优先使用项目内置虚拟环境 .venv，不存在则回退系统 Python
set PYTHON=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
    echo [INFO] 使用虚拟环境 .venv
)

REM 检查数据库是否已初始化
%PYTHON% -c "import pymysql; pymysql.connect(host='127.0.0.1',port=3306,user='root',password='123456',database='bishe')" 2>nul
if errorlevel 1 (
    echo [INFO] 正在初始化数据库...
    %PYTHON% 初始化数据库.py
    echo.
)

echo [INFO] 启动 Flask 服务器...
echo [INFO] 访问地址: http://localhost:5000
echo [INFO] 接口文档: http://localhost:5000/docs
echo [INFO] 按 Ctrl+C 停止服务器
echo.

%PYTHON% 应用入口.py

pause
