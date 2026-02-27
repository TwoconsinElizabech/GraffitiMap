"""
大字典处理模块
提供大字典的拆分和自动分类功能
"""
import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QSpinBox, QFileDialog,
    QMessageBox, QProgressBar, QTextEdit, QComboBox,
    QCheckBox, QTabWidget, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from core.dictionary_manager import dictionary_manager
from utils.regex_helper import regex_helper


class BigDictionarySplitWorker(QThread):
    """大字典拆分工作线程"""
    progress = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str, list)
    
    def __init__(self, file_path: str, max_lines: int, output_dir: str):
        super().__init__()
        self.file_path = file_path
        self.max_lines = max_lines
        self.output_dir = output_dir
        
    def run(self):
        """执行拆分操作"""
        try:
            self.progress.emit(10, "读取字典文件...")
            
            # 读取文件
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            self.progress.emit(20, f"共读取 {total_lines} 行数据")
            
            if total_lines <= self.max_lines:
                self.finished_signal.emit(False, "文件行数小于等于指定的最大行数，无需拆分", [])
                return
            
            # 计算需要拆分的文件数
            file_count = (total_lines + self.max_lines - 1) // self.max_lines
            self.progress.emit(30, f"将拆分为 {file_count} 个文件")
            
            # 创建输出目录
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 获取原文件名（不含扩展名）
            base_name = Path(self.file_path).stem
            
            output_files = []
            
            # 拆分文件
            for i in range(file_count):
                start_idx = i * self.max_lines
                end_idx = min((i + 1) * self.max_lines, total_lines)
                
                # 生成输出文件名
                output_file = os.path.join(self.output_dir, f"{base_name}_part_{i+1:03d}.txt")
                
                # 写入文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    for line in lines[start_idx:end_idx]:
                        f.write(line)
                
                output_files.append(output_file)
                
                # 更新进度
                progress = 30 + int((i + 1) / file_count * 60)
                self.progress.emit(progress, f"已生成 {i+1}/{file_count} 个文件")
            
            self.progress.emit(100, "拆分完成")
            self.finished_signal.emit(True, f"成功拆分为 {file_count} 个文件", output_files)
            
        except Exception as e:
            self.finished_signal.emit(False, f"拆分失败: {str(e)}", [])


class BigDictionaryAutoWorker(QThread):
    """大字典自动分类工作线程"""
    progress = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str, dict)
    
    def __init__(self, file_path: str, output_dir: str, selected_patterns: List[Dict[str, str]]):
        super().__init__()
        self.file_path = file_path
        self.output_dir = output_dir
        self.selected_patterns = selected_patterns
        
    def run(self):
        """执行自动分类操作"""
        try:
            self.progress.emit(10, "读取字典文件...")
            
            # 读取文件
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            total_lines = len(lines)
            self.progress.emit(20, f"共读取 {total_lines} 行数据")
            
            # 编译正则表达式
            self.progress.emit(30, "编译正则表达式...")
            import re
            compiled_patterns = []
            for pattern_info in self.selected_patterns:
                try:
                    compiled_patterns.append({
                        'name': pattern_info['name'],
                        'pattern': re.compile(pattern_info['pattern']),
                        'matches': []
                    })
                except re.error as e:
                    self.finished_signal.emit(False, f"正则表达式错误 '{pattern_info['name']}': {str(e)}", {})
                    return
            
            # 分类词条
            self.progress.emit(40, "开始分类词条...")
            unmatched_words = []
            
            for i, word in enumerate(lines):
                matched = False
                
                # 检查每个模式
                for pattern_info in compiled_patterns:
                    if pattern_info['pattern'].search(word):
                        pattern_info['matches'].append(word)
                        matched = True
                        break  # 只匹配第一个模式
                
                if not matched:
                    unmatched_words.append(word)
                
                # 更新进度
                if i % 1000 == 0:
                    progress = 40 + int((i / total_lines) * 50)
                    self.progress.emit(progress, f"已处理 {i}/{total_lines} 个词条")
            
            # 创建输出目录
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 获取原文件名（不含扩展名）
            base_name = Path(self.file_path).stem
            
            # 保存分类结果
            self.progress.emit(90, "保存分类结果...")
            output_files = {}
            
            # 保存匹配的模式
            for pattern_info in compiled_patterns:
                if pattern_info['matches']:
                    output_file = os.path.join(self.output_dir, f"{base_name}_{pattern_info['name']}.txt")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        for word in pattern_info['matches']:
                            f.write(word + '\n')
                    output_files[pattern_info['name']] = {
                        'file': output_file,
                        'count': len(pattern_info['matches'])
                    }
            
            # 保存未匹配的词条
            if unmatched_words:
                unmatched_file = os.path.join(self.output_dir, f"{base_name}_未匹配.txt")
                with open(unmatched_file, 'w', encoding='utf-8') as f:
                    for word in unmatched_words:
                        f.write(word + '\n')
                output_files['未匹配'] = {
                    'file': unmatched_file,
                    'count': len(unmatched_words)
                }
            
            self.progress.emit(100, "自动分类完成")
            self.finished_signal.emit(True, "自动分类完成", output_files)
            
        except Exception as e:
            self.finished_signal.emit(False, f"自动分类失败: {str(e)}", {})


