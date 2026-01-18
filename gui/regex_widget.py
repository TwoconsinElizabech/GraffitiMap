"""
正则表达式管理界面模块
提供正则表达式模式的管理和测试功能
"""
import logging
from typing import List, Dict, Any, Optional
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
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPalette

from utils.regex_helper import regex_helper
from config.settings import THEME_COLORS


class RegexWidget(QWidget):
    """正则表达式管理组件"""
    
    # 信号定义
    status_message = pyqtSignal(str)
    
    def __init__(self):
        """初始化正则表达式组件"""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 组件引用
        self.pattern_list = None
        self.pattern_edit = None
        self.test_input = None
        self.test_results = None
        
        self.setup_ui()
        self.connect_signals()
        self.refresh_data()
    
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：模式管理
        left_panel = self.create_pattern_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：测试面板
        right_panel = self.create_test_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
    
    def create_pattern_panel(self) -> QWidget:
        """创建模式管理面板"""
        panel = QGroupBox("正则表达式模式")
        layout = QVBoxLayout(panel)
        
        # 模式列表
        self.pattern_list = QListWidget()
        self.pattern_list.setAlternatingRowColors(True)
        layout.addWidget(self.pattern_list)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ 添加")
        add_btn.clicked.connect(self.add_pattern)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ 编辑")
        edit_btn.clicked.connect(self.edit_pattern)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ 删除")
        delete_btn.clicked.connect(self.delete_pattern)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        import_btn = QPushButton("📁 导入")
        import_btn.clicked.connect(self.import_patterns)
        button_layout.addWidget(import_btn)
        
        export_btn = QPushButton("💾 导出")
        export_btn.clicked.connect(self.export_patterns)
        button_layout.addWidget(export_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def create_test_panel(self) -> QWidget:
        """创建测试面板"""
        panel = QGroupBox("正则表达式测试")
        layout = QVBoxLayout(panel)
        
        # 测试输入
        input_group = QGroupBox("测试文本")
        input_layout = QVBoxLayout(input_group)
        
        self.test_input = QTextEdit()
        self.test_input.setPlaceholderText("在此输入要测试的文本...")
        self.test_input.setMaximumHeight(150)
        input_layout.addWidget(self.test_input)
        
        # 测试按钮
        test_layout = QHBoxLayout()
        test_btn = QPushButton("🔍 测试选中模式")
        test_btn.clicked.connect(self.test_pattern)
        test_layout.addWidget(test_btn)
        
        test_all_btn = QPushButton("🔍 测试所有模式")
        test_all_btn.clicked.connect(self.test_all_patterns)
        test_layout.addWidget(test_all_btn)
        
        test_layout.addStretch()
        input_layout.addLayout(test_layout)
        
        layout.addWidget(input_group)
        
        # 测试结果
        results_group = QGroupBox("测试结果")
        results_layout = QVBoxLayout(results_group)
        
        self.test_results = QTableWidget()
        self.test_results.setColumnCount(3)
        self.test_results.setHorizontalHeaderLabels(["模式名称", "匹配结果", "匹配内容"])
        self.test_results.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.test_results.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.test_results.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.test_results)
        
        layout.addWidget(results_group)
        
        return panel
    
    def connect_signals(self):
        """连接信号"""
        self.pattern_list.itemSelectionChanged.connect(self.on_pattern_selected)
        self.pattern_list.itemDoubleClicked.connect(self.edit_pattern)
    
    def refresh_data(self):
        """刷新数据"""
        self.load_patterns()
    
    def load_patterns(self):
        """加载正则表达式模式"""
        try:
            self.pattern_list.clear()
            
            # 获取所有模式
            pattern_names = regex_helper.get_all_pattern_names()
            
            for pattern_name in pattern_names:
                pattern_info = regex_helper.get_pattern_info(pattern_name)
                if pattern_info:
                    item = QListWidgetItem()
                    item.setText(f"{pattern_name}")
                    item.setData(Qt.ItemDataRole.UserRole, pattern_info)
                    item.setToolTip(f"描述: {pattern_info.get('description', '无描述')}\n"
                                  f"模式: {pattern_info.get('pattern', '无模式')}")
                    self.pattern_list.addItem(item)
            
            self.status_message.emit(f"已加载 {len(pattern_names)} 个正则表达式模式")
            
        except Exception as e:
            self.logger.error(f"加载正则表达式模式失败: {e}")
            QMessageBox.critical(self, "错误", f"加载模式失败: {str(e)}")
    
    def on_pattern_selected(self):
        """模式选择变化"""
        current_item = self.pattern_list.currentItem()
        if current_item:
            pattern_info = current_item.data(Qt.ItemDataRole.UserRole)
            if pattern_info:
                # 可以在这里显示模式详情
                pass
    
    def add_pattern(self):
        """添加新模式"""
        dialog = PatternEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pattern_data = dialog.get_pattern_data()
            try:
                # 这里应该调用regex_helper的添加方法
                # 由于当前实现是从文件加载，这里只是示例
                QMessageBox.information(self, "提示", "添加功能需要实现保存到配置文件的逻辑")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加模式失败: {str(e)}")
    
    def edit_pattern(self):
        """编辑选中模式"""
        current_item = self.pattern_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要编辑的模式")
            return
        
        pattern_info = current_item.data(Qt.ItemDataRole.UserRole)
        dialog = PatternEditDialog(self, pattern_info)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pattern_data = dialog.get_pattern_data()
            try:
                # 这里应该调用regex_helper的更新方法
                QMessageBox.information(self, "提示", "编辑功能需要实现保存到配置文件的逻辑")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"编辑模式失败: {str(e)}")
    
    def delete_pattern(self):
        """删除选中模式"""
        current_item = self.pattern_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要删除的模式")
            return
        
        pattern_name = current_item.text()
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除模式 '{pattern_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 这里应该调用regex_helper的删除方法
                QMessageBox.information(self, "提示", "删除功能需要实现从配置文件删除的逻辑")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除模式失败: {str(e)}")
    
    def test_pattern(self):
        """测试选中的模式"""
        current_item = self.pattern_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要测试的模式")
            return
        
        test_text = self.test_input.toPlainText().strip()
        if not test_text:
            QMessageBox.warning(self, "警告", "请输入测试文本")
            return
        
        pattern_name = current_item.text()
        self.run_pattern_test([pattern_name], test_text)
    
    def test_all_patterns(self):
        """测试所有模式"""
        test_text = self.test_input.toPlainText().strip()
        if not test_text:
            QMessageBox.warning(self, "警告", "请输入测试文本")
            return
        
        pattern_names = regex_helper.get_all_pattern_names()
        self.run_pattern_test(pattern_names, test_text)
    
    def run_pattern_test(self, pattern_names: List[str], test_text: str):
        """运行模式测试"""
        try:
            self.test_results.setRowCount(0)
            
            for pattern_name in pattern_names:
                try:
                    matches = regex_helper.match_pattern(test_text, pattern_name)
                    
                    row = self.test_results.rowCount()
                    self.test_results.insertRow(row)
                    
                    # 模式名称
                    name_item = QTableWidgetItem(pattern_name)
                    self.test_results.setItem(row, 0, name_item)
                    
                    # 匹配结果
                    if matches:
                        result_item = QTableWidgetItem(f"✅ 匹配 ({len(matches)})")
                        result_item.setBackground(QPalette().color(QPalette.ColorRole.Base))
                    else:
                        result_item = QTableWidgetItem("❌ 无匹配")
                        result_item.setBackground(QPalette().color(QPalette.ColorRole.AlternateBase))
                    
                    self.test_results.setItem(row, 1, result_item)
                    
                    # 匹配内容
                    if matches:
                        content = ", ".join(matches[:5])  # 只显示前5个匹配
                        if len(matches) > 5:
                            content += f" ... (共{len(matches)}个)"
                    else:
                        content = ""
                    
                    content_item = QTableWidgetItem(content)
                    self.test_results.setItem(row, 2, content_item)
                    
                except Exception as e:
                    # 处理单个模式测试失败
                    row = self.test_results.rowCount()
                    self.test_results.insertRow(row)
                    
                    name_item = QTableWidgetItem(pattern_name)
                    self.test_results.setItem(row, 0, name_item)
                    
                    error_item = QTableWidgetItem(f"❌ 错误: {str(e)}")
                    self.test_results.setItem(row, 1, error_item)
                    
                    self.test_results.setItem(row, 2, QTableWidgetItem(""))
            
            self.status_message.emit(f"测试完成，共测试 {len(pattern_names)} 个模式")
            
        except Exception as e:
            self.logger.error(f"模式测试失败: {e}")
            QMessageBox.critical(self, "错误", f"测试失败: {str(e)}")
    
    def import_patterns(self):
        """导入模式"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入正则表达式模式", "",
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
                
                # 这里应该实现导入逻辑
                QMessageBox.information(self, "提示", f"导入功能需要实现，文件: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
    
    def export_patterns(self):
        """导出模式"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出正则表达式模式", "regex_patterns.json",
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if file_path:
            try:
                # 获取所有模式数据
                patterns = {}
                pattern_names = regex_helper.get_all_pattern_names()
                
                for pattern_name in pattern_names:
                    pattern_info = regex_helper.get_pattern_info(pattern_name)
                    if pattern_info:
                        patterns[pattern_name] = pattern_info
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(patterns, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "成功", f"已导出 {len(patterns)} 个模式到: {file_path}")
                self.status_message.emit(f"模式已导出: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")


