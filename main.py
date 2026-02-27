"""
字典管理工具主启动文件
提供应用程序的入口点和初始化功能
"""
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 检查PyQt6并提供解决方案
def check_and_fix_pyqt6():
    """检查PyQt6并提供修复建议"""
    try:
        # 尝试导入PyQt6
        from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
        from PyQt6.QtCore import Qt, QDir, QTimer, QThread, pyqtSignal
        from PyQt6.QtGui import QIcon, QPixmap, QPainter, QFont
        return True, None
        
    except ImportError as e:
        error_msg = str(e)
        
        # 记录详细错误信息到日志
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        with open(log_dir / "error.log", "a", encoding="utf-8") as f:
            f.write(f"PyQt6导入失败: {error_msg}\n")
            f.write(f"Python路径: {sys.executable}\n")
            f.write(f"工作目录: {os.getcwd()}\n")
        
        # 根据错误类型提供具体解决方案
        if "DLL load failed" in error_msg:
            if "QtCore" in error_msg:
                print("❌ PyQt6 DLL加载失败 - QtCore模块")
                print("\n🔧 这是Anaconda环境中的常见问题，请执行以下修复步骤:")
                print("\n方法1 - 自动修复 (推荐):")
                print("  python fix_pyqt6_dll.py")
                print("\n方法2 - 手动修复:")
                print("  1. conda uninstall pyqt")
                print("  2. conda install -c conda-forge pyqt")
                print("\n方法3 - 使用pip:")
                print("  1. pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip")
                print("  2. pip install PyQt6")
                print("\n方法4 - 安装VC++ Redistributable:")
                print("  下载: https://aka.ms/vs/17/release/vc_redist.x64.exe")
                
            else:
                print("❌ PyQt6 DLL加载失败")
                print("请安装Microsoft Visual C++ Redistributable")
                print("下载: https://aka.ms/vs/17/release/vc_redist.x64.exe")
        else:
            print("❌ PyQt6未安装或安装不完整")
            print("请运行: pip install PyQt6")
        
        print(f"\n详细错误信息: {error_msg}")
        print("错误日志已保存到: logs/error.log")
        
        return False, error_msg

# 检查PyQt6
pyqt6_ok, error_msg = check_and_fix_pyqt6()

if not pyqt6_ok:
    print("\n💡 建议:")
    print("1. 如果是Anaconda环境，运行: python fix_pyqt6_dll.py")
    print("2. 或者使用命令行模式: python start_graffiti.py")
    sys.exit(1)

# 如果检查通过，导入PyQt6模块
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtCore import Qt, QDir, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QFont

from gui.main_window import MainWindow
from core.database import db_manager
from config.settings import APP_NAME, APP_VERSION, DATABASE_PATH, LOG_LEVEL, THEME_COLORS


class InitializationWorker(QThread):
    """初始化工作线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def run(self):
        """执行初始化任务"""
        try:
            # 步骤1: 设置数据库
            self.progress.emit(20, "初始化数据库...")
            if not self.setup_database():
                self.finished.emit(False, "数据库初始化失败")
                return
            
            # 步骤2: 加载配置
            self.progress.emit(40, "加载配置文件...")
            self.load_configurations()
            
            # 步骤3: 初始化核心模块
            self.progress.emit(60, "初始化核心模块...")
            self.initialize_core_modules()
            
            # 步骤4: 预加载数据
            self.progress.emit(80, "预加载数据...")
            self.preload_data()
            
            # 完成
            self.progress.emit(100, "初始化完成")
            self.finished.emit(True, "初始化成功")
            
        except Exception as e:
            logging.error(f"初始化失败: {e}")
            self.finished.emit(False, f"初始化失败: {str(e)}")
    
    def setup_database(self) -> bool:
        """设置数据库"""
        try:
            # 确保数据目录存在
            db_path = Path(DATABASE_PATH)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 初始化数据库
            db_manager.create_tables()
            logging.info("数据库初始化成功")
            return True
            
        except Exception as e:
            logging.error(f"数据库初始化失败: {e}")
            return False
    
    def load_configurations(self):
        """加载配置文件"""
        try:
            # 加载正则表达式配置
            from utils.regex_helper import regex_helper
            # regex_helper 在初始化时已经自动加载配置
            
            # 加载其他配置
            logging.info("配置文件加载成功")
            
        except Exception as e:
            logging.warning(f"配置文件加载失败: {e}")
    
    def initialize_core_modules(self):
        """初始化核心模块"""
        try:
            # 初始化管理器
            from core.dictionary_manager import dictionary_manager
            
            # 预热模块
            dictionary_manager.get_all_dictionaries()
            
            logging.info("核心模块初始化成功")
            
        except Exception as e:
            logging.warning(f"核心模块初始化失败: {e}")
    
    def preload_data(self):
        """预加载数据"""
        try:
            # 这里可以预加载一些常用数据
            logging.info("数据预加载完成")
            
        except Exception as e:
            logging.warning(f"数据预加载失败: {e}")


class SplashScreen(QSplashScreen):
    """启动画面"""
    
    def __init__(self):
        # 创建启动画面图片
        pixmap = self.create_splash_pixmap()
        super().__init__(pixmap)
        
        # 设置属性
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 初始化工作线程
        self.init_worker = InitializationWorker()
        self.init_worker.progress.connect(self.update_progress)
        self.init_worker.finished.connect(self.on_init_finished)
        
        # 状态
        self.init_success = False
        self.error_message = ""
    
    def create_splash_pixmap(self) -> QPixmap:
        """创建启动画面图片"""
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.GlobalColor.white)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景渐变
        from PyQt6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, 0, 300)
        gradient.setColorAt(0, Qt.GlobalColor.lightGray)
        gradient.setColorAt(1, Qt.GlobalColor.white)
        painter.fillRect(pixmap.rect(), gradient)
        
        # 绘制标题
        painter.setPen(Qt.GlobalColor.black)
        title_font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, APP_NAME)
        
        # 绘制版本信息
        version_font = QFont("Arial", 12)
        painter.setFont(version_font)
        painter.drawText(20, 280, f"版本 {APP_VERSION}")
        
        painter.end()
        return pixmap
    
    def start_initialization(self):
        """开始初始化"""
        self.show()
        self.showMessage("正在启动...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
        self.init_worker.start()
    
    def update_progress(self, progress: int, message: str):
        """更新进度"""
        self.showMessage(f"{message} ({progress}%)", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
    
    def on_init_finished(self, success: bool, message: str):
        """初始化完成"""
        self.init_success = success
        self.error_message = message
        
        if success:
            self.showMessage("启动成功！", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
            QTimer.singleShot(500, self.close)  # 延迟关闭
        else:
            self.showMessage(f"启动失败: {message}", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
            QTimer.singleShot(2000, self.close)  # 显示错误信息后关闭


def setup_logging():
    """设置日志配置"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "app.log"
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库日志级别
    logging.getLogger('PyQt6').setLevel(logging.WARNING)


