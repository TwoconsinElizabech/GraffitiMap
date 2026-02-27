"""
字典管理模块
负责字典的创建、删除、修改和查询操作
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .database import db_manager


class DictionaryManager:
    """字典管理器"""
    
    def __init__(self):
        """初始化字典管理器"""
        self.db = db_manager
    
    def create_dictionary(self, name: str, description: str = "") -> int:
        """
        创建新字典
        
        Args:
            name: 字典名称
            description: 字典描述
            
        Returns:
            int: 新创建字典的ID
            
        Raises:
            ValueError: 字典名称已存在
            Exception: 数据库操作失败
        """
        try:
            # 检查字典名称是否已存在
            existing = self.db.fetch_one(
                "SELECT id FROM dictionaries WHERE name = ?", (name,)
            )
            if existing:
                raise ValueError(f"字典名称 '{name}' 已存在")
            
            # 创建新字典
            cursor = self.db.execute_query(
                """INSERT INTO dictionaries (name, description, created_at, updated_at) 
                   VALUES (?, ?, ?, ?)""",
                (name, description, datetime.now(), datetime.now())
            )
            
            dictionary_id = cursor.lastrowid
            logging.info(f"创建字典成功: {name} (ID: {dictionary_id})")
            return dictionary_id
            
        except Exception as e:
            logging.error(f"创建字典失败: {e}")
            raise
    
    def delete_dictionary(self, dictionary_id: int) -> bool:
        """
        删除字典
        
        Args:
            dictionary_id: 字典ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 检查字典是否存在
            dictionary = self.get_dictionary_by_id(dictionary_id)
            if not dictionary:
                logging.warning(f"字典不存在: ID {dictionary_id}")
                return False
            
            # 删除字典（级联删除相关词条和标签关联）
            cursor = self.db.execute_query(
                "DELETE FROM dictionaries WHERE id = ?", (dictionary_id,)
            )
            
            success = cursor.rowcount > 0
            if success:
                logging.info(f"删除字典成功: {dictionary['name']} (ID: {dictionary_id})")
            
            return success
            
        except Exception as e:
            logging.error(f"删除字典失败: {e}")
            return False
    
    def rename_dictionary(self, dictionary_id: int, new_name: str) -> bool:
        """
        重命名字典
        
        Args:
            dictionary_id: 字典ID
            new_name: 新名称
            
        Returns:
            bool: 重命名是否成功
        """
        try:
            # 检查新名称是否已存在
            existing = self.db.fetch_one(
                "SELECT id FROM dictionaries WHERE name = ? AND id != ?", 
                (new_name, dictionary_id)
            )
            if existing:
                raise ValueError(f"字典名称 '{new_name}' 已存在")
            
            # 更新字典名称
            cursor = self.db.execute_query(
                "UPDATE dictionaries SET name = ?, updated_at = ? WHERE id = ?",
                (new_name, datetime.now(), dictionary_id)
            )
            
            success = cursor.rowcount > 0
            if success:
                logging.info(f"重命名字典成功: ID {dictionary_id} -> {new_name}")
            
            return success
            
        except Exception as e:
            logging.error(f"重命名字典失败: {e}")
            return False
    
    def update_dictionary_description(self, dictionary_id: int, description: str) -> bool:
        """
        更新字典描述
        
        Args:
            dictionary_id: 字典ID
            description: 新描述
            
        Returns:
            bool: 更新是否成功
        """
        try:
            cursor = self.db.execute_query(
                "UPDATE dictionaries SET description = ?, updated_at = ? WHERE id = ?",
                (description, datetime.now(), dictionary_id)
            )
            
            success = cursor.rowcount > 0
            if success:
                logging.info(f"更新字典描述成功: ID {dictionary_id}")
            
            return success
            
        except Exception as e:
            logging.error(f"更新字典描述失败: {e}")
            return False
    
    def get_all_dictionaries(self) -> List[Dict[str, Any]]:
        """
        获取所有字典
        
        Returns:
            List[Dict[str, Any]]: 字典列表
        """
        try:
            rows = self.db.fetch_all(
                """SELECT d.*, 
                          COUNT(w.id) as word_count
                   FROM dictionaries d
                   LEFT JOIN words w ON d.id = w.dictionary_id
                   GROUP BY d.id
                   ORDER BY d.created_at DESC"""
            )
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logging.error(f"获取字典列表失败: {e}")
            return []
    
    def get_dictionary_by_id(self, dictionary_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取字典
        
        Args:
            dictionary_id: 字典ID
            
        Returns:
            Optional[Dict[str, Any]]: 字典信息，如果不存在则返回None
        """
        try:
            row = self.db.fetch_one(
                """SELECT d.*, 
                          COUNT(w.id) as word_count
                   FROM dictionaries d
                   LEFT JOIN words w ON d.id = w.dictionary_id
                   WHERE d.id = ?
                   GROUP BY d.id""",
                (dictionary_id,)
            )
            
            return dict(row) if row else None
            
        except Exception as e:
            logging.error(f"获取字典失败: {e}")
            return None
    
    def get_dictionary_stats(self, dictionary_id: int) -> Dict[str, Any]:
        """
        获取字典统计信息
        
        Args:
            dictionary_id: 字典ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            stats = {}
            
            # 基本信息
            dictionary = self.get_dictionary_by_id(dictionary_id)
            if not dictionary:
                return {}
            
            stats.update(dictionary)
            
            # 词条统计
            word_stats = self.db.fetch_one(
                """SELECT COUNT(*) as total_words,
                          COUNT(DISTINCT w.word) as unique_words
                   FROM words w
                   WHERE w.dictionary_id = ?""",
                (dictionary_id,)
            )
            
            if word_stats:
                stats['total_words'] = word_stats['total_words']
                stats['unique_words'] = word_stats['unique_words']
                stats['duplicate_words'] = word_stats['total_words'] - word_stats['unique_words']
            
            # 标签统计
            tag_stats = self.db.fetch_one(
                """SELECT COUNT(DISTINCT wt.tag_id) as tagged_count
                   FROM words w
                   LEFT JOIN word_tags wt ON w.id = wt.word_id
                   WHERE w.dictionary_id = ?""",
                (dictionary_id,)
            )
            
            if tag_stats:
                stats['tagged_words'] = tag_stats['tagged_count'] or 0
            
            return stats
            
        except Exception as e:
            logging.error(f"获取字典统计信息失败: {e}")
            return {}
    
    def add_words(self, dictionary_id: int, words: List[str]) -> int:
        """
        向字典添加词条
        
        Args:
            dictionary_id: 字典ID
            words: 词条列表
            
        Returns:
            int: 成功添加的词条数量
        """
        try:
            # 检查字典是否存在
            if not self.get_dictionary_by_id(dictionary_id):
                raise ValueError(f"字典不存在: ID {dictionary_id}")
            
            # 准备插入数据
            current_time = datetime.now()
            word_data = [(word.strip(), dictionary_id, current_time) for word in words if word.strip()]
            
            if not word_data:
                return 0
            
            # 批量插入词条
            added_count = self.db.execute_many(
                "INSERT INTO words (word, dictionary_id, created_at) VALUES (?, ?, ?)",
                word_data
            )
            
            # 更新字典的更新时间
            self.db.execute_query(
                "UPDATE dictionaries SET updated_at = ? WHERE id = ?",
                (current_time, dictionary_id)
            )
            
            logging.info(f"添加词条成功: {added_count} 个词条添加到字典 {dictionary_id}")
            return added_count
            
        except Exception as e:
            logging.error(f"添加词条失败: {e}")
            return 0
    
    def remove_words(self, dictionary_id: int, word_ids: List[int]) -> int:
        """
        从字典删除词条
        
        Args:
            dictionary_id: 字典ID
            word_ids: 要删除的词条ID列表
            
        Returns:
            int: 成功删除的词条数量
        """
        try:
            if not word_ids:
                return 0
            
            # 构建删除查询
            placeholders = ','.join(['?'] * len(word_ids))
            query = f"""DELETE FROM words 
                       WHERE id IN ({placeholders}) 
                       AND dictionary_id = ?"""
            
            params = word_ids + [dictionary_id]
            cursor = self.db.execute_query(query, params)
            
            deleted_count = cursor.rowcount
            
            # 更新字典的更新时间
            if deleted_count > 0:
                self.db.execute_query(
                    "UPDATE dictionaries SET updated_at = ? WHERE id = ?",
                    (datetime.now(), dictionary_id)
                )
            
            logging.info(f"删除词条成功: {deleted_count} 个词条从字典 {dictionary_id} 删除")
            return deleted_count
            
        except Exception as e:
            logging.error(f"删除词条失败: {e}")
            return 0
    
    def search_words(self, dictionary_id: int, keyword: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        在字典中搜索词条
        
        Args:
            dictionary_id: 字典ID
            keyword: 搜索关键词
            limit: 结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        try:
            if not keyword.strip():
                return self.get_words(dictionary_id, limit=limit)
            
            rows = self.db.fetch_all(
                """SELECT w.*, 
                          GROUP_CONCAT(t.name) as tag_names
                   FROM words w
                   LEFT JOIN word_tags wt ON w.id = wt.word_id
                   LEFT JOIN tags t ON wt.tag_id = t.id
                   WHERE w.dictionary_id = ? AND w.word LIKE ?
                   GROUP BY w.id
                   ORDER BY w.word
                   LIMIT ?""",
                (dictionary_id, f"%{keyword}%", limit)
            )
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logging.error(f"搜索词条失败: {e}")
            return []
    
    def get_words(self, dictionary_id: int, offset: int = 0, limit: int = None) -> List[Dict[str, Any]]:
        """
        获取字典中的词条
        
        Args:
            dictionary_id: 字典ID
            offset: 偏移量
            limit: 数量限制，None表示获取所有数据
            
        Returns:
            List[Dict[str, Any]]: 词条列表
        """
        try:
            if limit is None:
                # 获取所有数据
                rows = self.db.fetch_all(
                    """SELECT w.*,
                              GROUP_CONCAT(t.name) as tag_names
                       FROM words w
                       LEFT JOIN word_tags wt ON w.id = wt.word_id
                       LEFT JOIN tags t ON wt.tag_id = t.id
                       WHERE w.dictionary_id = ?
                       GROUP BY w.id
                       ORDER BY w.id DESC""",
                    (dictionary_id,)
                )
            else:
                # 限制数量
                rows = self.db.fetch_all(
                    """SELECT w.*,
                              GROUP_CONCAT(t.name) as tag_names
                       FROM words w
                       LEFT JOIN word_tags wt ON w.id = wt.word_id
                       LEFT JOIN tags t ON wt.tag_id = t.id
                       WHERE w.dictionary_id = ?
                       GROUP BY w.id
                       ORDER BY w.id DESC
                       LIMIT ? OFFSET ?""",
                    (dictionary_id, limit, offset)
                )
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logging.error(f"获取词条失败: {e}")
            return []
    
    def get_words_by_tag(self, dictionary_id: int, tag_id: int) -> List[Dict[str, Any]]:
        """
        根据标签获取词条
        
        Args:
            dictionary_id: 字典ID
            tag_id: 标签ID
            
        Returns:
            List[Dict[str, Any]]: 词条列表
        """
        try:
            rows = self.db.fetch_all(
                """SELECT w.*, t.name as tag_name
                   FROM words w
                   JOIN word_tags wt ON w.id = wt.word_id
                   JOIN tags t ON wt.tag_id = t.id
                   WHERE w.dictionary_id = ? AND t.id = ?
                   ORDER BY w.word""",
                (dictionary_id, tag_id)
            )
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logging.error(f"根据标签获取词条失败: {e}")
            return []
    
    def copy_words_to_dictionary(self, source_dict_id: int, target_dict_id: int, word_ids: List[int] = None) -> int:
        """
        复制词条到另一个字典
        
        Args:
            source_dict_id: 源字典ID
            target_dict_id: 目标字典ID
            word_ids: 要复制的词条ID列表，如果为None则复制所有词条
            
        Returns:
            int: 成功复制的词条数量
        """
        try:
            # 检查字典是否存在
            if not self.get_dictionary_by_id(source_dict_id):
                raise ValueError(f"源字典不存在: ID {source_dict_id}")
            if not self.get_dictionary_by_id(target_dict_id):
                raise ValueError(f"目标字典不存在: ID {target_dict_id}")
            
            # 构建查询条件
            if word_ids:
                placeholders = ','.join(['?'] * len(word_ids))
                where_clause = f"AND w.id IN ({placeholders})"
                params = [source_dict_id] + word_ids
            else:
                where_clause = ""
                params = [source_dict_id]
            
            # 获取要复制的词条
            query = f"""SELECT w.word FROM words w 
                       WHERE w.dictionary_id = ? {where_clause}"""
            
            rows = self.db.fetch_all(query, params)
            words = [row['word'] for row in rows]
            
            if not words:
                return 0
            
            # 添加到目标字典
            copied_count = self.add_words(target_dict_id, words)
            
            logging.info(f"复制词条成功: {copied_count} 个词条从字典 {source_dict_id} 复制到字典 {target_dict_id}")
            return copied_count
            
        except Exception as e:
            logging.error(f"复制词条失败: {e}")
            return 0
    
    def get_dictionary_word_count(self, dictionary_id: int) -> int:
        """
        获取字典的词条数量
        
        Args:
            dictionary_id: 字典ID
            
        Returns:
            int: 词条数量
        """
        try:
            result = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM words WHERE dictionary_id = ?",
                (dictionary_id,)
            )
            return result['count'] if result else 0
            
        except Exception as e:
            logging.error(f"获取字典词条数量失败: {e}")
            return 0


# 全局字典管理器实例
dictionary_manager = DictionaryManager()


if __name__ == "__main__":
    # 测试字典管理功能
    logging.basicConfig(level=logging.INFO)
    
    # 初始化数据库
    from .database import init_database
    init_database()
    
    # 测试创建字典
    dict_id = dictionary_manager.create_dictionary("测试字典", "这是一个测试字典")
    print(f"创建字典ID: {dict_id}")
    
    # 测试添加词条
    words = ["test1", "test2", "test3"]
    added = dictionary_manager.add_words(dict_id, words)
    print(f"添加词条数量: {added}")
    
    # 测试获取字典统计
    stats = dictionary_manager.get_dictionary_stats(dict_id)
    print(f"字典统计: {stats}")
    
    # 测试搜索词条
    results = dictionary_manager.search_words(dict_id, "test")
    print(f"搜索结果: {len(results)} 个词条")