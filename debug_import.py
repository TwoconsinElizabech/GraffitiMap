"""
调试导入问题的脚本
"""
import sys
import os
from pathlib import Path

print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.executable}")
print(f"当前工作目录: {os.getcwd()}")
print(f"Python模块搜索路径:")
for path in sys.path:
    print(f"  {path}")

print("\n尝试导入PyQt6...")
try:
    import PyQt6
    print(f"✓ PyQt6导入成功，版本: {PyQt6.__version__ if hasattr(PyQt6, '__version__') else '未知'}")
    
    from PyQt6.QtWidgets import QApplication
    print("✓ PyQt6.QtWidgets导入成功")
    
    from PyQt6.QtCore import Qt
    print("✓ PyQt6.QtCore导入成功")
    
    from PyQt6.QtGui import QIcon
    print("✓ PyQt6.QtGui导入成功")
    
except ImportError as e:
    print(f"✗ PyQt6导入失败: {e}")
    print("请检查PyQt6安装:")
    print("  pip list | findstr PyQt6")
    sys.exit(1)

print("\n尝试导入项目模块...")
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import APP_NAME, APP_VERSION
    print(f"✓ 配置模块导入成功: {APP_NAME} v{APP_VERSION}")
except ImportError as e:
    print(f"✗ 配置模块导入失败: {e}")

try:
    from core.database import db_manager
    print("✓ 数据库模块导入成功")
except ImportError as e:
    print(f"✗ 数据库模块导入失败: {e}")

try:
    from gui.main_window import MainWindow
    print("✓ 主窗口模块导入成功")
except ImportError as e:
    print(f"✗ 主窗口模块导入失败: {e}")

print("\n所有导入测试完成")