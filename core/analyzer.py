"""
分析功能模块
提供基于正则表达式的词条分析功能
"""
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
import json

from .database import db_manager
from .dictionary_manager import dictionary_manager
from .tag_manager import tag_manager
from utils.regex_helper import regex_helper


class RegexAnalyzer:
    """正则表达式分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.db = db_manager
        self.dict_manager = dictionary_manager
        self.tag_manager = tag_manager
        self.regex_helper = regex_helper
    
    def analyze_words(self, words: List[str], pattern_names: List[str]) -> Dict[str, Any]:
        """
        分析词条列表
        
        Args:
            words: 词条列表
            pattern_names: 要使用的模式名称列表
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            analysis_result = {
                "analysis_time": datetime.now().isoformat(),
                "total_words": len(words),
                "patterns_used": pattern_names,
                "pattern_results": {},
                "summary": {
                    "matched_words": 0,
                    "total_matches": 0,
                    "unmatched_words": 0
                },
                "matched_words_detail": {},
                "unmatched_words": []
            }
            
            matched_words = set()
            total_matches = 0
            
            # 对每个模式进行分析
            for pattern_name in pattern_names:
                pattern_result = self._analyze_single_pattern(words, pattern_name)
                analysis_result["pattern_results"][pattern_name] = pattern_result
                
                # 更新统计信息
                for word in pattern_result["matched_words"]:
                    matched_words.add(word)
                    if word not in analysis_result["matched_words_detail"]:
                        analysis_result["matched_words_detail"][word] = []
                    analysis_result["matched_words_detail"][word].append(pattern_name)
                
                total_matches += pattern_result["total_matches"]
            
            # 计算汇总信息
            analysis_result["summary"]["matched_words"] = len(matched_words)
            analysis_result["summary"]["total_matches"] = total_matches
            analysis_result["summary"]["unmatched_words"] = len(words) - len(matched_words)
            analysis_result["summary"]["match_rate"] = len(matched_words) / len(words) * 100 if words else 0
            
            # 获取未匹配的词条
            analysis_result["unmatched_words"] = [word for word in words if word not in matched_words]
            
            logging.info(f"词条分析完成: {len(words)} 个词条, {len(matched_words)} 个匹配")
            return analysis_result
            
        except Exception as e:
            logging.error(f"词条分析失败: {e}")
            return {}
    
    def _analyze_single_pattern(self, words: List[str], pattern_name: str) -> Dict[str, Any]:
        """
        使用单个模式分析词条
        
        Args:
            words: 词条列表
            pattern_name: 模式名称
            
        Returns:
            Dict[str, Any]: 单个模式的分析结果
        """
        result = {
            "pattern_name": pattern_name,
            "matched_words": [],
            "match_details": {},
            "total_matches": 0,
            "match_rate": 0
        }
        
        try:
            pattern_info = self.regex_helper.get_pattern_info(pattern_name)
            if pattern_info:
                result["pattern_description"] = pattern_info.get("description", "")
                result["pattern_regex"] = pattern_info.get("pattern", "")
            
            for word in words:
                matches = self.regex_helper.match_pattern(word, pattern_name)
                if matches:
                    result["matched_words"].append(word)
                    result["match_details"][word] = matches
                    result["total_matches"] += len(matches)
            
            result["match_rate"] = len(result["matched_words"]) / len(words) * 100 if words else 0
            
        except Exception as e:
            logging.error(f"单模式分析失败 {pattern_name}: {e}")
        
        return result
    
    def analyze_dictionary(self, dictionary_id: int, pattern_names: List[str]) -> Dict[str, Any]:
        """
        分析字典中的词条
        
        Args:
            dictionary_id: 字典ID
            pattern_names: 要使用的模式名称列表
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # 获取字典信息
            dictionary = self.dict_manager.get_dictionary_by_id(dictionary_id)
            if not dictionary:
                raise ValueError(f"字典不存在: ID {dictionary_id}")
            
            # 获取字典中的所有词条
            words_data = self.db.fetch_all(
                "SELECT word FROM words WHERE dictionary_id = ?",
                (dictionary_id,)
            )
            
            words = [row['word'] for row in words_data]
            
            if not words:
                logging.warning(f"字典 {dictionary_id} 中没有词条")
                return {}
            
            # 执行分析
            analysis_result = self.analyze_words(words, pattern_names)
            
            # 添加字典信息
            analysis_result["dictionary_info"] = {
                "id": dictionary_id,
                "name": dictionary["name"],
                "description": dictionary.get("description", "")
            }
            
            return analysis_result
            
        except Exception as e:
            logging.error(f"字典分析失败: {e}")
            return {}
    
    def batch_analyze_dictionaries(self, dictionary_ids: List[int], pattern_names: List[str]) -> Dict[int, Dict[str, Any]]:
        """
        批量分析多个字典
        
        Args:
            dictionary_ids: 字典ID列表
            pattern_names: 要使用的模式名称列表
            
        Returns:
            Dict[int, Dict[str, Any]]: 字典ID到分析结果的映射
        """
        results = {}
        
        for dictionary_id in dictionary_ids:
            try:
                result = self.analyze_dictionary(dictionary_id, pattern_names)
                if result:
                    results[dictionary_id] = result
                    logging.info(f"字典 {dictionary_id} 分析完成")
                else:
                    logging.warning(f"字典 {dictionary_id} 分析失败或无结果")
                    
            except Exception as e:
                logging.error(f"字典 {dictionary_id} 分析失败: {e}")
                results[dictionary_id] = {"error": str(e)}
        
        return results
    
    def create_tags_from_analysis(self, analysis_result: Dict[str, Any], dictionary_id: int = None) -> Dict[str, int]:
        """
        根据分析结果创建标签
        
        Args:
            analysis_result: 分析结果
            dictionary_id: 字典ID，如果提供则为匹配的词条添加标签
            
        Returns:
            Dict[str, int]: 模式名称到标签ID的映射
        """
        created_tags = {}
        
        try:
            for pattern_name, pattern_result in analysis_result.get("pattern_results", {}).items():
                if not pattern_result.get("matched_words"):
                    continue
                
                # 创建或获取标签
                existing_tag = self.tag_manager.get_tag_by_name(pattern_name)
                if existing_tag:
                    tag_id = existing_tag["id"]
                    logging.info(f"使用现有标签: {pattern_name} (ID: {tag_id})")
                else:
                    # 创建新标签
                    description = pattern_result.get("pattern_description", f"匹配模式: {pattern_name}")
                    tag_id = self.tag_manager.create_tag(pattern_name, description=description)
                    logging.info(f"创建新标签: {pattern_name} (ID: {tag_id})")
                
                created_tags[pattern_name] = tag_id
                
                # 如果提供了字典ID，为匹配的词条添加标签
                if dictionary_id is not None:
                    matched_words = pattern_result["matched_words"]
                    word_ids = self._get_word_ids(dictionary_id, matched_words)
                    
                    if word_ids:
                        added_count = self.tag_manager.batch_tag_words(word_ids, [tag_id])
                        logging.info(f"为 {added_count} 个词条添加标签 {pattern_name}")
            
            return created_tags
            
        except Exception as e:
            logging.error(f"根据分析结果创建标签失败: {e}")
            return {}
    
    def _get_word_ids(self, dictionary_id: int, words: List[str]) -> List[int]:
        """
        获取词条的ID列表
        
        Args:
            dictionary_id: 字典ID
            words: 词条列表
            
        Returns:
            List[int]: 词条ID列表
        """
        try:
            if not words:
                return []
            
            placeholders = ','.join(['?'] * len(words))
            query = f"""SELECT id FROM words 
                       WHERE dictionary_id = ? AND word IN ({placeholders})"""
            
            params = [dictionary_id] + words
            rows = self.db.fetch_all(query, params)
            
            return [row['id'] for row in rows]
            
        except Exception as e:
            logging.error(f"获取词条ID失败: {e}")
            return []
    
    def export_analysis_result(self, analysis_result: Dict[str, Any], file_path: str, format: str = "json") -> bool:
        """
        导出分析结果
        
        Args:
            analysis_result: 分析结果
            file_path: 导出文件路径
            format: 导出格式 (json, txt, csv)
            
        Returns:
            bool: 导出是否成功
        """
        try:
            from pathlib import Path
            
            # 确保导出目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "json":
                return self._export_json(analysis_result, file_path)
            elif format.lower() == "txt":
                return self._export_txt(analysis_result, file_path)
            elif format.lower() == "csv":
                return self._export_csv(analysis_result, file_path)
            else:
                logging.error(f"不支持的导出格式: {format}")
                return False
                
        except Exception as e:
            logging.error(f"导出分析结果失败: {e}")
            return False
    
    def _export_json(self, analysis_result: Dict[str, Any], file_path: str) -> bool:
        """导出为JSON格式"""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(analysis_result, file, ensure_ascii=False, indent=2)
            
            logging.info(f"分析结果导出为JSON成功: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"JSON导出失败: {e}")
            return False
    
    def _export_txt(self, analysis_result: Dict[str, Any], file_path: str) -> bool:
        """导出为TXT格式"""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write("=== 字典分析报告 ===\n\n")
                
                # 基本信息
                file.write(f"分析时间: {analysis_result.get('analysis_time', 'N/A')}\n")
                file.write(f"总词条数: {analysis_result.get('total_words', 0)}\n")
                file.write(f"使用模式: {', '.join(analysis_result.get('patterns_used', []))}\n\n")
                
                # 汇总信息
                summary = analysis_result.get('summary', {})
                file.write("=== 分析汇总 ===\n")
                file.write(f"匹配词条数: {summary.get('matched_words', 0)}\n")
                file.write(f"总匹配次数: {summary.get('total_matches', 0)}\n")
                file.write(f"未匹配词条数: {summary.get('unmatched_words', 0)}\n")
                file.write(f"匹配率: {summary.get('match_rate', 0):.2f}%\n\n")
                
                # 各模式详细结果
                file.write("=== 模式分析详情 ===\n")
                for pattern_name, pattern_result in analysis_result.get('pattern_results', {}).items():
                    file.write(f"\n--- {pattern_name} ---\n")
                    file.write(f"描述: {pattern_result.get('pattern_description', 'N/A')}\n")
                    file.write(f"正则表达式: {pattern_result.get('pattern_regex', 'N/A')}\n")
                    file.write(f"匹配词条数: {len(pattern_result.get('matched_words', []))}\n")
                    file.write(f"匹配率: {pattern_result.get('match_rate', 0):.2f}%\n")
                    
                    matched_words = pattern_result.get('matched_words', [])
                    if matched_words:
                        file.write("匹配词条:\n")
                        for word in matched_words[:20]:  # 只显示前20个
                            file.write(f"  - {word}\n")
                        if len(matched_words) > 20:
                            file.write(f"  ... 还有 {len(matched_words) - 20} 个词条\n")
                
                # 未匹配词条
                unmatched = analysis_result.get('unmatched_words', [])
                if unmatched:
                    file.write(f"\n=== 未匹配词条 ({len(unmatched)} 个) ===\n")
                    for word in unmatched[:50]:  # 只显示前50个
                        file.write(f"  - {word}\n")
                    if len(unmatched) > 50:
                        file.write(f"  ... 还有 {len(unmatched) - 50} 个词条\n")
            
            logging.info(f"分析结果导出为TXT成功: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"TXT导出失败: {e}")
            return False
    
    def _export_csv(self, analysis_result: Dict[str, Any], file_path: str) -> bool:
        """导出为CSV格式"""
        try:
            import csv
            
            with open(file_path, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                
                # 写入标题行
                writer.writerow(['词条', '匹配模式', '匹配详情'])
                
                # 写入匹配的词条
                for word, patterns in analysis_result.get('matched_words_detail', {}).items():
                    pattern_str = ', '.join(patterns)
                    
                    # 获取匹配详情
                    details = []
                    for pattern_name in patterns:
                        pattern_result = analysis_result.get('pattern_results', {}).get(pattern_name, {})
                        word_matches = pattern_result.get('match_details', {}).get(word, [])
                        if word_matches:
                            details.append(f"{pattern_name}: {', '.join(word_matches)}")
                    
                    detail_str = '; '.join(details)
                    writer.writerow([word, pattern_str, detail_str])
                
                # 写入未匹配的词条
                for word in analysis_result.get('unmatched_words', []):
                    writer.writerow([word, '无匹配', ''])
            
            logging.info(f"分析结果导出为CSV成功: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"CSV导出失败: {e}")
            return False
    
    def get_analysis_suggestions(self, analysis_result: Dict[str, Any]) -> List[str]:
        """
        根据分析结果提供建议
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            List[str]: 建议列表
        """
        suggestions = []
        
        try:
            summary = analysis_result.get('summary', {})
            match_rate = summary.get('match_rate', 0)
            unmatched_count = summary.get('unmatched_words', 0)
            
            # 基于匹配率的建议
            if match_rate < 20:
                suggestions.append("匹配率较低，建议检查正则表达式模式是否适合当前词条类型")
            elif match_rate > 80:
                suggestions.append("匹配率很高，词条分类效果良好")
            
            # 基于未匹配词条的建议
            if unmatched_count > 100:
                suggestions.append(f"有 {unmatched_count} 个未匹配词条，建议添加更多正则模式或检查词条质量")
            
            # 基于各模式效果的建议
            pattern_results = analysis_result.get('pattern_results', {})
            low_performance_patterns = []
            high_performance_patterns = []
            
            for pattern_name, result in pattern_results.items():
                pattern_match_rate = result.get('match_rate', 0)
                if pattern_match_rate < 5:
                    low_performance_patterns.append(pattern_name)
                elif pattern_match_rate > 50:
                    high_performance_patterns.append(pattern_name)
            
            if low_performance_patterns:
                suggestions.append(f"以下模式匹配率较低，建议优化: {', '.join(low_performance_patterns)}")
            
            if high_performance_patterns:
                suggestions.append(f"以下模式效果良好，可作为主要分类依据: {', '.join(high_performance_patterns)}")
            
            # 基于词条特征的建议
            if analysis_result.get('total_words', 0) < 100:
                suggestions.append("词条数量较少，分析结果可能不够准确，建议增加更多词条")
            
        except Exception as e:
            logging.error(f"生成分析建议失败: {e}")
        
        return suggestions


class DictionaryAnalyzer:
    """字典分析器 - 兼容性类"""
    
    def __init__(self, db_manager):
        """初始化字典分析器"""
        self.db_manager = db_manager
        self.regex_analyzer = RegexAnalyzer()
    
    def analyze_dictionary(self, dictionary_id: int) -> Dict[str, Any]:
        """
        分析字典统计信息
        
        Args:
            dictionary_id: 字典ID
            
        Returns:
            字典统计信息
        """
        try:
            cursor = self.db_manager.get_cursor()
            
            # 基本统计
            cursor.execute("SELECT COUNT(*) FROM words WHERE dictionary_id = ?", (dictionary_id,))
            total_words = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT word) FROM words WHERE dictionary_id = ?", (dictionary_id,))
            unique_words = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(LENGTH(word)) FROM words WHERE dictionary_id = ?", (dictionary_id,))
            avg_length = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT MIN(LENGTH(word)), MAX(LENGTH(word)) FROM words WHERE dictionary_id = ?", (dictionary_id,))
            min_length, max_length = cursor.fetchone()
            
            return {
                'total_words': total_words,
                'unique_words': unique_words,
                'avg_length': float(avg_length),
                'min_length': min_length or 0,
                'max_length': max_length or 0
            }
            
        except Exception as e:
            logging.error(f"字典分析失败: {e}")
            return {
                'total_words': 0,
                'unique_words': 0,
                'avg_length': 0,
                'min_length': 0,
                'max_length': 0
            }

# 全局分析器实例
analyzer = RegexAnalyzer()


if __name__ == "__main__":
    # 测试分析功能
    logging.basicConfig(level=logging.INFO)
    
    # 测试数据
    test_words = [
        "/api/users",
        "/swagger-ui.html",
        "wp-admin/admin.php",
        "example@test.com",
        "192.168.1.1:8080",
        "select * from users",
        "<script>alert('xss')</script>",
        "normal_word",
        "another_word"
    ]
    
    # 获取可用的模式
    pattern_names = regex_helper.get_all_pattern_names()[:5]  # 只使用前5个模式
    
    print(f"测试词条: {test_words}")
    print(f"使用模式: {pattern_names}")
    
    # 执行分析
    result = analyzer.analyze_words(test_words, pattern_names)
    
    print(f"\n分析结果汇总:")
    print(f"  总词条数: {result.get('total_words', 0)}")
    print(f"  匹配词条数: {result.get('summary', {}).get('matched_words', 0)}")
    print(f"  匹配率: {result.get('summary', {}).get('match_rate', 0):.2f}%")
    
    # 显示各模式结果
    for pattern_name, pattern_result in result.get('pattern_results', {}).items():
        matched_count = len(pattern_result.get('matched_words', []))
        if matched_count > 0:
            print(f"\n模式 '{pattern_name}':")
            print(f"  匹配词条数: {matched_count}")
            print(f"  匹配词条: {pattern_result.get('matched_words', [])}")
    
    # 获取建议
    suggestions = analyzer.get_analysis_suggestions(result)
    if suggestions:
        print(f"\n分析建议:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")