#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6 DLL问题修复工具
专门解决 "DLL load failed while importing QtCore: 找不到指定的程序" 错误
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

def log_info(message):
    """记录信息"""
    print(f"[INFO] {message}")
    with open("logs/fix_pyqt6.log", "a", encoding="utf-8") as f:
        f.write(f"[INFO] {message}\n")

def log_error(message):
    """记录错误"""
    print(f"[ERROR] {message}")
    with open("logs/fix_pyqt6.log", "a", encoding="utf-8") as f:
        f.write(f"[ERROR] {message}\n")

def check_python_environment():
    """检查Python环境"""
    log_info("=== Python环境检查 ===")
    log_info(f"Python版本: {sys.version}")
    log_info(f"Python路径: {sys.executable}")
    log_info(f"架构: {sys.maxsize > 2**32 and '64位' or '32位'}")
    
    # 检查是否是Anaconda环境
    if "anaconda" in sys.executable.lower() or "conda" in sys.executable.lower():
        log_info("检测到Anaconda环境")
        return "anaconda"
    else:
        log_info("检测到标准Python环境")
        return "standard"

def check_pyqt6_installation():
    """检查PyQt6安装状态"""
    log_info("=== PyQt6安装检查 ===")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "show", "PyQt6"], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            log_info("PyQt6已通过pip安装:")
            log_info(result.stdout)
            return True
        else:
            log_error("PyQt6未通过pip安装")
            return False
    except Exception as e:
        log_error(f"检查PyQt6安装时出错: {e}")
        return False

