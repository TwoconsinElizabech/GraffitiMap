"""
GraffitiMap v2.0.0 新功能测试脚本
测试组合生成、大小写转换、URL分析、模糊测试等新功能
"""
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_extensions():
    """测试数据库扩展"""
    logger.info("测试数据库扩展...")
    
    try:
        from core.database import db_manager
        
        # 初始化数据库
        db_manager.create_tables()
        
        # 检查新表是否存在
        tables_to_check = ['url_analysis', 'combination_configs', 'fuzzing_configs']
        
        for table in tables_to_check:
            try:
                result = db_manager.fetch_one(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if result:
                    logger.info(f"✓ 表 {table} 存在")
                else:
                    logger.error(f"✗ 表 {table} 不存在")
            except Exception as e:
                logger.error(f"✗ 检查表 {table} 失败: {e}")
        
        logger.info("数据库扩展测试完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库扩展测试失败: {e}")
        return False

def test_combination_generator():
    """测试组合生成功能"""
    logger.info("测试组合生成功能...")
    
    try:
        from core.combination_generator import combination_generator
        
        # 测试配置
        test_config = {
            'area_a': {'type': 'custom', 'data': 'admin\nuser\ntest'},
            'area_b': {'type': 'custom', 'data': 'login,panel,dashboard'},
            'area_c': {'type': 'date', 'data': {'start_year': 2023, 'end_year': 2024, 'format': 'YYYY'}},
            'connector': '_',
            'areas_enabled': ['a', 'b', 'c']
        }
        
        # 估算数量
        count = combination_generator.estimate_combination_count(test_config)
        logger.info(f"估算组合数量: {count}")
        
        # 生成组合
        combinations = list(combination_generator.generate_combinations(test_config))
        logger.info(f"实际生成数量: {len(combinations)}")
        
        # 显示前几个组合
        for i, combo in enumerate(combinations[:5]):
            logger.info(f"组合 {i+1}: {combo}")
        
        # 测试保存和加载配置
        config_id = combination_generator.save_combination_config("测试配置", test_config)
        logger.info(f"保存配置ID: {config_id}")
        
        loaded_config = combination_generator.load_combination_config(config_id)
        if loaded_config:
            logger.info("✓ 配置保存和加载成功")
        else:
            logger.error("✗ 配置加载失败")
        
        logger.info("组合生成功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"组合生成功能测试失败: {e}")
        return False

def test_case_transformer():
    """测试大小写转换功能"""
    logger.info("测试大小写转换功能...")
    
    try:
        from core.case_transformer import case_transformer, CaseStrategy
        
        test_words = ["admin", "user_login", "test-panel", "AdminDashboard", "API_KEY"]
        
        # 测试不同策略
        strategies = [
            (CaseStrategy.RANDOM_CHAR, "完全随机字符"),
            (CaseStrategy.RANDOM_WORD, "随机单词"),
            (CaseStrategy.FIRST_LETTER, "首字母随机"),
            (CaseStrategy.ALTERNATING, "交替大小写"),
            (CaseStrategy.CAMEL_CASE, "驼峰命名"),
            (CaseStrategy.PASCAL_CASE, "帕斯卡命名"),
            (CaseStrategy.SNAKE_CASE_UPPER, "蛇形大写"),
            (CaseStrategy.KEBAB_CASE_UPPER, "短横线大写")
        ]
        
        for strategy, description in strategies:
            logger.info(f"测试策略: {description}")
            
            for word in test_words[:3]:  # 只测试前3个词条
                if strategy in [CaseStrategy.RANDOM_CHAR, CaseStrategy.RANDOM_WORD, CaseStrategy.FIRST_LETTER]:
                    # 随机策略生成多个变体
                    variants = case_transformer.generate_random_variants(word, 3, strategy)
                    logger.info(f"  {word} -> {variants}")
                else:
                    # 确定性策略只生成一个变体
                    variant = case_transformer.transform_text(word, strategy)
                    logger.info(f"  {word} -> {variant}")
        
        # 测试批量转换
        transformed_words = case_transformer.transform_word_list(
            test_words, CaseStrategy.CAMEL_CASE, keep_original=True
        )
        logger.info(f"批量转换结果数量: {len(transformed_words)}")
        
        logger.info("大小写转换功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"大小写转换功能测试失败: {e}")
        return False

def test_url_analyzer():
    """测试URL分析功能"""
    logger.info("测试URL分析功能...")
    
    try:
        from core.url_analyzer import url_analyzer
        
        test_urls = [
            "https://example.com/api/users?id=123&name=admin",
            "https://test.com/login",
            "https://api.example.com/v1/data?token=abc123&format=json&limit=10",
            "/admin/panel?session=xyz789",
            "https://site.com/search?q=test&page=1&sort=date"
        ]
        
        logger.info("测试URL列表:")
        for url in test_urls:
            logger.info(f"  {url}")
        
        # 测试URL分析
        for url in test_urls:
            analysis = url_analyzer.analyze_url(url)
            logger.info(f"URL: {url}")
            logger.info(f"  域名: {analysis.get('domain', 'N/A')}")
            logger.info(f"  路径: {analysis.get('path', 'N/A')}")
            logger.info(f"  有参数: {analysis['has_params']}")
            logger.info(f"  参数数量: {analysis['param_count']}")
            logger.info(f"  参数名: {analysis['param_names']}")
        
        # 测试分类
        categories = url_analyzer.categorize_urls(test_urls)
        logger.info("URL分类:")
        logger.info(f"  带参数: {len(categories['with_params'])} 个")
        logger.info(f"  不带参数: {len(categories['without_params'])} 个")
        logger.info(f"  多参数: {len(categories['multiple_params'])} 个")
        logger.info(f"  单参数: {len(categories['single_param'])} 个")
        
        # 测试常见参数
        common_params = url_analyzer.extract_common_parameters(test_urls)
        logger.info("常见参数:")
        for param, count in common_params.items():
            logger.info(f"  {param}: {count} 次")
        
        logger.info("URL分析功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"URL分析功能测试失败: {e}")
        return False

def test_fuzzing_generator():
    """测试模糊测试生成功能"""
    logger.info("测试模糊测试生成功能...")
    
    try:
        from core.fuzzing_generator import fuzzing_generator
        
        test_targets = [
            "/api/v2/add/user",
            "/admin/panel/v1/config",
            "https://example.com/api/v3/users?id=123&token=abc",
            "/app/1/dashboard/settings"
        ]
        
        # 测试配置
        test_config = {
            'replacement_rules': {
                'v2': ['v1', 'v3', 'v4'],
                'v1': ['v2', 'v3'],
                'v3': ['v1', 'v2', 'v4'],
                'user': ['admin', 'root', 'test'],
                'add': ['create', 'new', 'insert'],
                '1': ['2', '3', '0'],
                '123': ['456', '789', '000']
            },
            'position_swap': True,
            'param_injection': True,
            'path_traversal': True,
            'max_results': 20
        }
        
        logger.info("测试目标:")
        for target in test_targets:
            logger.info(f"  {target}")
        
        # 生成模糊测试变体
        for target in test_targets:
            logger.info(f"目标: {target}")
            variants = fuzzing_generator.generate_fuzzing_variants(target, test_config)
            logger.info(f"生成 {len(variants)} 个变体:")
            for i, variant in enumerate(variants[:5]):  # 只显示前5个
                logger.info(f"  {i+1}: {variant}")
            if len(variants) > 5:
                logger.info(f"  ... 还有 {len(variants) - 5} 个变体")
        
        # 测试保存和加载配置
        config_id = fuzzing_generator.save_fuzzing_config(
            "测试配置",
            test_config['replacement_rules'],
            test_config['position_swap'],
            test_config['param_injection'],
            test_config['path_traversal']
        )
        logger.info(f"保存配置ID: {config_id}")
        
        loaded_config = fuzzing_generator.load_fuzzing_config(config_id)
        if loaded_config:
            logger.info("✓ 配置保存和加载成功")
        else:
            logger.error("✗ 配置加载失败")
        
        logger.info("模糊测试生成功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"模糊测试生成功能测试失败: {e}")
        return False

def test_dictionary_integration():
    """测试字典集成功能"""
    logger.info("测试字典集成功能...")
    
    try:
        from core.dictionary_manager import dictionary_manager
        
        # 创建测试字典
        dict_id = dictionary_manager.create_dictionary("v2.0测试字典", "用于测试v2.0新功能的字典")
        logger.info(f"创建测试字典ID: {dict_id}")
        
        # 添加测试词条
        test_words = ["admin", "user", "test", "login", "panel"]
        added_count = dictionary_manager.add_words(dict_id, test_words)
        logger.info(f"添加词条数量: {added_count}")
        
        # 获取字典统计
        stats = dictionary_manager.get_dictionary_stats(dict_id)
        logger.info(f"字典统计: {stats}")
        
        # 测试搜索
        search_results = dictionary_manager.search_words(dict_id, "admin")
        logger.info(f"搜索结果数量: {len(search_results)}")
        
        logger.info("字典集成功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"字典集成功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("开始GraffitiMap v2.0.0新功能测试")
    
    test_results = []
    
    # 执行各项测试
    tests = [
        ("数据库扩展", test_database_extensions),
        ("组合生成功能", test_combination_generator),
        ("大小写转换功能", test_case_transformer),
        ("URL分析功能", test_url_analyzer),
        ("模糊测试生成功能", test_fuzzing_generator),
        ("字典集成功能", test_dictionary_integration)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"开始测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            test_results.append((test_name, result))
            
            if result:
                logger.info(f"✓ {test_name} 测试通过")
            else:
                logger.error(f"✗ {test_name} 测试失败")
                
        except Exception as e:
            logger.error(f"✗ {test_name} 测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试总结
    logger.info(f"\n{'='*50}")
    logger.info("测试总结")
    logger.info(f"{'='*50}")
    
    passed_count = 0
    total_count = len(test_results)
    
    for test_name, result in test_results:
        status = "通过" if result else "失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    logger.info(f"\n总计: {passed_count}/{total_count} 项测试通过")
    
    if passed_count == total_count:
        logger.info("🎉 所有测试通过！GraffitiMap v2.0.0新功能运行正常")
        return 0
    else:
        logger.error(f"❌ {total_count - passed_count} 项测试失败，请检查相关功能")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)