"""
字典导出功能模块
提供字典数据的导出功能，支持多种格式和过滤条件
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .database import db_manager
from .dictionary_manager import dictionary_manager
from .file_handler import file_handler
from config.settings import DEFAULT_EXPORT_FORMAT, EXPORT_BATCH_SIZE


class DictionaryExporter:
    """字典导出器"""
    
    def __init__(self):
        """初始化导出器"""
        self.db = db_manager
        self.dict_manager = dictionary_manager
        self.file_handler = file_handler
        self.supported_formats = ['txt', 'json', 'csv', 'xlsx']
    
    def export_dictionary(self, dictionary_id: int, file_path: str, format: str = None, 
                         include_tags: bool = True, encoding: str = 'utf-8') -> bool:
        """
        导出完整字典
        
        Args:
            dictionary_id: 字典ID
            file_path: 导出文件路径
            format: 导出格式，如果为None则根据文件扩展名判断
            include_tags: 是否包含标签信息
            encoding: 文件编码
            
        Returns:
            bool: 导出是否成功
        """
        try:
            # 检查字典是否存在
            dictionary = self.dict_manager.get_dictionary_by_id(dictionary_id)
            if not dictionary:
                raise ValueError(f"字典不存在: ID {dictionary_id}")
            
            # 确定导出格式
            if format is None:
                format = self._detect_format_from_path(file_path)
            
            if format not in self.supported_formats:
                raise ValueError(f"不支持的导出格式: {format}")
            
            # 获取词条数据
            words_data = self._get_dictionary_words(dictionary_id, include_tags)
            
            if not words_data:
                logging.warning(f"字典 {dictionary_id} 中没有词条")
                return False
            
            # 执行导出
            success = self._export_by_format(words_data, file_path, format, encoding, dictionary)
            
            if success:
                logging.info(f"字典导出成功: {dictionary['name']} -> {file_path} ({len(words_data)} 个词条)")
            
            return success
            
        except Exception as e:
            logging.error(f"字典导出失败: {e}")
            return False
    
    def export_filtered_words(self, dictionary_id: int, filters: Dict[str, Any], 
                            file_path: str, format: str = None, encoding: str = 'utf-8') -> bool:
        """
        导出过滤后的词条
        
        Args:
            dictionary_id: 字典ID
            filters: 过滤条件
            file_path: 导出文件路径
            format: 导出格式
            encoding: 文件编码
            
        Returns:
            bool: 导出是否成功
        """
        try:
            # 检查字典是否存在
            dictionary = self.dict_manager.get_dictionary_by_id(dictionary_id)
            if not dictionary:
                raise ValueError(f"字典不存在: ID {dictionary_id}")
            
            # 确定导出格式
            if format is None:
                format = self._detect_format_from_path(file_path)
            
            # 获取过滤后的词条数据
            words_data = self._get_filtered_words(dictionary_id, filters)
            
            if not words_data:
                logging.warning("没有符合过滤条件的词条")
                return False
            
            # 执行导出
            success = self._export_by_format(words_data, file_path, format, encoding, dictionary)
            
            if success:
                logging.info(f"过滤词条导出成功: {len(words_data)} 个词条 -> {file_path}")
            
            return success
            
        except Exception as e:
            logging.error(f"过滤词条导出失败: {e}")
            return False
    
    
    def export_analysis_result(self, analysis_result: Dict[str, Any], 
                             file_path: str, format: str = None) -> bool:
        """
        导出分析结果
        
        Args:
            analysis_result: 分析结果
            file_path: 导出文件路径
            format: 导出格式
            
        Returns:
            bool: 导出是否成功
        """
        try:
            # 确定导出格式
            if format is None:
                format = self._detect_format_from_path(file_path)
            
            # 准备导出数据
            export_data = self._prepare_analysis_export_data(analysis_result)
            
            # 执行导出
            if format == 'json':
                import json
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(analysis_result, file, ensure_ascii=False, indent=2)
                success = True
            elif format in ['csv', 'xlsx']:
                success = self._export_by_format(export_data, file_path, format, 'utf-8')
            else:
                # TXT格式
                success = self._export_analysis_txt(analysis_result, file_path)
            
            if success:
                logging.info(f"分析结果导出成功: {file_path}")
            
            return success
            
        except Exception as e:
            logging.error(f"分析结果导出失败: {e}")
            return False
    
    def batch_export_dictionaries(self, dictionary_ids: List[int], 
                                 output_dir: str, format: str = None) -> Dict[int, bool]:
        """
        批量导出字典
        
        Args:
            dictionary_ids: 字典ID列表
            output_dir: 输出目录
            format: 导出格式
            
        Returns:
            Dict[int, bool]: 字典ID到导出结果的映射
        """
        results = {}
        
        if format is None:
            format = DEFAULT_EXPORT_FORMAT
        
        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for dictionary_id in dictionary_ids:
            try:
                # 获取字典信息
                dictionary = self.dict_manager.get_dictionary_by_id(dictionary_id)
                if not dictionary:
                    results[dictionary_id] = False
                    continue
                
                # 构建输出文件路径
                safe_name = self._make_safe_filename(dictionary['name'])
                file_path = Path(output_dir) / f"{safe_name}.{format}"
                
                # 导出字典
                success = self.export_dictionary(dictionary_id, str(file_path), format)
                results[dictionary_id] = success
                
                if success:
                    logging.info(f"批量导出成功: {dictionary['name']}")
                else:
                    logging.error(f"批量导出失败: {dictionary['name']}")
                    
            except Exception as e:
                logging.error(f"批量导出字典 {dictionary_id} 失败: {e}")
                results[dictionary_id] = False
        
        return results
    
    def create_backup(self, backup_path: str, include_data: bool = True) -> bool:
        """
        创建完整备份
        
        Args:
            backup_path: 备份文件路径
            include_data: 是否包含数据文件
            
        Returns:
            bool: 备份是否成功
        """
        try:
            import zipfile
            import json
            from datetime import datetime
            
            # 确保备份目录存在
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 备份数据库
                if include_data:
                    db_backup_success = self.db.backup_database("temp_backup.db")
                    if db_backup_success and Path("temp_backup.db").exists():
                        zipf.write("temp_backup.db", "database.db")
                        Path("temp_backup.db").unlink()  # 删除临时文件
                
                # 备份配置文件
                config_files = [
                    "config/settings.py",
                    "config/regex_patterns.json"
                ]
                
                for config_file in config_files:
                    if Path(config_file).exists():
                        zipf.write(config_file, config_file)
                
                # 创建备份信息文件
                backup_info = {
                    "backup_time": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "include_data": include_data,
                    "dictionaries": []
                }
                
                # 获取字典信息
                dictionaries = self.dict_manager.get_all_dictionaries()
                for dictionary in dictionaries:
                    backup_info["dictionaries"].append({
                        "id": dictionary["id"],
                        "name": dictionary["name"],
                        "description": dictionary.get("description", ""),
                        "word_count": dictionary.get("word_count", 0)
                    })
                
                # 添加备份信息到压缩包
                zipf.writestr("backup_info.json", json.dumps(backup_info, ensure_ascii=False, indent=2))
            
            logging.info(f"备份创建成功: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"创建备份失败: {e}")
            return False
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        从备份恢复
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            import zipfile
            import json
            
            if not Path(backup_path).exists():
                raise FileNotFoundError(f"备份文件不存在: {backup_path}")
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # 检查备份信息
                if "backup_info.json" in zipf.namelist():
                    backup_info_data = zipf.read("backup_info.json")
                    backup_info = json.loads(backup_info_data.decode('utf-8'))
                    logging.info(f"备份信息: {backup_info}")
                
                # 恢复数据库
                if "database.db" in zipf.namelist():
                    zipf.extract("database.db", "temp_restore/")
                    db_restore_success = self.db.restore_database("temp_restore/database.db")
                    
                    if db_restore_success:
                        logging.info("数据库恢复成功")
                    else:
                        logging.error("数据库恢复失败")
                        return False
                    
                    # 清理临时文件
                    import shutil
                    if Path("temp_restore").exists():
                        shutil.rmtree("temp_restore")
                
                # 恢复配置文件
                config_files = ["config/settings.py", "config/regex_patterns.json"]
                for config_file in config_files:
                    if config_file in zipf.namelist():
                        zipf.extract(config_file, ".")
                        logging.info(f"配置文件恢复: {config_file}")
            
            logging.info(f"备份恢复成功: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"备份恢复失败: {e}")
            return False
    
    def _get_dictionary_words(self, dictionary_id: int, include_tags: bool = True) -> List[Dict[str, Any]]:
        """获取字典中的词条数据"""
        try:
            query = """
                SELECT w.id, w.word, w.created_at
                FROM words w
                WHERE w.dictionary_id = ?
                ORDER BY w.word
            """
            
            rows = self.db.fetch_all(query, (dictionary_id,))
            return [dict(row) for row in rows]
            
        except Exception as e:
            logging.error(f"获取字典词条失败: {e}")
            return []
    
    def _get_filtered_words(self, dictionary_id: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取过滤后的词条"""
        try:
            base_query = """
                SELECT w.id, w.word, w.created_at
                FROM words w
                WHERE w.dictionary_id = ?
            """
            
            params = [dictionary_id]
            conditions = []
            
            # 关键词过滤
            if 'keyword' in filters and filters['keyword']:
                conditions.append("w.word LIKE ?")
                params.append(f"%{filters['keyword']}%")
            
            # 长度过滤
            if 'min_length' in filters:
                conditions.append("LENGTH(w.word) >= ?")
                params.append(filters['min_length'])
            
            if 'max_length' in filters:
                conditions.append("LENGTH(w.word) <= ?")
                params.append(filters['max_length'])
            
            # 添加条件到查询
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            base_query += " ORDER BY w.word"
            
            # 限制结果数量
            if 'limit' in filters:
                base_query += " LIMIT ?"
                params.append(filters['limit'])
            
            rows = self.db.fetch_all(base_query, params)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logging.error(f"获取过滤词条失败: {e}")
            return []
    
    def _export_by_format(self, words_data: List[Dict[str, Any]], file_path: str, 
                         format: str, encoding: str = 'utf-8', 
                         dictionary: Dict[str, Any] = None) -> bool:
        """根据格式导出数据"""
        try:
            if format == 'txt':
                words = [word_data['word'] for word_data in words_data]
                return self.file_handler.export_txt(words, file_path, encoding)
            
            elif format == 'json':
                # 构建JSON数据结构
                export_data = {
                    "dictionary_info": dictionary or {},
                    "export_time": datetime.now().isoformat(),
                    "total_words": len(words_data),
                    "words": words_data
                }
                return self.file_handler.export_json([export_data], file_path, encoding)
            
            elif format == 'csv':
                return self.file_handler.export_csv(words_data, file_path, encoding)
            
            elif format == 'xlsx':
                return self.file_handler.export_excel(words_data, file_path)
            
            else:
                logging.error(f"不支持的导出格式: {format}")
                return False
                
        except Exception as e:
            logging.error(f"格式化导出失败: {e}")
            return False
    
    def _detect_format_from_path(self, file_path: str) -> str:
        """从文件路径检测格式"""
        suffix = Path(file_path).suffix.lower()
        
        format_map = {
            '.txt': 'txt',
            '.json': 'json',
            '.csv': 'csv',
            '.xlsx': 'xlsx',
            '.xls': 'xlsx'
        }
        
        return format_map.get(suffix, DEFAULT_EXPORT_FORMAT)
    
    def _make_safe_filename(self, name: str) -> str:
        """创建安全的文件名"""
        import re
        # 移除或替换不安全的字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        safe_name = safe_name.strip()
        
        # 限制长度
        if len(safe_name) > 100:
            safe_name = safe_name[:100]
        
        return safe_name or "unnamed"
    
    def _prepare_analysis_export_data(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """准备分析结果的导出数据"""
        export_data = []
        
        # 导出匹配的词条
        for word, patterns in analysis_result.get('matched_words_detail', {}).items():
            export_data.append({
                'word': word,
                'matched_patterns': ', '.join(patterns),
                'status': 'matched'
            })
        
        # 导出未匹配的词条
        for word in analysis_result.get('unmatched_words', []):
            export_data.append({
                'word': word,
                'matched_patterns': '',
                'status': 'unmatched'
            })
        
        return export_data
    
    def _export_analysis_txt(self, analysis_result: Dict[str, Any], file_path: str) -> bool:
        """导出分析结果为TXT格式"""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write("=== 字典分析报告 ===\n\n")
                
                # 基本信息
                file.write(f"分析时间: {analysis_result.get('analysis_time', 'N/A')}\n")
                file.write(f"总词条数: {analysis_result.get('total_words', 0)}\n\n")
                
                # 汇总信息
                summary = analysis_result.get('summary', {})
                file.write("=== 分析汇总 ===\n")
                file.write(f"匹配词条数: {summary.get('matched_words', 0)}\n")
                file.write(f"未匹配词条数: {summary.get('unmatched_words', 0)}\n")
                file.write(f"匹配率: {summary.get('match_rate', 0):.2f}%\n\n")
                
                # 匹配词条详情
                file.write("=== 匹配词条 ===\n")
                for word, patterns in analysis_result.get('matched_words_detail', {}).items():
                    file.write(f"{word} -> {', '.join(patterns)}\n")
                
                # 未匹配词条
                unmatched = analysis_result.get('unmatched_words', [])
                if unmatched:
                    file.write(f"\n=== 未匹配词条 ===\n")
                    for word in unmatched:
                        file.write(f"{word}\n")
            
            return True
            
        except Exception as e:
            logging.error(f"TXT格式分析结果导出失败: {e}")
            return False


# 全局导出器实例
exporter = DictionaryExporter()


if __name__ == "__main__":
    # 测试导出功能
    logging.basicConfig(level=logging.INFO)
    
    # 这里需要先有数据库和字典数据才能测试
    print("导出器模块已加载，需要配合实际数据进行测试")