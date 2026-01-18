"""
数据库管理模块
负责SQLite数据库的创建、连接和基础操作
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from config.settings import DATABASE_PATH


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        self.db_path = db_path or DATABASE_PATH
        self._ensure_database_exists()
        
    def _ensure_database_exists(self):
        """确保数据库文件和目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
    def get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接 - 每次调用都创建新连接以避免线程问题
        
        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        # 每次都创建新连接，避免跨线程使用同一连接的问题
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        return connection
    
    def close(self):
        """关闭数据库连接 - 由于每次都创建新连接，这个方法现在主要用于兼容性"""
        pass
    
    def create_tables(self):
        """创建数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 创建字典表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dictionaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建词条表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    dictionary_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dictionary_id) REFERENCES dictionaries(id) ON DELETE CASCADE
                )
            ''')
            
            # 创建标签表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT DEFAULT '#007bff',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建词条标签关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS word_tags (
                    word_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (word_id, tag_id),
                    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                )
            ''')
            
            # 创建索引以优化查询性能
            self._create_indexes(cursor)
            
            conn.commit()
            logging.info("数据库表创建成功")
            
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"创建数据库表失败: {e}")
            raise
    
    def _create_indexes(self, cursor: sqlite3.Cursor):
        """创建数据库索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_words_dictionary_id ON words(dictionary_id)",
            "CREATE INDEX IF NOT EXISTS idx_words_word ON words(word)",
            "CREATE INDEX IF NOT EXISTS idx_word_tags_word_id ON word_tags(word_id)",
            "CREATE INDEX IF NOT EXISTS idx_word_tags_tag_id ON word_tags(tag_id)",
            "CREATE INDEX IF NOT EXISTS idx_dictionaries_name ON dictionaries(name)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def execute_query(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            sqlite3.Cursor: 查询结果游标
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"执行查询失败: {query}, 错误: {e}")
            raise
        finally:
            conn.close()
    
    def fetch_all(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """
        执行查询并返回所有结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            List[sqlite3.Row]: 查询结果列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"执行查询失败: {query}, 错误: {e}")
            raise
        finally:
            conn.close()
    
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """
        执行查询并返回单个结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            Optional[sqlite3.Row]: 查询结果，如果没有结果则返回None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"执行查询失败: {query}, 错误: {e}")
            raise
        finally:
            conn.close()
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        批量执行SQL语句
        
        Args:
            query: SQL语句
            params_list: 参数列表
            
        Returns:
            int: 影响的行数
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"批量执行失败: {query}, 错误: {e}")
            raise
        finally:
            conn.close()
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            List[Dict[str, Any]]: 表结构信息
        """
        query = f"PRAGMA table_info({table_name})"
        rows = self.fetch_all(query)
        return [dict(row) for row in rows]
    
    def backup_database(self, backup_path: str) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 备份是否成功
        """
        try:
            # 确保备份目录存在
            backup_dir = Path(backup_path).parent
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建备份连接
            backup_conn = sqlite3.connect(backup_path)
            
            # 执行备份
            with self.get_connection() as source_conn:
                source_conn.backup(backup_conn)
            
            backup_conn.close()
            logging.info(f"数据库备份成功: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"数据库备份失败: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """
        从备份恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            if not Path(backup_path).exists():
                logging.error(f"备份文件不存在: {backup_path}")
                return False
            
            # 关闭当前连接
            self.close()
            
            # 创建备份连接
            backup_conn = sqlite3.connect(backup_path)
            
            # 恢复数据库
            with sqlite3.connect(self.db_path) as target_conn:
                backup_conn.backup(target_conn)
            
            backup_conn.close()
            logging.info(f"数据库恢复成功: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"数据库恢复失败: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            Dict[str, Any]: 数据库统计信息
        """
        stats = {}
        
        try:
            # 获取各表的记录数
            tables = ['dictionaries', 'words', 'tags', 'word_tags']
            for table in tables:
                count_query = f"SELECT COUNT(*) as count FROM {table}"
                result = self.fetch_one(count_query)
                stats[f"{table}_count"] = result['count'] if result else 0
            
            # 获取数据库文件大小
            if Path(self.db_path).exists():
                stats['database_size'] = Path(self.db_path).stat().st_size
            else:
                stats['database_size'] = 0
            
            # 获取最后更新时间
            last_update_query = """
                SELECT MAX(updated_at) as last_update 
                FROM dictionaries
            """
            result = self.fetch_one(last_update_query)
            stats['last_update'] = result['last_update'] if result and result['last_update'] else None
            
        except Exception as e:
            logging.error(f"获取数据库统计信息失败: {e}")
            
        return stats
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 全局数据库实例
db_manager = DatabaseManager()


def init_database():
    """初始化数据库"""
    try:
        db_manager.create_tables()
        logging.info("数据库初始化完成")
    except Exception as e:
        logging.error(f"数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    # 测试数据库功能
    logging.basicConfig(level=logging.INFO)
    
    with DatabaseManager() as db:
        db.create_tables()
        stats = db.get_database_stats()
        print("数据库统计信息:", stats)