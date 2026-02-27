#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraffitiMap v2.0.0 - 最终启动器
一次性解决所有问题的完整启动程序
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_pyqt6():
    """检查PyQt6是否可用"""
    try:
        from PyQt6.QtWidgets import QApplication
        return True
    except ImportError:
        return False

def initialize_core_modules():
    """初始化核心模块"""
    try:
        # 初始化数据库
        from core.database import DatabaseManager, init_database
        init_database()
        db_manager = DatabaseManager()
        
        # 初始化标签管理器
        from core.tag_manager import initialize_tag_manager
        initialize_tag_manager(db_manager)
        
        print("✅ 核心模块初始化成功")
        return True
    except Exception as e:
        print(f"❌ 核心模块初始化失败: {e}")
        return False

def run_gui_mode():
    """运行GUI模式"""
    try:
        from PyQt6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        app.setApplicationName("GraffitiMap")
        app.setApplicationVersion("2.0.0")
        
        window = MainWindow()
        window.show()
        
        print("🚀 GUI模式启动成功")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ GUI模式启动失败: {e}")
        return False

def run_cli_mode():
    """运行命令行模式"""
    print("=" * 60)
    print("🎯 GraffitiMap v2.0.0 - 命令行模式")
    print("=" * 60)
    print()
    
    try:
        from core.dictionary_manager import dictionary_manager
        from core.combination_generator import CombinationGenerator
        from core.case_transformer import CaseTransformer
        from core.url_analyzer import URLAnalyzer
        from core.fuzzing_generator import FuzzingGenerator
        from core.analyzer import DictionaryAnalyzer, analyzer
        from core.database import DatabaseManager
        
        print("✅ 所有功能模块加载成功")
        print()
        
        # 显示功能菜单
        while True:
            print("-" * 50)
            print("📋 可用功能:")
            print("1. 字典管理 (导入/导出/查看)")
            print("2. 字典分析 (统计信息)")
            print("3. 组合生成 (笛卡尔积)")
            print("4. 大小写转换 (8种策略)")
            print("5. URL分析 (参数提取)")
            print("6. 模糊测试字典生成")
            print("7. 正则表达式分析")
            print("q. 退出程序")
            print("-" * 50)
            
            choice = input("请选择功能 (1-7, q): ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == '1':
                cli_dictionary_management()
            elif choice == '2':
                cli_dictionary_analysis()
            elif choice == '3':
                cli_combination_generation()
            elif choice == '4':
                cli_case_transformation()
            elif choice == '5':
                cli_url_analysis()
            elif choice == '6':
                cli_fuzzing_generation()
            elif choice == '7':
                cli_regex_analysis()
            else:
                print("❌ 无效选择，请重试")
        
        print("👋 感谢使用GraffitiMap v2.0.0!")
        
    except Exception as e:
        print(f"❌ 命令行模式启动失败: {e}")
        import traceback
        traceback.print_exc()

def cli_dictionary_management():
    """字典管理功能"""
    print("\n📚 === 字典管理 ===")
    from core.dictionary_manager import dictionary_manager
    
    print("1. 查看所有字典")
    print("2. 创建新字典")
    print("3. 导入字典文件")
    print("4. 导出字典")
    
    choice = input("选择操作: ").strip()
    
    if choice == '1':
        dictionaries = dictionary_manager.get_all_dictionaries()
        if dictionaries:
            print(f"\n📋 现有字典 ({len(dictionaries)} 个):")
            for i, d in enumerate(dictionaries, 1):
                print(f"{i}. {d['name']} ({d.get('word_count', 0)} 词条) - {d.get('created_at', 'N/A')}")
        else:
            print("📭 暂无字典")
    
    elif choice == '2':
        name = input("字典名称: ").strip()
        desc = input("字典描述 (可选): ").strip()
        if name:
            try:
                dict_id = dictionary_manager.create_dictionary(name, desc)
                print(f"✅ 字典创建成功，ID: {dict_id}")
            except Exception as e:
                print(f"❌ 创建失败: {e}")
    
    elif choice == '3':
        file_path = input("字典文件路径: ").strip()
        if os.path.exists(file_path):
            name = input("字典名称: ").strip()
            if name:
                try:
                    # 读取文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        words = [line.strip() for line in f if line.strip()]
                    
                    # 创建字典并添加词条
                    dict_id = dictionary_manager.create_dictionary(name)
                    added = dictionary_manager.add_words(dict_id, words)
                    print(f"✅ 导入成功: {added} 个词条")
                except Exception as e:
                    print(f"❌ 导入失败: {e}")
        else:
            print("❌ 文件不存在")

def cli_dictionary_analysis():
    """字典分析功能"""
    print("\n📊 === 字典分析 ===")
    from core.dictionary_manager import dictionary_manager
    from core.analyzer import DictionaryAnalyzer
    from core.database import DatabaseManager
    
    dictionaries = dictionary_manager.get_all_dictionaries()
    if not dictionaries:
        print("📭 暂无字典可分析")
        return
    
    print("可用字典:")
    for i, d in enumerate(dictionaries, 1):
        print(f"{i}. {d['name']} ({d.get('word_count', 0)} 词条)")
    
    try:
        choice = int(input("选择字典编号: ")) - 1
        if 0 <= choice < len(dictionaries):
            dict_id = dictionaries[choice]['id']
            
            # 使用DictionaryAnalyzer进行分析
            db_manager = DatabaseManager()
            analyzer = DictionaryAnalyzer(db_manager)
            stats = analyzer.analyze_dictionary(dict_id)
            
            print(f"\n📈 字典统计:")
            print(f"总词条数: {stats['total_words']}")
            print(f"唯一词条数: {stats['unique_words']}")
            print(f"平均长度: {stats['avg_length']:.2f}")
            print(f"最短长度: {stats['min_length']}")
            print(f"最长长度: {stats['max_length']}")
        else:
            print("❌ 无效选择")
    except ValueError:
        print("❌ 请输入有效数字")

def cli_combination_generation():
    """组合生成功能"""
    print("\n🔄 === 组合生成 ===")
    from core.combination_generator import CombinationGenerator
    
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
        
        print(f"\n🎯 生成了 {len(combinations)} 个组合:")
        for combo in combinations[:20]:
            print(f"  {combo}")
        
        if len(combinations) > 20:
            print(f"  ... 还有 {len(combinations) - 20} 个组合")
        
        save = input("\n💾 是否保存到文件? (y/n): ").strip().lower()
        if save == 'y':
            filename = input("文件名: ").strip()
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for combo in combinations:
                        f.write(combo + '\n')
                print(f"✅ 已保存到 {filename}")
            except Exception as e:
                print(f"❌ 保存失败: {e}")
    else:
        print("❌ 至少需要两个区域的词条")

def cli_case_transformation():
    """大小写转换功能"""
    print("\n🔤 === 大小写转换 ===")
    from core.case_transformer import CaseTransformer
    
    words = []
    print("请输入要转换的词条 (每行一个，空行结束):")
    while True:
        word = input().strip()
        if not word:
            break
        words.append(word)
    
    if not words:
        print("❌ 没有输入词条")
        return
    
    print("\n🎨 转换策略:")
    strategies = [
        ("lower", "全小写"),
        ("upper", "全大写"), 
        ("capitalize", "首字母大写"),
        ("random", "随机大小写"),
        ("alternate", "交替大小写"),
        ("reverse_alternate", "反向交替"),
        ("title", "单词首字母大写"),
        ("random_word", "随机单词大写")
    ]
    
    for i, (key, desc) in enumerate(strategies, 1):
        print(f"{i}. {desc}")
    
    try:
        choice = int(input("选择策略 (1-8): ")) - 1
        if 0 <= choice < len(strategies):
            strategy_key = strategies[choice][0]
            transformer = CaseTransformer()
            transformed = transformer.transform_words(words, strategy_key)
            
            print(f"\n✨ 转换结果 ({len(transformed)} 个词条):")
            for word in transformed[:20]:
                print(f"  {word}")
            
            if len(transformed) > 20:
                print(f"  ... 还有 {len(transformed) - 20} 个词条")
        else:
            print("❌ 无效选择")
    except ValueError:
        print("❌ 请输入有效数字")

def cli_url_analysis():
    """URL分析功能"""
    print("\n🔗 === URL分析 ===")
    from core.url_analyzer import URLAnalyzer
    
    urls = []
    print("请输入要分析的URL (每行一个，空行结束):")
    while True:
        url = input().strip()
        if not url:
            break
        urls.append(url)
    
    if not urls:
        print("❌ 没有输入URL")
        return
    
    analyzer = URLAnalyzer()
    results = analyzer.analyze_urls(urls)
    
    print(f"\n🔍 分析结果:")
    print(f"总URL数: {results['total_urls']}")
    print(f"带参数URL数: {results['urls_with_params']}")
    print(f"唯一参数数: {len(results['unique_params'])}")
    
    if results['unique_params']:
        print(f"\n📋 参数列表:")
        for param in list(results['unique_params'])[:20]:
            print(f"  {param}")

def cli_fuzzing_generation():
    """模糊测试生成功能"""
    print("\n🎯 === 模糊测试字典生成 ===")
    from core.fuzzing_generator import FuzzingGenerator
    
    base_words = []
    print("请输入基础词条 (每行一个，空行结束):")
    while True:
        word = input().strip()
        if not word:
            break
        base_words.append(word)
    
    if not base_words:
        print("❌ 没有输入基础词条")
        return
    
    generator = FuzzingGenerator()
    fuzz_dict = generator.generate_fuzzing_dictionary(base_words)
    
    print(f"\n🚀 生成了 {len(fuzz_dict)} 个模糊测试词条:")
    for word in fuzz_dict[:30]:
        print(f"  {word}")
    
    if len(fuzz_dict) > 30:
        print(f"  ... 还有 {len(fuzz_dict) - 30} 个词条")

def cli_regex_analysis():
    """正则表达式分析功能"""
    print("\n🔍 === 正则表达式分析 ===")
    from core.analyzer import analyzer
    from utils.regex_helper import regex_helper
    
    words = []
    print("请输入要分析的词条 (每行一个，空行结束):")
    while True:
        word = input().strip()
        if not word:
            break
        words.append(word)
    
    if not words:
        print("❌ 没有输入词条")
        return
    
    # 获取可用的正则模式
    try:
        pattern_names = regex_helper.get_all_pattern_names()[:5]  # 使用前5个模式
        
        print(f"\n🎯 使用模式: {', '.join(pattern_names)}")
        
        # 执行分析
        result = analyzer.analyze_words(words, pattern_names)
        
        print(f"\n📊 分析结果:")
        print(f"总词条数: {result.get('total_words', 0)}")
        print(f"匹配词条数: {result.get('summary', {}).get('matched_words', 0)}")
        print(f"匹配率: {result.get('summary', {}).get('match_rate', 0):.2f}%")
        
        # 显示各模式结果
        for pattern_name, pattern_result in result.get('pattern_results', {}).items():
            matched_count = len(pattern_result.get('matched_words', []))
            if matched_count > 0:
                print(f"\n🔸 模式 '{pattern_name}':")
                print(f"  匹配词条数: {matched_count}")
                print(f"  匹配词条: {pattern_result.get('matched_words', [])[:10]}")
    
    except Exception as e:
        print(f"❌ 正则分析失败: {e}")

def main():
    """主函数"""
    print("🚀 GraffitiMap v2.0.0 启动中...")
    print()
    
    # 初始化核心模块
    if not initialize_core_modules():
        print("❌ 核心模块初始化失败，程序退出")
        return
    
    # 检查PyQt6
    if check_pyqt6():
        print("✅ PyQt6可用，启动GUI模式")
        run_gui_mode()
    else:
        print("⚠️  PyQt6不可用，启动命令行模式")
        print("\n💡 修复PyQt6的方法:")
        print("1. 安装Microsoft Visual C++ Redistributable:")
        print("   https://aka.ms/vs/17/release/vc_redist.x64.exe")
        print("2. 重新安装PyQt6:")
        print("   pip uninstall PyQt6 && pip install PyQt6")
        print("3. 或使用conda: conda install pyqt")
        print()
        run_cli_mode()

if __name__ == "__main__":
    main()