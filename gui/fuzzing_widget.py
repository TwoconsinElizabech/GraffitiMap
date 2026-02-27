"""
模糊测试字典生成界面模块
提供路径变换、参数注入等模糊测试功能的图形界面
"""
import logging
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QProgressDialog, QMessageBox, QFileDialog,
    QSplitter, QCheckBox, QLineEdit, QSpinBox, QComboBox,
    QListWidget, QListWidgetItem, QHeaderView, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont

from core.fuzzing_generator import fuzzing_generator
from core.dictionary_manager import dictionary_manager


class FuzzingWorker(QThread):
    """模糊测试生成工作线程"""
    progress = pyqtSignal(int, str)
    result_ready = pyqtSignal(list, int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, targets: List[str], config: Dict[str, Any]):
        super().__init__()
        self.targets = targets
        self.config = config
    
    def run(self):
        try:
            self.progress.emit(10, "准备生成模糊测试变体...")
            
            all_variants = []
            total_targets = len(self.targets)
            
            for i, target in enumerate(self.targets):
                self.progress.emit(
                    20 + int((i / total_targets) * 60), 
                    f"处理目标 {i+1}/{total_targets}: {target[:50]}..."
                )
                
                variants = fuzzing_generator.generate_fuzzing_variants(target, self.config)
                all_variants.extend(variants)
            
            # 去重
            unique_variants = list(set(all_variants))
            
            self.progress.emit(90, f"生成完成，共 {len(unique_variants)} 个变体")
            self.result_ready.emit(unique_variants, len(unique_variants))
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class FuzzingWidget(QWidget):
    """模糊测试字典生成组件"""
    
    status_message = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 组件引用
        self.target_input = None
        self.replacement_table = None
        self.result_table = None
        
        # 配置选项
        self.position_swap_cb = None
        self.param_injection_cb = None
        self.path_traversal_cb = None
        self.max_results_spin = None
        
        # 工作线程
        self.fuzzing_worker = None
        
        # 当前结果
        self.current_variants = []
        
        self.setup_ui()
        self.connect_signals()
        self.load_default_replacements()
    
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("🎯 模糊测试字典生成")
        title_label.setFont(QFont("", 14, QFont.Weight.Bold))
        main_layout.addWidget(title_label)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 配置标签页
        config_tab = self.create_config_tab()
        tab_widget.addTab(config_tab, "🔧 配置")
        
        # 结果标签页
        result_tab = self.create_result_tab()
        tab_widget.addTab(result_tab, "📋 结果")
        
        main_layout.addWidget(tab_widget)
    
    def create_config_tab(self) -> QWidget:
        """创建配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：目标输入和基本配置
        left_widget = self.create_input_panel()
        splitter.addWidget(left_widget)
        
        # 右侧：替换规则配置
        right_widget = self.create_replacement_panel()
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        
        # 底部控制按钮
        control_layout = QHBoxLayout()
        
        generate_btn = QPushButton("🚀 生成模糊测试变体")
        generate_btn.clicked.connect(self.generate_variants)
        control_layout.addWidget(generate_btn)
        
        control_layout.addStretch()
        
        save_config_btn = QPushButton("💾 保存配置")
        save_config_btn.clicked.connect(self.save_configuration)
        control_layout.addWidget(save_config_btn)
        
        load_config_btn = QPushButton("📁 加载配置")
        load_config_btn.clicked.connect(self.load_configuration)
        control_layout.addWidget(load_config_btn)
        
        layout.addLayout(control_layout)
        
        return widget
    
    def create_input_panel(self) -> QWidget:
        """创建输入面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 目标输入
        target_group = QGroupBox("🎯 目标输入")
        target_layout = QVBoxLayout(target_group)
        
        target_layout.addWidget(QLabel("输入要进行模糊测试的路径或URL（每行一个）:"))
        self.target_input = QTextEdit()
        self.target_input.setPlaceholderText("例如:\n/api/v2/add/user\n/admin/panel/v1/config\nhttps://example.com/api/v3/users?id=123")
        target_layout.addWidget(self.target_input)
        
        # 示例按钮
        example_btn = QPushButton("📝 填入示例")
        example_btn.clicked.connect(self.fill_example)
        target_layout.addWidget(example_btn)
        
        layout.addWidget(target_group)
        
        # 基本配置
        config_group = QGroupBox("⚙️ 基本配置")
        config_layout = QVBoxLayout(config_group)
        
        # 功能开关
        self.position_swap_cb = QCheckBox("启用位置交换")
        self.position_swap_cb.setChecked(True)
        self.position_swap_cb.setToolTip("交换路径段的位置，如 /api/v1/user -> /v1/api/user")
        config_layout.addWidget(self.position_swap_cb)
        
        self.param_injection_cb = QCheckBox("启用参数注入")
        self.param_injection_cb.setChecked(True)
        self.param_injection_cb.setToolTip("在URL参数中注入测试载荷")
        config_layout.addWidget(self.param_injection_cb)
        
        self.path_traversal_cb = QCheckBox("启用路径遍历")
        self.path_traversal_cb.setChecked(True)
        self.path_traversal_cb.setToolTip("添加路径遍历载荷，如 ../../../etc/passwd")
        config_layout.addWidget(self.path_traversal_cb)
        
        # 结果数量限制
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("最大结果数:"))
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(10, 10000)
        self.max_results_spin.setValue(500)
        self.max_results_spin.setToolTip("限制生成的变体数量，避免结果过多")
        limit_layout.addWidget(self.max_results_spin)
        limit_layout.addStretch()
        
        config_layout.addLayout(limit_layout)
        
        layout.addWidget(config_group)
        
        return widget
    
    def create_replacement_panel(self) -> QWidget:
        """创建替换规则面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 替换规则
        replacement_group = QGroupBox("🔄 替换规则")
        replacement_layout = QVBoxLayout(replacement_group)
        
        replacement_layout.addWidget(QLabel("配置字符串替换规则（原字符串 -> 替换选项）:"))
        
        # 替换规则表格
        self.replacement_table = QTableWidget()
        self.replacement_table.setColumnCount(2)
        self.replacement_table.setHorizontalHeaderLabels(["原字符串", "替换选项（逗号分隔）"])
        
        # 设置表格属性
        header = self.replacement_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.replacement_table.setAlternatingRowColors(True)
        replacement_layout.addWidget(self.replacement_table)
        
        # 替换规则操作按钮
        replacement_btn_layout = QHBoxLayout()
        
        add_rule_btn = QPushButton("➕ 添加规则")
        add_rule_btn.clicked.connect(self.add_replacement_rule)
        replacement_btn_layout.addWidget(add_rule_btn)
        
        remove_rule_btn = QPushButton("➖ 删除规则")
        remove_rule_btn.clicked.connect(self.remove_replacement_rule)
        replacement_btn_layout.addWidget(remove_rule_btn)
        
        clear_rules_btn = QPushButton("🗑️ 清空规则")
        clear_rules_btn.clicked.connect(self.clear_replacement_rules)
        replacement_btn_layout.addWidget(clear_rules_btn)
        
        load_default_btn = QPushButton("🔄 加载默认")
        load_default_btn.clicked.connect(self.load_default_replacements)
        replacement_btn_layout.addWidget(load_default_btn)
        
        replacement_layout.addLayout(replacement_btn_layout)
        
        layout.addWidget(replacement_group)
        
        return widget
    
    def create_result_tab(self) -> QWidget:
        """创建结果标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题和统计
        header_layout = QHBoxLayout()
        
        result_title = QLabel("📋 生成结果")
        result_title.setFont(QFont("", 12, QFont.Weight.Bold))
        header_layout.addWidget(result_title)
        
        self.result_count_label = QLabel("变体数: 0")
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
        self.result_table.setHorizontalHeaderLabels(["序号", "模糊测试变体"])
        
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
    
    def fill_example(self):
        """填入示例"""
        example_text = """/api/v2/add/user
/admin/panel/v1/config
/app/1/dashboard/settings
https://example.com/api/v3/users?id=123&token=abc
https://test.com/admin/2/panel?session=xyz&debug=true"""
        
        self.target_input.setPlainText(example_text)
    
    def load_default_replacements(self):
        """加载默认替换规则"""
        default_config = fuzzing_generator.get_default_config()
        replacement_rules = default_config['replacement_rules']
        
        self.replacement_table.setRowCount(len(replacement_rules))
        
        for row, (original, replacements) in enumerate(replacement_rules.items()):
            # 原字符串
            original_item = QTableWidgetItem(original)
            self.replacement_table.setItem(row, 0, original_item)
            
            # 替换选项
            replacement_text = ', '.join(replacements)
            replacement_item = QTableWidgetItem(replacement_text)
            self.replacement_table.setItem(row, 1, replacement_item)
    
    def add_replacement_rule(self):
        """添加替换规则"""
        row_count = self.replacement_table.rowCount()
        self.replacement_table.insertRow(row_count)
        
        # 设置默认值
        original_item = QTableWidgetItem("v1")
        self.replacement_table.setItem(row_count, 0, original_item)
        
        replacement_item = QTableWidgetItem("v2, v3, v4")
        self.replacement_table.setItem(row_count, 1, replacement_item)
    
    def remove_replacement_rule(self):
        """删除替换规则"""
        current_row = self.replacement_table.currentRow()
        if current_row >= 0:
            self.replacement_table.removeRow(current_row)
    
    def clear_replacement_rules(self):
        """清空替换规则"""
        self.replacement_table.setRowCount(0)
    
    def get_replacement_rules(self) -> Dict[str, List[str]]:
        """获取替换规则"""
        rules = {}
        
        for row in range(self.replacement_table.rowCount()):
            original_item = self.replacement_table.item(row, 0)
            replacement_item = self.replacement_table.item(row, 1)
            
            if original_item and replacement_item:
                original = original_item.text().strip()
                replacement_text = replacement_item.text().strip()
                
                if original and replacement_text:
                    replacements = [r.strip() for r in replacement_text.split(',') if r.strip()]
                    if replacements:
                        rules[original] = replacements
        
        return rules
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            'replacement_rules': self.get_replacement_rules(),
            'position_swap': self.position_swap_cb.isChecked(),
            'param_injection': self.param_injection_cb.isChecked(),
            'path_traversal': self.path_traversal_cb.isChecked(),
            'max_results': self.max_results_spin.value()
        }
    
    def generate_variants(self):
        """生成模糊测试变体"""
        target_text = self.target_input.toPlainText().strip()
        if not target_text:
            QMessageBox.warning(self, "警告", "请输入目标路径或URL")
            return
        
        # 解析目标列表
        targets = [line.strip() for line in target_text.split('\n') if line.strip()]
        if not targets:
            QMessageBox.warning(self, "警告", "没有有效的目标")
            return
        
        try:
            config = self.get_current_config()
            
            # 创建进度对话框
            progress_dialog = QProgressDialog("正在生成模糊测试变体...", "取消", 0, 100, self)
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.show()
            
            # 创建工作线程
            self.fuzzing_worker = FuzzingWorker(targets, config)
            self.fuzzing_worker.progress.connect(
                lambda v, m: (progress_dialog.setValue(v), progress_dialog.setLabelText(m))
            )
            self.fuzzing_worker.result_ready.connect(self.on_variants_ready)
            self.fuzzing_worker.error_occurred.connect(self.on_fuzzing_error)
            self.fuzzing_worker.finished.connect(progress_dialog.close)
            
            # 连接取消信号
            progress_dialog.canceled.connect(self.fuzzing_worker.terminate)
            
            self.fuzzing_worker.start()
            
        except Exception as e:
            self.logger.error(f"生成模糊测试变体失败: {e}")
            QMessageBox.critical(self, "错误", f"生成失败: {str(e)}")
    
    @pyqtSlot(list, int)
    def on_variants_ready(self, variants: List[str], count: int):
        """变体生成完成"""
        self.current_variants = variants
        self.update_result_table()
        self.result_count_label.setText(f"变体数: {count:,}")
        self.status_message.emit(f"成功生成 {count:,} 个模糊测试变体")
    
    @pyqtSlot(str)
    def on_fuzzing_error(self, error_message: str):
        """模糊测试生成错误"""
        QMessageBox.critical(self, "生成错误", f"生成失败: {error_message}")
        self.status_message.emit(f"生成失败: {error_message}")
    
    def update_result_table(self):
        """更新结果表格"""
        self.result_table.setRowCount(len(self.current_variants))
        
        for row, variant in enumerate(self.current_variants):
            # 序号
            index_item = QTableWidgetItem(str(row + 1))
            index_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.result_table.setItem(row, 0, index_item)
            
            # 变体
            variant_item = QTableWidgetItem(variant)
            self.result_table.setItem(row, 1, variant_item)
    
    def export_results(self):
        """导出结果"""
        if not self.current_variants:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出模糊测试变体", "fuzzing_variants.txt",
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
            for variant in self.current_variants:
                f.write(variant + '\n')
    
    def export_as_json(self, file_path: str):
        """导出为JSON文件"""
        import json
        from datetime import datetime
        
        export_data = {
            'export_time': datetime.now().isoformat(),
            'variant_count': len(self.current_variants),
            'config': self.get_current_config(),
            'variants': self.current_variants
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def export_as_csv(self, file_path: str):
        """导出为CSV文件"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['序号', '模糊测试变体'])
            
            for i, variant in enumerate(self.current_variants):
                writer.writerow([i + 1, variant])
    
    def save_to_dictionary(self):
        """保存到字典"""
        if not self.current_variants:
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
                f"模糊测试生成的字典，包含 {len(self.current_variants)} 个变体"
            )
            
            # 添加变体
            added_count = dictionary_manager.add_words(dictionary_id, self.current_variants)
            
            QMessageBox.information(
                self, "保存成功", 
                f"已创建字典 '{name}'\n成功保存 {added_count} 个变体"
            )
            
            self.status_message.emit(f"已保存 {added_count} 个变体到字典 '{name}'")
            
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
            config_id = fuzzing_generator.save_fuzzing_config(
                name.strip(),
                config['replacement_rules'],
                config['position_swap'],
                config['param_injection'],
                config['path_traversal']
            )
            
            QMessageBox.information(self, "保存成功", f"配置 '{name}' 已保存")
            self.status_message.emit(f"配置 '{name}' 已保存")
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
    
    def load_configuration(self):
        """加载配置"""
        try:
            configs = fuzzing_generator.get_all_fuzzing_configs()
            if not configs:
                QMessageBox.information(self, "提示", "没有保存的配置")
                return
            
            from PyQt6.QtWidgets import QInputDialog
            
            config_names = [f"{config['name']} (ID: {config['id']})" for config in configs]
            name, ok = QInputDialog.getItem(self, "加载配置", "选择配置:", config_names, 0, False)
            
            if ok and name:
                # 提取配置ID
                config_id = int(name.split("ID: ")[1].rstrip(")"))
                config_data = fuzzing_generator.load_fuzzing_config(config_id)
                
                if config_data:
                    self.apply_configuration(config_data)
                    QMessageBox.information(self, "加载成功", f"配置 '{config_data['name']}' 已加载")
                    self.status_message.emit(f"配置 '{config_data['name']}' 已加载")
                
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            QMessageBox.critical(self, "错误", f"加载配置失败: {str(e)}")
    
    def apply_configuration(self, config_data: Dict[str, Any]):
        """应用配置"""
        try:
            # 基本配置
            self.position_swap_cb.setChecked(config_data.get('position_swap', False))
            self.param_injection_cb.setChecked(config_data.get('param_injection', False))
            self.path_traversal_cb.setChecked(config_data.get('path_traversal', False))
            
            # 替换规则
            replacement_rules = config_data.get('replacement_rules', {})
            self.replacement_table.setRowCount(len(replacement_rules))
            
            for row, (original, replacements) in enumerate(replacement_rules.items()):
                # 原字符串
                original_item = QTableWidgetItem(original)
                self.replacement_table.setItem(row, 0, original_item)
                
                # 替换选项
                replacement_text = ', '.join(replacements)
                replacement_item = QTableWidgetItem(replacement_text)
                self.replacement_table.setItem(row, 1, replacement_item)
            
        except Exception as e:
            self.logger.error(f"应用配置失败: {e}")


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = FuzzingWidget()
    widget.show()
    sys.exit(app.exec())