class BigDictionaryMergeWorker(QThread):
    """大字典合并工作线程"""
    progress = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str, dict)
    
    def __init__(self, file_paths: List[str], output_file: str, remove_duplicates: bool = True):
        super().__init__()
        self.file_paths = file_paths
        self.output_file = output_file
        self.remove_duplicates = remove_duplicates
        
    def run(self):
        """执行合并操作"""
        try:
            self.progress.emit(10, "开始读取文件...")
            
            all_words = []
            total_files = len(self.file_paths)
            
            # 读取所有文件
            for i, file_path in enumerate(self.file_paths):
                self.progress.emit(10 + int((i / total_files) * 40), f"读取文件 {i+1}/{total_files}...")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        words = [line.strip() for line in f.readlines() if line.strip()]
                        all_words.extend(words)
                except Exception as e:
                    self.finished_signal.emit(False, f"读取文件 {file_path} 失败: {str(e)}", {})
                    return
            
            original_count = len(all_words)
            self.progress.emit(50, f"共读取 {original_count} 个词条")
            
            # 去重处理
            if self.remove_duplicates:
                self.progress.emit(60, "去重处理中...")
                unique_words = list(set(all_words))
                duplicate_count = original_count - len(unique_words)
                self.progress.emit(80, f"去重完成，移除 {duplicate_count} 个重复词条")
            else:
                unique_words = all_words
                duplicate_count = 0
            
            # 排序
            self.progress.emit(85, "排序中...")
            unique_words.sort()
            
            # 写入输出文件
            self.progress.emit(90, "写入输出文件...")
            with open(self.output_file, 'w', encoding='utf-8') as f:
                for word in unique_words:
                    f.write(word + '\n')
            
            result = {
                'original_count': original_count,
                'final_count': len(unique_words),
                'duplicate_count': duplicate_count,
                'files_merged': total_files,
                'output_file': self.output_file
            }
            
            self.progress.emit(100, "合并完成")
            self.finished_signal.emit(True, "字典合并完成", result)
            
        except Exception as e:
            self.finished_signal.emit(False, f"合并失败: {str(e)}", {})


