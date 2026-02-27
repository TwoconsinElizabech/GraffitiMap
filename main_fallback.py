#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraffitiMap v2.0.0 - 带PyQt6依赖检查的启动器
如果PyQt6不可用，将提供命令行界面
"""

import sys
import os

def check_pyqt6():
    """检查PyQt6是否可用"""
    try:
        from PyQt6.QtWidgets import QApplication
        return True
    except ImportError as e:
        print(f"PyQt6导入失败: {e}")
        print("\n可能的解决方案:")
        print("1. 安装Microsoft Visual C++ Redistributable:")
        print("   https://aka.ms/vs/17/release/vc_redist.x64.exe")
        print("2. 重新安装PyQt6:")
        print("   pip uninstall PyQt6")
        print("   pip install PyQt6")
        print("3. 或者使用conda安装:")
        print("   conda install pyqt")
        return False

def run_gui_mode():
    """运行GUI模式"""
    try:
        from gui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        app.setApplicationName("GraffitiMap")
        app.setApplicationVersion("2.0.0")
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"GUI启动失败: {e}")
        return False

def run_cli_mode():
    """运行命令行模式"""
    print("=" * 60)
    print("GraffitiMap v2.0.0 - 命令行模式")
    print("=" * 60)
    print()
    print("由于PyQt6不可用，程序将以命令行模式运行")
    print()
    
    # 导入核心功能
    try:
        from core.database import DatabaseManager
        from core.dictionary_manager import DictionaryManager
        from core.analyzer import DictionaryAnalyzer
        from core.combination_generator import CombinationGenerator
        from core.case_transformer import CaseTransformer
        from core.url_analyzer import URLAnalyzer
        from core.fuzzing_generator import FuzzingGenerator
        
        print("✅ 核心功能模块加载成功")
        
        # 初始化数据库
        db_manager = DatabaseManager()
        dict_manager = DictionaryManager()
        
        print("✅ 数据库连接成功")
        print()
        
        # 显示可用功能
        print("可用功能:")
        print("1. 字典管理 (导入/导出/去重)")
        print("2. 字典分析 (统计/模式分析)")
        print("3. 组合生成 (笛卡尔积组合)")
        print("4. 大小写转换 (8种转换策略)")
        print("5. URL分析 (参数提取/统计)")
        print("6. 模糊测试字典生成")
        print()
        
        # 简单的交互式菜单
        while True:
            print("-" * 40)
            choice = input("请选择功能 (1-6, q退出): ").strip()
            
            if choice.lower() == 'q':
                break
            elif choice == '1':
                cli_dictionary_management(dict_manager)
            elif choice == '2':
                cli_dictionary_analysis(dict_manager)
            elif choice == '3':
                cli_combination_generation()
            elif choice == '4':
                cli_case_transformation()
            elif choice == '5':
                cli_url_analysis()
            elif choice == '6':
                cli_fuzzing_generation()
            else:
                print("无效选择，请重试")
        
        print("感谢使用GraffitiMap!")
        
    except Exception as e:
        print(f"❌ 核心功能加载失败: {e}")
        print("请检查项目文件完整性")

def cli_dictionary_management(dict_manager):
    """命令行字典管理"""
    print("\n=== 字典管理 ===")
    print("1. 导入字典文件")
    print("2. 导出字典")
    print("3. 查看字典列表")
    print("4. 删除字典")
    
    choice = input("选择操作: ").strip()
    
    if choice == '1':
        file_path = input("请输入字典文件路径: ").strip()
        if os.path.exists(file_path):
            name = input("请输入字典名称: ").strip()
            try:
                dict_manager.import_dictionary(file_path, name)
                print(f"✅ 字典 '{name}' 导入成功")
            except Exception as e:
                print(f"❌ 导入失败: {e}")
        else:
            print("❌ 文件不存在")
    
    elif choice == '3':
        dictionaries = dict_manager.get_all_dictionaries()
        if dictionaries:
            print("\n现有字典:")
            for i, (dict_id, name, word_count, created_at) in enumerate(dictionaries, 1):
                print(f"{i}. {name} ({word_count}个词条) - {created_at}")
        else:
            print("暂无字典")

def cli_dictionary_analysis(dict_manager):
    """命令行字典分析"""
    print("\n=== 字典分析 ===")
    dictionaries = dict_manager.get_all_dictionaries()
    if not dictionaries:
        print("暂无字典可分析")
        return
    
    print("可用字典:")
    for i, (dict_id, name, word_count, created_at) in enumerate(dictionaries, 1):
        print(f"{i}. {name} ({word_count}个词条)")
    
    try:
        choice = int(input("选择字典编号: ")) - 1
        if 0 <= choice < len(dictionaries):
            dict_id = dictionaries[choice][0]
            analyzer = DictionaryAnalyzer(dict_manager.db_manager)
            stats = analyzer.analyze_dictionary(dict_id)
            
            print(f"\n字典统计:")
            print(f"总词条数: {stats['total_words']}")
            print(f"唯一词条数: {stats['unique_words']}")
            print(f"平均长度: {stats['avg_length']:.2f}")
            print(f"最短长度: {stats['min_length']}")
            print(f"最长长度: {stats['max_length']}")
        else:
            print("无效选择")
    except ValueError:
        print("请输入有效数字")

def cli_combination_generation():
    """命令行组合生成"""
    print("\n=== 组合生成 ===")
    print("请输入三个区域的词条 (每行一个，空行结束):")
    
    areas = []
    for i in range(3):
        print(f"\n区域 {i+1}:")
        area_words = []
        while True:
            word = input().strip()
            if not word:
                break
            area_words.append(word)
        if area_words:
            areas.append(area_words)
    
    if len(areas) >= 2:
        generator = CombinationGenerator()
        combinations = generator.generate_combinations(areas)
        
        print(f"\n生成了 {len(combinations)} 个组合:")
        for combo in combinations[:20]:  # 只显示前20个
            print(combo)
        
        if len(combinations) > 20:
            print(f"... 还有 {len(combinations) - 20} 个组合")
        
        save = input("\n是否保存到文件? (y/n): ").strip().lower()
        if save == 'y':
            filename = input("输入文件名: ").strip()
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for combo in combinations:
                        f.write(combo + '\n')
                print(f"✅ 已保存到 {filename}")
            except Exception as e:
                print(f"❌ 保存失败: {e}")
    else:
        print("至少需要两个区域的词条")

def cli_case_transformation():
    """命令行大小写转换"""
    print("\n=== 大小写转换 ===")
    
    # 输入词条
    words = []
    print("请输入要转换的词条 (每行一个，空行结束):")
    while True:
        word = input().strip()
        if not word:
            break
        words.append(word)
    
    if not words:
        print("没有输入词条")
        return
    
    # 选择转换策略
    print("\n转换策略:")
    strategies = [
        "全小写", "全大写", "首字母大写", "随机大小写",
        "交替大小写", "反向交替", "单词首字母大写", "随机单词大写"
    ]
    
    for i, strategy in enumerate(strategies, 1):
        print(f"{i}. {strategy}")
    
    try:
        choice = int(input("选择策略 (1-8): ")) - 1
        if 0 <= choice < len(strategies):
            transformer = CaseTransformer()
            strategy_name = ['lower', 'upper', 'capitalize', 'random', 
                           'alternate', 'reverse_alternate', 'title', 'random_word'][choice]
            
            transformed = transformer.transform_words(words, strategy_name)
            
            print(f"\n转换结果 ({len(transformed)} 个词条):")
            for word in transformed[:20]:  # 只显示前20个
                print(word)
            
            if len(transformed) > 20:
                print(f"... 还有 {len(transformed) - 20} 个词条")
        else:
            print("无效选择")
    except ValueError:
        print("请输入有效数字")

def cli_url_analysis():
    """命令行URL分析"""
    print("\n=== URL分析 ===")
    
    # 输入URL
    urls = []
    print("请输入要分析的URL (每行一个，空行结束):")
    while True:
        url = input().strip()
        if not url:
            break
        urls.append(url)
    
    if not urls:
        print("没有输入URL")
        return
    
    analyzer = URLAnalyzer()
    results = analyzer.analyze_urls(urls)
    
    print(f"\n分析结果:")
    print(f"总URL数: {results['total_urls']}")
    print(f"带参数URL数: {results['urls_with_params']}")
    print(f"唯一参数数: {len(results['unique_params'])}")
    
    if results['unique_params']:
        print(f"\n参数列表:")
        for param in list(results['unique_params'])[:20]:
            print(f"  {param}")

def cli_fuzzing_generation():
    """命令行模糊测试生成"""
    print("\n=== 模糊测试字典生成 ===")
    
    base_words = []
    print("请输入基础词条 (每行一个，空行结束):")
    while True:
        word = input().strip()
        if not word:
            break
        base_words.append(word)
    
    if not base_words:
        print("没有输入基础词条")
        return
    
    generator = FuzzingGenerator()
    fuzz_dict = generator.generate_fuzzing_dictionary(base_words)
    
    print(f"\n生成了 {len(fuzz_dict)} 个模糊测试词条:")
    for word in fuzz_dict[:30]:  # 只显示前30个
        print(word)
    
    if len(fuzz_dict) > 30:
        print(f"... 还有 {len(fuzz_dict) - 30} 个词条")

def main():
    """主函数"""
    print("GraffitiMap v2.0.0 启动中...")
    
    # 检查PyQt6
    if check_pyqt6():
        print("✅ PyQt6可用，启动GUI模式")
        run_gui_mode()
    else:
        print("⚠️  PyQt6不可用，启动命令行模式")
        run_cli_mode()

if __name__ == "__main__":
    main()