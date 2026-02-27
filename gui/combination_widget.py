"""
组合模式字典生成界面模块
提供三区域组合生成功能的图形界面
"""
import logging
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QTextEdit, QComboBox, QPushButton, QSpinBox,
    QCheckBox, QLineEdit, QListWidget, QListWidgetItem,
    QGroupBox, QProgressDialog, QMessageBox, QFileDialog,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont

try:
    from core.combination_generator import combination_generator
    from core.dictionary_manager import dictionary_manager
except ImportError as e:
    print(f"组合模块导入失败: {e}")
    # 创建空的占位符类
    class DummyGenerator:
        def estimate_combination_count(self, config): return 0
        def generate_combinations(self, config): return []
        def save_combination_config(self, name, config): return 0
        def load_combination_config(self, config_id): return None
        def get_all_combination_configs(self): return []
    
    combination_generator = DummyGenerator()
    
    class DummyManager:
        def get_all_dictionaries(self): return []
        def create_dictionary(self, name, desc): return 0
        def add_words(self, dict_id, words): return 0
    
    dictionary_manager = DummyManager()


class CombinationWorker(QThread):
    """组合生成工作线程"""
    progress = pyqtSignal(int, str)
    result_ready = pyqtSignal(list, int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
    
    def run(self):
        try:
            self.progress.emit(10, "准备生成组合...")
            
            # 估算数量
            estimated_count = combination_generator.estimate_combination_count(self.config)
            self.progress.emit(20, f"预计生成 {estimated_count} 个组合...")
            
            if estimated_count > 100000:
                self.error_occurred.emit(f"组合数量过多 ({estimated_count})，请减少输入数据")
                return
            
            self.progress.emit(30, "开始生成组合...")
            
            # 生成组合
            combinations = list(combination_generator.generate_combinations(self.config))
            
            self.progress.emit(90, f"生成完成，共 {len(combinations)} 个组合")
            self.result_ready.emit(combinations, len(combinations))
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class CombinationWidget(QWidget):
    """组合模式字典生成组件"""
    
    status_message = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 组件引用
        self.area_a_input = None
        self.area_b_list = None
        self.area_c_type_combo = None
        self.area_c_config = None
        self.connector_input = None
        self.result_table = None
        self.generate_btn = None
        
        # 工作线程
        self.combination_worker = None
        
        # 当前结果
        self.current_combinations = []
        
        self.setup_ui()
        self.connect_signals()
        self.load_dictionaries()
    
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上半部分：配置区域
        config_widget = self.create_config_panel()
        splitter.addWidget(config_widget)
        
        # 下半部分：结果区域
        result_widget = self.create_result_panel()
        splitter.addWidget(result_widget)
        
        # 设置分割比例
        splitter.setSizes([400, 300])
        
        main_layout.addWidget(splitter)
    
    def create_config_panel(self) -> QWidget:
        """创建配置面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题
        title_label = QLabel("🔧 组合模式字典生成")
        title_label.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 三区域配置
        areas_layout = QHBoxLayout()
        
        # A区域（自定义输入）
        area_a_group = self.create_area_a_panel()
        areas_layout.addWidget(area_a_group)
        
        # B区域（字典选择）
        area_b_group = self.create_area_b_panel()
        areas_layout.addWidget(area_b_group)
        
        # C区域（日期/数字序列）
        area_c_group = self.create_area_c_panel()
        areas_layout.addWidget(area_c_group)
        
        layout.addLayout(areas_layout)
        
        # 连接符和控制区域
        control_layout = QHBoxLayout()
        
        # 连接符设置
        connector_group = QGroupBox("连接符设置")
        connector_layout = QVBoxLayout(connector_group)
        
        self.connector_input = QLineEdit("_")
        self.connector_input.setPlaceholderText("留空表示无连接符")
        connector_layout.addWidget(QLabel("连接符:"))
        connector_layout.addWidget(self.connector_input)
        
        control_layout.addWidget(connector_group)
        
        # 操作按钮
        button_group = QGroupBox("操作")
        button_layout = QVBoxLayout(button_group)
        
        self.generate_btn = QPushButton("🚀 生成组合")
        self.generate_btn.clicked.connect(self.generate_combinations)
        button_layout.addWidget(self.generate_btn)
        
        estimate_btn = QPushButton("📊 估算数量")
        estimate_btn.clicked.connect(self.estimate_combinations)
        button_layout.addWidget(estimate_btn)
        
        save_config_btn = QPushButton("💾 保存配置")
        save_config_btn.clicked.connect(self.save_configuration)
        button_layout.addWidget(save_config_btn)
        
        load_config_btn = QPushButton("📁 加载配置")
        load_config_btn.clicked.connect(self.load_configuration)
        button_layout.addWidget(load_config_btn)
        
        control_layout.addWidget(button_group)
        
        layout.addLayout(control_layout)
        
        return widget
    
    def create_area_a_panel(self) -> QGroupBox:
        """创建A区域面板（自定义输入）"""
        group = QGroupBox("A区域 (自定义)")
        layout = QVBoxLayout(group)
        
        # 启用复选框
        self.area_a_enabled = QCheckBox("启用A区域")
        self.area_a_enabled.setChecked(True)
        layout.addWidget(self.area_a_enabled)
        
        # 输入框
        self.area_a_input = QTextEdit()
        self.area_a_input.setPlaceholderText("每行一个词条，或用逗号分隔\n例如:\nadmin\nuser\ntest")
        self.area_a_input.setMaximumHeight(150)
        layout.addWidget(self.area_a_input)
        
        # 示例按钮
        example_btn = QPushButton("📝 填入示例")
        example_btn.clicked.connect(lambda: self.area_a_input.setPlainText("admin\nuser\ntest\nroot"))
        layout.addWidget(example_btn)
        
        return group
    
    def create_area_b_panel(self) -> QGroupBox:
        """创建B区域面板（字典选择）"""
        group = QGroupBox("B区域 (字典)")
        layout = QVBoxLayout(group)
        
        # 启用复选框
        self.area_b_enabled = QCheckBox("启用B区域")
        self.area_b_enabled.setChecked(True)
        layout.addWidget(self.area_b_enabled)
        
        # 字典列表
        self.area_b_list = QListWidget()
        self.area_b_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.area_b_list.setMaximumHeight(120)
        layout.addWidget(self.area_b_list)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新字典")
        refresh_btn.clicked.connect(self.load_dictionaries)
        layout.addWidget(refresh_btn)
        
        return group
    
    def create_area_c_panel(self) -> QGroupBox:
        """创建C区域面板（日期/数字序列）"""
        group = QGroupBox("C区域 (日期/数字)")
        layout = QVBoxLayout(group)
        
        # 启用复选框
        self.area_c_enabled = QCheckBox("启用C区域")
        self.area_c_enabled.setChecked(True)
        layout.addWidget(self.area_c_enabled)
        
        # 类型选择
        self.area_c_type_combo = QComboBox()
        self.area_c_type_combo.addItems(["年份 (YYYY)", "两位年份 (YY)", "月份 (MM)", "日期 (DD)", "数字序列", "自定义"])
        self.area_c_type_combo.currentTextChanged.connect(self.on_area_c_type_changed)
        layout.addWidget(QLabel("类型:"))
        layout.addWidget(self.area_c_type_combo)
        
        # 配置区域
        self.area_c_config = QWidget()
        self.area_c_config_layout = QVBoxLayout(self.area_c_config)
        layout.addWidget(self.area_c_config)
        
        # 初始化配置
        self.on_area_c_type_changed("年份 (YYYY)")
        
        return group
    
    def on_area_c_type_changed(self, type_text: str):
        """C区域类型改变事件"""
        # 清空配置区域
        for i in reversed(range(self.area_c_config_layout.count())):
            item = self.area_c_config_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                else:
                    # 如果是布局项，递归删除
                    layout = item.layout()
                    if layout:
                        self.clear_layout(layout)
                        self.area_c_config_layout.removeItem(item)
        
        if "年份" in type_text or "两位年份" in type_text:
            # 年份配置
            year_layout = QHBoxLayout()
            
            self.start_year_spin = QSpinBox()
            self.start_year_spin.setRange(1900, 2100)
            self.start_year_spin.setValue(2020)
            
            self.end_year_spin = QSpinBox()
            self.end_year_spin.setRange(1900, 2100)
            self.end_year_spin.setValue(2024)
            
            year_layout.addWidget(QLabel("从:"))
            year_layout.addWidget(self.start_year_spin)
            year_layout.addWidget(QLabel("到:"))
            year_layout.addWidget(self.end_year_spin)
            
            self.area_c_config_layout.addLayout(year_layout)
            
        elif "数字序列" in type_text:
            # 数字序列配置
            number_layout = QVBoxLayout()
            
            range_layout = QHBoxLayout()
            self.start_number_spin = QSpinBox()
            self.start_number_spin.setRange(0, 9999)
            self.start_number_spin.setValue(1)
            
            self.end_number_spin = QSpinBox()
            self.end_number_spin.setRange(0, 9999)
            self.end_number_spin.setValue(10)
            
            range_layout.addWidget(QLabel("从:"))
            range_layout.addWidget(self.start_number_spin)
            range_layout.addWidget(QLabel("到:"))
            range_layout.addWidget(self.end_number_spin)
            
            number_layout.addLayout(range_layout)
            
            # 格式设置
            format_layout = QHBoxLayout()
            self.number_format_input = QLineEdit("{:02d}")
            self.number_format_input.setPlaceholderText("如 {:02d} 表示两位数补零")
            
            format_layout.addWidget(QLabel("格式:"))
            format_layout.addWidget(self.number_format_input)
            
            number_layout.addLayout(format_layout)
            self.area_c_config_layout.addLayout(number_layout)
            
        elif "自定义" in type_text:
            # 自定义输入
            self.area_c_custom_input = QTextEdit()
            self.area_c_custom_input.setPlaceholderText("每行一个项目")
            self.area_c_custom_input.setMaximumHeight(80)
            self.area_c_config_layout.addWidget(self.area_c_custom_input)
    
    def clear_layout(self, layout):
        """递归清空布局"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self.clear_layout(item.layout())
    
    def create_result_panel(self) -> QWidget:
        """创建结果面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题和统计
        header_layout = QHBoxLayout()
        
        result_title = QLabel("📋 生成结果")
        result_title.setFont(QFont("", 12, QFont.Weight.Bold))
        header_layout.addWidget(result_title)
        
        self.result_count_label = QLabel("组合数: 0")
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
        self.result_table.setHorizontalHeaderLabels(["序号", "组合结果"])
        
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
            self.area_b_list.clear()
            dictionaries = dictionary_manager.get_all_dictionaries()
            
            for dictionary in dictionaries:
                item = QListWidgetItem()
                item.setText(f"{dictionary['name']} ({dictionary.get('word_count', 0)} 词条)")
                item.setData(Qt.ItemDataRole.UserRole, dictionary['id'])
                self.area_b_list.addItem(item)
            
            self.status_message.emit(f"加载了 {len(dictionaries)} 个字典")
            
        except Exception as e:
            self.logger.error(f"加载字典列表失败: {e}")
            QMessageBox.critical(self, "错误", f"加载字典列表失败: {str(e)}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        config = {
            'areas_enabled': [],
            'connector': self.connector_input.text()
        }
        
        # A区域配置
        if self.area_a_enabled.isChecked():
            config['areas_enabled'].append('a')
            config['area_a'] = {
                'type': 'custom',
                'data': self.area_a_input.toPlainText()
            }
        
        # B区域配置
        if self.area_b_enabled.isChecked():
            selected_items = self.area_b_list.selectedItems()
            if selected_items:
                config['areas_enabled'].append('b')
                dictionary_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
                config['area_b'] = {
                    'type': 'dictionary',
                    'data': dictionary_ids
                }
        
        # C区域配置
        if self.area_c_enabled.isChecked():
            config['areas_enabled'].append('c')
            type_text = self.area_c_type_combo.currentText()
            
            if "年份" in type_text:
                format_str = "YYYY" if "年份 (YYYY)" in type_text else "YY"
                config['area_c'] = {
                    'type': 'date',
                    'data': {
                        'start_year': self.start_year_spin.value(),
                        'end_year': self.end_year_spin.value(),
                        'format': format_str
                    }
                }
            elif "月份" in type_text:
                config['area_c'] = {
                    'type': 'date',
                    'data': {
                        'start_year': 2024,
                        'end_year': 2024,
                        'format': 'MM'
                    }
                }
            elif "日期" in type_text:
                config['area_c'] = {
                    'type': 'date',
                    'data': {
                        'start_year': 2024,
                        'end_year': 2024,
                        'format': 'DD'
                    }
                }
            elif "数字序列" in type_text:
                config['area_c'] = {
                    'type': 'number',
                    'data': {
                        'start': self.start_number_spin.value(),
                        'end': self.end_number_spin.value(),
                        'format': self.number_format_input.text() or '{:d}'
                    }
                }
            elif "自定义" in type_text:
                if hasattr(self, 'area_c_custom_input'):
                    config['area_c'] = {
                        'type': 'custom',
                        'data': self.area_c_custom_input.toPlainText()
                    }
        
        return config
    
    def estimate_combinations(self):
        """估算组合数量"""
        try:
            config = self.get_current_config()
            count = combination_generator.estimate_combination_count(config)
            
            QMessageBox.information(
                self, "估算结果", 
                f"预计生成 {count:,} 个组合\n\n"
                f"建议：\n"
                f"• 少于 10,000 个：快速生成\n"
                f"• 10,000 - 100,000 个：需要等待\n"
                f"• 超过 100,000 个：建议减少输入数据"
            )
            
        except Exception as e:
            self.logger.error(f"估算组合数量失败: {e}")
            QMessageBox.critical(self, "错误", f"估算失败: {str(e)}")
    
    def generate_combinations(self):
        """生成组合"""
        try:
            config = self.get_current_config()
            
            if not config['areas_enabled']:
                QMessageBox.warning(self, "警告", "请至少启用一个区域")
                return
            
            # 创建进度对话框
            progress_dialog = QProgressDialog("正在生成组合...", "取消", 0, 100, self)
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.show()
            
            # 创建工作线程
            self.combination_worker = CombinationWorker(config)
            self.combination_worker.progress.connect(
                lambda v, m: (progress_dialog.setValue(v), progress_dialog.setLabelText(m))
            )
            self.combination_worker.result_ready.connect(self.on_combinations_ready)
            self.combination_worker.error_occurred.connect(self.on_combination_error)
            self.combination_worker.finished.connect(progress_dialog.close)
            
            # 连接取消信号
            progress_dialog.canceled.connect(self.combination_worker.terminate)
            
            self.combination_worker.start()
            
        except Exception as e:
            self.logger.error(f"生成组合失败: {e}")
            QMessageBox.critical(self, "错误", f"生成失败: {str(e)}")
    
    @pyqtSlot(list, int)
    def on_combinations_ready(self, combinations: List[str], count: int):
        """组合生成完成"""
        self.current_combinations = combinations
        self.update_result_table()
        self.result_count_label.setText(f"组合数: {count:,}")
        self.status_message.emit(f"成功生成 {count:,} 个组合")
    
    @pyqtSlot(str)
    def on_combination_error(self, error_message: str):
        """组合生成错误"""
        QMessageBox.critical(self, "生成错误", f"生成失败: {error_message}")
        self.status_message.emit(f"生成失败: {error_message}")
    
    def update_result_table(self):
        """更新结果表格"""
        self.result_table.setRowCount(len(self.current_combinations))
        
        for row, combination in enumerate(self.current_combinations):
            # 序号
            index_item = QTableWidgetItem(str(row + 1))
            index_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.result_table.setItem(row, 0, index_item)
            
            # 组合结果
            combo_item = QTableWidgetItem(combination)
            self.result_table.setItem(row, 1, combo_item)
    
    def export_results(self):
        """导出结果"""
        if not self.current_combinations:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出组合结果", "combinations.txt",
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
            for combination in self.current_combinations:
                f.write(combination + '\n')
    
    def export_as_json(self, file_path: str):
        """导出为JSON文件"""
        import json
        from datetime import datetime
        
        export_data = {
            'export_time': datetime.now().isoformat(),
            'combination_count': len(self.current_combinations),
            'combinations': self.current_combinations
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def export_as_csv(self, file_path: str):
        """导出为CSV文件"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['序号', '组合结果'])
            
            for i, combination in enumerate(self.current_combinations):
                writer.writerow([i + 1, combination])
    
    def save_to_dictionary(self):
        """保存到字典"""
        if not self.current_combinations:
            QMessageBox.warning(self, "警告", "没有可保存的结果")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        
        # 获取字典名称
        name, ok = QInputDialog.getText(self, "保存到字典", "字典名称:")
        if not ok or not name.strip():
            return
        
        try:
            # 创建新字典
            dictionary_id = dictionary_manager.create_dictionary(
                name.strip(), 
                f"组合模式生成的字典，包含 {len(self.current_combinations)} 个词条"
            )
            
            # 添加词条
            added_count = dictionary_manager.add_words(dictionary_id, self.current_combinations)
            
            QMessageBox.information(
                self, "保存成功", 
                f"已创建字典 '{name}'\n成功保存 {added_count} 个词条"
            )
            
            self.status_message.emit(f"已保存 {added_count} 个组合到字典 '{name}'")
            
        except Exception as e:
            self.logger.error(f"保存到字典失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def save_configuration(self):
        """保存配置"""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "保存配置", "配置名称:")
        if not ok or not name.strip():
            return
        
        try:
            config = self.get_current_config()
            config_id = combination_generator.save_combination_config(name.strip(), config)
            
            QMessageBox.information(self, "保存成功", f"配置 '{name}' 已保存")
            self.status_message.emit(f"配置 '{name}' 已保存")
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
    
    def load_configuration(self):
        """加载配置"""
        try:
            configs = combination_generator.get_all_combination_configs()
            if not configs:
                QMessageBox.information(self, "提示", "没有保存的配置")
                return
            
            from PyQt6.QtWidgets import QInputDialog
            
            config_names = [f"{config['name']} (ID: {config['id']})" for config in configs]
            name, ok = QInputDialog.getItem(self, "加载配置", "选择配置:", config_names, 0, False)
            
            if ok and name:
                # 提取配置ID
                config_id = int(name.split("ID: ")[1].rstrip(")"))
                config_data = combination_generator.load_combination_config(config_id)
                
                if config_data:
                    self.apply_configuration(config_data['config'])
                    QMessageBox.information(self, "加载成功", f"配置 '{config_data['name']}' 已加载")
                    self.status_message.emit(f"配置 '{config_data['name']}' 已加载")
                
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            QMessageBox.critical(self, "错误", f"加载配置失败: {str(e)}")
    
    def apply_configuration(self, config: Dict[str, Any]):
        """应用配置"""
        try:
            # 连接符
            self.connector_input.setText(config.get('connector', ''))
            
            # 区域启用状态
            areas_enabled = config.get('areas_enabled', [])
            self.area_a_enabled.setChecked('a' in areas_enabled)
            self.area_b_enabled.setChecked('b' in areas_enabled)
            self.area_c_enabled.setChecked('c' in areas_enabled)
            
            # A区域
            if 'area_a' in config:
                area_a = config['area_a']
                if area_a['type'] == 'custom':
                    self.area_a_input.setPlainText(area_a['data'])
            
            # B区域（字典选择需要手动处理）
            if 'area_b' in config:
                area_b = config['area_b']
                if area_b['type'] == 'dictionary':
                    dictionary_ids = area_b['data']
                    # 选中对应的字典项
                    for i in range(self.area_b_list.count()):
                        item = self.area_b_list.item(i)
                        if item.data(Qt.ItemDataRole.UserRole) in dictionary_ids:
                            item.setSelected(True)
            
            # C区域
            if 'area_c' in config:
                area_c = config['area_c']
                if area_c['type'] == 'date':
                    date_config = area_c['data']
                    format_str = date_config.get('format', 'YYYY')
                    
                    if format_str == 'YYYY':
                        self.area_c_type_combo.setCurrentText("年份 (YYYY)")
                    elif format_str == 'YY':
                        self.area_c_type_combo.setCurrentText("两位年份 (YY)")
                    elif format_str == 'MM':
                        self.area_c_type_combo.setCurrentText("月份 (MM)")
                    elif format_str == 'DD':
                        self.area_c_type_combo.setCurrentText("日期 (DD)")
                    
                    if hasattr(self, 'start_year_spin'):
                        self.start_year_spin.setValue(date_config.get('start_year', 2020))
                        self.end_year_spin.setValue(date_config.get('end_year', 2024))
                
                elif area_c['type'] == 'number':
                    self.area_c_type_combo.setCurrentText("数字序列")
                    number_config = area_c['data']
                    
                    if hasattr(self, 'start_number_spin'):
                        self.start_number_spin.setValue(number_config.get('start', 1))
                        self.end_number_spin.setValue(number_config.get('end', 10))
                        self.number_format_input.setText(number_config.get('format', '{:d}'))
                
                elif area_c['type'] == 'custom':
                    self.area_c_type_combo.setCurrentText("自定义")
                    if hasattr(self, 'area_c_custom_input'):
                        self.area_c_custom_input.setPlainText(area_c['data'])
            
        except Exception as e:
            self.logger.error(f"应用配置失败: {e}")


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = CombinationWidget()
    widget.show()
    sys.exit(app.exec())