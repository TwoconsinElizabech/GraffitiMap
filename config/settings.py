"""
应用配置文件
"""
import os
from pathlib import Path

# 应用基础配置
APP_NAME = "GraffitiMap"
APP_VERSION = "2.0.0"
APP_AUTHOR = "TwoconsinElizabech"

# 路径配置
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
TEMP_DIR = BASE_DIR / "temp"

# 数据库配置
DATABASE_PATH = DATA_DIR / "dictionary.db"
BACKUP_DIR = DATA_DIR / "backups"

# 文件配置
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
SUPPORTED_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'big5']
CHUNK_SIZE = 10000  # 大文件分块处理大小

# GUI配置
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
THEME_COLORS = {
    'primary': '#007bff',
    'secondary': '#6c757d',
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545'
}

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 去重配置
SIMILARITY_THRESHOLD = 0.8
DEFAULT_DEDUP_STRATEGY = "exact"

# 导出配置
DEFAULT_EXPORT_FORMAT = "txt"
EXPORT_BATCH_SIZE = 5000

# 确保必要目录存在
def ensure_directories():
    """确保必要的目录存在"""
    directories = [DATA_DIR, BACKUP_DIR, TEMP_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# 初始化时创建目录
ensure_directories()