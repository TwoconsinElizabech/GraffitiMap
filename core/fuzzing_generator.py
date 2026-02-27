"""
模糊测试字典生成模块
支持路径变换、参数注入、版本替换等多种模糊测试策略
"""
import logging
import json
import re
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from .database import db_manager


class FuzzingGenerator:
    """模糊测试字典生成器"""
    
    def __init__(self):
        """初始化模糊测试生成器"""
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
        # 预设替换规则
        self.default_replacements = {
            'versions': ['v1', 'v2', 'v3', 'v4', 'v5', 'version1', 'version2', 'ver1', 'ver2'],
            'numbers': ['1', '2', '3', '4', '5', '0', '10', '100'],
            'common_words': ['admin', 'user', 'test', 'api', 'app', 'web', 'mobile'],
            'file_extensions': ['php', 'asp', 'jsp', 'html', 'htm', 'js', 'css'],
            'methods': ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']
        }
        
        # 路径遍历载荷
        self.path_traversal_payloads = [
            '../', '..\\', '..../', '....\\',
            '%2e%2e%2f', '%2e%2e%5c', '%252e%252e%252f',
            '..%2f', '..%5c', '..%252f', '..%255c'
        ]
        
        # 参数注入载荷
        self.param_injection_payloads = [
            "' OR '1'='1", '" OR "1"="1', '1 OR 1=1',
            '<script>alert(1)</script>', '${7*7}', '{{7*7}}',
            '../../../etc/passwd', '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            'file:///etc/passwd', 'http://evil.com/callback'
        ]
    
    def extract_path_segments(self, path: str) -> List[str]:
        """
        提取路径段
        
        Args:
            path: 路径字符串
            
        Returns:
            List[str]: 路径段列表
        """
        # 移除开头和结尾的斜杠，然后分割
        path = path.strip('/')
        if not path:
            return []
        
        return path.split('/')
    
    def replace_path_segments(self, path: str, replacements: Dict[str, List[str]]) -> List[str]:
        """
        替换路径段
        
        Args:
            path: 原始路径
            replacements: 替换规则字典
            
        Returns:
            List[str]: 替换后的路径列表
        """
        segments = self.extract_path_segments(path)
        if not segments:
            return [path]
        
        results = set([path])  # 包含原始路径
        
        # 对每个段进行替换
        for i, segment in enumerate(segments):
            for pattern, replacement_list in replacements.items():
                # 检查段是否匹配模式
                if self._matches_pattern(segment, pattern):
                    for replacement in replacement_list:
                        new_segments = segments.copy()
                        new_segments[i] = replacement
                        new_path = '/' + '/'.join(new_segments)
                        results.add(new_path)
                
                # 部分替换（如果段包含模式）
                if pattern in segment:
                    for replacement in replacement_list:
                        new_segment = segment.replace(pattern, replacement)
                        new_segments = segments.copy()
                        new_segments[i] = new_segment
                        new_path = '/' + '/'.join(new_segments)
                        results.add(new_path)
        
        return list(results)
    
    def _matches_pattern(self, segment: str, pattern: str) -> bool:
        """
        检查段是否匹配模式
        
        Args:
            segment: 路径段
            pattern: 模式
            
        Returns:
            bool: 是否匹配
        """
        # 精确匹配
        if segment == pattern:
            return True
        
        # 版本号匹配
        if pattern in ['v1', 'v2', 'v3', 'v4', 'v5']:
            return re.match(r'^v\d+$', segment) is not None
        
        # 数字匹配
        if pattern.isdigit():
            return segment.isdigit()
        
        return False
    
    def swap_path_positions(self, path: str) -> List[str]:
        """
        交换路径段位置
        
        Args:
            path: 原始路径
            
        Returns:
            List[str]: 位置交换后的路径列表
        """
        segments = self.extract_path_segments(path)
        if len(segments) < 2:
            return [path]
        
        results = set([path])  # 包含原始路径
        
        # 相邻段交换
        for i in range(len(segments) - 1):
            new_segments = segments.copy()
            new_segments[i], new_segments[i + 1] = new_segments[i + 1], new_segments[i]
            new_path = '/' + '/'.join(new_segments)
            results.add(new_path)
        
        # 首尾交换
        if len(segments) > 2:
            new_segments = segments.copy()
            new_segments[0], new_segments[-1] = new_segments[-1], new_segments[0]
            new_path = '/' + '/'.join(new_segments)
            results.add(new_path)
        
        # 随机位置交换（限制数量避免过多）
        import random
        for _ in range(min(3, len(segments))):
            if len(segments) >= 2:
                new_segments = segments.copy()
                i, j = random.sample(range(len(segments)), 2)
                new_segments[i], new_segments[j] = new_segments[j], new_segments[i]
                new_path = '/' + '/'.join(new_segments)
                results.add(new_path)
        
        return list(results)
    
    def add_path_traversal(self, path: str, max_depth: int = 3) -> List[str]:
        """
        添加路径遍历载荷
        
        Args:
            path: 原始路径
            max_depth: 最大遍历深度
            
        Returns:
            List[str]: 包含路径遍历的路径列表
        """
        results = set([path])  # 包含原始路径
        
        for payload in self.path_traversal_payloads:
            # 在路径前添加遍历载荷
            for depth in range(1, max_depth + 1):
                traversal = payload * depth
                new_path = traversal + path.lstrip('/')
                results.add('/' + new_path)
            
            # 在路径段之间插入遍历载荷
            segments = self.extract_path_segments(path)
            if segments:
                for i in range(len(segments)):
                    new_segments = segments.copy()
                    new_segments.insert(i, payload.rstrip('/\\'))
                    new_path = '/' + '/'.join(new_segments)
                    results.add(new_path)
        
        return list(results)
    
    def add_parameter_injection(self, url: str) -> List[str]:
        """
        添加参数注入载荷
        
        Args:
            url: 原始URL
            
        Returns:
            List[str]: 包含参数注入的URL列表
        """
        try:
            parsed = urlparse(url)
            if not parsed.query:
                return [url]
            
            results = set([url])  # 包含原始URL
            params = parse_qs(parsed.query, keep_blank_values=True)
            
            # 对每个参数添加注入载荷
            for param_name, param_values in params.items():
                for payload in self.param_injection_payloads:
                    # 替换参数值
                    new_params = params.copy()
                    new_params[param_name] = [payload]
                    
                    new_query = urlencode(new_params, doseq=True)
                    new_parsed = parsed._replace(query=new_query)
                    new_url = urlunparse(new_parsed)
                    results.add(new_url)
                    
                    # 追加到原参数值
                    if param_values:
                        new_params = params.copy()
                        new_params[param_name] = [param_values[0] + payload]
                        
                        new_query = urlencode(new_params, doseq=True)
                        new_parsed = parsed._replace(query=new_query)
                        new_url = urlunparse(new_parsed)
                        results.add(new_url)
            
            # 添加新的恶意参数
            malicious_params = ['debug', 'test', 'admin', 'root', 'file', 'path', 'url', 'redirect']
            for param_name in malicious_params:
                for payload in self.param_injection_payloads[:5]:  # 限制数量
                    new_params = params.copy()
                    new_params[param_name] = [payload]
                    
                    new_query = urlencode(new_params, doseq=True)
                    new_parsed = parsed._replace(query=new_query)
                    new_url = urlunparse(new_parsed)
                    results.add(new_url)
            
            return list(results)
            
        except Exception as e:
            self.logger.error(f"添加参数注入失败: {e}")
            return [url]
    
    def generate_fuzzing_variants(self, target: str, config: Dict[str, Any]) -> List[str]:
        """
        生成模糊测试变体
        
        Args:
            target: 目标路径或URL
            config: 模糊测试配置
            
        Returns:
            List[str]: 模糊测试变体列表
        """
        try:
            results = set([target])  # 包含原始目标
            
            # 字符替换
            if config.get('replacement_rules'):
                replacement_rules = config['replacement_rules']
                replaced_targets = self.replace_path_segments(target, replacement_rules)
                results.update(replaced_targets)
            
            # 位置交换
            if config.get('position_swap', False):
                swapped_targets = self.swap_path_positions(target)
                results.update(swapped_targets)
            
            # 路径遍历
            if config.get('path_traversal', False):
                traversal_targets = self.add_path_traversal(target)
                results.update(traversal_targets)
            
            # 参数注入（仅对URL）
            if config.get('param_injection', False) and ('http' in target or '?' in target):
                injection_targets = self.add_parameter_injection(target)
                results.update(injection_targets)
            
            # 限制结果数量避免过多
            max_results = config.get('max_results', 1000)
            result_list = list(results)
            
            if len(result_list) > max_results:
                # 保留原始目标和随机选择的其他结果
                import random
                other_results = [r for r in result_list if r != target]
                selected_results = random.sample(other_results, max_results - 1)
                result_list = [target] + selected_results
            
            return result_list
            
        except Exception as e:
            self.logger.error(f"生成模糊测试变体失败: {e}")
            return [target]
    
    def save_fuzzing_config(self, name: str, replacement_rules: Dict[str, List[str]], 
                           position_swap: bool = False, param_injection: bool = False, 
                           path_traversal: bool = False) -> int:
        """
        保存模糊测试配置
        
        Args:
            name: 配置名称
            replacement_rules: 替换规则
            position_swap: 是否启用位置交换
            param_injection: 是否启用参数注入
            path_traversal: 是否启用路径遍历
            
        Returns:
            int: 配置ID
        """
        try:
            rules_json = json.dumps(replacement_rules, ensure_ascii=False)
            
            cursor = self.db.execute_query(
                """INSERT INTO fuzzing_configs 
                   (name, replacement_rules, position_swap, param_injection, path_traversal, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, rules_json, position_swap, param_injection, path_traversal, 
                 datetime.now(), datetime.now())
            )
            
            config_id = cursor.lastrowid
            self.logger.info(f"保存模糊测试配置成功: {name} (ID: {config_id})")
            return config_id
            
        except Exception as e:
            self.logger.error(f"保存模糊测试配置失败: {e}")
            raise
    
    def load_fuzzing_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        """
        加载模糊测试配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        try:
            row = self.db.fetch_one(
                "SELECT * FROM fuzzing_configs WHERE id = ?",
                (config_id,)
            )
            
            if row:
                replacement_rules = json.loads(row['replacement_rules'])
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'replacement_rules': replacement_rules,
                    'position_swap': bool(row['position_swap']),
                    'param_injection': bool(row['param_injection']),
                    'path_traversal': bool(row['path_traversal']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"加载模糊测试配置失败: {e}")
            return None
    
    def get_all_fuzzing_configs(self) -> List[Dict[str, Any]]:
        """
        获取所有模糊测试配置
        
        Returns:
            List[Dict[str, Any]]: 配置列表
        """
        try:
            rows = self.db.fetch_all(
                "SELECT * FROM fuzzing_configs ORDER BY created_at DESC"
            )
            
            configs = []
            for row in rows:
                try:
                    replacement_rules = json.loads(row['replacement_rules'])
                    configs.append({
                        'id': row['id'],
                        'name': row['name'],
                        'replacement_rules': replacement_rules,
                        'position_swap': bool(row['position_swap']),
                        'param_injection': bool(row['param_injection']),
                        'path_traversal': bool(row['path_traversal']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                except json.JSONDecodeError:
                    self.logger.warning(f"配置数据解析失败: ID {row['id']}")
                    continue
            
            return configs
            
        except Exception as e:
            self.logger.error(f"获取模糊测试配置列表失败: {e}")
            return []
    
    def delete_fuzzing_config(self, config_id: int) -> bool:
        """
        删除模糊测试配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            cursor = self.db.execute_query(
                "DELETE FROM fuzzing_configs WHERE id = ?",
                (config_id,)
            )
            
            success = cursor.rowcount > 0
            if success:
                self.logger.info(f"删除模糊测试配置成功: ID {config_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"删除模糊测试配置失败: {e}")
            return False
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            Dict[str, Any]: 默认配置
        """
        return {
            'replacement_rules': self.default_replacements,
            'position_swap': True,
            'param_injection': True,
            'path_traversal': True,
            'max_results': 500
        }


# 全局模糊测试生成器实例
fuzzing_generator = FuzzingGenerator()


if __name__ == "__main__":
    # 测试模糊测试功能
    logging.basicConfig(level=logging.INFO)
    
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
    
    print("测试目标:")
    for target in test_targets:
        print(f"  {target}")
    print()
    
    # 生成模糊测试变体
    for target in test_targets:
        print(f"目标: {target}")
        variants = fuzzing_generator.generate_fuzzing_variants(target, test_config)
        print(f"生成 {len(variants)} 个变体:")
        for i, variant in enumerate(variants[:10]):  # 只显示前10个
            print(f"  {i+1}: {variant}")
        if len(variants) > 10:
            print(f"  ... 还有 {len(variants) - 10} 个变体")
        print()