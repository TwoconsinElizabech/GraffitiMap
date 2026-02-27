#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标签管理模块
提供词条标签的创建、管理和关联功能
"""

import logging
from typing import List, Dict, Optional, Tuple
from .database import DatabaseManager

class TagManager:
    """标签管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化标签管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def create_tag(self, name: str, color: str = "#007bff", description: str = "") -> Optional[int]:
        """
        创建新标签
        
        Args:
            name: 标签名称
            color: 标签颜色 (十六进制格式)
            description: 标签描述
            
        Returns:
            标签ID，失败返回None
        """
        try:
            cursor = self.db_manager.get_cursor()
            
            # 检查标签是否已存在
            cursor.execute("SELECT id FROM tags WHERE name = ?", (name,))
            if cursor.fetchone():
                self.logger.warning(f"标签 '{name}' 已存在")
                return None
            
            # 创建新标签
            cursor.execute("""
                INSERT INTO tags (name, color, description, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (name, color, description))
            
            tag_id = cursor.lastrowid
            self.db_manager.commit()
            
            self.logger.info(f"创建标签成功: {name} (ID: {tag_id})")
            return tag_id
            
        except Exception as e:
            self.logger.error(f"创建标签失败: {e}")
            self.db_manager.rollback()
            return None
    
    def get_tag_by_id(self, tag_id: int) -> Optional[Dict]:
        """
        根据ID获取标签信息
        
        Args:
            tag_id: 标签ID
            
        Returns:
            标签信息字典，不存在返回None
        """
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("""
                SELECT id, name, color, description, created_at
                FROM tags WHERE id = ?
            """, (tag_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'description': row[3],
                    'created_at': row[4]
                }
            return None
            
        except Exception as e:
            self.logger.error(f"获取标签信息失败: {e}")
            return None
    
    def get_tag_by_name(self, name: str) -> Optional[Dict]:
        """
        根据名称获取标签信息
        
        Args:
            name: 标签名称
            
        Returns:
            标签信息字典，不存在返回None
        """
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("""
                SELECT id, name, color, description, created_at
                FROM tags WHERE name = ?
            """, (name,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'description': row[3],
                    'created_at': row[4]
                }
            return None
            
        except Exception as e:
            self.logger.error(f"获取标签信息失败: {e}")
            return None
    
    def get_all_tags(self) -> List[Dict]:
        """
        获取所有标签
        
        Returns:
            标签列表
        """
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("""
                SELECT id, name, color, description, created_at
                FROM tags ORDER BY name
            """)
            
            tags = []
            for row in cursor.fetchall():
                tags.append({
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'description': row[3],
                    'created_at': row[4]
                })
            
            return tags
            
        except Exception as e:
            self.logger.error(f"获取标签列表失败: {e}")
            return []
    
    def update_tag(self, tag_id: int, name: str = None, color: str = None, 
                   description: str = None) -> bool:
        """
        更新标签信息
        
        Args:
            tag_id: 标签ID
            name: 新名称
            color: 新颜色
            description: 新描述
            
        Returns:
            是否成功
        """
        try:
            cursor = self.db_manager.get_cursor()
            
            # 构建更新语句
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if color is not None:
                updates.append("color = ?")
                params.append(color)
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if not updates:
                return True
            
            params.append(tag_id)
            sql = f"UPDATE tags SET {', '.join(updates)} WHERE id = ?"
            
            cursor.execute(sql, params)
            self.db_manager.commit()
            
            self.logger.info(f"更新标签成功: ID {tag_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新标签失败: {e}")
            self.db_manager.rollback()
            return False
    
    def delete_tag(self, tag_id: int) -> bool:
        """
        删除标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            是否成功
        """
        try:
            cursor = self.db_manager.get_cursor()
            
            # 先删除词条-标签关联
            cursor.execute("DELETE FROM word_tags WHERE tag_id = ?", (tag_id,))
            
            # 删除标签
            cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            
            self.db_manager.commit()
            
            self.logger.info(f"删除标签成功: ID {tag_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除标签失败: {e}")
            self.db_manager.rollback()
            return False
    
    def add_tag_to_word(self, word_id: int, tag_id: int) -> bool:
        """
        为词条添加标签
        
        Args:
            word_id: 词条ID
            tag_id: 标签ID
            
        Returns:
            是否成功
        """
        try:
            cursor = self.db_manager.get_cursor()
            
            # 检查关联是否已存在
            cursor.execute("""
                SELECT 1 FROM word_tags WHERE word_id = ? AND tag_id = ?
            """, (word_id, tag_id))
            
            if cursor.fetchone():
                return True  # 已存在，视为成功
            
            # 添加关联
            cursor.execute("""
                INSERT INTO word_tags (word_id, tag_id, created_at)
                VALUES (?, ?, datetime('now'))
            """, (word_id, tag_id))
            
            self.db_manager.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"添加词条标签失败: {e}")
            self.db_manager.rollback()
            return False
    
    def remove_tag_from_word(self, word_id: int, tag_id: int) -> bool:
        """
        从词条移除标签
        
        Args:
            word_id: 词条ID
            tag_id: 标签ID
            
        Returns:
            是否成功
        """
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("""
                DELETE FROM word_tags WHERE word_id = ? AND tag_id = ?
            """, (word_id, tag_id))
            
            self.db_manager.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"移除词条标签失败: {e}")
            self.db_manager.rollback()
            return False
    
    def get_word_tags(self, word_id: int) -> List[Dict]:
        """
        获取词条的所有标签
        
        Args:
            word_id: 词条ID
            
        Returns:
            标签列表
        """
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("""
                SELECT t.id, t.name, t.color, t.description, t.created_at
                FROM tags t
                JOIN word_tags wt ON t.id = wt.tag_id
                WHERE wt.word_id = ?
                ORDER BY t.name
            """, (word_id,))
            
            tags = []
            for row in cursor.fetchall():
                tags.append({
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'description': row[3],
                    'created_at': row[4]
                })
            
            return tags
            
        except Exception as e:
            self.logger.error(f"获取词条标签失败: {e}")
            return []
    
    def get_tagged_words(self, tag_id: int) -> List[Tuple[int, str]]:
        """
        获取带有指定标签的所有词条
        
        Args:
            tag_id: 标签ID
            
        Returns:
            词条列表 [(word_id, word), ...]
        """
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("""
                SELECT w.id, w.word
                FROM words w
                JOIN word_tags wt ON w.id = wt.word_id
                WHERE wt.tag_id = ?
                ORDER BY w.word
            """, (tag_id,))
            
            return cursor.fetchall()
            
        except Exception as e:
            self.logger.error(f"获取标签词条失败: {e}")
            return []
    
    def batch_tag_words(self, word_ids: List[int], tag_ids: List[int]) -> int:
        """
        批量为词条添加标签
        
        Args:
            word_ids: 词条ID列表
            tag_ids: 标签ID列表
            
        Returns:
            成功添加的关联数量
        """
        try:
            cursor = self.db_manager.get_cursor()
            added_count = 0
            
            for word_id in word_ids:
                for tag_id in tag_ids:
                    # 检查关联是否已存在
                    cursor.execute("""
                        SELECT 1 FROM word_tags WHERE word_id = ? AND tag_id = ?
                    """, (word_id, tag_id))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO word_tags (word_id, tag_id, created_at)
                            VALUES (?, ?, datetime('now'))
                        """, (word_id, tag_id))
                        added_count += 1
            
            self.db_manager.commit()
            self.logger.info(f"批量添加标签成功: {added_count} 个关联")
            return added_count
            
        except Exception as e:
            self.logger.error(f"批量添加标签失败: {e}")
            self.db_manager.rollback()
            return 0
    
    def search_tags(self, keyword: str) -> List[Dict]:
        """
        搜索标签
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的标签列表
        """
        try:
            cursor = self.db_manager.get_cursor()
            cursor.execute("""
                SELECT id, name, color, description, created_at
                FROM tags
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY name
            """, (f"%{keyword}%", f"%{keyword}%"))
            
            tags = []
            for row in cursor.fetchall():
                tags.append({
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'description': row[3],
                    'created_at': row[4]
                })
            
            return tags
            
        except Exception as e:
            self.logger.error(f"搜索标签失败: {e}")
            return []
    
    def get_tag_statistics(self) -> Dict:
        """
        获取标签统计信息
        
        Returns:
            统计信息字典
        """
        try:
            cursor = self.db_manager.get_cursor()
            
            # 总标签数
            cursor.execute("SELECT COUNT(*) FROM tags")
            total_tags = cursor.fetchone()[0]
            
            # 使用中的标签数
            cursor.execute("""
                SELECT COUNT(DISTINCT tag_id) FROM word_tags
            """)
            used_tags = cursor.fetchone()[0]
            
            # 标签使用统计
            cursor.execute("""
                SELECT t.name, COUNT(wt.word_id) as word_count
                FROM tags t
                LEFT JOIN word_tags wt ON t.id = wt.tag_id
                GROUP BY t.id, t.name
                ORDER BY word_count DESC
                LIMIT 10
            """)
            
            top_tags = []
            for row in cursor.fetchall():
                top_tags.append({
                    'name': row[0],
                    'word_count': row[1]
                })
            
            return {
                'total_tags': total_tags,
                'used_tags': used_tags,
                'unused_tags': total_tags - used_tags,
                'top_tags': top_tags
            }
            
        except Exception as e:
            self.logger.error(f"获取标签统计失败: {e}")
            return {
                'total_tags': 0,
                'used_tags': 0,
                'unused_tags': 0,
                'top_tags': []
            }

# 创建全局实例
tag_manager = None

def initialize_tag_manager(db_manager: DatabaseManager):
    """初始化标签管理器"""
    global tag_manager
    tag_manager = TagManager(db_manager)