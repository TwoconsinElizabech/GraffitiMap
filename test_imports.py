"""
测试所有模块导入的脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("开始测试模块导入...")

# 测试PyQt6
try:
    from PyQt6.QtWidgets import QApplication
    print("✓ PyQt6导入成功")
except ImportError as e:
    print(f"✗ PyQt6导入失败: {e}")
    sys.exit(1)

# 测试配置模块
try:
    from config.settings import APP_NAME, APP_VERSION
    print(f"✓ 配置模块导入成功: {APP_NAME} v{APP_VERSION}")
except ImportError as e:
    print(f"✗ 配置模块导入失败: {e}")

# 测试核心模块
core_modules = [
    'core.database',
    'core.dictionary_manager',
    'core.combination_generator',
    'core.case_transformer',
    'core.url_analyzer',
    'core.fuzzing_generator'
]

for module in core_modules:
    try:
        __import__(module)
        print(f"✓ {module} 导入成功")
    except ImportError as e:
        print(f"✗ {module} 导入失败: {e}")

# 测试GUI模块
gui_modules = [
    'gui.main_window',
    'gui.dictionary_widget',
    'gui.combination_widget',
    'gui.case_transform_widget',
    'gui.url_analyzer_widget',
    'gui.fuzzing_widget'
]

for module in gui_modules:
    try:
        __import__(module)
        print(f"✓ {module} 导入成功")
    except ImportError as e:
        print(f"✗ {module} 导入失败: {e}")

print("\n模块导入测试完成")