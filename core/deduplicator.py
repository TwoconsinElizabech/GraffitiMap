"""
去重功能模块
提供多种去重策略，包括精确匹配、忽略大小写、相似度匹配等
"""
import logging
import re
from typing import List, Dict, Set, Callable, Tuple, Any
from difflib import SequenceMatcher
from collections import defaultdict, Counter

from .database import db_manager
from config.settings import SIMILARITY_THRESHOLD, DEFAULT_DEDUP_STRATEGY


class Deduplicator:
    """去重器"""
    
    def __init__(self):
        """初始化去重器"""
        self.db = db_manager
        self.strategies = {
            'exact': self.exact_duplicate,
            'case_insensitive': self.case_insensitive_duplicate,
            'similarity': self.similarity_duplicate,
            'length': self.length_duplicate,
            'pattern': self.pattern_duplicate
        }
    
    def exact_duplicate(self, words: List[str]) -> List[str]:
        """
        精确去重 - 完全相同的词条
        
        Args:
            words: 词条列表
            
        Returns:
            List[str]: 去重后的词条列表
        """
        seen = set()
        unique_words = []
        
        for word in words:
            if word not in seen:
                seen.add(word)
                unique_words.append(word)
        
        removed_count = len(words) - len(unique_words)
        logging.info(f"精确去重完成: 移除 {removed_count} 个重复词条")
        
        return unique_words
    
    def case_insensitive_duplicate(self, words: List[str]) -> List[str]:
        """
        忽略大小写去重
        
        Args:
            words: 词条列表
            
        Returns:
            List[str]: 去重后的词条列表
        """
        seen = set()
        unique_words = []
        
        for word in words:
            word_lower = word.lower()
            if word_lower not in seen:
                seen.add(word_lower)
                unique_words.append(word)
        
        removed_count = len(words) - len(unique_words)
        logging.info(f"忽略大小写去重完成: 移除 {removed_count} 个重复词条")
        
        return unique_words
    
    def similarity_duplicate(self, words: List[str], threshold: float = None) -> List[str]:
        """
        相似度去重 - 基于字符串相似度
        
        Args:
            words: 词条列表
            threshold: 相似度阈值，默认使用配置中的值
            
        Returns:
            List[str]: 去重后的词条列表
        """
        if threshold is None:
            threshold = SIMILARITY_THRESHOLD
        
        unique_words = []
        
        for word in words:
            is_similar = False
            
            for existing_word in unique_words:
                similarity = self._calculate_similarity(word, existing_word)
                if similarity >= threshold:
                    is_similar = True
                    break
            
            if not is_similar:
                unique_words.append(word)
        
        removed_count = len(words) - len(unique_words)
        logging.info(f"相似度去重完成 (阈值: {threshold}): 移除 {removed_count} 个相似词条")
        
        return unique_words
    
    def length_duplicate(self, words: List[str], keep_longest: bool = True) -> List[str]:
        """
        长度去重 - 对于相似的词条，保留最长或最短的
        
        Args:
            words: 词条列表
            keep_longest: 是否保留最长的词条
            
        Returns:
            List[str]: 去重后的词条列表
        """
        # 按长度分组
        length_groups = defaultdict(list)
        for word in words:
            length_groups[len(word)].append(word)
        
        unique_words = []
        
        # 对每个长度组进行去重
        for length, group_words in length_groups.items():
            if keep_longest:
                # 保留最长的，先去除完全重复的
                unique_group = list(set(group_words))
                unique_words.extend(unique_group)
            else:
                # 保留最短的，只保留一个
                unique_words.append(group_words[0])
        
        removed_count = len(words) - len(unique_words)
        logging.info(f"长度去重完成 (保留{'最长' if keep_longest else '最短'}): 移除 {removed_count} 个词条")
        
        return unique_words
    
    def pattern_duplicate(self, words: List[str], pattern: str = None) -> List[str]:
        """
        模式去重 - 基于正则表达式模式
        
        Args:
            words: 词条列表
            pattern: 正则表达式模式，用于提取关键部分进行比较
            
        Returns:
            List[str]: 去重后的词条列表
        """
        if pattern is None:
            # 默认模式：提取字母数字部分
            pattern = r'[a-zA-Z0-9]+'
        
        try:
            regex = re.compile(pattern)
            seen_patterns = set()
            unique_words = []
            
            for word in words:
                # 提取匹配模式的部分
                matches = regex.findall(word)
                pattern_key = ''.join(matches).lower()
                
                if pattern_key not in seen_patterns:
                    seen_patterns.add(pattern_key)
                    unique_words.append(word)
            
            removed_count = len(words) - len(unique_words)
            logging.info(f"模式去重完成 (模式: {pattern}): 移除 {removed_count} 个词条")
            
            return unique_words
            
        except re.error as e:
            logging.error(f"正则表达式错误: {e}")
            return self.exact_duplicate(words)
    
    def custom_duplicate(self, words: List[str], custom_func: Callable[[str, str], bool]) -> List[str]:
        """
        自定义去重函数
        
        Args:
            words: 词条列表
            custom_func: 自定义比较函数，返回True表示重复
            
        Returns:
            List[str]: 去重后的词条列表
        """
        unique_words = []
        
        for word in words:
            is_duplicate = False
            
            for existing_word in unique_words:
                if custom_func(word, existing_word):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_words.append(word)
        
        removed_count = len(words) - len(unique_words)
        logging.info(f"自定义去重完成: 移除 {removed_count} 个词条")
        
        return unique_words
    
    def get_duplicate_groups(self, words: List[str], strategy: str = 'exact') -> Dict[str, List[str]]:
        """
        获取重复词条分组
        
        Args:
            words: 词条列表
            strategy: 去重策略
            
        Returns:
            Dict[str, List[str]]: 重复分组，键为代表词条，值为重复词条列表
        """
        duplicate_groups = defaultdict(list)
        
        if strategy == 'exact':
            word_counts = Counter(words)
            for word, count in word_counts.items():
                if count > 1:
                    duplicate_groups[word] = [word] * count
                    
        elif strategy == 'case_insensitive':
            case_groups = defaultdict(list)
            for word in words:
                case_groups[word.lower()].append(word)
            
            for key, group in case_groups.items():
                if len(group) > 1:
                    duplicate_groups[group[0]] = group
                    
        elif strategy == 'similarity':
            processed = set()
            for i, word1 in enumerate(words):
                if word1 in processed:
                    continue
                    
                similar_group = [word1]
                processed.add(word1)
                
                for j, word2 in enumerate(words[i+1:], i+1):
                    if word2 in processed:
                        continue
                        
                    if self._calculate_similarity(word1, word2) >= SIMILARITY_THRESHOLD:
                        similar_group.append(word2)
                        processed.add(word2)
                
                if len(similar_group) > 1:
                    duplicate_groups[word1] = similar_group
        
        return dict(duplicate_groups)
    
    def remove_duplicates_from_dictionary(self, dictionary_id: int, strategy: str = None) -> int:
        """
        从数据库中的字典移除重复词条
        
        Args:
            dictionary_id: 字典ID
            strategy: 去重策略
            
        Returns:
            int: 移除的词条数量
        """
        if strategy is None:
            strategy = DEFAULT_DEDUP_STRATEGY
        
        try:
            # 获取字典中的所有词条
            words_data = self.db.fetch_all(
                "SELECT id, word FROM words WHERE dictionary_id = ?",
                (dictionary_id,)
            )
            
            if not words_data:
                return 0
            
            # 提取词条文本
            words = [row['word'] for row in words_data]
            word_id_map = {row['word']: row['id'] for row in words_data}
            
            # 执行去重
            if strategy in self.strategies:
                unique_words = self.strategies[strategy](words)
            else:
                logging.warning(f"未知的去重策略: {strategy}，使用精确去重")
                unique_words = self.exact_duplicate(words)
            
            # 找出要删除的词条ID
            unique_word_set = set(unique_words)
            words_to_delete = []
            
            for word in words:
                if word not in unique_word_set:
                    words_to_delete.append(word_id_map[word])
                else:
                    # 从集合中移除，避免重复保留
                    unique_word_set.discard(word)
            
            # 删除重复词条
            if words_to_delete:
                placeholders = ','.join(['?'] * len(words_to_delete))
                query = f"DELETE FROM words WHERE id IN ({placeholders})"
                cursor = self.db.execute_query(query, words_to_delete)
                deleted_count = cursor.rowcount
                
                # 更新字典的更新时间
                from datetime import datetime
                self.db.execute_query(
                    "UPDATE dictionaries SET updated_at = ? WHERE id = ?",
                    (datetime.now(), dictionary_id)
                )
                
                logging.info(f"从字典 {dictionary_id} 中移除 {deleted_count} 个重复词条")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logging.error(f"数据库去重失败: {e}")
            return 0
    
    def analyze_duplicates(self, words: List[str]) -> Dict[str, Any]:
        """
        分析重复情况
        
        Args:
            words: 词条列表
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        analysis = {
            'total_words': len(words),
            'unique_exact': len(set(words)),
            'unique_case_insensitive': len(set(word.lower() for word in words)),
            'strategies': {}
        }
        
        # 分析各种策略的去重效果
        for strategy_name, strategy_func in self.strategies.items():
            try:
                if strategy_name == 'similarity':
                    unique_words = strategy_func(words.copy(), SIMILARITY_THRESHOLD)
                elif strategy_name in ['length', 'pattern']:
                    unique_words = strategy_func(words.copy())
                else:
                    unique_words = strategy_func(words.copy())
                
                analysis['strategies'][strategy_name] = {
                    'unique_count': len(unique_words),
                    'removed_count': len(words) - len(unique_words),
                    'removal_rate': (len(words) - len(unique_words)) / len(words) * 100
                }
            except Exception as e:
                logging.error(f"分析策略 {strategy_name} 失败: {e}")
                analysis['strategies'][strategy_name] = {
                    'unique_count': 0,
                    'removed_count': 0,
                    'removal_rate': 0,
                    'error': str(e)
                }
        
        return analysis
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        计算两个字符串的相似度
        
        Args:
            str1: 字符串1
            str2: 字符串2
            
        Returns:
            float: 相似度 (0-1)
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def get_similarity_matrix(self, words: List[str], threshold: float = 0.8) -> List[Tuple[str, str, float]]:
        """
        获取词条相似度矩阵
        
        Args:
            words: 词条列表
            threshold: 相似度阈值
            
        Returns:
            List[Tuple[str, str, float]]: 相似词条对列表 (词条1, 词条2, 相似度)
        """
        similar_pairs = []
        
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                similarity = self._calculate_similarity(words[i], words[j])
                if similarity >= threshold:
                    similar_pairs.append((words[i], words[j], similarity))
        
        # 按相似度降序排序
        similar_pairs.sort(key=lambda x: x[2], reverse=True)
        
        return similar_pairs
    
    def suggest_dedup_strategy(self, words: List[str]) -> str:
        """
        建议最佳去重策略
        
        Args:
            words: 词条列表
            
        Returns:
            str: 建议的策略名称
        """
        analysis = self.analyze_duplicates(words)
        
        # 如果精确重复很多，建议精确去重
        exact_removal_rate = analysis['strategies']['exact']['removal_rate']
        if exact_removal_rate > 20:
            return 'exact'
        
        # 如果大小写重复较多，建议忽略大小写去重
        case_removal_rate = analysis['strategies']['case_insensitive']['removal_rate']
        if case_removal_rate > 10:
            return 'case_insensitive'
        
        # 如果相似度重复较多，建议相似度去重
        similarity_removal_rate = analysis['strategies']['similarity']['removal_rate']
        if similarity_removal_rate > 5:
            return 'similarity'
        
        # 默认建议精确去重
        return 'exact'


# 全局去重器实例
deduplicator = Deduplicator()


if __name__ == "__main__":
    # 测试去重功能
    logging.basicConfig(level=logging.INFO)
    
    # 测试数据
    test_words = [
        "test", "Test", "TEST", "test1", "test2",
        "example", "Example", "sample", "Sample",
        "duplicate", "duplicate", "unique"
    ]
    
    print(f"原始词条数量: {len(test_words)}")
    print(f"原始词条: {test_words}")
    
    # 测试各种去重策略
    for strategy_name, strategy_func in deduplicator.strategies.items():
        try:
            if strategy_name == 'similarity':
                result = strategy_func(test_words.copy(), 0.8)
            else:
                result = strategy_func(test_words.copy())
            
            print(f"\n{strategy_name} 去重结果:")
            print(f"  去重后数量: {len(result)}")
            print(f"  去重后词条: {result}")
        except Exception as e:
            print(f"\n{strategy_name} 去重失败: {e}")
    
    # 测试重复分析
    analysis = deduplicator.analyze_duplicates(test_words)
    print(f"\n重复分析结果:")
    for key, value in analysis.items():
        print(f"  {key}: {value}")
    
    # 测试相似度矩阵
    similar_pairs = deduplicator.get_similarity_matrix(test_words, 0.6)
    print(f"\n相似词条对 (阈值 0.6):")
    for pair in similar_pairs[:5]:  # 只显示前5个
        print(f"  {pair[0]} <-> {pair[1]} (相似度: {pair[2]:.2f})")