#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6 依赖问题诊断和修复工具
"""

import sys
import os
import subprocess
import importlib.util

def check_python_info():
    """检查Python环境信息"""
    print("=== Python环境信息 ===")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"架构: {sys.maxsize > 2**32 and '64位' or '32位'}")
    print()

def check_pyqt6_installation():
    """检查PyQt6安装状态"""
    print("=== PyQt6安装检查 ===")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "show", "PyQt6"], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print("PyQt6已安装:")
            print(result.stdout)
        else:
            print("PyQt6未安装")
            return False
    except Exception as e:
        print(f"检查PyQt6安装时出错: {e}")
        return False
    
    return True

def test_pyqt6_import():
    """测试PyQt6导入"""
    print("=== PyQt6导入测试 ===")
    
    # 测试基础导入
    modules_to_test = [
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui'
    ]
    
    for module in modules_to_test:
        try:
            spec = importlib.util.find_spec(module)
            if spec is None:
                print(f"❌ {module}: 模块未找到")
                continue
                
            # 尝试导入
            imported_module = importlib.import_module(module)
            print(f"✅ {module}: 导入成功")
            
            # 如果是QtCore，显示版本信息
            if module == 'PyQt6.QtCore':
                try:
                    print(f"   Qt版本: {imported_module.qVersion()}")
                    print(f"   PyQt版本: {imported_module.PYQT_VERSION_STR}")
                except:
                    pass
                    
        except ImportError as e:
            print(f"❌ {module}: 导入失败 - {e}")
        except Exception as e:
            print(f"❌ {module}: 其他错误 - {e}")
    
    print()

def test_simple_widget():
    """测试创建简单的Qt组件"""
    print("=== Qt组件创建测试 ===")
    try:
        from PyQt6.QtWidgets import QApplication, QWidget
        from PyQt6.QtCore import Qt
        
        # 创建应用程序实例（不显示窗口）
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # 创建简单窗口
        widget = QWidget()
        widget.setWindowTitle("测试窗口")
        widget.resize(200, 100)
        
        print("✅ Qt组件创建成功")
        
        # 清理
        widget.close()
        return True
        
    except Exception as e:
        print(f"❌ Qt组件创建失败: {e}")
        return False

def suggest_fixes():
    """建议修复方案"""
    print("=== 修复建议 ===")
    print("如果PyQt6导入失败，请尝试以下解决方案：")
    print()
    print("1. 重新安装PyQt6:")
    print("   pip uninstall PyQt6")
    print("   pip install PyQt6")
    print()
    print("2. 安装Microsoft Visual C++ Redistributable:")
    print("   下载并安装最新的VC++ Redistributable (x64)")
    print("   https://aka.ms/vs/17/release/vc_redist.x64.exe")
    print()
    print("3. 尝试安装PyQt6的所有组件:")
    print("   pip install PyQt6[all]")
    print()
    print("4. 如果仍有问题，尝试使用conda安装:")
    print("   conda install pyqt")
    print()
    print("5. 检查系统PATH环境变量是否包含Python Scripts目录")
    print()

def main():
    """主函数"""
    print("PyQt6 依赖问题诊断工具")
    print("=" * 50)
    print()
    
    # 检查Python环境
    check_python_info()
    
    # 检查PyQt6安装
    if not check_pyqt6_installation():
        print("请先安装PyQt6: pip install PyQt6")
        return
    
    # 测试导入
    test_pyqt6_import()
    
    # 测试组件创建
    success = test_simple_widget()
    
    if not success:
        suggest_fixes()
    else:
        print("🎉 PyQt6工作正常！")

if __name__ == "__main__":
    main()