class PatternEditDialog(QDialog):
    """模式编辑对话框"""
    
    def __init__(self, parent=None, pattern_data=None):
        super().__init__(parent)
        self.pattern_data = pattern_data or {}
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("编辑正则表达式模式")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 描述
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("描述:"))
        self.desc_edit = QLineEdit()
        desc_layout.addWidget(self.desc_edit)
        layout.addLayout(desc_layout)
        
        # 模式
        layout.addWidget(QLabel("正则表达式:"))
        self.pattern_edit = QTextEdit()
        self.pattern_edit.setMaximumHeight(100)
        layout.addWidget(self.pattern_edit)
        
        # 测试
        layout.addWidget(QLabel("测试文本:"))
        self.test_edit = QTextEdit()
        self.test_edit.setMaximumHeight(80)
        layout.addWidget(self.test_edit)
        
        test_btn = QPushButton("🔍 测试")
        test_btn.clicked.connect(self.test_pattern)
        layout.addWidget(test_btn)
        
        # 结果
        self.result_label = QLabel("测试结果将显示在这里")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_data(self):
        """加载数据"""
        if self.pattern_data:
            self.name_edit.setText(self.pattern_data.get('name', ''))
            self.desc_edit.setText(self.pattern_data.get('description', ''))
            self.pattern_edit.setPlainText(self.pattern_data.get('pattern', ''))
    
    def test_pattern(self):
        """测试模式"""
        pattern = self.pattern_edit.toPlainText().strip()
        test_text = self.test_edit.toPlainText().strip()
        
        if not pattern:
            self.result_label.setText("❌ 请输入正则表达式")
            return
        
        if not test_text:
            self.result_label.setText("❌ 请输入测试文本")
            return
        
        try:
            regex = re.compile(pattern)
            matches = regex.findall(test_text)
            
            if matches:
                result = f"✅ 匹配成功！找到 {len(matches)} 个匹配:\n"
                result += ", ".join(matches[:10])  # 显示前10个
                if len(matches) > 10:
                    result += f" ... (共{len(matches)}个)"
            else:
                result = "❌ 无匹配结果"
            
            self.result_label.setText(result)
            
        except re.error as e:
            self.result_label.setText(f"❌ 正则表达式错误: {str(e)}")
        except Exception as e:
            self.result_label.setText(f"❌ 测试失败: {str(e)}")
    
    def get_pattern_data(self):
        """获取模式数据"""
        return {
            'name': self.name_edit.text().strip(),
            'description': self.desc_edit.text().strip(),
            'pattern': self.pattern_edit.toPlainText().strip()
        }


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = RegexWidget()
    widget.show()
    sys.exit(app.exec())