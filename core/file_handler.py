"""
文件处理模块
负责字典文件的导入和导出功能，支持TXT、JSON、CSV格式
"""
import json
import csv
import logging
import chardet
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from config.settings import SUPPORTED_ENCODINGS, MAX_FILE_SIZE, CHUNK_SIZE


class FileHandler:
    """文件处理器"""
    
    def __init__(self):
        """初始化文件处理器"""
        self.supported_formats = ['.txt', '.json', '.csv', '.xlsx', '.xls']
    
    def detect_encoding(self, file_path: str) -> str:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 检测到的编码格式
        """
        try:
            with open(file_path, 'rb') as file:
                # 读取文件的前几KB来检测编码
                raw_data = file.read(8192)
                result = chardet.detect(raw_data)
                
                detected_encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                
                # 如果置信度太低，使用默认编码
                if confidence < 0.7:
                    for encoding in SUPPORTED_ENCODINGS:
                        try:
                            with open(file_path, 'r', encoding=encoding) as test_file:
                                test_file.read(1024)
                            return encoding
                        except UnicodeDecodeError:
                            continue
                    return 'utf-8'
                
                return detected_encoding
                
        except Exception as e:
            logging.warning(f"编码检测失败，使用默认编码: {e}")
            return 'utf-8'
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        验证文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            path = Path(file_path)
            
            # 检查文件是否存在
            if not path.exists():
                return False, "文件不存在"
            
            # 检查文件大小
            if path.stat().st_size > MAX_FILE_SIZE:
                return False, f"文件过大，超过 {MAX_FILE_SIZE // (1024*1024)}MB 限制"
            
            # 检查文件格式
            if path.suffix.lower() not in self.supported_formats:
                return False, f"不支持的文件格式: {path.suffix}"
            
            return True, ""
            
        except Exception as e:
            return False, f"文件验证失败: {e}"
    
    def import_txt(self, file_path: str) -> List[str]:
        """
        导入TXT文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 词条列表
        """
        try:
            encoding = self.detect_encoding(file_path)
            words = []
            
            with open(file_path, 'r', encoding=encoding) as file:
                for line in file:
                    word = line.strip()
                    if word:  # 跳过空行
                        words.append(word)
            
            logging.info(f"TXT文件导入成功: {len(words)} 个词条")
            return words
            
        except Exception as e:
            logging.error(f"TXT文件导入失败: {e}")
            raise
    
    def import_json(self, file_path: str) -> List[str]:
        """
        导入JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 词条列表
        """
        try:
            encoding = self.detect_encoding(file_path)
            
            with open(file_path, 'r', encoding=encoding) as file:
                data = json.load(file)
            
            words = []
            
            # 处理不同的JSON格式
            if isinstance(data, list):
                # 简单列表格式: ["word1", "word2", ...]
                for item in data:
                    if isinstance(item, str):
                        words.append(item.strip())
                    elif isinstance(item, dict) and 'word' in item:
                        words.append(str(item['word']).strip())
                        
            elif isinstance(data, dict):
                # 字典格式: {"words": [...]} 或 {"dictionary_name": "...", "words": [...]}
                if 'words' in data:
                    word_list = data['words']
                    if isinstance(word_list, list):
                        for item in word_list:
                            if isinstance(item, str):
                                words.append(item.strip())
                            elif isinstance(item, dict) and 'word' in item:
                                words.append(str(item['word']).strip())
                else:
                    # 尝试从所有值中提取词条
                    for value in data.values():
                        if isinstance(value, list):
                            for item in value:
                                if isinstance(item, str):
                                    words.append(item.strip())
            
            # 过滤空词条
            words = [word for word in words if word]
            
            logging.info(f"JSON文件导入成功: {len(words)} 个词条")
            return words
            
        except Exception as e:
            logging.error(f"JSON文件导入失败: {e}")
            raise
    
    def import_csv(self, file_path: str) -> List[str]:
        """
        导入CSV文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 词条列表
        """
        try:
            encoding = self.detect_encoding(file_path)
            words = []
            
            with open(file_path, 'r', encoding=encoding, newline='') as file:
                # 尝试检测CSV分隔符
                sample = file.read(1024)
                file.seek(0)
                
                sniffer = csv.Sniffer()
                try:
                    delimiter = sniffer.sniff(sample).delimiter
                except:
                    delimiter = ','
                
                reader = csv.reader(file, delimiter=delimiter)
                
                # 跳过可能的标题行
                first_row = next(reader, None)
                if first_row:
                    # 如果第一行看起来像标题，跳过它
                    if any(header.lower() in ['word', 'term', 'keyword', '词条', '关键词'] 
                           for header in first_row):
                        pass  # 跳过标题行
                    else:
                        # 第一行是数据，处理它
                        for cell in first_row:
                            word = str(cell).strip()
                            if word:
                                words.append(word)
                
                # 处理剩余行
                for row in reader:
                    for cell in row:
                        word = str(cell).strip()
                        if word:
                            words.append(word)
            
            logging.info(f"CSV文件导入成功: {len(words)} 个词条")
            return words
            
        except Exception as e:
            logging.error(f"CSV文件导入失败: {e}")
            raise
    
    def import_excel(self, file_path: str) -> List[str]:
        """
        导入Excel文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 词条列表
        """
        try:
            # 使用pandas读取Excel文件
            df = pd.read_excel(file_path)
            words = []
            
            # 从所有列中提取数据
            for column in df.columns:
                for value in df[column].dropna():
                    word = str(value).strip()
                    if word:
                        words.append(word)
            
            logging.info(f"Excel文件导入成功: {len(words)} 个词条")
            return words
            
        except Exception as e:
            logging.error(f"Excel文件导入失败: {e}")
            raise
    
    def import_file(self, file_path: str) -> List[str]:
        """
        根据文件类型自动导入文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 词条列表
        """
        # 验证文件
        is_valid, error_msg = self.validate_file(file_path)
        if not is_valid:
            raise ValueError(error_msg)
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.txt':
            return self.import_txt(file_path)
        elif file_ext == '.json':
            return self.import_json(file_path)
        elif file_ext == '.csv':
            return self.import_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            return self.import_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
    
    def export_txt(self, words: List[str], file_path: str, encoding: str = 'utf-8') -> bool:
        """
        导出为TXT文件
        
        Args:
            words: 词条列表
            file_path: 输出文件路径
            encoding: 文件编码
            
        Returns:
            bool: 导出是否成功
        """
        try:
            # 确保输出目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as file:
                for word in words:
                    file.write(f"{word}\n")
            
            logging.info(f"TXT文件导出成功: {len(words)} 个词条 -> {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"TXT文件导出失败: {e}")
            return False
    
    def export_json(self, words: List[Dict[str, Any]], file_path: str, encoding: str = 'utf-8') -> bool:
        """
        导出为JSON文件
        
        Args:
            words: 词条数据列表
            file_path: 输出文件路径
            encoding: 文件编码
            
        Returns:
            bool: 导出是否成功
        """
        try:
            # 确保输出目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 构建JSON数据结构
            export_data = {
                "dictionary_name": Path(file_path).stem,
                "export_time": str(pd.Timestamp.now()),
                "total_words": len(words),
                "words": words
            }
            
            with open(file_path, 'w', encoding=encoding) as file:
                json.dump(export_data, file, ensure_ascii=False, indent=2)
            
            logging.info(f"JSON文件导出成功: {len(words)} 个词条 -> {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"JSON文件导出失败: {e}")
            return False
    
    def export_csv(self, words: List[Dict[str, Any]], file_path: str, encoding: str = 'utf-8') -> bool:
        """
        导出为CSV文件
        
        Args:
            words: 词条数据列表
            file_path: 输出文件路径
            encoding: 文件编码
            
        Returns:
            bool: 导出是否成功
        """
        try:
            # 确保输出目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            if not words:
                return False
            
            # 获取所有可能的字段
            fieldnames = set()
            for word_data in words:
                fieldnames.update(word_data.keys())
            
            fieldnames = sorted(list(fieldnames))
            
            with open(file_path, 'w', encoding=encoding, newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(words)
            
            logging.info(f"CSV文件导出成功: {len(words)} 个词条 -> {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"CSV文件导出失败: {e}")
            return False
    
    def export_excel(self, words: List[Dict[str, Any]], file_path: str) -> bool:
        """
        导出为Excel文件
        
        Args:
            words: 词条数据列表
            file_path: 输出文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            # 确保输出目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            if not words:
                return False
            
            # 使用pandas导出Excel
            df = pd.DataFrame(words)
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            logging.info(f"Excel文件导出成功: {len(words)} 个词条 -> {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Excel文件导出失败: {e}")
            return False
    
    def batch_import(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        批量导入文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            Dict[str, List[str]]: 文件路径到词条列表的映射
        """
        results = {}
        
        for file_path in file_paths:
            try:
                words = self.import_file(file_path)
                results[file_path] = words
                logging.info(f"批量导入成功: {file_path} ({len(words)} 个词条)")
                
            except Exception as e:
                logging.error(f"批量导入失败: {file_path}, 错误: {e}")
                results[file_path] = []
        
        return results
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 文件信息
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {}
            
            stat = path.stat()
            
            info = {
                'name': path.name,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'extension': path.suffix.lower(),
                'created_time': pd.Timestamp.fromtimestamp(stat.st_ctime),
                'modified_time': pd.Timestamp.fromtimestamp(stat.st_mtime),
                'encoding': self.detect_encoding(file_path) if path.suffix.lower() in ['.txt', '.csv', '.json'] else None
            }
            
            return info
            
        except Exception as e:
            logging.error(f"获取文件信息失败: {e}")
            return {}


# 全局文件处理器实例
file_handler = FileHandler()


if __name__ == "__main__":
    # 测试文件处理功能
    logging.basicConfig(level=logging.INFO)
    
    # 测试创建示例文件
    test_words = ["test1", "test2", "test3", "测试词条"]
    
    # 测试TXT导出和导入
    txt_file = "test_export.txt"
    if file_handler.export_txt(test_words, txt_file):
        imported_words = file_handler.import_txt(txt_file)
        print(f"TXT测试: 导出 {len(test_words)} 个词条, 导入 {len(imported_words)} 个词条")
    
    # 测试JSON导出和导入
    json_file = "test_export.json"
    word_data = [{"word": word, "tags": ["test"]} for word in test_words]
    if file_handler.export_json(word_data, json_file):
        # 为了测试导入，我们需要创建一个简单的JSON格式
        simple_json = {"words": test_words}
        with open("test_simple.json", 'w', encoding='utf-8') as f:
            json.dump(simple_json, f, ensure_ascii=False)
        
        imported_words = file_handler.import_json("test_simple.json")
        print(f"JSON测试: 导出 {len(word_data)} 个词条, 导入 {len(imported_words)} 个词条")
    
    # 清理测试文件
    import os
    for test_file in [txt_file, json_file, "test_simple.json"]:
        if os.path.exists(test_file):
            os.remove(test_file)