def check_conda_pyqt():
    """检查conda中的PyQt安装"""
    log_info("=== Conda PyQt检查 ===")
    
    try:
        result = subprocess.run(["conda", "list", "pyqt"], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            log_info("Conda PyQt信息:")
            log_info(result.stdout)
            return True
        else:
            log_error("Conda中未找到PyQt")
            return False
    except Exception as e:
        log_error(f"检查conda PyQt时出错: {e}")
        return False

def find_qt_dlls():
    """查找Qt DLL文件"""
    log_info("=== 查找Qt DLL文件 ===")
    
    # 可能的Qt DLL位置
    possible_paths = [
        Path(sys.executable).parent / "Lib" / "site-packages" / "PyQt6" / "Qt6" / "bin",
        Path(sys.executable).parent / "Library" / "bin",  # Anaconda
        Path(sys.executable).parent / "DLLs",
        Path(sys.executable).parent / "Scripts",
    ]
    
    qt_dlls_found = []
    
    for path in possible_paths:
        if path.exists():
            log_info(f"检查路径: {path}")
            qt_files = list(path.glob("Qt6*.dll"))
            if qt_files:
                log_info(f"找到Qt DLL文件: {len(qt_files)} 个")
                qt_dlls_found.extend(qt_files)
            else:
                log_info("未找到Qt DLL文件")
    
    return qt_dlls_found

def check_vc_redist():
    """检查Visual C++ Redistributable"""
    log_info("=== Visual C++ Redistributable检查 ===")
    
    # 检查注册表中的VC++ Redistributable
    try:
        import winreg
        
        # 检查常见的VC++ Redistributable版本
        vc_versions = [
            "Microsoft Visual C++ 2015-2022 Redistributable (x64)",
            "Microsoft Visual C++ 2019 Redistributable (x64)",
            "Microsoft Visual C++ 2017 Redistributable (x64)",
        ]
        
        found_versions = []
        
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        if any(vc in display_name for vc in vc_versions):
                            found_versions.append(display_name)
                    except FileNotFoundError:
                        pass
                    
                    winreg.CloseKey(subkey)
                    i += 1
                    
                except OSError:
                    break
                    
            winreg.CloseKey(key)
            
        except Exception as e:
            log_error(f"检查注册表时出错: {e}")
        
        if found_versions:
            log_info("找到以下VC++ Redistributable版本:")
            for version in found_versions:
                log_info(f"  - {version}")
            return True
        else:
            log_error("未找到VC++ Redistributable")
            return False
            
    except ImportError:
        log_error("无法导入winreg模块")
        return False

def fix_pyqt6_anaconda():
    """修复Anaconda环境中的PyQt6问题"""
    log_info("=== 修复Anaconda PyQt6 ===")
    
    try:
        # 方法1: 重新安装conda pyqt
        log_info("尝试重新安装conda pyqt...")
        result = subprocess.run(["conda", "uninstall", "-y", "pyqt"], 
                              capture_output=True, text=True)
        log_info(f"卸载结果: {result.returncode}")
        
        result = subprocess.run(["conda", "install", "-y", "pyqt"], 
                              capture_output=True, text=True)
        log_info(f"安装结果: {result.returncode}")
        
        if result.returncode == 0:
            log_info("conda pyqt重新安装成功")
            return True
        
        # 方法2: 使用conda-forge
        log_info("尝试从conda-forge安装...")
        result = subprocess.run(["conda", "install", "-y", "-c", "conda-forge", "pyqt"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            log_info("从conda-forge安装成功")
            return True
        
        return False
        
    except Exception as e:
        log_error(f"修复Anaconda PyQt6时出错: {e}")
        return False

def fix_pyqt6_pip():
    """修复pip安装的PyQt6问题"""
    log_info("=== 修复pip PyQt6 ===")
    
    try:
        # 完全卸载PyQt6相关包
        packages_to_remove = ["PyQt6", "PyQt6-Qt6", "PyQt6-sip"]
        
        for package in packages_to_remove:
            log_info(f"卸载 {package}...")
            result = subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", package], 
                                  capture_output=True, text=True)
            log_info(f"卸载 {package} 结果: {result.returncode}")
        
        # 清理pip缓存
        log_info("清理pip缓存...")
        subprocess.run([sys.executable, "-m", "pip", "cache", "purge"], 
                      capture_output=True, text=True)
        
        # 重新安装PyQt6
        log_info("重新安装PyQt6...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "PyQt6"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            log_info("PyQt6重新安装成功")
            return True
        else:
            log_error(f"PyQt6安装失败: {result.stderr}")
            return False
            
    except Exception as e:
        log_error(f"修复pip PyQt6时出错: {e}")
        return False

def test_pyqt6_import():
    """测试PyQt6导入"""
    log_info("=== 测试PyQt6导入 ===")
    
    try:
        # 测试基础导入
        import PyQt6
        log_info(f"PyQt6 导入成功: {PyQt6.__file__}")
        
        from PyQt6 import QtCore
        log_info(f"QtCore 导入成功, Qt版本: {QtCore.QT_VERSION_STR}")
        
        from PyQt6 import QtWidgets
        log_info("QtWidgets 导入成功")
        
        # 测试创建应用
        app = QtWidgets.QApplication([])
        log_info("QApplication 创建成功")
        app.quit()
        
        return True
        
    except Exception as e:
        log_error(f"PyQt6导入测试失败: {e}")
        return False

def main():
    """主修复流程"""
    # 创建日志目录
    Path("logs").mkdir(exist_ok=True)
    
    # 清空之前的日志
    with open("logs/fix_pyqt6.log", "w", encoding="utf-8") as f:
        f.write("PyQt6 DLL问题修复日志\n")
        f.write("=" * 50 + "\n")
    
    log_info("开始PyQt6 DLL问题修复")
    
    # 1. 检查Python环境
    env_type = check_python_environment()
    
    # 2. 检查PyQt6安装
    pyqt6_installed = check_pyqt6_installation()
    
    # 3. 检查conda PyQt（如果是Anaconda环境）
    if env_type == "anaconda":
        check_conda_pyqt()
    
    # 4. 查找Qt DLL文件
    qt_dlls = find_qt_dlls()
    if qt_dlls:
        log_info(f"找到 {len(qt_dlls)} 个Qt DLL文件")
    else:
        log_error("未找到Qt DLL文件，这可能是问题的根源")
    
    # 5. 检查VC++ Redistributable
    vc_redist_ok = check_vc_redist()
    if not vc_redist_ok:
        log_error("未找到VC++ Redistributable，这是DLL加载失败的常见原因")
        log_info("请下载并安装: https://aka.ms/vs/17/release/vc_redist.x64.exe")
    
    # 6. 尝试修复
    log_info("=== 开始修复 ===")
    
    if env_type == "anaconda":
        log_info("尝试修复Anaconda环境...")
        if fix_pyqt6_anaconda():
            log_info("Anaconda修复成功，测试导入...")
            if test_pyqt6_import():
                log_info("✅ 修复成功！PyQt6现在可以正常使用")
                return True
    
    log_info("尝试修复pip安装...")
    if fix_pyqt6_pip():
        log_info("pip修复成功，测试导入...")
        if test_pyqt6_import():
            log_info("✅ 修复成功！PyQt6现在可以正常使用")
            return True
    
    # 7. 如果修复失败，提供建议
    log_error("❌ 自动修复失败，请尝试以下手动解决方案:")
    log_error("1. 安装Microsoft Visual C++ Redistributable (x64):")
    log_error("   https://aka.ms/vs/17/release/vc_redist.x64.exe")
    log_error("2. 完全重新安装Python和PyQt6")
    log_error("3. 使用不同的Python发行版（如官方Python而非Anaconda）")
    log_error("4. 检查系统PATH环境变量")
    
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 PyQt6修复成功！现在可以运行 python main.py")
    else:
        print("\n❌ 自动修复失败，请查看 logs/fix_pyqt6.log 获取详细信息")
        print("并按照日志中的建议手动解决问题")