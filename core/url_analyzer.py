"""
URL过滤分析模块
通过正则表达式过滤和分析URL，提取带参数的URL
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from .database import db_manager


class URLAnalyzer:
    """URL分析器"""
    
    def __init__(self):
        """初始化URL分析器"""
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
        # URL匹配正则表达式
        self.url_patterns = {
            'http_url': re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+'),
            'url_with_params': re.compile(r'https?://[^\s<>"{}|\\^`\[\]]*\?[^\s<>"{}|\\^`\[\]]+'),
            'relative_url_with_params': re.compile(r'/[^\s<>"{}|\\^`\[\]]*\?[^\s<>"{}|\\^`\[\]]+'),
            'path_with_params': re.compile(r'[^\s<>"{}|\\^`\[\]]*\?[^\s<>"{}|\\^`\[\]]+')
        }
        
        # 参数模式
        self.param_patterns = {
            'query_param': re.compile(r'[?&]([^=&]+)=([^&]*)'),
            'has_params': re.compile(r'\?.*='),
            'multiple_params': re.compile(r'[?&][^=&]+=[^&]*(&[^=&]+=[^&]*)+')
        }
    
    def extract_urls_from_text(self, text: str, pattern_name: str = 'http_url') -> List[str]:
        """
        从文本中提取URL
        
        Args:
            text: 输入文本
            pattern_name: 使用的正则模式名称
            
        Returns:
            List[str]: 提取的URL列表
        """
        if pattern_name not in self.url_patterns:
            self.logger.warning(f"未知的URL模式: {pattern_name}")
            pattern_name = 'http_url'
        
        pattern = self.url_patterns[pattern_name]
        urls = pattern.findall(text)
        
        # 去重并排序
        return sorted(list(set(urls)))
    
    def has_parameters(self, url: str) -> bool:
        """
        检查URL是否包含参数
        
        Args:
            url: URL字符串
            
        Returns:
            bool: 是否包含参数
        """
        return bool(self.param_patterns['has_params'].search(url))
    
    def extract_parameters(self, url: str) -> Dict[str, List[str]]:
        """
        提取URL参数
        
        Args:
            url: URL字符串
            
        Returns:
            Dict[str, List[str]]: 参数字典
        """
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            return params
        except Exception as e:
            self.logger.error(f"解析URL参数失败: {e}")
            return {}
    
    def analyze_url(self, url: str) -> Dict[str, Any]:
        """
        分析单个URL
        
        Args:
            url: URL字符串
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            parsed = urlparse(url)
            params = self.extract_parameters(url)
            
            analysis = {
                'url': url,
                'scheme': parsed.scheme,
                'domain': parsed.netloc,
                'path': parsed.path,
                'query': parsed.query,
                'fragment': parsed.fragment,
                'has_params': bool(parsed.query),
                'param_count': len(params),
                'param_names': list(params.keys()),
                'params': params
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析URL失败: {e}")
            return {
                'url': url,
                'error': str(e),
                'has_params': False,
                'param_count': 0,
                'param_names': [],
                'params': {}
            }
    
    def filter_urls_with_params(self, urls: List[str]) -> List[str]:
        """
        过滤出带参数的URL
        
        Args:
            urls: URL列表
            
        Returns:
            List[str]: 带参数的URL列表
        """
        return [url for url in urls if self.has_parameters(url)]
    
    def categorize_urls(self, urls: List[str]) -> Dict[str, List[str]]:
        """
        对URL进行分类
        
        Args:
            urls: URL列表
            
        Returns:
            Dict[str, List[str]]: 分类结果
        """
        categories = {
            'with_params': [],
            'without_params': [],
            'multiple_params': [],
            'single_param': [],
            'domains': {}
        }
        
        for url in urls:
            analysis = self.analyze_url(url)
            
            if analysis['has_params']:
                categories['with_params'].append(url)
                
                if analysis['param_count'] > 1:
                    categories['multiple_params'].append(url)
                else:
                    categories['single_param'].append(url)
            else:
                categories['without_params'].append(url)
            
            # 按域名分类
            domain = analysis.get('domain', 'unknown')
            if domain:
                if domain not in categories['domains']:
                    categories['domains'][domain] = []
                categories['domains'][domain].append(url)
        
        return categories
    
    def extract_common_parameters(self, urls: List[str]) -> Dict[str, int]:
        """
        提取常见参数名称及其出现频率
        
        Args:
            urls: URL列表
            
        Returns:
            Dict[str, int]: 参数名称及出现次数
        """
        param_counts = {}
        
        for url in urls:
            params = self.extract_parameters(url)
            for param_name in params.keys():
                param_counts[param_name] = param_counts.get(param_name, 0) + 1
        
        # 按出现次数排序
        return dict(sorted(param_counts.items(), key=lambda x: x[1], reverse=True))
    
    def save_url_analysis(self, dictionary_id: int, urls: List[str]) -> int:
        """
        保存URL分析结果到数据库
        
        Args:
            dictionary_id: 字典ID
            urls: URL列表
            
        Returns:
            int: 保存的记录数
        """
        try:
            # 清除该字典的旧分析结果
            self.db.execute_query(
                "DELETE FROM url_analysis WHERE dictionary_id = ?",
                (dictionary_id,)
            )
            
            # 分析并保存新结果
            analysis_data = []
            current_time = datetime.now()
            
            for url in urls:
                analysis = self.analyze_url(url)
                
                analysis_data.append((
                    dictionary_id,
                    url,
                    analysis['has_params'],
                    analysis.get('domain', ''),
                    analysis.get('path', ''),
                    analysis.get('query', ''),
                    current_time
                ))
            
            if analysis_data:
                saved_count = self.db.execute_many(
                    """INSERT INTO url_analysis 
                       (dictionary_id, url, has_params, domain, path, params, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    analysis_data
                )
                
                self.logger.info(f"保存URL分析结果: {saved_count} 条记录")
                return saved_count
            
            return 0
            
        except Exception as e:
            self.logger.error(f"保存URL分析结果失败: {e}")
            return 0
    
    def get_url_analysis(self, dictionary_id: int, has_params: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        获取URL分析结果
        
        Args:
            dictionary_id: 字典ID
            has_params: 是否只获取带参数的URL，None表示获取所有
            
        Returns:
            List[Dict[str, Any]]: 分析结果列表
        """
        try:
            if has_params is None:
                query = "SELECT * FROM url_analysis WHERE dictionary_id = ? ORDER BY created_at DESC"
                params = (dictionary_id,)
            else:
                query = "SELECT * FROM url_analysis WHERE dictionary_id = ? AND has_params = ? ORDER BY created_at DESC"
                params = (dictionary_id, has_params)
            
            rows = self.db.fetch_all(query, params)
            return [dict(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"获取URL分析结果失败: {e}")
            return []
    
    def get_url_statistics(self, dictionary_id: int) -> Dict[str, Any]:
        """
        获取URL统计信息
        
        Args:
            dictionary_id: 字典ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            stats = {}
            
            # 总URL数量
            total_result = self.db.fetch_one(
                "SELECT COUNT(*) as total FROM url_analysis WHERE dictionary_id = ?",
                (dictionary_id,)
            )
            stats['total_urls'] = total_result['total'] if total_result else 0
            
            # 带参数的URL数量
            params_result = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM url_analysis WHERE dictionary_id = ? AND has_params = 1",
                (dictionary_id,)
            )
            stats['urls_with_params'] = params_result['count'] if params_result else 0
            
            # 不带参数的URL数量
            stats['urls_without_params'] = stats['total_urls'] - stats['urls_with_params']
            
            # 域名统计
            domain_results = self.db.fetch_all(
                "SELECT domain, COUNT(*) as count FROM url_analysis WHERE dictionary_id = ? GROUP BY domain ORDER BY count DESC",
                (dictionary_id,)
            )
            stats['domains'] = {row['domain']: row['count'] for row in domain_results}
            
            # 参数统计（需要解析params字段）
            param_urls = self.get_url_analysis(dictionary_id, has_params=True)
            param_counts = {}
            
            for url_data in param_urls:
                url = url_data['url']
                params = self.extract_parameters(url)
                for param_name in params.keys():
                    param_counts[param_name] = param_counts.get(param_name, 0) + 1
            
            stats['common_params'] = dict(sorted(param_counts.items(), key=lambda x: x[1], reverse=True))
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取URL统计信息失败: {e}")
            return {}
    
    def process_url_file(self, file_path: str) -> Tuple[List[str], Dict[str, Any]]:
        """
        处理URL文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[List[str], Dict[str, Any]]: (URL列表, 分析统计)
        """
        try:
            urls = []
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取URL
            all_urls = self.extract_urls_from_text(content, 'http_url')
            
            # 分类和统计
            categories = self.categorize_urls(all_urls)
            
            # 提取带参数的URL
            urls_with_params = categories['with_params']
            
            # 生成统计信息
            stats = {
                'total_urls': len(all_urls),
                'urls_with_params': len(urls_with_params),
                'urls_without_params': len(categories['without_params']),
                'multiple_params': len(categories['multiple_params']),
                'single_param': len(categories['single_param']),
                'domains': len(categories['domains']),
                'common_params': self.extract_common_parameters(urls_with_params)
            }
            
            return urls_with_params, stats
            
        except Exception as e:
            self.logger.error(f"处理URL文件失败: {e}")
            return [], {}
    
    def generate_param_variations(self, base_url: str, param_values: Dict[str, List[str]]) -> List[str]:
        """
        生成参数变体URL
        
        Args:
            base_url: 基础URL（不含参数）
            param_values: 参数值字典
            
        Returns:
            List[str]: 变体URL列表
        """
        try:
            from itertools import product
            
            if not param_values:
                return [base_url]
            
            # 获取参数名和值列表
            param_names = list(param_values.keys())
            param_value_lists = [param_values[name] for name in param_names]
            
            # 生成所有组合
            variations = []
            for value_combination in product(*param_value_lists):
                params = []
                for i, value in enumerate(value_combination):
                    params.append(f"{param_names[i]}={value}")
                
                param_string = "&".join(params)
                if '?' in base_url:
                    url = f"{base_url}&{param_string}"
                else:
                    url = f"{base_url}?{param_string}"
                
                variations.append(url)
            
            return variations
            
        except Exception as e:
            self.logger.error(f"生成参数变体失败: {e}")
            return [base_url]


# 全局URL分析器实例
url_analyzer = URLAnalyzer()


if __name__ == "__main__":
    # 测试URL分析功能
    logging.basicConfig(level=logging.INFO)
    
    test_urls = [
        "https://example.com/api/users?id=123&name=admin",
        "https://test.com/login",
        "https://api.example.com/v1/data?token=abc123&format=json&limit=10",
        "/admin/panel?session=xyz789",
        "https://site.com/search?q=test&page=1&sort=date"
    ]
    
    print("测试URL列表:")
    for url in test_urls:
        print(f"  {url}")
    print()
    
    # 测试URL分析
    print("URL分析结果:")
    for url in test_urls:
        analysis = url_analyzer.analyze_url(url)
        print(f"URL: {url}")
        print(f"  域名: {analysis.get('domain', 'N/A')}")
        print(f"  路径: {analysis.get('path', 'N/A')}")
        print(f"  有参数: {analysis['has_params']}")
        print(f"  参数数量: {analysis['param_count']}")
        print(f"  参数名: {analysis['param_names']}")
        print()
    
    # 测试分类
    categories = url_analyzer.categorize_urls(test_urls)
    print("URL分类:")
    print(f"  带参数: {len(categories['with_params'])} 个")
    print(f"  不带参数: {len(categories['without_params'])} 个")
    print(f"  多参数: {len(categories['multiple_params'])} 个")
    print(f"  单参数: {len(categories['single_param'])} 个")
    print()
    
    # 测试常见参数
    common_params = url_analyzer.extract_common_parameters(test_urls)
    print("常见参数:")
    for param, count in common_params.items():
        print(f"  {param}: {count} 次")