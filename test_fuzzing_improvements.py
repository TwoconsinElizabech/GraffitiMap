#!/usr/bin/env python3
"""
测试模糊测试功能改进
验证位置交换、参数注入、路径遍历功能是否正确保持HTTP/HTTPS主域名不变
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.fuzzing_generator import fuzzing_generator

def test_url_preservation():
    """测试URL主域名保持功能"""
    print("=" * 60)
    print("测试URL主域名保持功能")
    print("=" * 60)
    
    test_urls = [
        "https://example.com/api/v2/users",
        "http://test.com/admin/panel/v1/config",
        "https://domain.com/app/1/dashboard/settings?id=123&token=abc",
        "/api/v2/users",  # 相对路径
        "/admin/panel/v1/config"  # 相对路径
    ]
    
    for url in test_urls:
        print(f"\n原始URL: {url}")
        
        # 测试位置交换
        print("位置交换结果:")
        swapped = fuzzing_generator.swap_path_positions(url)
        for i, variant in enumerate(swapped[:5]):  # 只显示前5个
            print(f"  {i+1}: {variant}")
        
        # 测试路径遍历
        print("路径遍历结果:")
        traversal = fuzzing_generator.add_path_traversal(url, max_depth=2)
        for i, variant in enumerate(traversal[:5]):  # 只显示前5个
            print(f"  {i+1}: {variant}")
        
        # 测试参数注入（仅对有参数的URL）
        if '?' in url:
            print("参数注入结果:")
            injection = fuzzing_generator.add_parameter_injection(url)
            for i, variant in enumerate(injection[:5]):  # 只显示前5个
                print(f"  {i+1}: {variant}")

def test_selective_replacement():
    """测试选择性替换规则"""
    print("\n" + "=" * 60)
    print("测试选择性替换规则功能")
    print("=" * 60)
    
    test_url = "https://example.com/api/v2/users/123"
    replacement_rules = {
        'v2': ['v1', 'v3', 'v4'],
        'users': ['admin', 'root', 'test'],
        '123': ['456', '789', '000']
    }
    
    print(f"原始URL: {test_url}")
    print(f"替换规则: {replacement_rules}")
    
    # 测试全部规则
    print("\n执行所有规则:")
    all_results = fuzzing_generator.replace_path_segments(test_url, replacement_rules)
    for i, variant in enumerate(all_results[:10]):
        print(f"  {i+1}: {variant}")
    
    # 测试选择性规则
    selected_rules = ['v2', '123']  # 只选择这两个规则
    print(f"\n只执行选中的规则 {selected_rules}:")
    selected_results = fuzzing_generator.replace_path_segments(test_url, replacement_rules, selected_rules)
    for i, variant in enumerate(selected_results[:10]):
        print(f"  {i+1}: {variant}")

def test_complete_fuzzing():
    """测试完整的模糊测试流程"""
    print("\n" + "=" * 60)
    print("测试完整的模糊测试流程")
    print("=" * 60)
    
    target = "https://example.com/api/v2/users?id=123&token=abc"
    config = {
        'replacement_rules': {
            'v2': ['v1', 'v3'],
            'users': ['admin', 'test'],
            '123': ['456', '789']
        },
        'selected_replacement_rules': ['v2', 'users'],  # 只选择部分规则
        'position_swap': True,
        'param_injection': True,
        'path_traversal': True,
        'max_results': 20
    }
    
    print(f"目标URL: {target}")
    print(f"配置: {config}")
    
    variants = fuzzing_generator.generate_fuzzing_variants(target, config)
    
    print(f"\n生成了 {len(variants)} 个变体:")
    for i, variant in enumerate(variants):
        print(f"  {i+1}: {variant}")
    
    # 验证主域名是否保持不变
    print("\n验证主域名保持:")
    original_domain = "https://example.com"
    for variant in variants:
        if variant.startswith('http'):
            if not variant.startswith(original_domain):
                print(f"  ❌ 主域名被改变: {variant}")
            else:
                print(f"  ✅ 主域名保持: {variant}")

if __name__ == "__main__":
    print("开始测试模糊测试功能改进...")
    
    try:
        test_url_preservation()
        test_selective_replacement()
        test_complete_fuzzing()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()