def setup_application(app: QApplication):
    """设置应用程序属性"""
    # 基本信息
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Dictionary Tools")
    app.setOrganizationDomain("dictionary-tools.local")
    
    # 高DPI支持 - 在较新版本的PyQt6中，高DPI缩放是默认启用的
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    except AttributeError:
        # 在PyQt6 6.5+中，这个属性已被移除，因为高DPI缩放默认启用
        pass
    
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # 在较新版本中可能也被移除
        pass
    
    # 设置应用程序图标（如果存在）
    icon_path = project_root / "resources" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # 设置样式
    app.setStyle("Fusion")  # 使用Fusion样式以获得更好的跨平台外观


def check_system_requirements() -> tuple[bool, str]:
    """检查系统要求"""
    try:
        # 检查Python版本
        if sys.version_info < (3, 8):
            return False, "需要Python 3.8或更高版本"
        
        # 检查PyQt6
        try:
            from PyQt6.QtCore import QT_VERSION_STR
            logging.info(f"PyQt6 版本: {QT_VERSION_STR}")
        except ImportError:
            return False, "未找到PyQt6，请安装PyQt6"
        
        # 检查写入权限
        try:
            test_file = project_root / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
        except Exception:
            return False, "程序目录没有写入权限"
        
        return True, "系统要求检查通过"
        
    except Exception as e:
        return False, f"系统要求检查失败: {str(e)}"


def check_dependencies():
    """检查依赖包"""
    required_packages = [
        ('PyQt6', 'PyQt6'),
        ('pandas', 'pandas'),
        ('chardet', 'chardet'),
        ('openpyxl', 'openpyxl')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        return False, f"缺少以下依赖包: {', '.join(missing_packages)}"
    
    return True, "依赖包检查通过"


def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.critical("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))
    
    # 显示错误对话框
    try:
        from PyQt6.QtWidgets import QApplication
        if QApplication.instance():
            QMessageBox.critical(
                None, "严重错误",
                f"程序遇到未处理的错误:\n{exc_type.__name__}: {exc_value}\n\n"
                "详细信息已记录到日志文件中。"
            )
    except:
        pass


def main():
    """主函数"""
    # 设置全局异常处理器
    sys.excepthook = handle_exception
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info(f"启动 {APP_NAME} v{APP_VERSION}")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {os.getcwd()}")
    logger.info(f"项目根目录: {project_root}")
    logger.info("=" * 50)
    
    # 检查系统要求
    requirements_ok, requirements_msg = check_system_requirements()
    if not requirements_ok:
        logger.error(f"系统要求检查失败: {requirements_msg}")
        print(f"错误: {requirements_msg}")
        return 1
    
    logger.info(requirements_msg)
    
    # 检查依赖包
    deps_ok, deps_msg = check_dependencies()
    if not deps_ok:
        logger.error(f"依赖检查失败: {deps_msg}")
        print(f"错误: {deps_msg}")
        print("请运行: pip install -r requirements.txt")
        return 1
    
    logger.info(deps_msg)
    
    # 创建应用程序
    app = QApplication(sys.argv)
    setup_application(app)
    
    try:
        # 显示启动画面
        splash = SplashScreen()
        splash.start_initialization()
        
        # 等待初始化完成
        while splash.init_worker.isRunning():
            app.processEvents()
        
        # 检查初始化结果
        if not splash.init_success:
            QMessageBox.critical(
                None, "启动失败", 
                f"程序初始化失败:\n{splash.error_message}\n\n请检查日志文件获取详细信息。"
            )
            return 1
        
        # 创建主窗口
        logger.info("创建主窗口...")
        main_window = MainWindow()
        
        # 等待启动画面关闭
        while splash.isVisible():
            app.processEvents()
        
        # 显示主窗口
        main_window.show()
        logger.info("主窗口显示成功")
        
        # 记录启动完成
        logger.info(f"{APP_NAME} 启动完成")
        
        # 运行应用程序事件循环
        exit_code = app.exec()
        
        logger.info(f"{APP_NAME} 正常退出，退出码: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"应用程序运行时错误: {e}", exc_info=True)
        QMessageBox.critical(
            None, "运行时错误", 
            f"应用程序运行时遇到错误:\n{str(e)}\n\n详细信息已记录到日志文件中。"
        )
        return 1
    
    finally:
        # 清理资源
        try:
            if 'db_manager' in globals():
                db_manager.close()
            logger.info("资源清理完成")
        except Exception as e:
            logger.warning(f"资源清理时出现警告: {e}")


if __name__ == "__main__":
    sys.exit(main())