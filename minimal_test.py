"""
最小化测试脚本 - 直接测试PyQt6和程序启动
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=== 最小化测试开始 ===")

# 1. 测试Python基础
print(f"Python版本: {sys.version}")
print(f"项目路径: {project_root}")

# 2. 测试PyQt6导入
print("\n测试PyQt6导入...")
try:
    import PyQt6
    print("✓ PyQt6基础包导入成功")
    
    from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
    print("✓ PyQt6.QtWidgets导入成功")
    
    from PyQt6.QtCore import Qt
    print("✓ PyQt6.QtCore导入成功")
    
    # 创建最简单的应用测试
    app = QApplication([])
    widget = QWidget()
    layout = QVBoxLayout()
    label = QLabel("PyQt6测试成功！")
    layout.addWidget(label)
    widget.setLayout(layout)
    widget.setWindowTitle("PyQt6测试")
    widget.show()
    
    print("✓ PyQt6应用创建成功")
    
    # 立即关闭应用
    widget.close()
    app.quit()
    
    print("✓ PyQt6功能测试通过")
    
except Exception as e:
    print(f"✗ PyQt6测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试项目配置导入
print("\n测试项目配置...")
try:
    from config.settings import APP_NAME, APP_VERSION
    print(f"✓ 配置导入成功: {APP_NAME} v{APP_VERSION}")
except Exception as e:
    print(f"✗ 配置导入失败: {e}")
    sys.exit(1)

print("\n=== 所有测试通过！程序应该可以正常启动 ===")