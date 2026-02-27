"""
简单的导入测试脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Python版本:", sys.version)
print("项目路径:", project_root)

# 测试PyQt6导入
print("\n1. 测试PyQt6导入...")
try:
    import PyQt6
    print("✓ PyQt6基础模块导入成功")
    
    from PyQt6.QtWidgets import QApplication
    print("✓ PyQt6.QtWidgets导入成功")
    
    from PyQt6.QtCore import Qt
    print("✓ PyQt6.QtCore导入成功")
    
except Exception as e:
    print(f"✗ PyQt6导入失败: {e}")
    sys.exit(1)

# 测试项目模块导入
print("\n2. 测试项目模块导入...")

try:
    from config.settings import APP_NAME, APP_VERSION
    print(f"✓ 配置模块: {APP_NAME} v{APP_VERSION}")
except Exception as e:
    print(f"✗ 配置模块导入失败: {e}")

try:
    from core.database import db_manager
    print("✓ 数据库模块导入成功")
except Exception as e:
    print(f"✗ 数据库模块导入失败: {e}")

# 测试新功能模块
new_modules = [
    'core.combination_generator',
    'core.case_transformer', 
    'core.url_analyzer',
    'core.fuzzing_generator'
]

print("\n3. 测试新功能模块...")
for module in new_modules:
    try:
        __import__(module)
        print(f"✓ {module} 导入成功")
    except Exception as e:
        print(f"✗ {module} 导入失败: {e}")

# 测试GUI模块
print("\n4. 测试GUI模块...")
try:
    from gui.main_window import MainWindow
    print("✓ 主窗口模块导入成功")
except Exception as e:
    print(f"✗ 主窗口模块导入失败: {e}")

print("\n导入测试完成")