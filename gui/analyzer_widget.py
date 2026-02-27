"""
分析功能界面模块
提供基于正则表达式的字典分析和筛选功能
"""
import logging
from typing import List, Dict, Any, Optional, Set
import json
import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QFileDialog,
    QDialog, QDialogButtonBox, QTextEdit, QComboBox,
    QGroupBox, QCheckBox, QSpinBox, QProgressBar,
    QTabWidget, QHeaderView, QAbstractItemView, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QTimer
from PyQt6.QtGui import QFont, QPalette

from core.dictionary_manager import dictionary_manager
from utils.regex_helper import regex_helper
from config.settings import THEME_COLORS


class SimilarityAnalysisWorker(QThread):
    """相似性分析工作线程"""
    progress = pyqtSignal(int, str)
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, dict1_id: int, dict2_id: int, algorithm: str):
        super().__init__()
        self.dict1_id = dict1_id
        self.dict2_id = dict2_id
        self.algorithm = algorithm
    
    def run(self):
        try:
            self.progress.emit(10, "获取字典数据...")
            
            # 获取两个字典的词条
            words1_data = dictionary_manager.get_words(self.dict1_id, limit=None)
            words2_data = dictionary_manager.get_words(self.dict2_id, limit=None)
            
            words1 = set(word['word'] for word in words1_data)
            words2 = set(word['word'] for word in words2_data)
            
            self.progress.emit(30, "计算相似度...")
            
            if self.algorithm == "Jaccard相似度":
                similarity = self.calculate_jaccard_similarity(words1, words2)
            elif self.algorithm == "余弦相似度":
                similarity = self.calculate_cosine_similarity(words1, words2)
            else:  # 编辑距离相似度
                similarity = self.calculate_edit_distance_similarity(words1, words2)
            
            self.progress.emit(80, "生成分析报告...")
            
            # 计算交集和差集
            intersection = words1 & words2
            only_in_dict1 = words1 - words2
            only_in_dict2 = words2 - words1
            
            result = {
                'similarity': similarity,
                'algorithm': self.algorithm,
                'dict1_size': len(words1),
                'dict2_size': len(words2),
                'intersection_size': len(intersection),
                'only_in_dict1_size': len(only_in_dict1),
                'only_in_dict2_size': len(only_in_dict2),
                'intersection': list(intersection)[:100],  # 只返回前100个交集词条
                'only_in_dict1': list(only_in_dict1)[:100],
                'only_in_dict2': list(only_in_dict2)[:100]
            }
            
            self.progress.emit(100, "分析完成")
            self.result_ready.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def calculate_jaccard_similarity(self, set1: set, set2: set) -> float:
        """计算Jaccard相似度"""
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def calculate_cosine_similarity(self, set1: set, set2: set) -> float:
        """计算余弦相似度"""
        intersection = len(set1 & set2)
        magnitude1 = len(set1) ** 0.5
        magnitude2 = len(set2) ** 0.5
        return intersection / (magnitude1 * magnitude2) if magnitude1 > 0 and magnitude2 > 0 else 0.0
    
    def calculate_edit_distance_similarity(self, set1: set, set2: set) -> float:
        """计算基于编辑距离的相似度（简化版本）"""
        # 这里使用集合差异作为编辑距离的近似
        symmetric_diff = len(set1 ^ set2)  # 对称差集
        total_size = len(set1 | set2)
        return 1.0 - (symmetric_diff / total_size) if total_size > 0 else 0.0


