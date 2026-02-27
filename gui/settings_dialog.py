"""
设置对话框模块
提供数据库管理和系统设置功能
"""
import logging
from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QProgressBar, QGroupBox, QTextEdit,
    QHeaderView, QAbstractItemView, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from core.database import db_manager
from core.dictionary_manager import dictionary_manager


class DatabaseCleanupThread(QThread):
    """数据库清理线程"""
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def run(self):
        """执行清理操作"""
        try:
            self.status_update.emit("正在清理数据库...")
            self.progress_update.emit(20)
            
            # 清空所有字典数据
            db_manager.execute_query("DELETE FROM words")
            self.progress_update.emit(50)
            
            # 清空字典表
            db_manager.execute_query("DELETE FROM dictionaries")
            self.progress_update.emit(80)
            
            # 重置自增ID
            db_manager.execute_query("DELETE FROM sqlite_sequence WHERE name IN ('dictionaries', 'words')")
            self.progress_update.emit(100)
            
            self.status_update.emit("清理完成")
            self.finished_signal.emit(True, "数据库已成功清空")
            
        except Exception as e:
            self.finished_signal.emit(False, f"清理失败: {str(e)}")


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        """初始化设置对话框"""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 数据存储
        self.dictionaries_data = []
        self.cleanup_thread = None
        
        self.setup_ui()
        self.load_database_info()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("系统设置")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 数据库管理标签页
        db_tab = self.create_database_tab()
        tab_widget.addTab(db_tab, "📊 数据库管理")
        
        # 系统信息标签页
        info_tab = self.create_info_tab()
        tab_widget.addTab(info_tab, "ℹ️ 系统信息")
        
        main_layout.addWidget(tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
    def create_database_tab(self):
        """创建数据库管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 数据库统计信息
        stats_group = QGroupBox("数据库统计")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("正在加载统计信息...")
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        # 字典管理区域
        dict_group = QGroupBox("字典管理")
        dict_layout = QVBoxLayout(dict_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 刷新列表")
        refresh_btn.clicked.connect(self.refresh_dictionaries)
        button_layout.addWidget(refresh_btn)
        
        delete_selected_btn = QPushButton("🗑️ 删除选中")
        delete_selected_btn.clicked.connect(self.delete_selected_dictionaries)
        button_layout.addWidget(delete_selected_btn)
        
        clear_all_btn = QPushButton("⚠️ 清空所有数据")
        clear_all_btn.setStyleSheet("QPushButton { background-color: #ff4444; color: white; }")
        clear_all_btn.clicked.connect(self.clear_all_data)
        button_layout.addWidget(clear_all_btn)
        
        button_layout.addStretch()
        dict_layout.addLayout(button_layout)
        
        # 字典列表表格
        self.dict_table = QTableWidget()
        self.dict_table.setColumnCount(4)
        self.dict_table.setHorizontalHeaderLabels(["ID", "字典名称", "词条数量", "创建时间"])
        self.dict_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.dict_table.setAlternatingRowColors(True)
        
        # 设置列宽
        header = self.dict_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        dict_layout.addWidget(self.dict_table)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        dict_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("")
        dict_layout.addWidget(self.status_label)
        
        layout.addWidget(dict_group)
        
        return widget
        
    def create_info_tab(self):
        """创建系统信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 系统信息
        info_group = QGroupBox("系统信息")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(200)
        
        # 获取系统信息
        try:
            import sys
            import platform
            from config.settings import APP_NAME, APP_VERSION
            
            system_info = f"""
应用程序: {APP_NAME} v{APP_VERSION}
Python版本: {sys.version}
操作系统: {platform.system()} {platform.release()}
架构: {platform.machine()}
数据库文件: {db_manager.db_path}
            """.strip()
            
            info_text.setPlainText(system_info)
            
        except Exception as e:
            info_text.setPlainText(f"获取系统信息失败: {e}")
            
        info_layout.addWidget(info_text)
        layout.addWidget(info_group)
        
        # 数据库文件信息
        db_group = QGroupBox("数据库文件信息")
        db_layout = QVBoxLayout(db_group)
        
        self.db_info_text = QTextEdit()
        self.db_info_text.setReadOnly(True)
        self.db_info_text.setMaximumHeight(150)
        
        db_layout.addWidget(self.db_info_text)
        layout.addWidget(db_group)
        
        layout.addStretch()
        
        return widget
        
    def load_database_info(self):
        """加载数据库信息"""
        try:
            # 加载统计信息
            stats = db_manager.get_database_stats()
            dict_count = stats.get('dictionaries_count', 0)
            word_count = stats.get('words_count', 0)
            
            stats_text = f"""
数据库统计信息:
• 字典总数: {dict_count} 个
• 词条总数: {word_count} 个
• 数据库大小: {self.get_db_size()} MB
            """.strip()
            
            self.stats_label.setText(stats_text)
            
            # 加载字典列表
            self.refresh_dictionaries()
            
            # 加载数据库文件信息
            self.load_db_file_info()
            
        except Exception as e:
            self.logger.error(f"加载数据库信息失败: {e}")
            self.stats_label.setText(f"加载失败: {e}")
            
    def get_db_size(self):
        """获取数据库文件大小"""
        try:
            import os
            size_bytes = os.path.getsize(db_manager.db_path)
            size_mb = size_bytes / (1024 * 1024)
            return f"{size_mb:.2f}"
        except:
            return "未知"
            
    def load_db_file_info(self):
        """加载数据库文件信息"""
        try:
            import os
            from datetime import datetime
            
            db_path = db_manager.db_path
            if os.path.exists(db_path):
                stat = os.stat(db_path)
                size_mb = stat.st_size / (1024 * 1024)
                modified_time = datetime.fromtimestamp(stat.st_mtime)
                
                info_text = f"""
数据库文件路径: {db_path}
文件大小: {size_mb:.2f} MB
最后修改时间: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}
                """.strip()
            else:
                info_text = "数据库文件不存在"
                
            self.db_info_text.setPlainText(info_text)
            
        except Exception as e:
            self.db_info_text.setPlainText(f"获取文件信息失败: {e}")
            
    def refresh_dictionaries(self):
        """刷新字典列表"""
        try:
            self.status_label.setText("正在加载字典列表...")
            
            # 获取所有字典
            dictionaries = dictionary_manager.get_all_dictionaries()
            self.dictionaries_data = dictionaries
            
            # 清空表格
            self.dict_table.setRowCount(0)
            
            # 填充数据
            for i, dict_info in enumerate(dictionaries):
                self.dict_table.insertRow(i)
                
                # ID
                id_item = QTableWidgetItem(str(dict_info['id']))
                id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.dict_table.setItem(i, 0, id_item)
                
                # 名称
                name_item = QTableWidgetItem(dict_info['name'])
                self.dict_table.setItem(i, 1, name_item)
                
                # 词条数量
                count = dictionary_manager.get_dictionary_word_count(dict_info['id'])
                count_item = QTableWidgetItem(str(count))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.dict_table.setItem(i, 2, count_item)
                
                # 创建时间
                time_item = QTableWidgetItem(dict_info['created_at'])
                time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.dict_table.setItem(i, 3, time_item)
            
            self.status_label.setText(f"已加载 {len(dictionaries)} 个字典")
            
            # 刷新统计信息
            self.load_database_info()
            
        except Exception as e:
            self.logger.error(f"刷新字典列表失败: {e}")
            self.status_label.setText(f"加载失败: {e}")
            
    def delete_selected_dictionaries(self):
        """删除选中的字典"""
        try:
            selected_rows = set()
            for item in self.dict_table.selectedItems():
                selected_rows.add(item.row())
                
            if not selected_rows:
                QMessageBox.information(self, "提示", "请先选择要删除的字典")
                return
                
            # 确认删除
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除选中的 {len(selected_rows)} 个字典吗？\n此操作不可撤销！",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
                
            # 执行删除
            deleted_count = 0
            for row in sorted(selected_rows, reverse=True):
                dict_id = int(self.dict_table.item(row, 0).text())
                dict_name = self.dict_table.item(row, 1).text()
                
                try:
                    dictionary_manager.delete_dictionary(dict_id)
                    deleted_count += 1
                    self.status_label.setText(f"已删除字典: {dict_name}")
                except Exception as e:
                    self.logger.error(f"删除字典 {dict_name} 失败: {e}")
                    
            # 刷新列表
            self.refresh_dictionaries()
            
            QMessageBox.information(self, "删除完成", f"成功删除 {deleted_count} 个字典")
            
        except Exception as e:
            self.logger.error(f"删除字典失败: {e}")
            QMessageBox.critical(self, "删除失败", str(e))
            
    def clear_all_data(self):
        """清空所有数据"""
        try:
            # 多重确认
            reply1 = QMessageBox.warning(
                self, "⚠️ 危险操作",
                "此操作将删除所有字典和词条数据！\n确定要继续吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply1 != QMessageBox.StandardButton.Yes:
                return
                
            reply2 = QMessageBox.critical(
                self, "⚠️ 最终确认",
                "这是最后一次确认！\n所有数据将被永久删除且无法恢复！\n\n确定要清空所有数据吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply2 != QMessageBox.StandardButton.Yes:
                return
                
            # 开始清理
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.cleanup_thread = DatabaseCleanupThread()
            self.cleanup_thread.progress_update.connect(self.progress_bar.setValue)
            self.cleanup_thread.status_update.connect(self.status_label.setText)
            self.cleanup_thread.finished_signal.connect(self.on_cleanup_finished)
            self.cleanup_thread.start()
            
        except Exception as e:
            self.logger.error(f"清空数据失败: {e}")
            QMessageBox.critical(self, "操作失败", str(e))
            
    def on_cleanup_finished(self, success: bool, message: str):
        """清理完成回调"""
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "清理完成", message)
            self.refresh_dictionaries()
        else:
            QMessageBox.critical(self, "清理失败", message)
            
        self.status_label.setText("就绪")