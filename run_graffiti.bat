@echo off
chcp 65001 >nul
echo GraffitiMap v2.0.0 启动器
echo ========================

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或不在PATH中
    echo 请安装Python 3.8+并添加到系统PATH
    pause
    exit /b 1
)

echo 正在启动GraffitiMap...
python main_fallback.py

if errorlevel 1 (
    echo.
    echo 程序启动失败，请检查以下问题:
    echo 1. Python环境是否正确配置
    echo 2. 依赖包是否已安装: pip install -r requirements.txt
    echo 3. PyQt6是否正确安装: pip install PyQt6
    echo.
    echo 如果PyQt6有问题，程序会自动切换到命令行模式
    pause
)