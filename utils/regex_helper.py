"""
正则表达式辅助工具模块
提供正则表达式配置加载、模式匹配和管理功能
"""
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

from config.settings import CONFIG_DIR


class RegexHelper:
    """正则表达式辅助工具"""
    
    def __init__(self, config_path: str = None):
        """
        初始化正则表达式辅助工具
        
        Args:
            config_path: 配置文件路径，默认使用配置目录中的文件
        """
        self.config_path = config_path or (CONFIG_DIR / "regex_patterns.json")
        self.patterns = {}
        self.compiled_patterns = {}
        self.load_patterns()
    
    def load_patterns(self) -> bool:
        """
        加载正则表达式配置
        
        Returns:
            bool: 加载是否成功
        """
        try:
            if not Path(self.config_path).exists():
                logging.warning(f"正则配置文件不存在: {self.config_path}")
                self._create_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
            
            self.patterns = config
            self._compile_patterns()
            
            logging.info(f"正则表达式配置加载成功: {len(self.get_all_pattern_names())} 个模式")
            return True
            
        except Exception as e:
            logging.error(f"加载正则表达式配置失败: {e}")
            return False
    
    def save_patterns(self) -> bool:
        """
        保存正则表达式配置
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保配置目录存在
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as file:
                json.dump(self.patterns, file, ensure_ascii=False, indent=2)
            
            logging.info("正则表达式配置保存成功")
            return True
            
        except Exception as e:
            logging.error(f"保存正则表达式配置失败: {e}")
            return False
    
    def _create_default_config(self):
        """创建默认配置"""
        default_config = {
            "preset_patterns": {
                "basic": {
                    "name": "基础模式",
                    "patterns": [
                        {
                            "name": "数字",
                            "pattern": r"\d+",
                            "description": "匹配数字"
                        },
                        {
                            "name": "邮箱",
                            "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                            "description": "匹配邮箱地址"
                        }
                    ]
                }
            },
            "custom_patterns": []
        }
        
        self.patterns = default_config
        self.save_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        self.compiled_patterns = {}
        
        # 编译预设模式
        for category_name, category in self.patterns.get("preset_patterns", {}).items():
            self.compiled_patterns[category_name] = {}
            for pattern_info in category.get("patterns", []):
                pattern_name = pattern_info["name"]
                pattern_str = pattern_info["pattern"]
                
                try:
                    compiled_pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                    self.compiled_patterns[category_name][pattern_name] = compiled_pattern
                except re.error as e:
                    logging.error(f"编译正则表达式失败: {pattern_name} - {e}")
        
        # 编译自定义模式
        custom_patterns = {}
        for pattern_info in self.patterns.get("custom_patterns", []):
            pattern_name = pattern_info["name"]
            pattern_str = pattern_info["pattern"]
            
            try:
                compiled_pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                custom_patterns[pattern_name] = compiled_pattern
            except re.error as e:
                logging.error(f"编译自定义正则表达式失败: {pattern_name} - {e}")
        
        if custom_patterns:
            self.compiled_patterns["custom"] = custom_patterns
    
    def get_categories(self) -> List[str]:
        """
        获取所有模式分类
        
        Returns:
            List[str]: 分类名称列表
        """
        categories = list(self.patterns.get("preset_patterns", {}).keys())
        if self.patterns.get("custom_patterns"):
            categories.append("custom")
        return categories
    
    def get_patterns_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        根据分类获取模式
        
        Args:
            category: 分类名称
            
        Returns:
            List[Dict[str, Any]]: 模式列表
        """
        if category == "custom":
            return self.patterns.get("custom_patterns", [])
        
        category_data = self.patterns.get("preset_patterns", {}).get(category, {})
        return category_data.get("patterns", [])
    
    def get_all_pattern_names(self) -> List[str]:
        """
        获取所有模式名称
        
        Returns:
            List[str]: 模式名称列表
        """
        pattern_names = []
        
        # 预设模式
        for category in self.patterns.get("preset_patterns", {}).values():
            for pattern in category.get("patterns", []):
                pattern_names.append(pattern["name"])
        
        # 自定义模式
        for pattern in self.patterns.get("custom_patterns", []):
            pattern_names.append(pattern["name"])
        
        return pattern_names
    
    def get_pattern_info(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模式信息
        
        Args:
            pattern_name: 模式名称
            
        Returns:
            Optional[Dict[str, Any]]: 模式信息，如果不存在则返回None
        """
        # 在预设模式中查找
        for category in self.patterns.get("preset_patterns", {}).values():
            for pattern in category.get("patterns", []):
                if pattern["name"] == pattern_name:
                    return pattern
        
        # 在自定义模式中查找
        for pattern in self.patterns.get("custom_patterns", []):
            if pattern["name"] == pattern_name:
                return pattern
        
        return None
    
    def add_custom_pattern(self, name: str, pattern: str, description: str = "") -> bool:
        """
        添加自定义模式
        
        Args:
            name: 模式名称
            pattern: 正则表达式
            description: 模式描述
            
        Returns:
            bool: 添加是否成功
        """
        try:
            # 检查名称是否已存在
            if name in self.get_all_pattern_names():
                raise ValueError(f"模式名称 '{name}' 已存在")
            
            # 验证正则表达式
            re.compile(pattern)
            
            # 添加到自定义模式
            if "custom_patterns" not in self.patterns:
                self.patterns["custom_patterns"] = []
            
            self.patterns["custom_patterns"].append({
                "name": name,
                "pattern": pattern,
                "description": description
            })
            
            # 重新编译模式
            self._compile_patterns()
            
            # 保存配置
            self.save_patterns()
            
            logging.info(f"添加自定义模式成功: {name}")
            return True
            
        except Exception as e:
            logging.error(f"添加自定义模式失败: {e}")
            return False
    
    def remove_custom_pattern(self, name: str) -> bool:
        """
        删除自定义模式
        
        Args:
            name: 模式名称
            
        Returns:
            bool: 删除是否成功
        """
        try:
            custom_patterns = self.patterns.get("custom_patterns", [])
            
            for i, pattern in enumerate(custom_patterns):
                if pattern["name"] == name:
                    del custom_patterns[i]
                    
                    # 重新编译模式
                    self._compile_patterns()
                    
                    # 保存配置
                    self.save_patterns()
                    
                    logging.info(f"删除自定义模式成功: {name}")
                    return True
            
            logging.warning(f"自定义模式不存在: {name}")
            return False
            
        except Exception as e:
            logging.error(f"删除自定义模式失败: {e}")
            return False
    
    def match_pattern(self, text: str, pattern_name: str) -> List[str]:
        """
        使用指定模式匹配文本
        
        Args:
            text: 要匹配的文本
            pattern_name: 模式名称
            
        Returns:
            List[str]: 匹配结果列表
        """
        try:
            # 查找编译后的模式
            compiled_pattern = None
            
            for category_patterns in self.compiled_patterns.values():
                if pattern_name in category_patterns:
                    compiled_pattern = category_patterns[pattern_name]
                    break
            
            if compiled_pattern is None:
                logging.warning(f"模式不存在: {pattern_name}")
                return []
            
            matches = compiled_pattern.findall(text)
            return matches
            
        except Exception as e:
            logging.error(f"模式匹配失败: {e}")
            return []
    
    def match_multiple_patterns(self, text: str, pattern_names: List[str]) -> Dict[str, List[str]]:
        """
        使用多个模式匹配文本
        
        Args:
            text: 要匹配的文本
            pattern_names: 模式名称列表
            
        Returns:
            Dict[str, List[str]]: 模式名称到匹配结果的映射
        """
        results = {}
        
        for pattern_name in pattern_names:
            matches = self.match_pattern(text, pattern_name)
            if matches:
                results[pattern_name] = matches
        
        return results
    
    def search_pattern(self, text: str, pattern_name: str) -> List[Tuple[int, int, str]]:
        """
        搜索模式并返回位置信息
        
        Args:
            text: 要搜索的文本
            pattern_name: 模式名称
            
        Returns:
            List[Tuple[int, int, str]]: 匹配结果列表 (开始位置, 结束位置, 匹配文本)
        """
        try:
            # 查找编译后的模式
            compiled_pattern = None
            
            for category_patterns in self.compiled_patterns.values():
                if pattern_name in category_patterns:
                    compiled_pattern = category_patterns[pattern_name]
                    break
            
            if compiled_pattern is None:
                return []
            
            matches = []
            for match in compiled_pattern.finditer(text):
                matches.append((match.start(), match.end(), match.group()))
            
            return matches
            
        except Exception as e:
            logging.error(f"模式搜索失败: {e}")
            return []
    
    def validate_pattern(self, pattern: str) -> Tuple[bool, str]:
        """
        验证正则表达式
        
        Args:
            pattern: 正则表达式字符串
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            re.compile(pattern)
            return True, ""
        except re.error as e:
            return False, str(e)
    
    def get_pattern_statistics(self, words: List[str], pattern_names: List[str] = None) -> Dict[str, Any]:
        """
        获取模式匹配统计信息
        
        Args:
            words: 词条列表
            pattern_names: 要统计的模式名称列表，如果为None则统计所有模式
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        if pattern_names is None:
            pattern_names = self.get_all_pattern_names()
        
        stats = {
            "total_words": len(words),
            "pattern_stats": {},
            "summary": {
                "matched_words": 0,
                "total_matches": 0
            }
        }
        
        matched_words = set()
        total_matches = 0
        
        for pattern_name in pattern_names:
            pattern_matches = 0
            pattern_words = 0
            
            for word in words:
                matches = self.match_pattern(word, pattern_name)
                if matches:
                    pattern_matches += len(matches)
                    pattern_words += 1
                    matched_words.add(word)
            
            stats["pattern_stats"][pattern_name] = {
                "matched_words": pattern_words,
                "total_matches": pattern_matches,
                "match_rate": pattern_words / len(words) * 100 if words else 0
            }
            
            total_matches += pattern_matches
        
        stats["summary"]["matched_words"] = len(matched_words)
        stats["summary"]["total_matches"] = total_matches
        stats["summary"]["overall_match_rate"] = len(matched_words) / len(words) * 100 if words else 0
        
        return stats
    
    def export_patterns(self, file_path: str, categories: List[str] = None) -> bool:
        """
        导出模式配置
        
        Args:
            file_path: 导出文件路径
            categories: 要导出的分类列表，如果为None则导出所有
            
        Returns:
            bool: 导出是否成功
        """
        try:
            export_data = {"preset_patterns": {}, "custom_patterns": []}
            
            # 导出预设模式
            if categories is None:
                export_data["preset_patterns"] = self.patterns.get("preset_patterns", {})
            else:
                for category in categories:
                    if category in self.patterns.get("preset_patterns", {}):
                        export_data["preset_patterns"][category] = self.patterns["preset_patterns"][category]
            
            # 导出自定义模式
            if categories is None or "custom" in categories:
                export_data["custom_patterns"] = self.patterns.get("custom_patterns", [])
            
            # 确保导出目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(export_data, file, ensure_ascii=False, indent=2)
            
            logging.info(f"模式配置导出成功: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"模式配置导出失败: {e}")
            return False
    
    def import_patterns(self, file_path: str, merge: bool = True) -> bool:
        """
        导入模式配置
        
        Args:
            file_path: 导入文件路径
            merge: 是否合并到现有配置，False表示替换
            
        Returns:
            bool: 导入是否成功
        """
        try:
            if not Path(file_path).exists():
                logging.error(f"导入文件不存在: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as file:
                import_data = json.load(file)
            
            if merge:
                # 合并模式
                preset_patterns = self.patterns.get("preset_patterns", {})
                for category, data in import_data.get("preset_patterns", {}).items():
                    preset_patterns[category] = data
                
                custom_patterns = self.patterns.get("custom_patterns", [])
                for pattern in import_data.get("custom_patterns", []):
                    # 检查是否已存在同名模式
                    existing_names = [p["name"] for p in custom_patterns]
                    if pattern["name"] not in existing_names:
                        custom_patterns.append(pattern)
                
                self.patterns["preset_patterns"] = preset_patterns
                self.patterns["custom_patterns"] = custom_patterns
            else:
                # 替换模式
                self.patterns = import_data
            
            # 重新编译和保存
            self._compile_patterns()
            self.save_patterns()
            
            logging.info(f"模式配置导入成功: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"模式配置导入失败: {e}")
            return False


# 全局正则表达式辅助工具实例
regex_helper = RegexHelper()


if __name__ == "__main__":
    # 测试正则表达式辅助工具
    logging.basicConfig(level=logging.INFO)
    
    # 测试数据
    test_words = [
        "/api/users",
        "/swagger-ui.html",
        "wp-admin/admin.php",
        "example@test.com",
        "192.168.1.1:8080",
        "select * from users",
        "<script>alert('xss')</script>"
    ]
    
    print(f"测试词条: {test_words}")
    
    # 测试获取所有模式
    pattern_names = regex_helper.get_all_pattern_names()
    print(f"\n可用模式: {pattern_names}")
    
    # 测试模式匹配
    for pattern_name in pattern_names[:5]:  # 只测试前5个模式
        matches = []
        for word in test_words:
            word_matches = regex_helper.match_pattern(word, pattern_name)
            if word_matches:
                matches.extend(word_matches)
        
        if matches:
            print(f"\n模式 '{pattern_name}' 匹配结果: {matches}")
    
    # 测试统计信息
    stats = regex_helper.get_pattern_statistics(test_words, pattern_names[:3])
    print(f"\n统计信息: {stats}")
    
    # 测试添加自定义模式
    success = regex_helper.add_custom_pattern(
        "测试模式", 
        r"test\d+", 
        "匹配test加数字"
    )
    print(f"\n添加自定义模式: {'成功' if success else '失败'}")