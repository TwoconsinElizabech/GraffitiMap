#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字典管理工具集成测试脚本
测试各功能模块的集成和基本功能
"""

import sys
import os
import logging
from pathlib import Path

# 设置控制台编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_integration.log', encoding='utf-8')
        ]
    )

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试核心模块
        from core.database import db_manager
        from core.dictionary_manager import dictionary_manager
        from core.file_handler import file_handler
        from core.deduplicator import deduplicator
        from core.tag_manager import tag_manager
        from core.analyzer import analyzer
        from core.exporter import exporter
        print("✅ 核心模块导入成功")
        
        # 测试工具模块
        from utils.regex_helper import regex_helper
        print("✅ 工具模块导入成功")
        
        # 测试配置模块
        from config.settings import APP_NAME, APP_VERSION
        print("✅ 配置模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_database():
    """测试数据库功能"""
    print("\n🗄️ 测试数据库功能...")
    
    try:
        from core.database import db_manager
        
        # 初始化数据库
        db_manager.create_tables()
        print("✅ 数据库初始化成功")
        
        # 获取统计信息
        stats = db_manager.get_database_stats()
        print(f"✅ 数据库统计: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_dictionary_manager():
    """测试字典管理功能"""
    print("\n📚 测试字典管理功能...")
    
    try:
        from core.dictionary_manager import dictionary_manager
        import time
        
        # 创建测试字典（使用时间戳避免重名）
        dict_name = f"测试字典_{int(time.time())}"
        dict_id = dictionary_manager.create_dictionary(dict_name, "集成测试用字典")
        print(f"✅ 创建字典成功，ID: {dict_id}")
        
        # 添加测试词条
        test_words = ["测试词条1", "测试词条2", "重复词条", "重复词条"]
        added_count = dictionary_manager.add_words(dict_id, test_words)
        print(f"✅ 添加词条成功: {added_count} 个")
        
        # 获取字典信息
        dict_info = dictionary_manager.get_dictionary_by_id(dict_id)
        print(f"✅ 字典信息: {dict_info['name']} - {dict_info['word_count']} 个词条")
        
        # 获取词条列表
        words = dictionary_manager.get_words(dict_id, limit=10)
        word_ids = [word['id'] for word in words]
        
        return dict_id, word_ids
        
    except Exception as e:
        print(f"❌ 字典管理测试失败: {e}")
        return None, []

def test_file_handler():
    """测试文件处理功能"""
    print("\n📁 测试文件处理功能...")
    
    try:
        from core.file_handler import file_handler
        
        # 测试读取test.txt文件
        if os.path.exists("test.txt"):
            words = file_handler.import_file("test.txt")
            print(f"✅ 读取test.txt成功，共 {len(words)} 个词条")
            
            # 显示前10个词条
            if words:
                print("📝 前10个词条:")
                for i, word in enumerate(words[:10]):
                    print(f"  {i+1}. {word}")
            
            return words
        else:
            print("⚠️ test.txt文件不存在")
            return []
            
    except Exception as e:
        print(f"❌ 文件处理测试失败: {e}")
        return []

def test_deduplicator(dict_id):
    """测试去重功能"""
    print("\n🔄 测试去重功能...")
    
    try:
        from core.deduplicator import deduplicator
        from core.dictionary_manager import dictionary_manager
        
        # 获取去重前的词条数量
        dict_stats = dictionary_manager.get_dictionary_stats(dict_id)
        before_count = dict_stats.get('total_words', 0)
        print(f"📊 去重前词条数量: {before_count}")
        
        # 执行去重 - 使用正确的方法名
        removed_count = deduplicator.remove_duplicates_from_dictionary(dict_id, strategy='exact')
        print(f"✅ 去重完成，移除 {removed_count} 个重复词条")
        
        # 获取去重后的词条数量
        dict_stats_after = dictionary_manager.get_dictionary_stats(dict_id)
        after_count = dict_stats_after.get('total_words', 0)
        print(f"📊 去重后词条数量: {after_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 去重功能测试失败: {e}")
        return False

def test_tag_manager(dict_id, word_ids):
    """测试标签管理功能"""
    print("\n🏷️ 测试标签管理功能...")
    
    try:
        from core.tag_manager import tag_manager
        import time
        
        # 创建测试标签（使用时间戳避免重名）
        tag_name = f"测试标签_{int(time.time())}"
        tag_id = tag_manager.create_tag(tag_name, "#FF5722", "集成测试标签")
        print(f"✅ 创建标签成功，ID: {tag_id}")
        
        # 为词条添加标签 - 使用正确的方法名
        if word_ids:
            for word_id in word_ids[:2]:  # 只为前两个词条添加标签
                if word_id:
                    tag_manager.add_tag_to_word(word_id, tag_id)
                    print(f"✅ 为词条 {word_id} 添加标签")
        
        # 获取标签信息
        tag_info = tag_manager.get_tag_by_id(tag_id)
        print(f"✅ 标签信息: {tag_info}")
        
        return tag_id
        
    except Exception as e:
        print(f"❌ 标签管理测试失败: {e}")
        return None

def test_analyzer(dict_id):
    """测试分析功能"""
    print("\n📊 测试分析功能...")
    
    try:
        from core.analyzer import analyzer
        from utils.regex_helper import regex_helper
        
        # 获取可用的正则模式
        pattern_names = regex_helper.get_all_pattern_names()[:3]  # 使用前3个模式
        print(f"📝 使用模式: {pattern_names}")
        
        # 分析字典
        analysis_result = analyzer.analyze_dictionary(dict_id, pattern_names)
        
        if analysis_result:
            summary = analysis_result.get('summary', {})
            print(f"✅ 分析完成:")
            print(f"   总词条数: {analysis_result.get('total_words', 0)}")
            print(f"   匹配词条数: {summary.get('matched_words', 0)}")
            print(f"   匹配率: {summary.get('match_rate', 0):.2f}%")
            
            # 显示各模式结果
            for pattern_name, pattern_result in analysis_result.get('pattern_results', {}).items():
                matched_count = len(pattern_result.get('matched_words', []))
                if matched_count > 0:
                    print(f"   模式 '{pattern_name}': {matched_count} 个匹配")
        else:
            print("⚠️ 分析结果为空")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析功能测试失败: {e}")
        return False

def test_regex_helper():
    """测试正则表达式工具"""
    print("\n🔍 测试正则表达式工具...")
    
    try:
        from utils.regex_helper import regex_helper
        
        # 获取可用模式
        pattern_names = regex_helper.get_all_pattern_names()
        print(f"✅ 加载了 {len(pattern_names)} 个正则模式")
        
        # 测试正则表达式匹配 - 使用包含WP的测试数据
        test_words = [
            "http://example.com/wp-admin",
            "https://test.com/wp-content/themes",
            "user@example.com",
            "192.168.1.1",
            "WordPress",
            "wp-config.php",
            "normal text without patterns"
        ]
        
        # 测试WP相关模式
        wp_pattern = "WordPress路径"
        if wp_pattern in pattern_names:
            matches = []
            for word in test_words:
                word_matches = regex_helper.match_pattern(word, wp_pattern)
                if word_matches:
                    matches.extend(word_matches)
            
            print(f"✅ WP路径匹配测试: 模式 '{wp_pattern}' 匹配到 {len(matches)} 个结果")
            if matches:
                print(f"📝 匹配结果: {matches}")
        
        # 测试URL模式
        url_pattern = "URL地址"
        if url_pattern in pattern_names:
            matches = []
            for word in test_words:
                word_matches = regex_helper.match_pattern(word, url_pattern)
                if word_matches:
                    matches.extend(word_matches)
            
            print(f"✅ URL匹配测试: 模式 '{url_pattern}' 匹配到 {len(matches)} 个结果")
            if matches:
                print(f"📝 匹配结果: {matches[:3]}")  # 显示前3个匹配结果
        
        # 如果没有找到特定模式，使用第一个可用模式进行测试
        if pattern_names and wp_pattern not in pattern_names and url_pattern not in pattern_names:
            pattern_name = pattern_names[0]
            matches = []
            for word in test_words:
                word_matches = regex_helper.match_pattern(word, pattern_name)
                if word_matches:
                    matches.extend(word_matches)
            
            print(f"✅ 通用匹配测试: 模式 '{pattern_name}' 匹配到 {len(matches)} 个结果")
            if matches:
                print(f"📝 匹配结果: {matches[:5]}")  # 只显示前5个结果
        
        return True
        
    except Exception as e:
        print(f"❌ 正则表达式测试失败: {e}")
        return False

def test_exporter(dict_id):
    """测试导出功能"""
    print("\n💾 测试导出功能...")
    
    try:
        from core.exporter import exporter
        
        # 导出为TXT格式
        output_file = "test_export.txt"
        success = exporter.export_dictionary(dict_id, output_file, format='txt')
        
        if success and os.path.exists(output_file):
            print(f"✅ 导出TXT成功: {output_file}")
            
            # 读取导出文件验证
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📝 导出内容预览: {content[:100]}...")
            
            # 清理测试文件
            os.remove(output_file)
            print("🧹 清理测试文件")
            
            return True
        else:
            print("❌ 导出失败")
            return False
            
    except Exception as e:
        print(f"❌ 导出功能测试失败: {e}")
        return False

def cleanup_test_data(dict_id, tag_id):
    """清理测试数据"""
    print("\n🧹 清理测试数据...")
    
    try:
        from core.dictionary_manager import dictionary_manager
        from core.tag_manager import tag_manager
        
        # 删除测试字典
        if dict_id:
            dictionary_manager.delete_dictionary(dict_id)
            print("✅ 删除测试字典")
        
        # 删除测试标签
        if tag_id:
            tag_manager.delete_tag(tag_id)
            print("✅ 删除测试标签")
            
    except Exception as e:
        print(f"⚠️ 清理数据时出错: {e}")

def main():
    """主测试函数"""
    print("🚀 开始字典管理工具集成测试")
    print("=" * 50)
    
    setup_logging()
    
    # 测试结果统计
    test_results = []
    
    # 1. 测试模块导入
    test_results.append(("模块导入", test_imports()))
    
    # 2. 测试数据库
    test_results.append(("数据库功能", test_database()))
    
    # 3. 测试字典管理
    dict_id, word_ids = test_dictionary_manager()
    test_results.append(("字典管理", dict_id is not None))
    
    # 4. 测试文件处理
    words = test_file_handler()
    test_results.append(("文件处理", len(words) > 0))
    
    # 5. 测试去重功能
    if dict_id:
        test_results.append(("去重功能", test_deduplicator(dict_id)))
    
    # 6. 测试标签管理
    tag_id = None
    if dict_id and word_ids:
        tag_id = test_tag_manager(dict_id, word_ids)
        test_results.append(("标签管理", tag_id is not None))
    
    # 7. 测试分析功能
    if dict_id:
        test_results.append(("分析功能", test_analyzer(dict_id)))
    
    # 8. 测试正则表达式工具
    test_results.append(("正则表达式", test_regex_helper()))
    
    # 9. 测试导出功能
    if dict_id:
        test_results.append(("导出功能", test_exporter(dict_id)))
    
    # 清理测试数据
    cleanup_test_data(dict_id, tag_id)
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("📋 测试结果汇总:")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<15} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！字典管理工具集成测试成功！")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查相关功能模块")
        return 1

if __name__ == "__main__":
    sys.exit(main())