class BigDictionaryWidget(QWidget):
    """大字典处理组件"""
    
    # 信号定义
    status_message = pyqtSignal(str)
    
    def __init__(self):
        """初始化大字典处理组件"""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 工作线程
        self.split_worker = None
        self.auto_worker = None
        self.merge_worker = None
        
        self.setup_ui()
        self.load_patterns()
    
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 拆分模式标签页
        split_tab = self.create_split_tab()
        tab_widget.addTab(split_tab, "📂 拆分模式")
        
        # 自动模式标签页
        auto_tab = self.create_auto_tab()
        tab_widget.addTab(auto_tab, "🤖 自动模式")
        
        # 合并模式标签页
        merge_tab = self.create_merge_tab()
        tab_widget.addTab(merge_tab, "🔗 合并模式")
        
        main_layout.addWidget(tab_widget)
        
        # 底部状态栏
        status_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        main_layout.addLayout(status_layout)
    
    def create_split_tab(self) -> QWidget:
        """创建拆分模式标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 文件选择
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        file_select_layout = QHBoxLayout()
        self.split_file_label = QLabel("未选择文件")
        file_select_layout.addWidget(self.split_file_label)
        
        select_file_btn = QPushButton("📁 选择文件")
        select_file_btn.clicked.connect(self.select_split_file)
        file_select_layout.addWidget(select_file_btn)
        
        file_layout.addLayout(file_select_layout)
        layout.addWidget(file_group)
        
        # 拆分设置
        settings_group = QGroupBox("拆分设置")
        settings_layout = QVBoxLayout(settings_group)
        
        # 最大行数设置
        lines_layout = QHBoxLayout()
        lines_layout.addWidget(QLabel("每个文件最大行数:"))
        
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setMinimum(1000)
        self.max_lines_spin.setMaximum(1000000)
        self.max_lines_spin.setValue(10000)
        self.max_lines_spin.setSuffix(" 行")
        lines_layout.addWidget(self.max_lines_spin)
        lines_layout.addStretch()
        
        settings_layout.addLayout(lines_layout)
        
        # 输出目录设置
        output_layout = QHBoxLayout()
        self.split_output_label = QLabel("未选择输出目录")
        output_layout.addWidget(self.split_output_label)
        
        select_output_btn = QPushButton("📁 选择目录")
        select_output_btn.clicked.connect(self.select_split_output_dir)
        output_layout.addWidget(select_output_btn)
        
        settings_layout.addLayout(output_layout)
        layout.addWidget(settings_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.split_start_btn = QPushButton("🔄 开始拆分")
        self.split_start_btn.clicked.connect(self.start_split)
        self.split_start_btn.setEnabled(False)
        button_layout.addWidget(self.split_start_btn)
        
        layout.addLayout(button_layout)
        
        # 结果显示
        result_group = QGroupBox("拆分结果")
        result_layout = QVBoxLayout(result_group)
        
        self.split_result_text = QTextEdit()
        self.split_result_text.setMaximumHeight(150)
        self.split_result_text.setReadOnly(True)
        result_layout.addWidget(self.split_result_text)
        
        layout.addWidget(result_group)
        
        layout.addStretch()
        return widget
    
    def create_auto_tab(self) -> QWidget:
        """创建自动模式标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 文件选择
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        file_select_layout = QHBoxLayout()
        self.auto_file_label = QLabel("未选择文件")
        file_select_layout.addWidget(self.auto_file_label)
        
        select_auto_file_btn = QPushButton("📁 选择文件")
        select_auto_file_btn.clicked.connect(self.select_auto_file)
        file_select_layout.addWidget(select_auto_file_btn)
        
        file_layout.addLayout(file_select_layout)
        layout.addWidget(file_group)
        
        # 模式选择
        pattern_group = QGroupBox("正则表达式模式选择")
        pattern_layout = QVBoxLayout(pattern_group)
        
        # 全选/全不选按钮
        pattern_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("✅ 全选")
        select_all_btn.clicked.connect(self.select_all_patterns)
        pattern_btn_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("❌ 全不选")
        select_none_btn.clicked.connect(self.select_none_patterns)
        pattern_btn_layout.addWidget(select_none_btn)
        
        pattern_btn_layout.addStretch()
        pattern_layout.addLayout(pattern_btn_layout)
        
        # 模式列表
        self.pattern_list = QListWidget()
        self.pattern_list.setMaximumHeight(200)
        pattern_layout.addWidget(self.pattern_list)
        
        layout.addWidget(pattern_group)
        
        # 输出目录设置
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout(output_group)
        
        output_dir_layout = QHBoxLayout()
        self.auto_output_label = QLabel("未选择输出目录")
        output_dir_layout.addWidget(self.auto_output_label)
        
        select_auto_output_btn = QPushButton("📁 选择目录")
        select_auto_output_btn.clicked.connect(self.select_auto_output_dir)
        output_dir_layout.addWidget(select_auto_output_btn)
        
        output_layout.addLayout(output_dir_layout)
        layout.addWidget(output_group)
        
        # 操作按钮
        auto_button_layout = QHBoxLayout()
        auto_button_layout.addStretch()
        
        self.auto_start_btn = QPushButton("🤖 开始自动分类")
        self.auto_start_btn.clicked.connect(self.start_auto_classification)
        self.auto_start_btn.setEnabled(False)
        auto_button_layout.addWidget(self.auto_start_btn)
        
        layout.addLayout(auto_button_layout)
        
        # 结果显示
        auto_result_group = QGroupBox("分类结果")
        auto_result_layout = QVBoxLayout(auto_result_group)
        
        self.auto_result_text = QTextEdit()
        self.auto_result_text.setMaximumHeight(150)
        self.auto_result_text.setReadOnly(True)
        auto_result_layout.addWidget(self.auto_result_text)
        
        layout.addWidget(auto_result_group)
        
        layout.addStretch()
        return widget
    
    def create_merge_tab(self) -> QWidget:
        """创建合并模式标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 文件选择
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        # 文件列表
        self.merge_file_list = QListWidget()
        self.merge_file_list.setMaximumHeight(150)
        file_layout.addWidget(QLabel("要合并的字典文件:"))
        file_layout.addWidget(self.merge_file_list)
        
        # 文件操作按钮
        file_btn_layout = QHBoxLayout()
        
        add_files_btn = QPushButton("📁 添加文件")
        add_files_btn.clicked.connect(self.add_merge_files)
        file_btn_layout.addWidget(add_files_btn)
        
        remove_file_btn = QPushButton("➖ 移除选中")
        remove_file_btn.clicked.connect(self.remove_merge_file)
        file_btn_layout.addWidget(remove_file_btn)
        
        clear_files_btn = QPushButton("🗑️ 清空列表")
        clear_files_btn.clicked.connect(self.clear_merge_files)
        file_btn_layout.addWidget(clear_files_btn)
        
        file_btn_layout.addStretch()
        file_layout.addLayout(file_btn_layout)
        
        layout.addWidget(file_group)
        
        # 合并设置
        merge_settings_group = QGroupBox("合并设置")
        merge_settings_layout = QVBoxLayout(merge_settings_group)
        
        # 去重选项
        self.remove_duplicates_checkbox = QCheckBox("自动去重（推荐）")
        self.remove_duplicates_checkbox.setChecked(True)
        merge_settings_layout.addWidget(self.remove_duplicates_checkbox)
        
        # 输出文件设置
        output_layout = QHBoxLayout()
        self.merge_output_label = QLabel("未选择输出文件")
        output_layout.addWidget(self.merge_output_label)
        
        select_merge_output_btn = QPushButton("📁 选择输出文件")
        select_merge_output_btn.clicked.connect(self.select_merge_output_file)
        output_layout.addWidget(select_merge_output_btn)
        
        merge_settings_layout.addLayout(output_layout)
        layout.addWidget(merge_settings_group)
        
        # 操作按钮
        merge_button_layout = QHBoxLayout()
        merge_button_layout.addStretch()
        
        self.merge_start_btn = QPushButton("🔗 开始合并")
        self.merge_start_btn.clicked.connect(self.start_merge)
        self.merge_start_btn.setEnabled(False)
        merge_button_layout.addWidget(self.merge_start_btn)
        
        layout.addLayout(merge_button_layout)
        
        # 结果显示
        merge_result_group = QGroupBox("合并结果")
        merge_result_layout = QVBoxLayout(merge_result_group)
        
        self.merge_result_text = QTextEdit()
        self.merge_result_text.setMaximumHeight(150)
        self.merge_result_text.setReadOnly(True)
        merge_result_layout.addWidget(self.merge_result_text)
        
        layout.addWidget(merge_result_group)
        
        layout.addStretch()
        return widget
    
    def load_patterns(self):
        """加载正则表达式模式"""
        try:
            pattern_names = regex_helper.get_all_pattern_names()
            
            for pattern_name in pattern_names:
                pattern_info = regex_helper.get_pattern_info(pattern_name)
                if pattern_info and 'pattern' in pattern_info:
                    item = QListWidgetItem(pattern_name)
                    item.setCheckState(Qt.CheckState.Unchecked)
                    item.setToolTip(f"正则表达式: {pattern_info['pattern']}\n描述: {pattern_info.get('description', '无描述')}")
                    self.pattern_list.addItem(item)
            
        except Exception as e:
            self.logger.error(f"加载正则表达式模式失败: {e}")
    
    def select_split_file(self):
        """选择要拆分的文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要拆分的字典文件", "",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            self.split_file_path = file_path
            self.split_file_label.setText(f"已选择: {Path(file_path).name}")
            self.check_split_ready()
    
    def select_split_output_dir(self):
        """选择拆分输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        
        if dir_path:
            self.split_output_dir = dir_path
            self.split_output_label.setText(f"输出到: {dir_path}")
            self.check_split_ready()
    
    def check_split_ready(self):
        """检查拆分是否准备就绪"""
        ready = (hasattr(self, 'split_file_path') and 
                hasattr(self, 'split_output_dir'))
        self.split_start_btn.setEnabled(ready)
    
    def select_auto_file(self):
        """选择要自动分类的文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要自动分类的字典文件", "",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            self.auto_file_path = file_path
            self.auto_file_label.setText(f"已选择: {Path(file_path).name}")
            self.check_auto_ready()
    
    def select_auto_output_dir(self):
        """选择自动分类输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        
        if dir_path:
            self.auto_output_dir = dir_path
            self.auto_output_label.setText(f"输出到: {dir_path}")
            self.check_auto_ready()
    
    def check_auto_ready(self):
        """检查自动分类是否准备就绪"""
        ready = (hasattr(self, 'auto_file_path') and
                hasattr(self, 'auto_output_dir') and
                bool(self.get_selected_patterns()))
        self.auto_start_btn.setEnabled(ready)
    
    def select_all_patterns(self):
        """全选模式"""
        for i in range(self.pattern_list.count()):
            item = self.pattern_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
        self.check_auto_ready()
    
    def select_none_patterns(self):
        """全不选模式"""
        for i in range(self.pattern_list.count()):
            item = self.pattern_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
        self.check_auto_ready()
    
    def get_selected_patterns(self) -> List[Dict[str, str]]:
        """获取选中的模式"""
        selected_patterns = []
        
        for i in range(self.pattern_list.count()):
            item = self.pattern_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                pattern_name = item.text()
                pattern_info = regex_helper.get_pattern_info(pattern_name)
                if pattern_info and 'pattern' in pattern_info:
                    selected_patterns.append({
                        'name': pattern_name,
                        'pattern': pattern_info['pattern']
                    })
        
        return selected_patterns
    
    def add_merge_files(self):
        """添加要合并的文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择要合并的字典文件", "",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_paths:
            for file_path in file_paths:
                # 检查是否已存在
                existing_items = [self.merge_file_list.item(i).text()
                                for i in range(self.merge_file_list.count())]
                if file_path not in existing_items:
                    self.merge_file_list.addItem(file_path)
            
            self.check_merge_ready()
    
    def remove_merge_file(self):
        """移除选中的文件"""
        current_row = self.merge_file_list.currentRow()
        if current_row >= 0:
            self.merge_file_list.takeItem(current_row)
            self.check_merge_ready()
    
    def clear_merge_files(self):
        """清空文件列表"""
        self.merge_file_list.clear()
        self.check_merge_ready()
    
    def select_merge_output_file(self):
        """选择合并输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出文件", "merged_dictionary.txt",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            self.merge_output_file = file_path
            self.merge_output_label.setText(f"输出到: {Path(file_path).name}")
            self.check_merge_ready()
    
    def check_merge_ready(self):
        """检查合并是否准备就绪"""
        ready = (self.merge_file_list.count() >= 2 and
                hasattr(self, 'merge_output_file'))
        self.merge_start_btn.setEnabled(ready)
    
    def start_merge(self):
        """开始合并"""
        if self.merge_file_list.count() < 2:
            QMessageBox.warning(self, "警告", "请至少选择两个文件进行合并")
            return
        
        if not hasattr(self, 'merge_output_file'):
            QMessageBox.warning(self, "警告", "请选择输出文件")
            return
        
        # 获取文件列表
        file_paths = [self.merge_file_list.item(i).text()
                     for i in range(self.merge_file_list.count())]
        
        remove_duplicates = self.remove_duplicates_checkbox.isChecked()
        
        # 启动合并工作线程
        if self.merge_worker and self.merge_worker.isRunning():
            self.merge_worker.terminate()
            self.merge_worker.wait()
        
        self.merge_worker = BigDictionaryMergeWorker(
            file_paths, self.merge_output_file, remove_duplicates
        )
        self.merge_worker.progress.connect(self.update_progress)
        self.merge_worker.finished_signal.connect(self.on_merge_finished)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.merge_start_btn.setEnabled(False)
        self.status_label.setText("合并中...")
        
        self.merge_worker.start()
    
    def start_split(self):
        """开始拆分"""
        if not hasattr(self, 'split_file_path') or not hasattr(self, 'split_output_dir'):
            QMessageBox.warning(self, "警告", "请先选择文件和输出目录")
            return
        
        max_lines = self.max_lines_spin.value()
        
        # 启动拆分工作线程
        if self.split_worker and self.split_worker.isRunning():
            self.split_worker.terminate()
            self.split_worker.wait()
        
        self.split_worker = BigDictionarySplitWorker(
            self.split_file_path, max_lines, self.split_output_dir
        )
        self.split_worker.progress.connect(self.update_progress)
        self.split_worker.finished_signal.connect(self.on_split_finished)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.split_start_btn.setEnabled(False)
        self.status_label.setText("拆分中...")
        
        self.split_worker.start()
    
    def start_auto_classification(self):
        """开始自动分类"""
        if not hasattr(self, 'auto_file_path') or not hasattr(self, 'auto_output_dir'):
            QMessageBox.warning(self, "警告", "请先选择文件和输出目录")
            return
        
        selected_patterns = self.get_selected_patterns()
        if not selected_patterns:
            QMessageBox.warning(self, "警告", "请至少选择一个正则表达式模式")
            return
        
        # 启动自动分类工作线程
        if self.auto_worker and self.auto_worker.isRunning():
            self.auto_worker.terminate()
            self.auto_worker.wait()
        
        self.auto_worker = BigDictionaryAutoWorker(
            self.auto_file_path, self.auto_output_dir, selected_patterns
        )
        self.auto_worker.progress.connect(self.update_progress)
        self.auto_worker.finished_signal.connect(self.on_auto_finished)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.auto_start_btn.setEnabled(False)
        self.status_label.setText("自动分类中...")
        
        self.auto_worker.start()
    
    def update_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def on_split_finished(self, success: bool, message: str, output_files: List[str]):
        """拆分完成处理"""
        self.progress_bar.setVisible(False)
        self.split_start_btn.setEnabled(True)
        self.status_label.setText("就绪")
        
        if success:
            result_text = f"拆分成功！\n\n{message}\n\n生成的文件:\n"
            for i, file_path in enumerate(output_files, 1):
                result_text += f"{i}. {Path(file_path).name}\n"
            
            self.split_result_text.setPlainText(result_text)
            QMessageBox.information(self, "拆分成功", message)
            self.status_message.emit(f"拆分完成：生成 {len(output_files)} 个文件")
        else:
            self.split_result_text.setPlainText(f"拆分失败：{message}")
            QMessageBox.critical(self, "拆分失败", message)
            self.status_message.emit(f"拆分失败：{message}")
    
    def on_auto_finished(self, success: bool, message: str, output_files: Dict[str, Dict]):
        """自动分类完成处理"""
        self.progress_bar.setVisible(False)
        self.auto_start_btn.setEnabled(True)
        self.status_label.setText("就绪")
        
        if success:
            result_text = f"自动分类成功！\n\n生成的文件:\n"
            total_words = 0
            
            for pattern_name, file_info in output_files.items():
                result_text += f"• {pattern_name}: {file_info['count']} 个词条\n"
                result_text += f"  文件: {Path(file_info['file']).name}\n\n"
                total_words += file_info['count']
            
            result_text += f"总计处理: {total_words} 个词条"
            
            self.auto_result_text.setPlainText(result_text)
            QMessageBox.information(self, "自动分类成功", f"成功分类 {len(output_files)} 个类别")
            self.status_message.emit(f"自动分类完成：生成 {len(output_files)} 个文件")
        else:
            self.auto_result_text.setPlainText(f"自动分类失败：{message}")
            QMessageBox.critical(self, "自动分类失败", message)
            self.status_message.emit(f"自动分类失败：{message}")
    
    def on_merge_finished(self, success: bool, message: str, result: Dict):
        """合并完成处理"""
        self.progress_bar.setVisible(False)
        self.merge_start_btn.setEnabled(True)
        self.status_label.setText("就绪")
        
        if success:
            result_text = f"字典合并成功！\n\n"
            result_text += f"合并文件数: {result['files_merged']} 个\n"
            result_text += f"原始词条数: {result['original_count']} 个\n"
            result_text += f"最终词条数: {result['final_count']} 个\n"
            result_text += f"去重词条数: {result['duplicate_count']} 个\n"
            result_text += f"去重率: {result['duplicate_count']/result['original_count']*100:.1f}%\n\n"
            result_text += f"输出文件: {Path(result['output_file']).name}"
            
            self.merge_result_text.setPlainText(result_text)
            
            # 显示详细信息
            info_message = f"合并完成！\n\n"
            info_message += f"• 合并了 {result['files_merged']} 个文件\n"
            info_message += f"• 原始词条: {result['original_count']} 个\n"
            info_message += f"• 最终词条: {result['final_count']} 个\n"
            info_message += f"• 去重: {result['duplicate_count']} 个 ({result['duplicate_count']/result['original_count']*100:.1f}%)"
            
            QMessageBox.information(self, "合并成功", info_message)
            self.status_message.emit(f"合并完成：去重 {result['duplicate_count']} 个词条")
        else:
            self.merge_result_text.setPlainText(f"合并失败：{message}")
            QMessageBox.critical(self, "合并失败", message)
            self.status_message.emit(f"合并失败：{message}")


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = BigDictionaryWidget()
    widget.show()
    sys.exit(app.exec())