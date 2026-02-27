"""
URL分析界面模块
提供URL过滤、分析和统计功能的图形界面
"""
import logging
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QProgressDialog, QMessageBox, QFileDialog,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QComboBox, QSpinBox, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont

try:
    from core.url_analyzer import url_analyzer
    from core.dictionary_manager import dictionary_manager
except ImportError as e:
    print(f"URL分析模块导入失败: {e}")
    # 创建空的占位符
    class DummyAnalyzer:
        def process_url_file(self, file_path): return [], {}
        def extract_urls_from_text(self, text): return []
        def categorize_urls(self, urls): return {'with_params': [], 'without_params': []}
        def extract_common_parameters(self, urls): return {}
        def analyze_url(self, url): return {'has_params': False, 'param_count': 0, 'param_names': [], 'params': {}}
        def save_url_analysis(self, dict_id, urls): return 0
    
    url_analyzer = DummyAnalyzer()
    
    class DummyManager:
        def get_all_dictionaries(self): return []
        def create_dictionary(self, name, desc): return 0
        def add_words(self, dict_id, words): return 0
    
    dictionary_manager = DummyManager()


class URLAnalysisWorker(QThread):
    """URL分析工作线程"""
    progress = pyqtSignal(int, str)
    result_ready = pyqtSignal(list, dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, file_path: str = None, text_content: str = None):
        super().__init__()
        self.file_path = file_path
        self.text_content = text_content
    
    def run(self):
        try:
            self.progress.emit(10, "开始分析URL...")
            
            if self.file_path:
                # 处理文件
                urls, stats = url_analyzer.process_url_file(self.file_path)
                self.progress.emit(50, f"从文件中提取到 {len(urls)} 个带参数的URL")
            else:
                # 处理文本内容
                self.progress.emit(30, "从文本中提取URL...")
                all_urls = url_analyzer.extract_urls_from_text(self.text_content)
                self.progress.emit(60, f"提取到 {len(all_urls)} 个URL")
                
                # 分类和统计
                categories = url_analyzer.categorize_urls(all_urls)
                urls = categories['with_params']
                
                stats = {
                    'total_urls': len(all_urls),
                    'urls_with_params': len(urls),
                    'urls_without_params': len(categories['without_params']),
                    'multiple_params': len(categories['multiple_params']),
                    'single_param': len(categories['single_param']),
                    'domains': len(categories['domains']),
                    'common_params': url_analyzer.extract_common_parameters(urls)
                }
            
            self.progress.emit(90, "分析完成")
            self.result_ready.emit(urls, stats)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class URLAnalyzerWidget(QWidget):
    """URL分析组件"""
    
    status_message = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 组件引用
        self.input_text = None
        self.url_table = None
        self.stats_tree = None
        self.param_table = None
        
        # 工作线程
        self.analysis_worker = None
        
        # 当前结果
        self.current_urls = []
        self.current_stats = {}
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("🔗 URL过滤分析")
        title_label.setFont(QFont("", 14, QFont.Weight.Bold))
        main_layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上半部分：输入和控制
        input_widget = self.create_input_panel()
        splitter.addWidget(input_widget)
        
        # 下半部分：结果显示
        result_widget = self.create_result_panel()
        splitter.addWidget(result_widget)
        
        # 设置分割比例
        splitter.setSizes([200, 500])
        
        main_layout.addWidget(splitter)
    
    def create_input_panel(self) -> QWidget:
        """创建输入面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 输入方式选择
        input_group = QGroupBox("输入方式")
        input_layout = QVBoxLayout(input_group)
        
        # 文件输入
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("选择包含URL的文件...")
        self.file_path_input.setReadOnly(True)
        
        browse_btn = QPushButton("📁 浏览文件")
        browse_btn.clicked.connect(self.browse_file)
        
        file_layout.addWidget(QLabel("文件:"))
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(browse_btn)
        
        input_layout.addLayout(file_layout)
        
        # 文本输入
        input_layout.addWidget(QLabel("或直接输入文本:"))
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("粘贴包含URL的文本内容...")
        self.input_text.setMaximumHeight(100)
        input_layout.addWidget(self.input_text)
        
        layout.addWidget(input_group)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        analyze_btn = QPushButton("🔍 分析URL")
        analyze_btn.clicked.connect(self.analyze_urls)
        control_layout.addWidget(analyze_btn)
        
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self.clear_input)
        control_layout.addWidget(clear_btn)
        
        control_layout.addStretch()
        
        # 示例按钮
        example_btn = QPushButton("📝 填入示例")
        example_btn.clicked.connect(self.fill_example)
        control_layout.addWidget(example_btn)
        
        layout.addLayout(control_layout)
        
        return widget
    
    def create_result_panel(self) -> QWidget:
        """创建结果面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 创建水平分割器
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：URL列表
        url_widget = self.create_url_list_panel()
        h_splitter.addWidget(url_widget)
        
        # 右侧：统计和参数
        stats_widget = self.create_stats_panel()
        h_splitter.addWidget(stats_widget)
        
        # 设置分割比例
        h_splitter.setSizes([600, 400])
        
        layout.addWidget(h_splitter)
        
        return widget
    
    def create_url_list_panel(self) -> QWidget:
        """创建URL列表面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题和操作
        header_layout = QHBoxLayout()
        
        url_title = QLabel("📋 带参数的URL")
        url_title.setFont(QFont("", 12, QFont.Weight.Bold))
        header_layout.addWidget(url_title)
        
        self.url_count_label = QLabel("数量: 0")
        header_layout.addWidget(self.url_count_label)
        
        header_layout.addStretch()
        
        # 导出按钮
        export_btn = QPushButton("💾 导出URL")
        export_btn.clicked.connect(self.export_urls)
        header_layout.addWidget(export_btn)
        
        # 保存到字典按钮
        save_btn = QPushButton("📚 保存到字典")
        save_btn.clicked.connect(self.save_to_dictionary)
        header_layout.addWidget(save_btn)
        
        layout.addLayout(header_layout)
        
        # URL表格
        self.url_table = QTableWidget()
        self.url_table.setColumnCount(4)
        self.url_table.setHorizontalHeaderLabels(["序号", "URL", "域名", "参数数量"])
        
        # 设置表格属性
        header = self.url_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.url_table.setAlternatingRowColors(True)
        self.url_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.url_table.itemSelectionChanged.connect(self.on_url_selected)
        
        layout.addWidget(self.url_table)
        
        return widget
    
    def create_stats_panel(self) -> QWidget:
        """创建统计面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 统计信息
        stats_group = QGroupBox("📊 统计信息")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_tree = QTreeWidget()
        self.stats_tree.setHeaderLabel("统计项目")
        stats_layout.addWidget(self.stats_tree)
        
        layout.addWidget(stats_group)
        
        # 参数详情
        param_group = QGroupBox("🔧 参数详情")
        param_layout = QVBoxLayout(param_group)
        
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(2)
        self.param_table.setHorizontalHeaderLabels(["参数名", "出现次数"])
        
        param_header = self.param_table.horizontalHeader()
        param_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        param_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        self.param_table.setAlternatingRowColors(True)
        param_layout.addWidget(self.param_table)
        
        layout.addWidget(param_group)
        
        return widget
    
    def connect_signals(self):
        """连接信号"""
        pass
    
    def browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择URL文件", "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            self.file_path_input.setText(file_path)
            self.input_text.clear()  # 清空文本输入
    
    def clear_input(self):
        """清空输入"""
        self.file_path_input.clear()
        self.input_text.clear()
        self.current_urls.clear()
        self.current_stats.clear()
        self.update_url_table()
        self.update_stats_display()
    
    def fill_example(self):
        """填入示例"""
        example_text = """https://example.com/api/users?id=123&name=admin
https://test.com/login?redirect=/dashboard&session=abc123
https://api.site.com/v1/data?token=xyz789&format=json&limit=10
https://admin.example.com/panel?user=root&action=view
https://shop.com/products?category=electronics&page=1&sort=price
/api/v2/search?q=test&type=user&active=1
/admin/config?module=security&debug=true"""
        
        self.input_text.setPlainText(example_text)
        self.file_path_input.clear()
    
    def analyze_urls(self):
        """分析URL"""
        file_path = self.file_path_input.text().strip()
        text_content = self.input_text.toPlainText().strip()
        
        if not file_path and not text_content:
            QMessageBox.warning(self, "警告", "请选择文件或输入文本内容")
            return
        
        try:
            # 创建进度对话框
            progress_dialog = QProgressDialog("正在分析URL...", "取消", 0, 100, self)
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.show()
            
            # 创建工作线程
            self.analysis_worker = URLAnalysisWorker(file_path, text_content)
            self.analysis_worker.progress.connect(
                lambda v, m: (progress_dialog.setValue(v), progress_dialog.setLabelText(m))
            )
            self.analysis_worker.result_ready.connect(self.on_analysis_ready)
            self.analysis_worker.error_occurred.connect(self.on_analysis_error)
            self.analysis_worker.finished.connect(progress_dialog.close)
            
            # 连接取消信号
            progress_dialog.canceled.connect(self.analysis_worker.terminate)
            
            self.analysis_worker.start()
            
        except Exception as e:
            self.logger.error(f"分析URL失败: {e}")
            QMessageBox.critical(self, "错误", f"分析失败: {str(e)}")
    
    @pyqtSlot(list, dict)
    def on_analysis_ready(self, urls: List[str], stats: Dict[str, Any]):
        """分析完成"""
        self.current_urls = urls
        self.current_stats = stats
        
        self.update_url_table()
        self.update_stats_display()
        
        self.status_message.emit(f"分析完成：找到 {len(urls)} 个带参数的URL")
    
    @pyqtSlot(str)
    def on_analysis_error(self, error_message: str):
        """分析错误"""
        QMessageBox.critical(self, "分析错误", f"分析失败: {error_message}")
        self.status_message.emit(f"分析失败: {error_message}")
    
    def update_url_table(self):
        """更新URL表格"""
        self.url_table.setRowCount(len(self.current_urls))
        self.url_count_label.setText(f"数量: {len(self.current_urls)}")
        
        for row, url in enumerate(self.current_urls):
            # 分析URL
            analysis = url_analyzer.analyze_url(url)
            
            # 序号
            index_item = QTableWidgetItem(str(row + 1))
            index_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.url_table.setItem(row, 0, index_item)
            
            # URL
            url_item = QTableWidgetItem(url)
            self.url_table.setItem(row, 1, url_item)
            
            # 域名
            domain_item = QTableWidgetItem(analysis.get('domain', 'N/A'))
            self.url_table.setItem(row, 2, domain_item)
            
            # 参数数量
            param_count_item = QTableWidgetItem(str(analysis['param_count']))
            param_count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.url_table.setItem(row, 3, param_count_item)
    
    def update_stats_display(self):
        """更新统计显示"""
        # 更新统计树
        self.stats_tree.clear()
        
        if self.current_stats:
            # 基本统计
            basic_item = QTreeWidgetItem(["基本统计"])
            basic_item.addChild(QTreeWidgetItem([f"总URL数: {self.current_stats.get('total_urls', 0)}"]))
            basic_item.addChild(QTreeWidgetItem([f"带参数URL: {self.current_stats.get('urls_with_params', 0)}"]))
            basic_item.addChild(QTreeWidgetItem([f"不带参数URL: {self.current_stats.get('urls_without_params', 0)}"]))
            basic_item.addChild(QTreeWidgetItem([f"多参数URL: {self.current_stats.get('multiple_params', 0)}"]))
            basic_item.addChild(QTreeWidgetItem([f"单参数URL: {self.current_stats.get('single_param', 0)}"]))
            basic_item.addChild(QTreeWidgetItem([f"域名数量: {self.current_stats.get('domains', 0)}"]))
            
            self.stats_tree.addTopLevelItem(basic_item)
            basic_item.setExpanded(True)
        
        # 更新参数表格
        common_params = self.current_stats.get('common_params', {})
        self.param_table.setRowCount(len(common_params))
        
        for row, (param_name, count) in enumerate(common_params.items()):
            # 参数名
            param_item = QTableWidgetItem(param_name)
            self.param_table.setItem(row, 0, param_item)
            
            # 出现次数
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.param_table.setItem(row, 1, count_item)
    
    def on_url_selected(self):
        """URL选择事件"""
        current_row = self.url_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_urls):
            url = self.current_urls[current_row]
            analysis = url_analyzer.analyze_url(url)
            
            # 在状态栏显示详细信息
            params_info = ", ".join([f"{k}={v[0] if v else ''}" for k, v in analysis['params'].items()])
            self.status_message.emit(f"URL: {url} | 参数: {params_info}")
    
    def export_urls(self):
        """导出URL"""
        if not self.current_urls:
            QMessageBox.warning(self, "警告", "没有可导出的URL")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出URL", "filtered_urls.txt",
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
                
                self.status_message.emit(f"URL已导出到: {file_path}")
                
            except Exception as e:
                self.logger.error(f"导出失败: {e}")
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def export_as_txt(self, file_path: str):
        """导出为文本文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for url in self.current_urls:
                f.write(url + '\n')
    
    def export_as_json(self, file_path: str):
        """导出为JSON文件"""
        import json
        from datetime import datetime
        
        # 分析每个URL
        url_analyses = []
        for url in self.current_urls:
            analysis = url_analyzer.analyze_url(url)
            url_analyses.append(analysis)
        
        export_data = {
            'export_time': datetime.now().isoformat(),
            'statistics': self.current_stats,
            'urls': url_analyses
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def export_as_csv(self, file_path: str):
        """导出为CSV文件"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['序号', 'URL', '域名', '路径', '参数数量', '参数名称'])
            
            for i, url in enumerate(self.current_urls):
                analysis = url_analyzer.analyze_url(url)
                writer.writerow([
                    i + 1,
                    url,
                    analysis.get('domain', ''),
                    analysis.get('path', ''),
                    analysis['param_count'],
                    ', '.join(analysis['param_names'])
                ])
    
    def save_to_dictionary(self):
        """保存到字典"""
        if not self.current_urls:
            QMessageBox.warning(self, "警告", "没有可保存的URL")
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
                f"URL过滤生成的字典，包含 {len(self.current_urls)} 个带参数的URL"
            )
            
            # 添加URL
            added_count = dictionary_manager.add_words(dictionary_id, self.current_urls)
            
            # 保存分析结果到数据库
            url_analyzer.save_url_analysis(dictionary_id, self.current_urls)
            
            QMessageBox.information(
                self, "保存成功", 
                f"已创建字典 '{name}'\n成功保存 {added_count} 个URL"
            )
            
            self.status_message.emit(f"已保存 {added_count} 个URL到字典 '{name}'")
            
        except Exception as e:
            self.logger.error(f"保存到字典失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = URLAnalyzerWidget()
    widget.show()
    sys.exit(app.exec())