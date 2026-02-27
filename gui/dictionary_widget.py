"""
字典管理界面模块
提供字典的新建、导入、删除功能，以及基于正则表达式的词条分类显示
"""
import logging
from typing import List, Dict, Any, Optional
import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QFileDialog,
    QDialog, QDialogButtonBox, QTextEdit, QComboBox,
    QProgressDialog, QMenu, QHeaderView, QAbstractItemView,
    QGroupBox, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QAction, QFont

from core.dictionary_manager import dictionary_manager
from core.file_handler import file_handler
from core.deduplicator import deduplicator
from core.exporter import exporter
from utils.regex_helper import regex_helper
from config.settings import THEME_COLORS


class ImportWorker(QThread):
    """导入工作线程"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str, int)
    
    def __init__(self, file_path: str, dictionary_id: int):
        super().__init__()
        self.file_path = file_path
        self.dictionary_id = dictionary_id
    
    def run(self):
        try:
            # 导入文件
            words = file_handler.import_file(self.file_path)
            self.progress.emit(50)
            
            if words:
                # 添加到字典
                added_count = dictionary_manager.add_words(self.dictionary_id, words)
                self.progress.emit(100)
                self.finished.emit(True, f"成功导入 {added_count} 个词条", added_count)
            else:
                self.finished.emit(False, "文件中没有找到有效词条", 0)
                
        except Exception as e:
            self.finished.emit(False, f"导入失败: {str(e)}", 0)


class RegexAnalysisWorker(QThread):
    """正则表达式分析工作线程"""
    progress = pyqtSignal(int, str)
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, dictionary_id: int, patterns: List[Dict[str, str]]):
        super().__init__()
        self.dictionary_id = dictionary_id
        self.patterns = patterns
    
    def run(self):
        try:
            self.progress.emit(10, "获取字典数据...")
            
            # 获取字典中的所有词条
            words_data = dictionary_manager.get_words(self.dictionary_id, limit=None)
            words = [word['word'] for word in words_data]
            
            if not words:
                self.result_ready.emit({'matches': {}, 'unmatched': []})
                return
            
            self.progress.emit(30, "编译正则表达式...")
            
            # 编译正则表达式
            compiled_patterns = []
            for pattern_info in self.patterns:
                try:
                    pattern_name = pattern_info['name']
                    pattern_regex = pattern_info['pattern']
                    compiled_patterns.append((pattern_name, re.compile(pattern_regex)))
                except re.error as e:
                    self.error_occurred.emit(f"正则表达式错误 '{pattern_info.get('name', 'Unknown')}': {str(e)}")
                    return
            
            self.progress.emit(50, "执行匹配分析...")
            
            # 执行匹配
            matches = {}
            unmatched_words = []
            total_words = len(words)
            
            for i, word in enumerate(words):
                word_matched = False
                for pattern_name, compiled_pattern in compiled_patterns:
                    if compiled_pattern.search(word):
                        if pattern_name not in matches:
                            matches[pattern_name] = []
                        matches[pattern_name].append(word)
                        word_matched = True
                        break  # 一个词条只匹配第一个符合的模式
                
                if not word_matched:
                    unmatched_words.append(word)
                
                # 更新进度
                if i % 100 == 0:
                    progress = 50 + int((i / total_words) * 40)
                    self.progress.emit(progress, f"分析中... {i}/{total_words}")
            
            self.progress.emit(100, "分析完成")
            
            result = {
                'matches': matches,
                'unmatched': unmatched_words,
                'total_words': total_words
            }
            
            self.result_ready.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class DictionaryWidget(QWidget):
    """字典管理组件 - 重新设计为只负责字典管理和正则分类显示"""
    
    # 信号定义
    status_message = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    
    def __init__(self):
        """初始化字典管理组件"""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 组件引用
        self.dictionary_list = None
        self.category_tree = None
        self.word_table = None
        self.current_dictionary_id = None
        self.analysis_result = {}
        
        # 工作线程
        self.import_worker = None
        self.analysis_worker = None
        
        self.setup_ui()
        self.connect_signals()
        self.refresh_data()
    
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：字典列表
        left_widget = self.create_dictionary_panel()
        splitter.addWidget(left_widget)
        
        # 中间：分类树
        middle_widget = self.create_category_panel()
        splitter.addWidget(middle_widget)
        
        # 右侧：词条显示
        right_widget = self.create_word_panel()
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([250, 300, 450])
        
        main_layout.addWidget(splitter)
    
    def create_dictionary_panel(self) -> QWidget:
        """创建字典面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题
        title_label = QLabel("📚 字典列表")
        title_label.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 字典列表
        self.dictionary_list = QListWidget()
        self.dictionary_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        layout.addWidget(self.dictionary_list)
        
        # 按钮区域
        button_layout = QVBoxLayout()
        
        # 新建字典按钮
        new_dict_btn = QPushButton("➕ 新建字典")
        new_dict_btn.clicked.connect(self.create_new_dictionary)
        button_layout.addWidget(new_dict_btn)
        
        # 导入字典按钮
        import_btn = QPushButton("📁 导入字典")
        import_btn.clicked.connect(self.import_dictionary)
        button_layout.addWidget(import_btn)
        
        # 删除字典按钮
        delete_btn = QPushButton("🗑️ 删除字典")
        delete_btn.clicked.connect(self.delete_dictionary)
        button_layout.addWidget(delete_btn)
        
        # 导出字典按钮
        export_btn = QPushButton("💾 导出字典")
        export_btn.clicked.connect(self.export_dictionary)
        button_layout.addWidget(export_btn)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def create_category_panel(self) -> QWidget:
        """创建分类面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题和分析按钮
        header_layout = QHBoxLayout()
        title_label = QLabel("🔍 正则分类")
        title_label.setFont(QFont("", 12, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        analyze_btn = QPushButton("📊 分析")
        analyze_btn.clicked.connect(self.analyze_dictionary)
        header_layout.addWidget(analyze_btn)
        
        layout.addLayout(header_layout)
        
        # 分类树
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabel("分类 (词条数)")
        layout.addWidget(self.category_tree)
        
        return widget
    
    def create_word_panel(self) -> QWidget:
        """创建词条面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题
        self.word_panel_title = QLabel("📝 词条列表")
        self.word_panel_title.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(self.word_panel_title)
        
        # 词条表格
        self.word_table = QTableWidget()
        self.word_table.setColumnCount(2)
        self.word_table.setHorizontalHeaderLabels(["词条", "创建时间"])
        
        # 设置表格属性
        self.word_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.word_table.setAlternatingRowColors(True)
        
        # 设置列宽
        header = self.word_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.word_table)
        
        # 底部状态栏
        status_layout = QHBoxLayout()
        self.word_count_label = QLabel("词条数: 0")
        status_layout.addWidget(self.word_count_label)
        
        # 导出选中分类按钮
        export_category_btn = QPushButton("💾 导出当前分类")
        export_category_btn.clicked.connect(self.export_current_category)
        status_layout.addWidget(export_category_btn)
        
        layout.addLayout(status_layout)
        
        return widget
    
    def connect_signals(self):
        """连接信号"""
        # 字典列表选择
        self.dictionary_list.itemSelectionChanged.connect(self.on_dictionary_selected)
        self.dictionary_list.customContextMenuRequested.connect(self.show_dictionary_context_menu)
        
        # 分类树选择
        self.category_tree.itemSelectionChanged.connect(self.on_category_selected)
    
    def refresh_data(self):
        """刷新数据"""
        self.load_dictionaries()
        self.clear_analysis_result()
    
    def load_dictionaries(self):
        """加载字典列表"""
        try:
            self.dictionary_list.clear()
            dictionaries = dictionary_manager.get_all_dictionaries()
            
            for dictionary in dictionaries:
                item = QListWidgetItem()
                item.setText(f"{dictionary['name']} ({dictionary.get('word_count', 0)} 词条)")
                item.setData(Qt.ItemDataRole.UserRole, dictionary['id'])
                
                # 设置工具提示
                tooltip = f"名称: {dictionary['name']}\n"
                tooltip += f"词条数: {dictionary.get('word_count', 0)}\n"
                tooltip += f"创建时间: {dictionary.get('created_at', 'N/A')}"
                if dictionary.get('description'):
                    tooltip += f"\n描述: {dictionary['description']}"
                item.setToolTip(tooltip)
                
                self.dictionary_list.addItem(item)
            
            self.status_message.emit(f"加载了 {len(dictionaries)} 个字典")
            
        except Exception as e:
            self.logger.error(f"加载字典列表失败: {e}")
            self.status_message.emit("加载字典列表失败")
    
    def on_dictionary_selected(self):
        """字典选择事件"""
        current_item = self.dictionary_list.currentItem()
        if current_item:
            self.current_dictionary_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.clear_analysis_result()
            self.status_message.emit("请点击'分析'按钮进行正则表达式分析")
    
    def analyze_dictionary(self):
        """分析字典"""
        if not self.current_dictionary_id:
            QMessageBox.warning(self, "警告", "请先选择一个字典")
            return
        
        # 获取所有正则表达式模式
        try:
            pattern_names = regex_helper.get_all_pattern_names()
            if not pattern_names:
                QMessageBox.information(self, "提示", "没有找到正则表达式模式，请先在正则表达式页面添加模式")
                return
            
            patterns = []
            for pattern_name in pattern_names:
                pattern_info = regex_helper.get_pattern_info(pattern_name)
                if pattern_info and 'pattern' in pattern_info:
                    patterns.append({
                        'name': pattern_name,
                        'pattern': pattern_info['pattern']
                    })
            
            if not patterns:
                QMessageBox.information(self, "提示", "没有有效的正则表达式模式")
                return
            
            # 创建进度对话框
            progress_dialog = QProgressDialog("正在分析字典...", "取消", 0, 100, self)
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.show()
            
            # 创建分析工作线程
            self.analysis_worker = RegexAnalysisWorker(self.current_dictionary_id, patterns)
            self.analysis_worker.progress.connect(lambda v, m: (progress_dialog.setValue(v), progress_dialog.setLabelText(m)))
            self.analysis_worker.result_ready.connect(self.on_analysis_finished)
            self.analysis_worker.error_occurred.connect(self.on_analysis_error)
            self.analysis_worker.finished.connect(progress_dialog.close)
            
            # 连接取消信号
            progress_dialog.canceled.connect(self.analysis_worker.terminate)
            
            self.analysis_worker.start()
            
        except Exception as e:
            self.logger.error(f"启动分析失败: {e}")
            QMessageBox.critical(self, "错误", f"启动分析失败: {str(e)}")
    
    @pyqtSlot(dict)
    def on_analysis_finished(self, result: dict):
        """分析完成处理"""
        self.analysis_result = result
        self.update_category_tree()
        self.status_message.emit(f"分析完成：总词条 {result['total_words']} 个，未匹配 {len(result['unmatched'])} 个")
    
    @pyqtSlot(str)
    def on_analysis_error(self, error_message: str):
        """分析错误处理"""
        QMessageBox.critical(self, "分析错误", f"分析失败: {error_message}")
        self.status_message.emit(f"分析失败: {error_message}")
    
    def update_category_tree(self):
        """更新分类树"""
        self.category_tree.clear()
        
        if not self.analysis_result:
            return
        
        matches = self.analysis_result.get('matches', {})
        unmatched = self.analysis_result.get('unmatched', [])
        
        # 添加匹配的分类
        for pattern_name, words in matches.items():
            if words:  # 只显示有词条的分类
                item = QTreeWidgetItem([f"{pattern_name} ({len(words)})"])
                item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'pattern', 'name': pattern_name, 'words': words})
                self.category_tree.addTopLevelItem(item)
        
        # 添加未匹配分类
        if unmatched:
            item = QTreeWidgetItem([f"未匹配 ({len(unmatched)})"])
            item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'unmatched', 'words': unmatched})
            self.category_tree.addTopLevelItem(item)
        
        # 展开所有项
        self.category_tree.expandAll()
    
    def on_category_selected(self):
        """分类选择事件"""
        current_item = self.category_tree.currentItem()
        if not current_item:
            return
        
        data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        words = data.get('words', [])
        category_type = data.get('type', '')
        category_name = data.get('name', '未匹配')
        
        # 更新标题
        self.word_panel_title.setText(f"📝 {category_name} ({len(words)} 词条)")
        
        # 更新词条表格
        self.word_table.setRowCount(len(words))
        
        for row, word in enumerate(words):
            # 词条
            word_item = QTableWidgetItem(word)
            self.word_table.setItem(row, 0, word_item)
            
            # 创建时间（这里简化处理，实际可以从数据库获取）
            time_item = QTableWidgetItem("--")
            self.word_table.setItem(row, 1, time_item)
        
        # 更新词条计数
        self.word_count_label.setText(f"词条数: {len(words)}")
    
    def clear_analysis_result(self):
        """清空分析结果"""
        self.analysis_result = {}
        self.category_tree.clear()
        self.word_table.setRowCount(0)
        self.word_panel_title.setText("📝 词条列表")
        self.word_count_label.setText("词条数: 0")
    
    def create_new_dictionary(self):
        """创建新字典"""
        dialog = DictionaryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, description = dialog.get_data()
            
            try:
                dictionary_id = dictionary_manager.create_dictionary(name, description)
                self.status_message.emit(f"字典 '{name}' 创建成功")
                self.refresh_data()
                
                # 选中新创建的字典
                for i in range(self.dictionary_list.count()):
                    item = self.dictionary_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == dictionary_id:
                        self.dictionary_list.setCurrentItem(item)
                        break
                        
            except Exception as e:
                self.logger.error(f"创建字典失败: {e}")
                QMessageBox.critical(self, "错误", f"创建字典失败: {str(e)}")
    
    def import_dictionary(self):
        """导入字典"""
        if not self.current_dictionary_id:
            QMessageBox.warning(self, "警告", "请先选择一个字典")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入字典文件", "",
            "支持的文件 (*.txt *.json *.csv *.xlsx *.xls);;文本文件 (*.txt);;JSON文件 (*.json);;CSV文件 (*.csv);;Excel文件 (*.xlsx *.xls)"
        )
        
        if file_path:
            # 创建进度对话框
            progress_dialog = QProgressDialog("正在导入文件...", "取消", 0, 100, self)
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.show()
            
            # 创建工作线程
            self.import_worker = ImportWorker(file_path, self.current_dictionary_id)
            self.import_worker.progress.connect(progress_dialog.setValue)
            self.import_worker.finished.connect(self.on_import_finished)
            self.import_worker.finished.connect(progress_dialog.close)
            
            # 连接取消信号
            progress_dialog.canceled.connect(self.import_worker.terminate)
            
            self.import_worker.start()
    
    @pyqtSlot(bool, str, int)
    def on_import_finished(self, success: bool, message: str, count: int):
        """导入完成处理"""
        if success:
            self.status_message.emit(message)
            self.refresh_data()
            self.clear_analysis_result()  # 清空分析结果，需要重新分析
        else:
            QMessageBox.critical(self, "导入失败", message)
        
        self.import_worker = None
    
    def export_dictionary(self):
        """导出整个字典"""
        if not self.current_dictionary_id:
            QMessageBox.warning(self, "警告", "请先选择一个字典")
            return
        
        # 获取字典信息
        dictionary = dictionary_manager.get_dictionary_by_id(self.current_dictionary_id)
        if not dictionary:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出字典", f"{dictionary['name']}.txt",
            "文本文件 (*.txt);;JSON文件 (*.json);;CSV文件 (*.csv);;Excel文件 (*.xlsx)"
        )
        
        if file_path:
            try:
                success = exporter.export_dictionary(self.current_dictionary_id, file_path)
                
                if success:
                    self.status_message.emit(f"字典导出成功: {file_path}")
                else:
                    QMessageBox.critical(self, "错误", "导出失败")
                    
            except Exception as e:
                self.logger.error(f"导出字典失败: {e}")
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def export_current_category(self):
        """导出当前选中的分类"""
        current_item = self.category_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个分类")
            return
        
        data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        words = data.get('words', [])
        category_name = data.get('name', '未匹配')
        
        if not words:
            QMessageBox.warning(self, "警告", "当前分类没有词条")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出分类", f"{category_name}.txt",
            "文本文件 (*.txt);;JSON文件 (*.json);;CSV文件 (*.csv)"
        )
        
        if file_path:
            try:
                # 根据文件扩展名确定格式
                if file_path.endswith('.json'):
                    self.export_category_as_json(file_path, category_name, words)
                elif file_path.endswith('.csv'):
                    self.export_category_as_csv(file_path, words)
                else:
                    self.export_category_as_txt(file_path, words)
                
                self.status_message.emit(f"分类 '{category_name}' 导出成功: {file_path}")
                
            except Exception as e:
                self.logger.error(f"导出分类失败: {e}")
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def export_category_as_txt(self, file_path: str, words: List[str]):
        """导出分类为文本文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for word in sorted(words):
                f.write(word + '\n')
    
    def export_category_as_json(self, file_path: str, category_name: str, words: List[str]):
        """导出分类为JSON文件"""
        import json
        from datetime import datetime
        
        export_data = {
            'category': category_name,
            'export_time': datetime.now().isoformat(),
            'word_count': len(words),
            'words': sorted(words)
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def export_category_as_csv(self, file_path: str, words: List[str]):
        """导出分类为CSV文件"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['词条'])
            
            for word in sorted(words):
                writer.writerow([word])
    
    def delete_dictionary(self):
        """删除字典"""
        current_item = self.dictionary_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个字典")
            return
        
        dictionary_id = current_item.data(Qt.ItemDataRole.UserRole)
        dictionary_name = current_item.text().split(" (")[0]
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除字典 '{dictionary_name}' 吗？\n此操作将删除字典中的所有词条，且无法恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = dictionary_manager.delete_dictionary(dictionary_id)
                
                if success:
                    self.status_message.emit(f"字典 '{dictionary_name}' 已删除")
                    self.current_dictionary_id = None
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, "错误", "删除字典失败")
                    
            except Exception as e:
                self.logger.error(f"删除字典失败: {e}")
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def show_dictionary_context_menu(self, position):
        """显示字典右键菜单"""
        item = self.dictionary_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # 重命名
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(self.rename_dictionary)
        menu.addAction(rename_action)
        
        # 导出
        export_action = QAction("导出", self)
        export_action.triggered.connect(self.export_dictionary)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        # 删除
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self.delete_dictionary)
        menu.addAction(delete_action)
        
        menu.exec(self.dictionary_list.mapToGlobal(position))
    
    def rename_dictionary(self):
        """重命名字典"""
        current_item = self.dictionary_list.currentItem()
        if not current_item:
            return
        
        dictionary_id = current_item.data(Qt.ItemDataRole.UserRole)
        old_name = current_item.text().split(" (")[0]
        
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, "重命名字典", "新名称:", text=old_name)
        
        if ok and new_name.strip():
            try:
                success = dictionary_manager.rename_dictionary(dictionary_id, new_name.strip())
                
                if success:
                    self.status_message.emit(f"字典已重命名为 '{new_name}'")
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, "错误", "重命名失败")
                    
            except Exception as e:
                self.logger.error(f"重命名字典失败: {e}")
                QMessageBox.critical(self, "错误", f"重命名失败: {str(e)}")


class DictionaryDialog(QDialog):
    """字典创建/编辑对话框"""
    
    def __init__(self, parent=None, dictionary_data=None):
        super().__init__(parent)
        self.dictionary_data = dictionary_data
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("新建字典" if not self.dictionary_data else "编辑字典")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # 名称输入
        layout.addWidget(QLabel("字典名称:"))
        self.name_edit = QLineEdit()
        if self.dictionary_data:
            self.name_edit.setText(self.dictionary_data.get('name', ''))
        layout.addWidget(self.name_edit)
        
        # 描述输入
        layout.addWidget(QLabel("描述 (可选):"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        if self.dictionary_data:
            self.description_edit.setPlainText(self.dictionary_data.get('description', ''))
        layout.addWidget(self.description_edit)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.name_edit.setFocus()
    
    def get_data(self):
        """获取输入数据"""
        return self.name_edit.text().strip(), self.description_edit.toPlainText().strip()
    
    def accept(self):
        """确认按钮处理"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入字典名称")
            return
        
        super().accept()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = DictionaryWidget()
    widget.show()
    sys.exit(app.exec())