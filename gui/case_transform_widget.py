"""
随机大小写转换界面模块
提供多种大小写转换策略的图形界面
"""
import logging
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QProgressDialog, QMessageBox, QFileDialog,
    QComboBox, QSpinBox, QCheckBox, QSlider, QDoubleSpinBox,
    QSplitter, QHeaderView, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont

from core.case_transformer import case_transformer, CaseStrategy
from core.dictionary_manager import dictionary_manager


class CaseTransformWorker(QThread):
    """大小写转换工作线程"""
    progress = pyqtSignal(int, str)
    result_ready = pyqtSignal(list, int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, words: List[str], strategy: CaseStrategy, keep_original: bool, **kwargs):
        super().__init__()
        self.words = words
        self.strategy = strategy
        self.keep_original = keep_original
        self.kwargs = kwargs
    
    def run(self):
        try:
            self.progress.emit(10, "准备转换大小写...")
            
            total_words = len(self.words)
            if total_words == 0:
                self.result_ready.emit([], 0)
                return
            
            self.progress.emit(30, f"开始转换 {total_words} 个词条...")
            
            # 转换词条列表
            transformed_words = case_transformer.transform_word_list(
                self.words, self.strategy, self.keep_original, **self.kwargs
            )
            
            self.progress.emit(90, f"转换完成，共 {len(transformed_words)} 个词条")
            self.result_ready.emit(transformed_words, len(transformed_words))
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class CaseTransformWidget(QWidget):
    """随机大小写转换组件"""
    
    status_message = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 组件引用
        self.input_text = None
        self.dictionary_list = None
        self.strategy_combo = None
        self.result_table = None
        
        # 策略参数控件
        self.probability_slider = None
        self.probability_label = None
        self.start_upper_cb = None
        self.keep_original_cb = None
        self.variant_count_spin = None
        
        # 工作线程
        self.transform_worker = None
        
        # 当前结果
        self.current_results = []
        
        self.setup_ui()
        self.connect_signals()
        self.load_dictionaries()
    
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("🔤 随机大小写转换")
        title_label.setFont(QFont("", 14, QFont.Weight.Bold))
        main_layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上半部分：输入和配置
        config_widget = self.create_config_panel()
        splitter.addWidget(config_widget)
        
        # 下半部分：结果显示
        result_widget = self.create_result_panel()
        splitter.addWidget(result_widget)
        
        # 设置分割比例
        splitter.setSizes([400, 300])
        
        main_layout.addWidget(splitter)
    
    def create_config_panel(self) -> QWidget:
        """创建配置面板"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # 左侧：输入源
        input_widget = self.create_input_panel()
        layout.addWidget(input_widget)
        
        # 右侧：转换配置
        config_widget = self.create_transform_config_panel()
        layout.addWidget(config_widget)
        
        return widget
    
    def create_input_panel(self) -> QWidget:
        """创建输入面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 输入源选择
        source_group = QGroupBox("📝 输入源")
        source_layout = QVBoxLayout(source_group)
        
        # 文本输入
        source_layout.addWidget(QLabel("直接输入词条（每行一个）:"))
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("输入要转换的词条，每行一个\n例如:\nadmin\nuser_login\ntest-panel")
        self.input_text.setMaximumHeight(120)
        source_layout.addWidget(self.input_text)
        
        # 示例按钮
        example_btn = QPushButton("📝 填入示例")
        example_btn.clicked.connect(self.fill_example)
        source_layout.addWidget(example_btn)
        
        # 或者从字典选择
        source_layout.addWidget(QLabel("或从现有字典选择:"))
        self.dictionary_list = QListWidget()
        self.dictionary_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.dictionary_list.setMaximumHeight(100)
        source_layout.addWidget(self.dictionary_list)
        
        # 刷新字典按钮
        refresh_btn = QPushButton("🔄 刷新字典")
        refresh_btn.clicked.connect(self.load_dictionaries)
        source_layout.addWidget(refresh_btn)
        
        layout.addWidget(source_group)
        
        return widget
    
    def create_transform_config_panel(self) -> QWidget:
        """创建转换配置面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 转换策略
        strategy_group = QGroupBox("⚙️ 转换策略")
        strategy_layout = QVBoxLayout(strategy_group)
        
        strategy_layout.addWidget(QLabel("选择转换策略:"))
        self.strategy_combo = QComboBox()
        
        # 添加策略选项
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
            self.strategy_combo.addItem(description, strategy)
        
        self.strategy_combo.currentTextChanged.connect(self.on_strategy_changed)
        strategy_layout.addWidget(self.strategy_combo)
        
        layout.addWidget(strategy_group)
        
        # 策略参数
        param_group = QGroupBox("🎛️ 参数设置")
        param_layout = QVBoxLayout(param_group)
        
        # 概率设置（用于随机策略）
        prob_layout = QHBoxLayout()
        prob_layout.addWidget(QLabel("大写概率:"))
        
        self.probability_slider = QSlider(Qt.Orientation.Horizontal)
        self.probability_slider.setRange(0, 100)
        self.probability_slider.setValue(50)
        self.probability_slider.valueChanged.connect(self.update_probability_label)
        prob_layout.addWidget(self.probability_slider)
        
        self.probability_label = QLabel("50%")
        self.probability_label.setMinimumWidth(40)
        prob_layout.addWidget(self.probability_label)
        
        param_layout.addLayout(prob_layout)
        
        # 交替大小写起始设置
        self.start_upper_cb = QCheckBox("交替大小写从大写开始")
        self.start_upper_cb.setChecked(True)
        param_layout.addWidget(self.start_upper_cb)
        
        # 随机变体数量（用于随机策略）
        variant_layout = QHBoxLayout()
        variant_layout.addWidget(QLabel("随机变体数量:"))
        
        self.variant_count_spin = QSpinBox()
        self.variant_count_spin.setRange(1, 20)
        self.variant_count_spin.setValue(5)
        variant_layout.addWidget(self.variant_count_spin)
        variant_layout.addStretch()
        
        param_layout.addLayout(variant_layout)
        
        layout.addWidget(param_group)
        
        # 输出选项
        output_group = QGroupBox("📤 输出选项")
        output_layout = QVBoxLayout(output_group)
        
        self.keep_original_cb = QCheckBox("保留原始词条")
        self.keep_original_cb.setChecked(True)
        self.keep_original_cb.setToolTip("在结果中包含原始词条")
        output_layout.addWidget(self.keep_original_cb)
        
        layout.addWidget(output_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        transform_btn = QPushButton("🔄 开始转换")
        transform_btn.clicked.connect(self.transform_case)
        button_layout.addWidget(transform_btn)
        
        preview_btn = QPushButton("👁️ 预览效果")
        preview_btn.clicked.connect(self.preview_transform)
        button_layout.addWidget(preview_btn)
        
        layout.addLayout(button_layout)
        
        # 初始化参数显示
        self.on_strategy_changed()
        
        return widget
    
    def create_result_panel(self) -> QWidget:
        """创建结果面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题和统计
        header_layout = QHBoxLayout()
        
        result_title = QLabel("📋 转换结果")
        result_title.setFont(QFont("", 12, QFont.Weight.Bold))
        header_layout.addWidget(result_title)
        
        self.result_count_label = QLabel("词条数: 0")
        header_layout.addWidget(self.result_count_label)
        
        header_layout.addStretch()
        
        # 导出按钮
        export_btn = QPushButton("💾 导出结果")
        export_btn.clicked.connect(self.export_results)
        header_layout.addWidget(export_btn)
        
        # 保存到字典按钮
        save_to_dict_btn = QPushButton("📚 保存到字典")
        save_to_dict_btn.clicked.connect(self.save_to_dictionary)
        header_layout.addWidget(save_to_dict_btn)
        
        layout.addLayout(header_layout)
        
        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["序号", "转换结果"])
        
        # 设置表格属性
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.result_table)
        
        return widget
    
    def connect_signals(self):
        """连接信号"""
        pass
    
    def load_dictionaries(self):
        """加载字典列表"""
        try:
            self.dictionary_list.clear()
            dictionaries = dictionary_manager.get_all_dictionaries()
            
            for dictionary in dictionaries:
                item = QListWidgetItem()
                item.setText(f"{dictionary['name']} ({dictionary.get('word_count', 0)} 词条)")
                item.setData(Qt.ItemDataRole.UserRole, dictionary['id'])
                self.dictionary_list.addItem(item)
            
            self.status_message.emit(f"加载了 {len(dictionaries)} 个字典")
            
        except Exception as e:
            self.logger.error(f"加载字典列表失败: {e}")
            QMessageBox.critical(self, "错误", f"加载字典列表失败: {str(e)}")
    
    def fill_example(self):
        """填入示例"""
        example_text = """admin
user_login
test-panel
AdminDashboard
API_KEY
getUserInfo
create-new-user
DELETE_ALL_DATA"""
        
        self.input_text.setPlainText(example_text)
    
    def on_strategy_changed(self):
        """策略改变事件"""
        current_strategy = self.strategy_combo.currentData()
        
        # 根据策略显示/隐藏相关参数
        is_random_strategy = current_strategy in [
            CaseStrategy.RANDOM_CHAR, 
            CaseStrategy.RANDOM_WORD, 
            CaseStrategy.FIRST_LETTER
        ]
        
        # 概率设置只对随机策略有效
        self.probability_slider.setVisible(is_random_strategy)
        self.probability_label.setVisible(is_random_strategy)
        
        # 交替大小写起始设置只对交替策略有效
        self.start_upper_cb.setVisible(current_strategy == CaseStrategy.ALTERNATING)
        
        # 随机变体数量只对随机策略有效
        self.variant_count_spin.setVisible(is_random_strategy)
    
    def update_probability_label(self):
        """更新概率标签"""
        value = self.probability_slider.value()
        self.probability_label.setText(f"{value}%")
    
    def get_input_words(self) -> List[str]:
        """获取输入词条"""
        words = []
        
        # 从文本输入获取
        text_input = self.input_text.toPlainText().strip()
        if text_input:
            text_words = [line.strip() for line in text_input.split('\n') if line.strip()]
            words.extend(text_words)
        
        # 从选中的字典获取
        selected_items = self.dictionary_list.selectedItems()
        if selected_items:
            dictionary_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
            
            for dict_id in dictionary_ids:
                dict_words_data = dictionary_manager.get_words(dict_id, limit=None)
                dict_words = [word['word'] for word in dict_words_data]
                words.extend(dict_words)
        
        # 去重并返回
        return list(set(words))
    
    def preview_transform(self):
        """预览转换效果"""
        words = self.get_input_words()
        if not words:
            QMessageBox.warning(self, "警告", "请输入词条或选择字典")
            return
        
        # 只预览前5个词条
        preview_words = words[:5]
        strategy = self.strategy_combo.currentData()
        
        # 获取策略参数
        kwargs = self.get_strategy_params()
        
        try:
            preview_results = []
            
            for word in preview_words:
                if strategy in [CaseStrategy.RANDOM_CHAR, CaseStrategy.RANDOM_WORD, CaseStrategy.FIRST_LETTER]:
                    # 随机策略生成多个变体
                    variants = case_transformer.generate_random_variants(word, 3, strategy)
                    preview_results.append(f"{word} -> {variants}")
                else:
                    # 确定性策略只生成一个变体
                    variant = case_transformer.transform_text(word, strategy, **kwargs)
                    preview_results.append(f"{word} -> {variant}")
            
            preview_text = "\n".join(preview_results)
            if len(words) > 5:
                preview_text += f"\n... 还有 {len(words) - 5} 个词条"
            
            QMessageBox.information(self, "预览效果", f"转换预览:\n\n{preview_text}")
            
        except Exception as e:
            self.logger.error(f"预览转换失败: {e}")
            QMessageBox.critical(self, "错误", f"预览失败: {str(e)}")
    
    def get_strategy_params(self) -> Dict[str, Any]:
        """获取策略参数"""
        params = {}
        
        strategy = self.strategy_combo.currentData()
        
        if strategy in [CaseStrategy.RANDOM_CHAR, CaseStrategy.RANDOM_WORD, CaseStrategy.FIRST_LETTER]:
            params['probability'] = self.probability_slider.value() / 100.0
        
        if strategy == CaseStrategy.ALTERNATING:
            params['start_upper'] = self.start_upper_cb.isChecked()
        
        return params
    
    def transform_case(self):
        """转换大小写"""
        words = self.get_input_words()
        if not words:
            QMessageBox.warning(self, "警告", "请输入词条或选择字典")
            return
        
        strategy = self.strategy_combo.currentData()
        keep_original = self.keep_original_cb.isChecked()
        kwargs = self.get_strategy_params()
        
        try:
            # 创建进度对话框
            progress_dialog = QProgressDialog("正在转换大小写...", "取消", 0, 100, self)
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.show()
            
            # 创建工作线程
            self.transform_worker = CaseTransformWorker(words, strategy, keep_original, **kwargs)
            self.transform_worker.progress.connect(
                lambda v, m: (progress_dialog.setValue(v), progress_dialog.setLabelText(m))
            )
            self.transform_worker.result_ready.connect(self.on_transform_ready)
            self.transform_worker.error_occurred.connect(self.on_transform_error)
            self.transform_worker.finished.connect(progress_dialog.close)
            
            # 连接取消信号
            progress_dialog.canceled.connect(self.transform_worker.terminate)
            
            self.transform_worker.start()
            
        except Exception as e:
            self.logger.error(f"转换大小写失败: {e}")
            QMessageBox.critical(self, "错误", f"转换失败: {str(e)}")
    
    @pyqtSlot(list, int)
    def on_transform_ready(self, results: List[str], count: int):
        """转换完成"""
        self.current_results = results
        self.update_result_table()
        self.result_count_label.setText(f"词条数: {count:,}")
        self.status_message.emit(f"成功转换生成 {count:,} 个词条")
    
    @pyqtSlot(str)
    def on_transform_error(self, error_message: str):
        """转换错误"""
        QMessageBox.critical(self, "转换错误", f"转换失败: {error_message}")
        self.status_message.emit(f"转换失败: {error_message}")
    
    def update_result_table(self):
        """更新结果表格"""
        self.result_table.setRowCount(len(self.current_results))
        
        for row, result in enumerate(self.current_results):
            # 序号
            index_item = QTableWidgetItem(str(row + 1))
            index_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.result_table.setItem(row, 0, index_item)
            
            # 转换结果
            result_item = QTableWidgetItem(result)
            self.result_table.setItem(row, 1, result_item)
    
    def export_results(self):
        """导出结果"""
        if not self.current_results:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出转换结果", "case_transformed.txt",
            "文本文件 (*.txt);;JSON文件 (*.json);;CSV文件 (*.csv)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    self.export_as_json(file_path)
                elif file_path.endswith('.csv'):
                    self.export_as_csv(file_path)
                else:
                    self.export_as_txt(file_path)
                
                self.status_message.emit(f"结果已导出到: {file_path}")
                
            except Exception as e:
                self.logger.error(f"导出失败: {e}")
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def export_as_txt(self, file_path: str):
        """导出为文本文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for result in self.current_results:
                f.write(result + '\n')
    
    def export_as_json(self, file_path: str):
        """导出为JSON文件"""
        import json
        from datetime import datetime
        
        export_data = {
            'export_time': datetime.now().isoformat(),
            'strategy': self.strategy_combo.currentText(),
            'result_count': len(self.current_results),
            'results': self.current_results
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def export_as_csv(self, file_path: str):
        """导出为CSV文件"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['序号', '转换结果'])
            
            for i, result in enumerate(self.current_results):
                writer.writerow([i + 1, result])
    
    def save_to_dictionary(self):
        """保存到字典"""
        if not self.current_results:
            QMessageBox.warning(self, "警告", "没有可保存的结果")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        
        # 获取字典名称
        name, ok = QInputDialog.getText(self, "保存到字典", "字典名称:")
        if not ok or not name.strip():
            return
        
        try:
            # 创建新字典
            strategy_name = self.strategy_combo.currentText()
            dictionary_id = dictionary_manager.create_dictionary(
                name.strip(), 
                f"大小写转换生成的字典（{strategy_name}），包含 {len(self.current_results)} 个词条"
            )
            
            # 添加词条
            added_count = dictionary_manager.add_words(dictionary_id, self.current_results)
            
            QMessageBox.information(
                self, "保存成功", 
                f"已创建字典 '{name}'\n成功保存 {added_count} 个词条"
            )
            
            self.status_message.emit(f"已保存 {added_count} 个词条到字典 '{name}'")
            
        except Exception as e:
            self.logger.error(f"保存到字典失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = CaseTransformWidget()
    widget.show()
    sys.exit(app.exec())