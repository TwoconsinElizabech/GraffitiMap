@echo off
echo 启动GraffitiMap v2.0.0...
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

REM 检查PyQt6是否安装
python -c "import PyQt6; print('PyQt6检查通过')" >nul 2>&1
if errorlevel 1 (
    echo 错误: PyQt6未正确安装或存在DLL加载问题
    echo 尝试重新安装PyQt6...
    pip uninstall PyQt6 -y
    pip install PyQt6
    echo.
)

REM 运行程序
echo 启动程序...
python main.py

REM 如果程序异常退出，显示错误信息
if errorlevel 1 (
    echo.
    echo 程序异常退出，请检查错误信息
    echo 可以运行 python debug_import.py 来诊断问题
    pause
)