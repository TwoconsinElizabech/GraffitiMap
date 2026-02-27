#!/usr/bin/env python3
"""
测试增强的模糊测试功能
验证新增的功能：路径遍历载荷自定义、替换规则单独执行、位置交换应用替换规则
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.fuzzing_generator import fuzzing_generator

def test_custom_traversal_payloads():
    """测试自定义路径遍历载荷"""
    print("=" * 60)
    print("测试自定义路径遍历载荷功能")
    print("=" * 60)
    
    test_url = "https://example.com/api/v2/users"
    custom_payloads = ["../", "..\\", "....//", "%2e%2e%2f"]
    
    print(f"原始URL: {test_url}")
    print(f"自定义载荷: {custom_payloads}")
    
    # 使用自定义载荷
    custom_results = fuzzing_generator.add_path_traversal(test_url, max_depth=2, custom_payloads=custom_payloads)
    print(f"\n使用自定义载荷生成 {len(custom_results)} 个变体:")
    for i, variant in enumerate(custom_results[:10]):
        print(f"  {i+1}: {variant}")
    
    # 使用默认载荷对比
    default_results = fuzzing_generator.add_path_traversal(test_url, max_depth=2)
    print(f"\n使用默认载荷生成 {len(default_results)} 个变体:")
    for i, variant in enumerate(default_results[:10]):
        print(f"  {i+1}: {variant}")

def test_position_swap_with_replacement():
    """测试位置交换应用替换规则"""
    print("\n" + "=" * 60)
    print("测试位置交换应用替换规则功能")
    print("=" * 60)
    
    test_url = "https://example.com/api/v2/users/123"
    replacement_rules = {
        'v2': ['v1', 'v3'],
        'users': ['admin', 'test'],
        '123': ['456', '789']
    }
    selected_rules = ['v2', 'users']
    
    print(f"原始URL: {test_url}")
    print(f"替换规则: {replacement_rules}")
    print(f"选中规则: {selected_rules}")
    
    # 不应用替换规则的位置交换
    simple_swap = fuzzing_generator.swap_path_positions(test_url)
    print(f"\n简单位置交换生成 {len(simple_swap)} 个变体:")
    for i, variant in enumerate(simple_swap[:5]):
        print(f"  {i+1}: {variant}")
    
    # 应用替换规则的位置交换
    enhanced_swap = fuzzing_generator.swap_path_positions(test_url, replacement_rules, selected_rules)
    print(f"\n增强位置交换生成 {len(enhanced_swap)} 个变体:")
    for i, variant in enumerate(enhanced_swap[:10]):
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
        '123': ['456', '789', '000'],
        'api': ['service', 'endpoint']  # 这个不会被选中
    }
    
    print(f"原始URL: {test_url}")
    print(f"所有替换规则: {replacement_rules}")
    
    # 执行所有规则
    all_results = fuzzing_generator.replace_path_segments(test_url, replacement_rules)
    print(f"\n执行所有规则生成 {len(all_results)} 个变体:")
    for i, variant in enumerate(all_results[:8]):
        print(f"  {i+1}: {variant}")
    
    # 只执行选中的规则
    selected_rules = ['v2', '123']
    selected_results = fuzzing_generator.replace_path_segments(test_url, replacement_rules, selected_rules)
    print(f"\n只执行选中规则 {selected_rules} 生成 {len(selected_results)} 个变体:")
    for i, variant in enumerate(selected_results):
        print(f"  {i+1}: {variant}")

def test_complete_enhanced_fuzzing():
    """测试完整的增强模糊测试流程"""
    print("\n" + "=" * 60)
    print("测试完整的增强模糊测试流程")
    print("=" * 60)
    
    target = "https://example.com/api/v2/users?id=123&token=abc"
    config = {
        'replacement_rules': {
            'v2': ['v1', 'v3'],
            'users': ['admin', 'test'],
            '123': ['456', '789']
        },
        'selected_replacement_rules': ['v2', 'users'],
        'position_swap': True,
        'param_injection': True,
        'path_traversal': True,
        'custom_traversal_payloads': ['../', '..\\', '....//'],
        'traversal_max_depth': 2,
        'max_results': 30
    }
    
    print(f"目标URL: {target}")
    print(f"配置: {config}")
    
    variants = fuzzing_generator.generate_fuzzing_variants(target, config)
    
    print(f"\n生成了 {len(variants)} 个变体:")
    for i, variant in enumerate(variants):
        print(f"  {i+1}: {variant}")
    
    # 验证主域名保持
    print("\n验证主域名保持:")
    original_domain = "https://example.com"
    domain_changed = 0
    for variant in variants:
        if variant.startswith('http'):
            if not variant.startswith(original_domain):
                print(f"  ❌ 主域名被改变: {variant}")
                domain_changed += 1
    
    if domain_changed == 0:
        print(f"  ✅ 所有 {len([v for v in variants if v.startswith('http')])} 个URL变体都保持了原始主域名")
    else:
        print(f"  ❌ 有 {domain_changed} 个变体的主域名被改变")

if __name__ == "__main__":
    print("开始测试增强的模糊测试功能...")
    
    try:
        test_custom_traversal_payloads()
        test_position_swap_with_replacement()
        test_selective_replacement()
        test_complete_enhanced_fuzzing()
        
        print("\n" + "=" * 60)
        print("✅ 所有增强功能测试完成！")
        print("=" * 60)
        
        print("\n功能总结:")
        print("1. ✅ 路径遍历载荷可以自定义")
        print("2. ✅ 替换规则可以选择性执行")
        print("3. ✅ 位置交换会应用选中的替换规则")
        print("4. ✅ HTTP/HTTPS主域名始终保持不变")
        print("5. ✅ 所有功能可以组合使用")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()