class RegexAnalysisWorker(QThread):
    """正则表达式分析工作线程"""
    progress = pyqtSignal(int, str)
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, dictionary_id: int, patterns: List[Dict[str, str]], full_analysis: bool = False, concurrency: int = 1):
        super().__init__()
        self.dictionary_id = dictionary_id
        self.patterns = patterns  # 现在是包含name和pattern的字典列表
        self.full_analysis = full_analysis  # 是否全量分析
        self.concurrency = concurrency  # 并发数
    
    def run(self):
        try:
            self.progress.emit(10, "获取字典数据...")
            
            # 获取字典中的词条，根据是否全量分析决定数量
            if self.full_analysis:
                words_data = dictionary_manager.get_words(self.dictionary_id, limit=None)  # 获取所有数据
                self.progress.emit(15, f"获取到 {len(words_data)} 条数据，开始全量分析...")
            else:
                words_data = dictionary_manager.get_words(self.dictionary_id, limit=1000)  # 限制1000条
                self.progress.emit(15, f"获取到前 {len(words_data)} 条数据，开始快速分析...")
            
            words = [word['word'] for word in words_data]
            
            if not words:
                self.result_ready.emit({'matches': [], 'total_words': 0})
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
            
            # 执行匹配 - 支持并发处理
            matches = []
            unmatched_words = []
            total_words = len(words)
            
            if self.full_analysis and self.concurrency > 1:
                # 全量分析时使用并发处理
                matches, unmatched_words = self._process_with_concurrency(words, compiled_patterns, total_words)
            else:
                # 快速分析或单线程处理
                matches, unmatched_words = self._process_sequential(words, compiled_patterns, total_words)
            
            self.progress.emit(100, "分析完成")
            
            result = {
                'matches': matches,
                'unmatched_words': unmatched_words,
                'total_words': total_words,
                'matched_words': len(matches),
                'patterns': [p['name'] for p in self.patterns],
                'full_analysis': self.full_analysis
            }
            
            self.result_ready.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _process_sequential(self, words, compiled_patterns, total_words):
        """顺序处理词条"""
        matches = []
        unmatched_words = []
        
        for i, word in enumerate(words):
            word_matches = []
            for pattern_name, compiled_pattern in compiled_patterns:
                if compiled_pattern.search(word):
                    word_matches.append(pattern_name)
            
            if word_matches:
                matches.append({
                    'word': word,
                    'patterns': word_matches,
                    'selected': False  # 默认未选中
                })
            else:
                unmatched_words.append(word)
            
            # 更新进度
            if i % 100 == 0:
                progress = 50 + int((i / total_words) * 40)
                self.progress.emit(progress, f"分析中... {i}/{total_words}")
        
        return matches, unmatched_words
    
    def _process_with_concurrency(self, words, compiled_patterns, total_words):
        """并发处理词条"""
        import concurrent.futures
        import threading
        
        matches = []
        unmatched_words = []
        matches_lock = threading.Lock()
        unmatched_lock = threading.Lock()
        processed_count = 0
        count_lock = threading.Lock()
        
        def process_chunk(word_chunk):
            chunk_matches = []
            chunk_unmatched = []
            
            for word in word_chunk:
                word_matches = []
                for pattern_name, compiled_pattern in compiled_patterns:
                    if compiled_pattern.search(word):
                        word_matches.append(pattern_name)
                
                if word_matches:
                    chunk_matches.append({
                        'word': word,
                        'patterns': word_matches,
                        'selected': False
                    })
                else:
                    chunk_unmatched.append(word)
            
            # 更新全局结果
            with matches_lock:
                matches.extend(chunk_matches)
            
            with unmatched_lock:
                unmatched_words.extend(chunk_unmatched)
            
            # 更新进度
            nonlocal processed_count
            with count_lock:
                processed_count += len(word_chunk)
                if processed_count % 500 == 0:
                    progress = 50 + int((processed_count / total_words) * 40)
                    self.progress.emit(progress, f"并发分析中... {processed_count}/{total_words}")
        
        # 将词条分块
        chunk_size = max(100, total_words // (self.concurrency * 4))
        word_chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
        
        # 使用线程池执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = [executor.submit(process_chunk, chunk) for chunk in word_chunks]
            concurrent.futures.wait(futures)
        
        return matches, unmatched_words


class AnalyzerWidget(QWidget):
    """分析功能组件 - 重新设计为基于正则匹配和选择导出"""
    
    # 信号定义
    status_message = pyqtSignal(str)
    progress_update = pyqtSignal(int, str)
    
    def __init__(self):
        """初始化分析组件"""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 组件引用
        self.dictionary_combo = None
        self.pattern_list = None
        self.results_table = None
        self.current_matches = []
        self.selected_words = set()
        self.pattern_data = []  # 存储模式数据（包含名称和正则表达式）
        self.unmatched_words = []  # 存储未匹配的词条
        
        # 工作线程
        self.analysis_worker = None
        
        self.setup_ui()
        self.connect_signals()
        self.refresh_data()
    
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 顶部控制面板
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：正则表达式设置
        left_panel = self.create_pattern_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：匹配结果
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setSizes([300, 700])
        main_layout.addWidget(splitter)
        
        
        # 底部状态栏
        status_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        main_layout.addLayout(status_layout)
    
    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QGroupBox("分析设置")
        layout = QVBoxLayout(panel)
        
        # 第一行：字典选择和分析类型
        first_row = QHBoxLayout()
        
        # 字典选择
        first_row.addWidget(QLabel("选择字典:"))
        self.dictionary_combo = QComboBox()
        self.dictionary_combo.setMinimumWidth(200)
        first_row.addWidget(self.dictionary_combo)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_dictionaries)
        first_row.addWidget(refresh_btn)
        
        # 分析类型选择
        first_row.addWidget(QLabel("分析类型:"))
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems(["正则匹配分析", "字典相似性分析"])
        self.analysis_type_combo.currentTextChanged.connect(self.on_analysis_type_changed)
        first_row.addWidget(self.analysis_type_combo)
        
        first_row.addStretch()
        layout.addLayout(first_row)
        
        # 第二行：正则匹配分析设置
        self.regex_settings_widget = QWidget()
        regex_layout = QHBoxLayout(self.regex_settings_widget)
        regex_layout.setContentsMargins(0, 0, 0, 0)
        
        # 分析模式选择
        regex_layout.addWidget(QLabel("分析模式:"))
        self.analysis_mode_combo = QComboBox()
        self.analysis_mode_combo.addItems(["快速分析(1K条)", "全量分析"])
        regex_layout.addWidget(self.analysis_mode_combo)
        
        # 并发数设置
        regex_layout.addWidget(QLabel("并发数:"))
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setMinimum(1)
        self.concurrency_spin.setMaximum(16)
        self.concurrency_spin.setValue(4)
        self.concurrency_spin.setEnabled(False)  # 默认禁用，只有全量分析时启用
        regex_layout.addWidget(self.concurrency_spin)
        
        regex_layout.addStretch()
        layout.addWidget(self.regex_settings_widget)
        
        # 第三行：相似性分析设置
        self.similarity_settings_widget = QWidget()
        similarity_layout = QHBoxLayout(self.similarity_settings_widget)
        similarity_layout.setContentsMargins(0, 0, 0, 0)
        
        similarity_layout.addWidget(QLabel("对比字典:"))
        self.compare_dictionary_combo = QComboBox()
        self.compare_dictionary_combo.setMinimumWidth(200)
        similarity_layout.addWidget(self.compare_dictionary_combo)
        
        # 相似度算法选择
        similarity_layout.addWidget(QLabel("算法:"))
        self.similarity_algorithm_combo = QComboBox()
        self.similarity_algorithm_combo.addItems(["Jaccard相似度", "余弦相似度", "编辑距离相似度"])
        similarity_layout.addWidget(self.similarity_algorithm_combo)
        
        similarity_layout.addStretch()
        layout.addWidget(self.similarity_settings_widget)
        
        # 默认隐藏相似性分析设置
        self.similarity_settings_widget.setVisible(False)
        
        # 第四行：操作按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 分析按钮
        self.analyze_btn = QPushButton("🔍 开始分析")
        self.analyze_btn.clicked.connect(self.start_analysis)
        button_layout.addWidget(self.analyze_btn)
        
        # 导出选中按钮
        self.export_selected_btn = QPushButton("💾 导出选中")
        self.export_selected_btn.clicked.connect(self.export_selected_words)
        self.export_selected_btn.setEnabled(False)
        button_layout.addWidget(self.export_selected_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def create_pattern_panel(self) -> QWidget:
        """创建正则表达式设置面板"""
        panel = QGroupBox("正则表达式设置")
        layout = QVBoxLayout(panel)
        
        # 预设模式选择
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("预设模式:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "选择预设...",
            "中文字符",
            "英文字符", 
            "数字",
            "特殊字符",
            "邮箱格式",
            "网址格式",
            "电话号码",
            "IP地址",
            "身份证号"
        ])
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)
        
        # 自定义模式输入
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("自定义模式:"))
        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText("输入正则表达式...")
        custom_layout.addWidget(self.pattern_edit)
        
        add_pattern_btn = QPushButton("➕")
        add_pattern_btn.clicked.connect(self.add_custom_pattern)
        custom_layout.addWidget(add_pattern_btn)
        layout.addLayout(custom_layout)
        
        # 已添加的模式列表
        layout.addWidget(QLabel("已添加的模式:"))
        self.pattern_list = QListWidget()
        self.pattern_list.setMaximumHeight(200)
        layout.addWidget(self.pattern_list)
        
        # 模式操作按钮
        pattern_btn_layout = QHBoxLayout()
        
        remove_pattern_btn = QPushButton("➖ 移除")
        remove_pattern_btn.clicked.connect(self.remove_pattern)
        pattern_btn_layout.addWidget(remove_pattern_btn)
        
        clear_patterns_btn = QPushButton("🗑️ 清空")
        clear_patterns_btn.clicked.connect(self.clear_patterns)
        pattern_btn_layout.addWidget(clear_patterns_btn)
        
        pattern_btn_layout.addStretch()
        layout.addLayout(pattern_btn_layout)
        
        # 从配置加载预设模式
        load_presets_btn = QPushButton("📁 加载预设")
        load_presets_btn.clicked.connect(self.load_preset_patterns)
        layout.addWidget(load_presets_btn)
        
        return panel
    
    def create_results_panel(self) -> QWidget:
        """创建结果面板"""
        panel = QGroupBox("匹配结果")
        layout = QVBoxLayout(panel)
        
        # 结果统计
        stats_layout = QHBoxLayout()
        self.total_words_label = QLabel("总词条: 0")
        self.matched_words_label = QLabel("匹配词条: 0")
        self.selected_words_label = QLabel("已选中: 0")
        
        stats_layout.addWidget(self.total_words_label)
        stats_layout.addWidget(self.matched_words_label)
        stats_layout.addWidget(self.selected_words_label)
        stats_layout.addStretch()
        
        # 批量操作按钮
        select_all_btn = QPushButton("✅ 全选")
        select_all_btn.clicked.connect(self.select_all_matches)
        stats_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("❌ 全不选")
        select_none_btn.clicked.connect(self.select_none_matches)
        stats_layout.addWidget(select_none_btn)
        
        layout.addLayout(stats_layout)
        
        # 未匹配词条显示区域
        unmatched_group = QGroupBox("未匹配词条")
        unmatched_layout = QVBoxLayout(unmatched_group)
        
        # 未匹配词条说明
        unmatched_info = QLabel("以下词条未被任何正则表达式匹配，可用于设置新的正则表达式:")
        unmatched_layout.addWidget(unmatched_info)
        
        # 未匹配词条列表
        self.unmatched_list = QListWidget()
        self.unmatched_list.setMaximumHeight(120)
        unmatched_layout.addWidget(self.unmatched_list)
        
        # 导出未匹配词条按钮
        export_unmatched_btn = QPushButton("💾 导出未匹配词条")
        export_unmatched_btn.clicked.connect(self.export_unmatched_words)
        unmatched_layout.addWidget(export_unmatched_btn)
        
        layout.addWidget(unmatched_group)
        
        # 相似性分析结果区域
        self.similarity_result_group = QGroupBox("相似性分析结果")
        similarity_result_layout = QVBoxLayout(self.similarity_result_group)
        
        self.similarity_result_label = QLabel("相似度: 未分析")
        self.similarity_result_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        similarity_result_layout.addWidget(self.similarity_result_label)
        
        self.similarity_details_text = QTextEdit()
        self.similarity_details_text.setMaximumHeight(100)
        self.similarity_details_text.setReadOnly(True)
        similarity_result_layout.addWidget(self.similarity_details_text)
        
        layout.addWidget(self.similarity_result_group)
        
        # 默认隐藏相似性分析结果
        self.similarity_result_group.setVisible(False)
        
        # 结果表格
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["选择", "词条", "匹配模式"])
        
        # 设置列宽
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # 设置表格属性
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSortingEnabled(True)
        
        layout.addWidget(self.results_table)
        
        return panel
    
    def connect_signals(self):
        """连接信号"""
        self.dictionary_combo.currentTextChanged.connect(self.on_dictionary_changed)
        self.results_table.cellChanged.connect(self.on_cell_changed)
        self.analysis_mode_combo.currentTextChanged.connect(self.on_analysis_mode_changed)
        
        # 刷新对比字典列表
        self.dictionary_combo.currentTextChanged.connect(self.refresh_compare_dictionaries)
    
    def refresh_data(self):
        """刷新数据"""
        self.load_dictionaries()
    
    def load_dictionaries(self):
        """加载字典列表"""
        try:
            self.dictionary_combo.clear()
            self.dictionary_combo.addItem("请选择字典...", None)
            
            dictionaries = dictionary_manager.get_all_dictionaries()
            
            for dictionary in dictionaries:
                self.dictionary_combo.addItem(
                    f"{dictionary['name']} ({dictionary.get('word_count', 0)} 词条)",
                    dictionary['id']
                )
            
        except Exception as e:
            self.logger.error(f"加载字典列表失败: {e}")
    
    def refresh_compare_dictionaries(self):
        """刷新对比字典列表"""
        try:
            current_dict_id = self.dictionary_combo.currentData()
            self.compare_dictionary_combo.clear()
            self.compare_dictionary_combo.addItem("请选择对比字典...", None)
            
            dictionaries = dictionary_manager.get_all_dictionaries()
            
            for dictionary in dictionaries:
                # 排除当前选中的字典
                if dictionary['id'] != current_dict_id:
                    self.compare_dictionary_combo.addItem(
                        f"{dictionary['name']} ({dictionary.get('word_count', 0)} 词条)",
                        dictionary['id']
                    )
            
        except Exception as e:
            self.logger.error(f"加载对比字典列表失败: {e}")
    
    def on_analysis_type_changed(self):
        """分析类型变化"""
        analysis_type = self.analysis_type_combo.currentText()
        
        if analysis_type == "正则匹配分析":
            self.regex_settings_widget.setVisible(True)
            self.similarity_settings_widget.setVisible(False)
            self.similarity_result_group.setVisible(False)
        else:  # 字典相似性分析
            self.regex_settings_widget.setVisible(False)
            self.similarity_settings_widget.setVisible(True)
            self.similarity_result_group.setVisible(True)
            self.refresh_compare_dictionaries()
    
    def on_dictionary_changed(self):
        """字典选择变化"""
        dictionary_id = self.dictionary_combo.currentData()
        self.analyze_btn.setEnabled(dictionary_id is not None)
        
        # 清空之前的结果
        self.clear_results()
    
    def on_analysis_mode_changed(self):
        """分析模式变化"""
        is_full_analysis = self.analysis_mode_combo.currentText() == "全量分析"
        self.concurrency_spin.setEnabled(is_full_analysis)
    
    def refresh_dictionaries(self):
        """刷新字典列表"""
        current_dict_id = self.dictionary_combo.currentData()
        self.load_dictionaries()
        
        # 尝试恢复之前选中的字典
        if current_dict_id:
            for i in range(self.dictionary_combo.count()):
                if self.dictionary_combo.itemData(i) == current_dict_id:
                    self.dictionary_combo.setCurrentIndex(i)
                    break
        
        self.status_message.emit("字典列表已刷新")
    
    def on_preset_changed(self):
        """预设模式变化"""
        preset = self.preset_combo.currentText()
        
        pattern_map = {
            "中文字符": r"[\u4e00-\u9fff]+",
            "英文字符": r"[a-zA-Z]+",
            "数字": r"\d+",
            "特殊字符": r"[^\w\s]+",
            "邮箱格式": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "网址格式": r"https?://[^\s]+",
            "电话号码": r"1[3-9]\d{9}",
            "IP地址": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
            "身份证号": r"\b\d{17}[\dXx]\b"
        }
        
        if preset in pattern_map:
            self.pattern_edit.setText(pattern_map[preset])
    
    def add_custom_pattern(self):
        """添加自定义模式"""
        pattern = self.pattern_edit.text().strip()
        if not pattern:
            return
        
        # 验证正则表达式
        try:
            re.compile(pattern)
        except re.error as e:
            QMessageBox.warning(self, "警告", f"无效的正则表达式: {str(e)}")
            return
        
        # 检查是否已存在
        for pattern_info in self.pattern_data:
            if pattern_info['pattern'] == pattern:
                QMessageBox.information(self, "提示", "该模式已存在")
                return
        
        # 生成自定义模式名称
        custom_name = f"自定义模式{len([p for p in self.pattern_data if p['name'].startswith('自定义模式')]) + 1}"
        
        # 添加到数据和列表
        pattern_info = {'name': custom_name, 'pattern': pattern}
        self.pattern_data.append(pattern_info)
        
        item = QListWidgetItem(custom_name)
        item.setToolTip(f"正则表达式: {pattern}")
        self.pattern_list.addItem(item)
        
        self.pattern_edit.clear()
    
    def remove_pattern(self):
        """移除选中的模式"""
        current_row = self.pattern_list.currentRow()
        if current_row >= 0:
            # 同时从数据列表中移除
            if current_row < len(self.pattern_data):
                self.pattern_data.pop(current_row)
            self.pattern_list.takeItem(current_row)
    
    def clear_patterns(self):
        """清空所有模式"""
        self.pattern_list.clear()
        self.pattern_data.clear()
    
    def load_preset_patterns(self):
        """从配置文件加载预设模式"""
        try:
            pattern_names = regex_helper.get_all_pattern_names()
            
            if not pattern_names:
                QMessageBox.information(self, "提示", "没有找到预设模式")
                return
            
            # 显示选择对话框
            dialog = PresetSelectionDialog(pattern_names, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_patterns = dialog.get_selected_patterns()
                
                for pattern_name in selected_patterns:
                    pattern_info = regex_helper.get_pattern_info(pattern_name)
                    if pattern_info and 'pattern' in pattern_info:
                        # 检查是否已存在
                        pattern = pattern_info['pattern']
                        exists = False
                        for existing_pattern in self.pattern_data:
                            if existing_pattern['pattern'] == pattern:
                                exists = True
                                break
                        
                        if not exists:
                            # 添加到数据列表
                            new_pattern_data = {
                                'name': pattern_name,
                                'pattern': pattern
                            }
                            self.pattern_data.append(new_pattern_data)
                            
                            # 添加到界面列表，显示名称而不是正则表达式
                            item = QListWidgetItem(pattern_name)
                            item.setToolTip(f"正则表达式: {pattern}\n描述: {pattern_info.get('description', '无描述')}")
                            self.pattern_list.addItem(item)
                
                self.status_message.emit(f"已加载 {len(selected_patterns)} 个预设模式")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载预设模式失败: {str(e)}")
    
    def start_analysis(self):
        """开始分析"""
        dictionary_id = self.dictionary_combo.currentData()
        if not dictionary_id:
            QMessageBox.warning(self, "警告", "请先选择字典")
            return
        
        analysis_type = self.analysis_type_combo.currentText()
        
        if analysis_type == "正则匹配分析":
            self.start_regex_analysis(dictionary_id)
        else:  # 字典相似性分析
            self.start_similarity_analysis(dictionary_id)
    
    def start_regex_analysis(self, dictionary_id: int):
        """开始正则匹配分析"""
        # 获取所有模式数据
        if not self.pattern_data:
            QMessageBox.warning(self, "警告", "请先添加要分析的正则表达式模式")
            return
        
        # 获取分析参数
        is_full_analysis = self.analysis_mode_combo.currentText() == "全量分析"
        concurrency = self.concurrency_spin.value() if is_full_analysis else 1
        
        # 启动分析工作线程
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.terminate()
            self.analysis_worker.wait()
        
        self.analysis_worker = RegexAnalysisWorker(dictionary_id, self.pattern_data, is_full_analysis, concurrency)
        self.analysis_worker.progress.connect(self.update_progress)
        self.analysis_worker.result_ready.connect(self.on_analysis_finished)
        self.analysis_worker.error_occurred.connect(self.on_analysis_error)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.analyze_btn.setEnabled(False)
        self.status_label.setText("分析中...")
        
        self.analysis_worker.start()
    
    def start_similarity_analysis(self, dictionary_id: int):
        """开始相似性分析"""
        compare_dict_id = self.compare_dictionary_combo.currentData()
        if not compare_dict_id:
            QMessageBox.warning(self, "警告", "请先选择对比字典")
            return
        
        algorithm = self.similarity_algorithm_combo.currentText()
        
        # 启动相似性分析工作线程
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.terminate()
            self.analysis_worker.wait()
        
        self.analysis_worker = SimilarityAnalysisWorker(dictionary_id, compare_dict_id, algorithm)
        self.analysis_worker.progress.connect(self.update_progress)
        self.analysis_worker.result_ready.connect(self.on_similarity_analysis_finished)
        self.analysis_worker.error_occurred.connect(self.on_analysis_error)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.analyze_btn.setEnabled(False)
        self.status_label.setText("相似性分析中...")
        
        self.analysis_worker.start()
    
    @pyqtSlot(int, str)
    def update_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    @pyqtSlot(dict)
    def on_analysis_finished(self, result: dict):
        """分析完成处理"""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.status_label.setText("分析完成")
        
        # 保存结果
        self.current_matches = result['matches']
        self.unmatched_words = result.get('unmatched_words', [])
        self.selected_words.clear()
        
        # 显示结果
        self.display_results(result)
        
        # 显示未匹配词条
        self.display_unmatched_words()
        
        self.status_message.emit(f"分析完成：找到 {result['matched_words']} 个匹配词条，{len(self.unmatched_words)} 个未匹配词条")
    
    @pyqtSlot(dict)
    def on_similarity_analysis_finished(self, result: dict):
        """相似性分析完成处理"""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.status_label.setText("相似性分析完成")
        
        # 显示相似性分析结果
        self.display_similarity_results(result)
        
        self.status_message.emit(f"相似性分析完成：相似度 {result['similarity']:.2%}")
    
    def display_unmatched_words(self):
        """显示未匹配的词条"""
        self.unmatched_list.clear()
        
        # 只显示前100个未匹配词条，避免界面卡顿
        display_count = min(100, len(self.unmatched_words))
        for i in range(display_count):
            word = self.unmatched_words[i]
            self.unmatched_list.addItem(word)
        
        # 如果有更多未匹配词条，添加提示
        if len(self.unmatched_words) > 100:
            self.unmatched_list.addItem(f"... 还有 {len(self.unmatched_words) - 100} 个未匹配词条")
    
    def display_similarity_results(self, result: dict):
        """显示相似性分析结果"""
        similarity = result['similarity']
        algorithm = result['algorithm']
        
        # 更新相似度标签
        self.similarity_result_label.setText(f"相似度: {similarity:.2%} ({algorithm})")
        
        # 生成详细报告
        details = []
        details.append(f"算法: {algorithm}")
        details.append(f"字典1大小: {result['dict1_size']} 词条")
        details.append(f"字典2大小: {result['dict2_size']} 词条")
        details.append(f"交集: {result['intersection_size']} 词条")
        details.append(f"仅在字典1: {result['only_in_dict1_size']} 词条")
        details.append(f"仅在字典2: {result['only_in_dict2_size']} 词条")
        
        if result.get('intersection'):
            details.append(f"\n交集示例 (前10个):")
            for word in result['intersection'][:10]:
                details.append(f"  - {word}")
        
        self.similarity_details_text.setText('\n'.join(details))
    
    def export_unmatched_words(self):
        """导出未匹配的词条"""
        if not self.unmatched_words:
            QMessageBox.warning(self, "警告", "没有未匹配的词条可导出")
            return
        
        # 选择导出路径
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "导出未匹配词条", "unmatched_words.txt",
            "文本文件 (*.txt);;JSON文件 (*.json);;CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            # 根据文件扩展名确定格式
            if file_path.endswith('.json'):
                self.export_unmatched_as_json(file_path)
            elif file_path.endswith('.csv'):
                self.export_unmatched_as_csv(file_path)
            else:
                self.export_unmatched_as_txt(file_path)
            
            QMessageBox.information(self, "导出成功", f"已导出 {len(self.unmatched_words)} 个未匹配词条到:\n{file_path}")
            self.status_message.emit(f"已导出 {len(self.unmatched_words)} 个未匹配词条")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出失败: {str(e)}")
    
    def export_unmatched_as_txt(self, file_path: str):
        """导出未匹配词条为文本文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for word in sorted(self.unmatched_words):
                f.write(word + '\n')
    
    def export_unmatched_as_json(self, file_path: str):
        """导出未匹配词条为JSON文件"""
        import json
        from datetime import datetime
        
        export_data = {
            'dictionary': self.dictionary_combo.currentText(),
            'export_time': datetime.now().isoformat(),
            'total_unmatched': len(self.unmatched_words),
            'unmatched_words': sorted(self.unmatched_words)
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def export_unmatched_as_csv(self, file_path: str):
        """导出未匹配词条为CSV文件"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['未匹配词条'])
            
            for word in sorted(self.unmatched_words):
                writer.writerow([word])
    
    @pyqtSlot(str)
    def on_analysis_error(self, error_message: str):
        """分析错误处理"""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.status_label.setText("分析失败")
        
        QMessageBox.critical(self, "分析错误", f"分析失败: {error_message}")
        self.status_message.emit(f"分析失败: {error_message}")
    
    def display_results(self, result: dict):
        """显示分析结果"""
        matches = result['matches']
        
        # 更新统计信息
        analysis_type = "全量分析" if result.get('full_analysis', False) else "快速分析(1K条)"
        self.total_words_label.setText(f"总词条: {result['total_words']} ({analysis_type})")
        self.matched_words_label.setText(f"匹配词条: {result['matched_words']}")
        self.update_selected_count()
        
        # 填充结果表格
        self.results_table.setRowCount(len(matches))
        
        for row, match_data in enumerate(matches):
            # 选择复选框
            checkbox = QCheckBox()
            checkbox.setChecked(match_data['selected'])
            checkbox.stateChanged.connect(lambda state, word=match_data['word']: self.on_checkbox_changed(word, state))
            self.results_table.setCellWidget(row, 0, checkbox)
            
            # 词条
            word_item = QTableWidgetItem(match_data['word'])
            word_item.setFlags(word_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 1, word_item)
            
            # 匹配的模式
            patterns_text = ", ".join(match_data['patterns'])
            pattern_item = QTableWidgetItem(patterns_text)
            pattern_item.setFlags(pattern_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 2, pattern_item)
        
        # 启用导出按钮
        self.export_selected_btn.setEnabled(True)
    
    def on_checkbox_changed(self, word: str, state: int):
        """复选框状态变化"""
        if state == Qt.CheckState.Checked.value:
            self.selected_words.add(word)
        else:
            self.selected_words.discard(word)
        
        self.update_selected_count()
    
    def on_cell_changed(self, row: int, column: int):
        """表格单元格变化"""
        # 这里可以处理其他单元格变化
        pass
    
    def update_selected_count(self):
        """更新选中数量"""
        self.selected_words_label.setText(f"已选中: {len(self.selected_words)}")
    
    def select_all_matches(self):
        """全选匹配结果"""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def select_none_matches(self):
        """全不选匹配结果"""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def export_selected_words(self):
        """导出选中的词条"""
        if not self.selected_words:
            QMessageBox.warning(self, "警告", "请先选择要导出的词条")
            return
        
        # 选择导出格式和路径
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "导出选中词条", "selected_words.txt",
            "文本文件 (*.txt);;JSON文件 (*.json);;CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            # 根据文件扩展名确定格式
            if file_path.endswith('.json'):
                self.export_as_json(file_path)
            elif file_path.endswith('.csv'):
                self.export_as_csv(file_path)
            else:
                self.export_as_txt(file_path)
            
            QMessageBox.information(self, "导出成功", f"已导出 {len(self.selected_words)} 个词条到:\n{file_path}")
            self.status_message.emit(f"已导出 {len(self.selected_words)} 个词条")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出失败: {str(e)}")
    
    def export_as_txt(self, file_path: str):
        """导出为文本文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for word in sorted(self.selected_words):
                f.write(word + '\n')
    
    def export_as_json(self, file_path: str):
        """导出为JSON文件"""
        # 获取选中词条的详细信息
        selected_data = []
        for match_data in self.current_matches:
            if match_data['word'] in self.selected_words:
                selected_data.append(match_data)
        
        export_data = {
            'dictionary': self.dictionary_combo.currentText(),
            'export_time': QTimer().currentTime().toString(),
            'total_selected': len(self.selected_words),
            'words': selected_data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def export_as_csv(self, file_path: str):
        """导出为CSV文件"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['词条', '匹配模式'])
            
            for match_data in self.current_matches:
                if match_data['word'] in self.selected_words:
                    patterns_text = ", ".join(match_data['patterns'])
                    writer.writerow([match_data['word'], patterns_text])
    
    def clear_results(self):
        """清空结果"""
        self.current_matches = []
        self.selected_words.clear()
        self.results_table.setRowCount(0)
        self.total_words_label.setText("总词条: 0")
        self.matched_words_label.setText("匹配词条: 0")
        self.selected_words_label.setText("已选中: 0")
        self.export_selected_btn.setEnabled(False)
        
        # 清空未匹配词条
        if hasattr(self, 'unmatched_list'):
            self.unmatched_list.clear()
        self.unmatched_words = []
    
    def clear_pattern_buttons(self):
        """清空模式按钮（已删除的功能，保留空方法避免错误）"""
        pass
    
    def update_pattern_buttons(self, result: dict):
        """更新模式按钮（已删除的功能，保留空方法避免错误）"""
        pass
    
    def on_pattern_button_clicked(self, pattern_name: str, checked: bool):
        """模式按钮点击事件（已删除的功能，保留空方法避免错误）"""
        pass


class PresetSelectionDialog(QDialog):
    """预设模式选择对话框"""
    
    def __init__(self, pattern_names: List[str], parent=None):
        super().__init__(parent)
        self.pattern_names = pattern_names
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("选择预设模式")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("请选择要加载的预设模式:"))
        
        # 模式列表
        self.pattern_list = QListWidget()
        
        for pattern_name in self.pattern_names:
            item = QListWidgetItem(pattern_name)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.pattern_list.addItem(item)
        
        layout.addWidget(self.pattern_list)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("全不选")
        select_none_btn.clicked.connect(self.select_none)
        button_layout.addWidget(select_none_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 对话框按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def select_all(self):
        """全选"""
        for i in range(self.pattern_list.count()):
            item = self.pattern_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
    
    def select_none(self):
        """全不选"""
        for i in range(self.pattern_list.count()):
            item = self.pattern_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
    
    def get_selected_patterns(self) -> List[str]:
        """获取选中的模式"""
        selected = []
        for i in range(self.pattern_list.count()):
            item = self.pattern_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = AnalyzerWidget()
    widget.show()
    sys.exit(app.exec())