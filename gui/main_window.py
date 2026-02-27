"""
主窗口模块
字典管理工具的主界面
"""
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QToolBar, QStatusBar, QTabWidget,
    QMessageBox, QFileDialog, QProgressBar,
    QLabel, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QAction

from config.settings import APP_NAME, APP_VERSION, THEME_COLORS
from core.database import db_manager
from core.dictionary_manager import dictionary_manager
from gui.dictionary_widget import DictionaryWidget
from gui.analyzer_widget import AnalyzerWidget
from gui.regex_widget import RegexWidget
from gui.big_dictionary_widget import BigDictionaryWidget
from gui.combination_widget import CombinationWidget
from gui.case_transform_widget import CaseTransformWidget
from gui.url_analyzer_widget import URLAnalyzerWidget
from gui.fuzzing_widget import FuzzingWidget


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 信号定义
    status_message = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.central_widget = None
        self.tab_widget = None
        self.dictionary_widget = None
        self.analyzer_widget = None
        self.regex_widget = None
        self.big_dictionary_widget = None
        self.combination_widget = None
        self.case_transform_widget = None
        self.url_analyzer_widget = None
        self.fuzzing_widget = None
        
        # 状态栏组件
        self.status_label = None
        self.progress_bar = None
        
        # 定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.clear_status_message)
        
        self.setup_ui()
        self.connect_signals()
        self.load_initial_data()
        
        self.logger.info("主窗口初始化完成")
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1000, 700)
        
        # 设置中央部件
        self.setup_central_widget()
        
        # 设置菜单栏
        self.setup_menu_bar()
        
        # 设置工具栏
        self.setup_tool_bar()
        
        # 设置状态栏
        self.setup_status_bar()
        
        # 应用样式
        self.apply_styles()
    
    def setup_central_widget(self):
        """设置中央部件"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建标签页组件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        
        # 创建各个功能页面
        self.dictionary_widget = DictionaryWidget()
        self.analyzer_widget = AnalyzerWidget()
        self.regex_widget = RegexWidget()
        self.big_dictionary_widget = BigDictionaryWidget()
        self.combination_widget = CombinationWidget()
        self.case_transform_widget = CaseTransformWidget()
        self.url_analyzer_widget = URLAnalyzerWidget()
        self.fuzzing_widget = FuzzingWidget()
        
        # 添加标签页
        self.tab_widget.addTab(self.dictionary_widget, "📚 字典管理")
        self.tab_widget.addTab(self.combination_widget, "🔧 组合生成")
        self.tab_widget.addTab(self.case_transform_widget, "🔤 大小写转换")
        self.tab_widget.addTab(self.url_analyzer_widget, "🔗 URL分析")
        self.tab_widget.addTab(self.fuzzing_widget, "🎯 模糊测试")
        self.tab_widget.addTab(self.analyzer_widget, "📊 分析功能")
        self.tab_widget.addTab(self.big_dictionary_widget, "📦 大字典处理")
        self.tab_widget.addTab(self.regex_widget, "🔍 正则表达式")
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 新建字典
        new_dict_action = QAction("新建字典(&N)", self)
        new_dict_action.setShortcut(QKeySequence.StandardKey.New)
        new_dict_action.setStatusTip("创建新的字典")
        new_dict_action.triggered.connect(self.new_dictionary)
        file_menu.addAction(new_dict_action)
        
        # 导入字典
        import_action = QAction("导入字典(&I)", self)
        import_action.setShortcut(QKeySequence.StandardKey.Open)
        import_action.setStatusTip("从文件导入字典")
        import_action.triggered.connect(self.import_dictionary)
        file_menu.addAction(import_action)
        
        # 导出字典
        export_action = QAction("导出字典(&E)", self)
        export_action.setShortcut(QKeySequence.StandardKey.Save)
        export_action.setStatusTip("导出字典到文件")
        export_action.triggered.connect(self.export_dictionary)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 备份数据
        backup_action = QAction("备份数据(&B)", self)
        backup_action.setShortcut(QKeySequence("Ctrl+B"))
        backup_action.setStatusTip("备份所有数据")
        backup_action.triggered.connect(self.backup_data)
        file_menu.addAction(backup_action)
        
        # 恢复数据
        restore_action = QAction("恢复数据(&R)", self)
        restore_action.setShortcut(QKeySequence("Ctrl+R"))
        restore_action.setStatusTip("从备份恢复数据")
        restore_action.triggered.connect(self.restore_data)
        file_menu.addAction(restore_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        # 撤销
        undo_action = QAction("撤销(&U)", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setEnabled(False)  # 暂时禁用
        edit_menu.addAction(undo_action)
        
        # 重做
        redo_action = QAction("重做(&R)", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setEnabled(False)  # 暂时禁用
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # 查找
        find_action = QAction("查找(&F)", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.setStatusTip("查找词条")
        find_action.triggered.connect(self.show_find_dialog)
        edit_menu.addAction(find_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 去重工具
        dedup_action = QAction("去重工具(&D)", self)
        dedup_action.setStatusTip("移除重复词条")
        dedup_action.triggered.connect(self.show_dedup_dialog)
        tools_menu.addAction(dedup_action)
        
        # 正则分析
        regex_action = QAction("正则分析(&A)", self)
        regex_action.setStatusTip("使用正则表达式分析词条")
        regex_action.triggered.connect(self.show_regex_analysis)
        tools_menu.addAction(regex_action)
        
        tools_menu.addSeparator()
        
        # 设置
        settings_action = QAction("设置(&S)", self)
        settings_action.setStatusTip("系统设置和数据库管理")
        settings_action.triggered.connect(self.show_settings_dialog)
        tools_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 使用说明
        help_action = QAction("使用说明(&H)", self)
        help_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        # 快捷键
        shortcuts_action = QAction("快捷键(&K)", self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_tool_bar(self):
        """设置工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 导入按钮
        import_btn = QAction("📁 导入", self)
        import_btn.setStatusTip("导入字典文件")
        import_btn.triggered.connect(self.import_dictionary)
        toolbar.addAction(import_btn)
        
        # 导出按钮
        export_btn = QAction("💾 导出", self)
        export_btn.setStatusTip("导出字典文件")
        export_btn.triggered.connect(self.export_dictionary)
        toolbar.addAction(export_btn)
        
        toolbar.addSeparator()
        
        # 去重按钮
        dedup_btn = QAction("🔄 去重", self)
        dedup_btn.setStatusTip("去除重复词条")
        dedup_btn.triggered.connect(self.show_dedup_dialog)
        toolbar.addAction(dedup_btn)
        
        # 分析按钮
        analysis_btn = QAction("📊 分析", self)
        analysis_btn.setStatusTip("分析词条")
        analysis_btn.triggered.connect(self.show_regex_analysis)
        toolbar.addAction(analysis_btn)
        
        # 刷新按钮
        refresh_btn = QAction("🔄 刷新", self)
        refresh_btn.setStatusTip("刷新数据")
        refresh_btn.triggered.connect(self.refresh_all_data)
        toolbar.addAction(refresh_btn)
        
        toolbar.addSeparator()
        
        # 设置按钮
        settings_btn = QAction("⚙️ 设置", self)
        settings_btn.setStatusTip("应用设置")
        settings_btn.triggered.connect(self.show_settings_dialog)
        toolbar.addAction(settings_btn)
    
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_label = QLabel("就绪")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        
        status_bar = self.statusBar()
        status_bar.addWidget(self.status_label, 1)
        status_bar.addPermanentWidget(self.progress_bar)
        
        # 显示数据库统计信息
        self.update_status_info()
    
    def apply_styles(self):
        """应用样式"""
        style = f"""
        QMainWindow {{
            background-color: #f5f5f5;
        }}
        
        QTabWidget::pane {{
            border: 1px solid #c0c0c0;
            background-color: white;
        }}
        
        QTabBar::tab {{
            background-color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {THEME_COLORS['primary']};
            color: white;
        }}
        
        QTabBar::tab:hover {{
            background-color: #d0d0d0;
        }}
        
        QToolBar {{
            background-color: #f0f0f0;
            border: 1px solid #d0d0d0;
            spacing: 3px;
            padding: 2px;
        }}
        
        QToolBar QAction {{
            padding: 5px 10px;
            margin: 1px;
        }}
        
        QStatusBar {{
            background-color: #f0f0f0;
            border-top: 1px solid #d0d0d0;
        }}
        """
        
        self.setStyleSheet(style)
    
    def connect_signals(self):
        """连接信号"""
        # 连接状态消息信号
        self.status_message.connect(self.show_status_message)
        self.progress_update.connect(self.update_progress)
        
        # 连接子组件信号
        if self.dictionary_widget:
            self.dictionary_widget.status_message.connect(self.show_status_message)
            self.dictionary_widget.progress_update.connect(self.update_progress)
        
        if self.analyzer_widget:
            self.analyzer_widget.status_message.connect(self.show_status_message)
            self.analyzer_widget.progress_update.connect(self.update_progress)
        
        if self.regex_widget:
            self.regex_widget.status_message.connect(self.show_status_message)
        
        if self.big_dictionary_widget:
            self.big_dictionary_widget.status_message.connect(self.show_status_message)
        
        # 连接新功能组件信号
        if self.combination_widget:
            self.combination_widget.status_message.connect(self.show_status_message)
        
        if self.case_transform_widget:
            self.case_transform_widget.status_message.connect(self.show_status_message)
        
        if self.url_analyzer_widget:
            self.url_analyzer_widget.status_message.connect(self.show_status_message)
        
        if self.fuzzing_widget:
            self.fuzzing_widget.status_message.connect(self.show_status_message)
    
    def load_initial_data(self):
        """加载初始数据"""
        try:
            # 更新状态信息
            self.update_status_info()
            
            # 刷新各个组件的数据
            if self.dictionary_widget:
                self.dictionary_widget.refresh_data()
            
            self.logger.info("初始数据加载完成")
            
        except Exception as e:
            self.logger.error(f"加载初始数据失败: {e}")
            self.show_error_message("数据加载失败", str(e))
    
    def show_status_message(self, message: str, timeout: int = 3000):
        """显示状态消息"""
        self.status_label.setText(message)
        if timeout > 0:
            self.status_timer.start(timeout)
    
    def clear_status_message(self):
        """清除状态消息"""
        self.status_timer.stop()
        self.update_status_info()
    
    def update_progress(self, value: int):
        """更新进度条"""
        if value < 0:
            self.progress_bar.setVisible(False)
        else:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(value)
    
    def update_status_info(self):
        """更新状态信息"""
        try:
            stats = db_manager.get_database_stats()
            dict_count = stats.get('dictionaries_count', 0)
            word_count = stats.get('words_count', 0)
            
            status_text = f"字典: {dict_count} 个 | 词条: {word_count} 个"
            self.status_label.setText(status_text)
            
        except Exception as e:
            self.logger.error(f"更新状态信息失败: {e}")
            self.status_label.setText("就绪")
    
    def show_error_message(self, title: str, message: str):
        """显示错误消息"""
        QMessageBox.critical(self, title, message)
    
    def show_info_message(self, title: str, message: str):
        """显示信息消息"""
        QMessageBox.information(self, title, message)
    
    def show_warning_message(self, title: str, message: str):
        """显示警告消息"""
        QMessageBox.warning(self, title, message)
    
    # 菜单动作实现
    def new_dictionary(self):
        """新建字典"""
        if self.dictionary_widget:
            self.dictionary_widget.create_new_dictionary()
    
    def import_dictionary(self):
        """导入字典"""
        if self.dictionary_widget:
            self.dictionary_widget.import_dictionary()
    
    def export_dictionary(self):
        """导出字典"""
        if self.dictionary_widget:
            self.dictionary_widget.export_dictionary()
    
    def backup_data(self):
        """备份数据"""
        try:
            from datetime import datetime
            file_path, _ = QFileDialog.getSaveFileName(
                self, "备份数据", f"dictionary_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                "备份文件 (*.zip)"
            )
            
            if file_path:
                from core.exporter import exporter
                success = exporter.create_backup(file_path, include_data=True)
                
                if success:
                    self.show_info_message("备份成功", f"数据已备份到: {file_path}")
                else:
                    self.show_error_message("备份失败", "备份过程中发生错误")
                    
        except Exception as e:
            self.logger.error(f"备份数据失败: {e}")
            self.show_error_message("备份失败", str(e))
    
    def restore_data(self):
        """恢复数据"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "恢复数据", "", "备份文件 (*.zip)"
            )
            
            if file_path:
                reply = QMessageBox.question(
                    self, "确认恢复", 
                    "恢复数据将覆盖当前所有数据，是否继续？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    from core.exporter import exporter
                    success = exporter.restore_backup(file_path)
                    
                    if success:
                        self.show_info_message("恢复成功", "数据已从备份恢复，请重启应用程序")
                        self.load_initial_data()  # 重新加载数据
                    else:
                        self.show_error_message("恢复失败", "恢复过程中发生错误")
                        
        except Exception as e:
            self.logger.error(f"恢复数据失败: {e}")
            self.show_error_message("恢复失败", str(e))
    
    def show_find_dialog(self):
        """显示查找对话框"""
        if self.dictionary_widget:
            self.dictionary_widget.show_search_dialog()
    
    def show_dedup_dialog(self):
        """显示去重对话框"""
        if self.dictionary_widget:
            self.dictionary_widget.show_dedup_dialog()
    
    def show_regex_analysis(self):
        """显示正则分析"""
        self.tab_widget.setCurrentIndex(1)  # 切换到分析页面
    
    def refresh_all_data(self):
        """刷新所有数据"""
        try:
            # 刷新字典组件
            if self.dictionary_widget:
                self.dictionary_widget.refresh_data()
            
            # 刷新分析组件的字典列表
            if self.analyzer_widget:
                self.analyzer_widget.refresh_dictionaries()
            
            self.show_status_message("数据已刷新")
            
        except Exception as e:
            self.logger.error(f"刷新数据失败: {e}")
            self.show_error_message("刷新失败", str(e))
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        try:
            from gui.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self)
            dialog.exec()
            
            # 刷新数据以反映可能的更改
            self.refresh_all_data()
            
        except Exception as e:
            self.logger.error(f"显示设置对话框失败: {e}")
            self.show_error_message("设置失败", str(e))
    
    def show_help(self):
        """显示帮助"""
        help_text = """
        <h3>GraffitiMap 使用说明</h3>
        
        <h4>主要功能：</h4>
        <ul>
        <li><b>字典管理</b>：创建、导入、导出和管理字典</li>
        <li><b>组合生成</b>：多区域内容的笛卡尔积组合生成</li>
        <li><b>大小写转换</b>：多种策略的随机大小写转换</li>
        <li><b>URL分析</b>：过滤和分析带参数的URL</li>
        <li><b>模糊测试</b>：路径变换、参数注入等模糊测试变体生成</li>
        <li><b>去重功能</b>：多种策略去除重复词条</li>
        <li><b>正则分析</b>：使用正则表达式分析和分类词条</li>
        <li><b>相似性分析</b>：分析两个字典的相似度</li>
        <li><b>大字典处理</b>：支持大文件合并和处理</li>
        <li><b>文件支持</b>：支持TXT、JSON、CSV、Excel格式</li>
        </ul>
        
        <h4>相似度算法说明：</h4>
        <ul>
        <li><b>Jaccard相似度</b>：适用于集合比较，计算交集与并集的比值。适合分析两个字典的重叠程度，值越高表示共同词条越多。</li>
        <li><b>余弦相似度</b>：基于向量空间模型，适合分析词条分布的相似性。在字典大小差异较大时表现更稳定。</li>
        <li><b>编辑距离相似度</b>：基于集合差异计算，反映两个字典的结构差异。适合评估字典的整体相似程度。</li>
        </ul>
        
        <h4>算法选择建议：</h4>
        <ul>
        <li><b>字典重叠分析</b>：推荐使用Jaccard相似度</li>
        <li><b>不同规模字典比较</b>：推荐使用余弦相似度</li>
        <li><b>整体结构比较</b>：推荐使用编辑距离相似度</li>
        </ul>
        
        <h4>快速开始：</h4>
        <ol>
        <li>点击"新建字典"创建字典或"导入字典"导入现有文件</li>
        <li>在字典管理页面添加或编辑词条</li>
        <li>使用分析功能进行正则表达式匹配或相似性分析</li>
        <li>导出处理后的字典</li>
        </ol>
        """
        
        QMessageBox.about(self, "使用说明", help_text)
    
    def show_shortcuts(self):
        """显示快捷键"""
        shortcuts_text = """
        <h3>快捷键列表</h3>
        
        <table>
        <tr><td><b>Ctrl+N</b></td><td>新建字典</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>导入字典</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>导出字典</td></tr>
        <tr><td><b>Ctrl+F</b></td><td>查找词条</td></tr>
        <tr><td><b>Ctrl+B</b></td><td>备份数据</td></tr>
        <tr><td><b>Ctrl+R</b></td><td>恢复数据</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>退出程序</td></tr>
        <tr><td><b>F1</b></td><td>显示帮助</td></tr>
        </table>
        """
        
        QMessageBox.about(self, "快捷键", shortcuts_text)
    
    def show_about(self):
        """显示关于对话框"""
        about_text = f"""
        <h3>{APP_NAME}</h3>
        <p>版本: {APP_VERSION}</p>
        
        <p>一个功能强大的字典管理和分析工具，支持：</p>
        <ul>
        <li>多格式文件导入导出（TXT、JSON、CSV、Excel）</li>
        <li>组合模式字典生成</li>
        <li>随机大小写转换</li>
        <li>URL过滤分析</li>
        <li>模糊测试字典生成</li>
        <li>智能去重功能</li>
        <li>正则表达式分析</li>
        <li>字典相似性分析</li>
        <li>数据备份恢复</li>
        </ul>
        
        <p>基于 PyQt6 开发</p>
        <p>© 2026 TwoconsinElizabech</p>
        """
        
        QMessageBox.about(self, "关于", about_text)
    
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self, "确认退出", 
            "确定要退出字典管理工具吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("应用程序正常退出")
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())