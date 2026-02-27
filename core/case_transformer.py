"""
随机大小写转换模块
提供多种大小写转换策略
"""
import logging
import random
import re
from typing import List, Dict, Any, Optional
from enum import Enum


class CaseStrategy(Enum):
    """大小写转换策略"""
    RANDOM_CHAR = "random_char"  # 完全随机每个字符
    RANDOM_WORD = "random_word"  # 按单词随机
    FIRST_LETTER = "first_letter"  # 首字母随机
    ALTERNATING = "alternating"  # 交替大小写
    CAMEL_CASE = "camel_case"  # 驼峰命名
    PASCAL_CASE = "pascal_case"  # 帕斯卡命名
    SNAKE_CASE_UPPER = "snake_case_upper"  # 蛇形命名大写
    KEBAB_CASE_UPPER = "kebab_case_upper"  # 短横线命名大写


class CaseTransformer:
    """大小写转换器"""
    
    def __init__(self):
        """初始化转换器"""
        self.logger = logging.getLogger(__name__)
        self.word_separators = [' ', '_', '-', '.', '/', '\\', ':', ';', '|']
    
    def split_into_words(self, text: str) -> List[str]:
        """
        将文本分割为单词
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 单词列表
        """
        # 使用正则表达式分割单词
        pattern = r'[' + re.escape(''.join(self.word_separators)) + r']+'
        words = re.split(pattern, text)
        return [word for word in words if word]
    
    def random_char_case(self, text: str, probability: float = 0.5) -> str:
        """
        完全随机每个字符的大小写
        
        Args:
            text: 输入文本
            probability: 大写概率 (0.0-1.0)
            
        Returns:
            str: 转换后的文本
        """
        result = []
        for char in text:
            if char.isalpha():
                if random.random() < probability:
                    result.append(char.upper())
                else:
                    result.append(char.lower())
            else:
                result.append(char)
        return ''.join(result)
    
    def random_word_case(self, text: str, probability: float = 0.5) -> str:
        """
        按单词随机大小写
        
        Args:
            text: 输入文本
            probability: 单词大写概率 (0.0-1.0)
            
        Returns:
            str: 转换后的文本
        """
        result = []
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if char.isalpha():
                # 找到单词的开始和结束
                word_start = i
                while i < len(text) and text[i].isalpha():
                    i += 1
                
                word = text[word_start:i]
                
                # 随机决定单词的大小写
                if random.random() < probability:
                    result.append(word.upper())
                else:
                    result.append(word.lower())
            else:
                result.append(char)
                i += 1
        
        return ''.join(result)
    
    def first_letter_random(self, text: str, probability: float = 0.5) -> str:
        """
        首字母随机大小写，其余保持小写
        
        Args:
            text: 输入文本
            probability: 首字母大写概率 (0.0-1.0)
            
        Returns:
            str: 转换后的文本
        """
        if not text:
            return text
        
        result = []
        first_letter_processed = False
        
        for char in text:
            if char.isalpha() and not first_letter_processed:
                if random.random() < probability:
                    result.append(char.upper())
                else:
                    result.append(char.lower())
                first_letter_processed = True
            elif char.isalpha():
                result.append(char.lower())
            else:
                result.append(char)
        
        return ''.join(result)
    
    def alternating_case(self, text: str, start_upper: bool = True) -> str:
        """
        交替大小写
        
        Args:
            text: 输入文本
            start_upper: 是否从大写开始
            
        Returns:
            str: 转换后的文本
        """
        result = []
        should_upper = start_upper
        
        for char in text:
            if char.isalpha():
                if should_upper:
                    result.append(char.upper())
                else:
                    result.append(char.lower())
                should_upper = not should_upper
            else:
                result.append(char)
        
        return ''.join(result)
    
    def camel_case(self, text: str) -> str:
        """
        转换为驼峰命名 (camelCase)
        
        Args:
            text: 输入文本
            
        Returns:
            str: 转换后的文本
        """
        words = self.split_into_words(text)
        if not words:
            return text
        
        result = [words[0].lower()]
        for word in words[1:]:
            if word:
                result.append(word.capitalize())
        
        return ''.join(result)
    
    def pascal_case(self, text: str) -> str:
        """
        转换为帕斯卡命名 (PascalCase)
        
        Args:
            text: 输入文本
            
        Returns:
            str: 转换后的文本
        """
        words = self.split_into_words(text)
        result = []
        
        for word in words:
            if word:
                result.append(word.capitalize())
        
        return ''.join(result)
    
    def snake_case_upper(self, text: str) -> str:
        """
        转换为蛇形命名大写 (SNAKE_CASE)
        
        Args:
            text: 输入文本
            
        Returns:
            str: 转换后的文本
        """
        words = self.split_into_words(text)
        return '_'.join(word.upper() for word in words if word)
    
    def kebab_case_upper(self, text: str) -> str:
        """
        转换为短横线命名大写 (KEBAB-CASE)
        
        Args:
            text: 输入文本
            
        Returns:
            str: 转换后的文本
        """
        words = self.split_into_words(text)
        return '-'.join(word.upper() for word in words if word)
    
    def transform_text(self, text: str, strategy: CaseStrategy, **kwargs) -> str:
        """
        根据策略转换文本
        
        Args:
            text: 输入文本
            strategy: 转换策略
            **kwargs: 策略参数
            
        Returns:
            str: 转换后的文本
        """
        try:
            if strategy == CaseStrategy.RANDOM_CHAR:
                probability = kwargs.get('probability', 0.5)
                return self.random_char_case(text, probability)
            elif strategy == CaseStrategy.RANDOM_WORD:
                probability = kwargs.get('probability', 0.5)
                return self.random_word_case(text, probability)
            elif strategy == CaseStrategy.FIRST_LETTER:
                probability = kwargs.get('probability', 0.5)
                return self.first_letter_random(text, probability)
            elif strategy == CaseStrategy.ALTERNATING:
                start_upper = kwargs.get('start_upper', True)
                return self.alternating_case(text, start_upper)
            elif strategy == CaseStrategy.CAMEL_CASE:
                return self.camel_case(text)
            elif strategy == CaseStrategy.PASCAL_CASE:
                return self.pascal_case(text)
            elif strategy == CaseStrategy.SNAKE_CASE_UPPER:
                return self.snake_case_upper(text)
            elif strategy == CaseStrategy.KEBAB_CASE_UPPER:
                return self.kebab_case_upper(text)
            else:
                self.logger.warning(f"未知的转换策略: {strategy}")
                return text
                
        except Exception as e:
            self.logger.error(f"文本转换失败: {e}")
            return text
    
    def transform_word_list(self, words: List[str], strategy: CaseStrategy, 
                          keep_original: bool = True, **kwargs) -> List[str]:
        """
        转换词条列表
        
        Args:
            words: 词条列表
            strategy: 转换策略
            keep_original: 是否保留原始词条
            **kwargs: 策略参数
            
        Returns:
            List[str]: 转换后的词条列表
        """
        result = []
        
        if keep_original:
            result.extend(words)
        
        for word in words:
            transformed = self.transform_text(word, strategy, **kwargs)
            if transformed != word:  # 只添加不同的变体
                result.append(transformed)
        
        return list(set(result))  # 去重
    
    def generate_multiple_variants(self, text: str, strategies: List[CaseStrategy], 
                                 strategy_params: Optional[Dict[CaseStrategy, Dict]] = None) -> List[str]:
        """
        使用多种策略生成变体
        
        Args:
            text: 输入文本
            strategies: 策略列表
            strategy_params: 每个策略的参数
            
        Returns:
            List[str]: 变体列表
        """
        if strategy_params is None:
            strategy_params = {}
        
        variants = [text]  # 包含原始文本
        
        for strategy in strategies:
            params = strategy_params.get(strategy, {})
            variant = self.transform_text(text, strategy, **params)
            if variant not in variants:
                variants.append(variant)
        
        return variants
    
    def generate_random_variants(self, text: str, count: int = 5, 
                               strategy: CaseStrategy = CaseStrategy.RANDOM_CHAR) -> List[str]:
        """
        生成指定数量的随机变体
        
        Args:
            text: 输入文本
            count: 变体数量
            strategy: 随机策略
            
        Returns:
            List[str]: 随机变体列表
        """
        variants = set([text])  # 使用集合避免重复
        
        max_attempts = count * 10  # 最大尝试次数，避免无限循环
        attempts = 0
        
        while len(variants) < count + 1 and attempts < max_attempts:
            if strategy == CaseStrategy.RANDOM_CHAR:
                variant = self.random_char_case(text)
            elif strategy == CaseStrategy.RANDOM_WORD:
                variant = self.random_word_case(text)
            elif strategy == CaseStrategy.FIRST_LETTER:
                variant = self.first_letter_random(text)
            else:
                # 对于非随机策略，只生成一次
                variant = self.transform_text(text, strategy)
                variants.add(variant)
                break
            
            variants.add(variant)
            attempts += 1
        
        return list(variants)


# 全局大小写转换器实例
case_transformer = CaseTransformer()


if __name__ == "__main__":
    # 测试大小写转换功能
    logging.basicConfig(level=logging.INFO)
    
    test_words = ["admin", "user_login", "test-panel", "AdminDashboard", "API_KEY"]
    
    print("原始词条:", test_words)
    print()
    
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
        print(f"{description}:")
        for word in test_words[:3]:  # 只测试前3个词条
            if strategy in [CaseStrategy.RANDOM_CHAR, CaseStrategy.RANDOM_WORD, CaseStrategy.FIRST_LETTER]:
                # 随机策略生成多个变体
                variants = case_transformer.generate_random_variants(word, 3, strategy)
                print(f"  {word} -> {variants}")
            else:
                # 确定性策略只生成一个变体
                variant = case_transformer.transform_text(word, strategy)
                print(f"  {word} -> {variant}")
        print()