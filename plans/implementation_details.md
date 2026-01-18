# 字典管理工具实现细节

## 依赖包清单

```txt
PyQt6>=6.4.0
PyQt6-tools>=6.4.0
pandas>=1.5.0
chardet>=5.0.0
openpyxl>=3.0.0
xlrd>=2.0.0
```

## 核心模块详细设计

### 1. 数据库模型 (core/database.py)

#### 表结构设计
```sql
-- 字典表
CREATE TABLE dictionaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 词条表
CREATE TABLE words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    dictionary_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dictionary_id) REFERENCES dictionaries(id) ON DELETE CASCADE
);

-- 标签表
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#007bff',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 词条标签关联表
CREATE TABLE word_tags (
    word_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (word_id, tag_id),
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 索引优化
CREATE INDEX idx_words_dictionary_id ON words(dictionary_id);
CREATE INDEX idx_words_word ON words(word);
CREATE INDEX idx_word_tags_word_id ON word_tags(word_id);
CREATE INDEX idx_word_tags_tag_id ON word_tags(tag_id);
```

#### 数据库操作类
```python
class DatabaseManager:
    def __init__(self, db_path: str)
    def create_tables(self)
    def get_connection(self)
    def execute_query(self, query: str, params: tuple = ())
    def fetch_all(self, query: str, params: tuple = ())
    def fetch_one(self, query: str, params: tuple = ())
    def close(self)
```

### 2. 字典管理器 (core/dictionary_manager.py)

#### 主要功能方法
```python
class DictionaryManager:
    def create_dictionary(self, name: str, description: str = "") -> int
    def delete_dictionary(self, dictionary_id: int) -> bool
    def rename_dictionary(self, dictionary_id: int, new_name: str) -> bool
    def get_all_dictionaries(self) -> List[Dict]
    def get_dictionary_stats(self, dictionary_id: int) -> Dict
    def add_words(self, dictionary_id: int, words: List[str]) -> int
    def remove_words(self, dictionary_id: int, word_ids: List[int]) -> int
    def search_words(self, dictionary_id: int, keyword: str) -> List[Dict]
    def get_words_by_tag(self, dictionary_id: int, tag_id: int) -> List[Dict]
```

### 3. 文件处理器 (core/file_handler.py)

#### 支持的文件格式处理
```python
class FileHandler:
    def detect_encoding(self, file_path: str) -> str
    def import_txt(self, file_path: str) -> List[str]
    def import_json(self, file_path: str) -> List[str]
    def import_csv(self, file_path: str) -> List[str]
    def export_txt(self, words: List[str], file_path: str) -> bool
    def export_json(self, words: List[Dict], file_path: str) -> bool
    def export_csv(self, words: List[Dict], file_path: str) -> bool
    def batch_import(self, file_paths: List[str]) -> Dict[str, List[str]]
```

#### 文件格式示例
```python
# TXT格式：每行一个词条
word1
word2
word3

# JSON格式：结构化数据
{
    "dictionary_name": "示例字典",
    "words": [
        {"word": "word1", "tags": ["tag1", "tag2"]},
        {"word": "word2", "tags": ["tag1"]}
    ]
}

# CSV格式：表格数据
word,tags,description
word1,"tag1,tag2","描述1"
word2,"tag1","描述2"
```

### 4. 去重功能 (core/deduplicator.py)

#### 去重策略
```python
class Deduplicator:
    def exact_duplicate(self, words: List[str]) -> List[str]
    def case_insensitive_duplicate(self, words: List[str]) -> List[str]
    def similarity_duplicate(self, words: List[str], threshold: float = 0.8) -> List[str]
    def custom_duplicate(self, words: List[str], custom_func: Callable) -> List[str]
    def get_duplicate_groups(self, words: List[str]) -> Dict[str, List[str]]
    def remove_duplicates(self, dictionary_id: int, strategy: str = "exact") -> int
```

### 5. 标签管理器 (core/tag_manager.py)

#### 标签操作方法
```python
class TagManager:
    def create_tag(self, name: str, color: str = "#007bff", description: str = "") -> int
    def delete_tag(self, tag_id: int) -> bool
    def update_tag(self, tag_id: int, **kwargs) -> bool
    def get_all_tags(self) -> List[Dict]
    def add_tag_to_word(self, word_id: int, tag_id: int) -> bool
    def remove_tag_from_word(self, word_id: int, tag_id: int) -> bool
    def batch_tag_words(self, word_ids: List[int], tag_ids: List[int]) -> int
    def get_word_tags(self, word_id: int) -> List[Dict]
    def get_tag_statistics(self) -> Dict[int, int]
```

### 6. 正则分析器 (core/analyzer.py)

#### 分析功能
```python
class RegexAnalyzer:
    def __init__(self, config_path: str)
    def load_patterns(self) -> Dict
    def add_custom_pattern(self, name: str, pattern: str, description: str = "") -> bool
    def analyze_words(self, words: List[str], pattern_names: List[str]) -> Dict
    def batch_analyze(self, dictionary_id: int, pattern_names: List[str]) -> Dict
    def get_pattern_matches(self, words: List[str], pattern: str) -> List[Dict]
    def export_analysis_result(self, result: Dict, file_path: str) -> bool
```

### 7. 导出器 (core/exporter.py)

#### 导出功能
```python
class DictionaryExporter:
    def export_dictionary(self, dictionary_id: int, format: str, file_path: str) -> bool
    def export_filtered_words(self, dictionary_id: int, filters: Dict, format: str, file_path: str) -> bool
    def export_analysis_result(self, analysis_result: Dict, format: str, file_path: str) -> bool
    def create_backup(self, file_path: str) -> bool
    def restore_backup(self, file_path: str) -> bool
```

## GUI界面详细设计

### 1. 主窗口 (gui/main_window.py)

#### 窗口组件布局
```python
class MainWindow(QMainWindow):
    def __init__(self)
    def setup_ui(self)
    def setup_menu_bar(self)
    def setup_tool_bar(self)
    def setup_status_bar(self)
    def setup_central_widget(self)
    def connect_signals(self)
```

#### 菜单结构
```
文件
├── 新建字典 (Ctrl+N)
├── 导入字典 (Ctrl+O)
├── 导出字典 (Ctrl+S)
├── ─────────────
├── 备份数据 (Ctrl+B)
├── 恢复数据 (Ctrl+R)
├── ─────────────
└── 退出 (Ctrl+Q)

编辑
├── 撤销 (Ctrl+Z)
├── 重做 (Ctrl+Y)
├── ─────────────
├── 复制 (Ctrl+C)
├── 粘贴 (Ctrl+V)
├── 删除 (Delete)
├── ─────────────
├── 全选 (Ctrl+A)
└── 查找 (Ctrl+F)

工具
├── 去重工具
├── 正则分析
├── 批量标签
├── ─────────────
└── 设置 (Ctrl+,)

帮助
├── 使用说明
├── 快捷键
├── ─────────────
└── 关于
```

### 2. 字典管理界面 (gui/dictionary_widget.py)

#### 界面组件
```python
class DictionaryWidget(QWidget):
    def __init__(self)
    def setup_ui(self)
    def setup_dictionary_list(self)  # 左侧字典列表
    def setup_word_table(self)       # 右侧词条表格
    def setup_search_bar(self)       # 搜索栏
    def setup_context_menu(self)     # 右键菜单
    def load_dictionaries(self)
    def load_words(self, dictionary_id: int)
    def add_words(self, words: List[str])
    def delete_selected_words(self)
    def search_words(self, keyword: str)
```

### 3. 标签管理界面 (gui/tag_widget.py)

#### 标签界面功能
```python
class TagWidget(QWidget):
    def __init__(self)
    def setup_ui(self)
    def setup_tag_list(self)         # 标签列表
    def setup_tag_editor(self)       # 标签编辑器
    def setup_color_picker(self)     # 颜色选择器
    def create_tag(self)
    def edit_tag(self, tag_id: int)
    def delete_tag(self, tag_id: int)
    def apply_tags_to_words(self, word_ids: List[int], tag_ids: List[int])
```

### 4. 分析界面 (gui/analysis_widget.py)

#### 分析功能界面
```python
class AnalysisWidget(QWidget):
    def __init__(self)
    def setup_ui(self)
    def setup_pattern_selector(self)  # 正则模式选择
    def setup_result_viewer(self)     # 结果查看器
    def setup_progress_bar(self)      # 进度条
    def run_analysis(self, dictionary_id: int, patterns: List[str])
    def display_results(self, results: Dict)
    def export_results(self, results: Dict)
```

## 配置文件设计

### 正则表达式配置 (config/regex_patterns.json)
```json
{
  "preset_patterns": {
    "web_security": {
      "name": "Web安全相关",
      "patterns": [
        {
          "name": "SQL注入关键词",
          "pattern": "(?i)(union|select|insert|update|delete|drop|create|alter)\\s*[\\(\\s]",
          "description": "检测SQL注入相关关键词"
        },
        {
          "name": "XSS脚本标签",
          "pattern": "(?i)<\\s*(script|iframe|object|embed|form)\\s*[^>]*>",
          "description": "检测XSS攻击相关标签"
        }
      ]
    },
    "cms_paths": {
      "name": "CMS路径",
      "patterns": [
        {
          "name": "WordPress路径",
          "pattern": "wp-(admin|content|includes|config|login|cron|mail|load|blog-header|comments-post|trackback|xmlrpc)",
          "description": "WordPress相关路径和文件"
        },
        {
          "name": "ThinkPHP路径",
          "pattern": "(Application|ThinkPHP|Public|Runtime|Conf|Lib|Common|Home|Admin)/",
          "description": "ThinkPHP框架相关路径"
        }
      ]
    },
    "file_extensions": {
      "name": "文件扩展名",
      "patterns": [
        {
          "name": "可执行文件",
          "pattern": "\\.(php|asp|aspx|jsp|py|pl|cgi|sh|bat|exe)$",
          "description": "可执行文件扩展名"
        },
        {
          "name": "配置文件",
          "pattern": "\\.(conf|config|ini|xml|json|yaml|yml|properties)$",
          "description": "配置文件扩展名"
        }
      ]
    }
  },
  "custom_patterns": []
}
```

### 应用配置 (config/settings.py)
```python
import os
from pathlib import Path

# 应用基础配置
APP_NAME = "字典管理工具"
APP_VERSION = "1.0.0"
APP_AUTHOR = "开发者"

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

# 去重配置
SIMILARITY_THRESHOLD = 0.8
DEFAULT_DEDUP_STRATEGY = "exact"

# 导出配置
DEFAULT_EXPORT_FORMAT = "txt"
EXPORT_BATCH_SIZE = 5000
```

## 实现优先级

### 第一阶段：核心功能
1. 数据库模型和基础操作
2. 字典管理基础功能
3. 文件导入导出（TXT格式）
4. 简单的GUI界面

### 第二阶段：扩展功能
1. 去重功能
2. 标签管理
3. 多格式文件支持（JSON、CSV）
4. 完善GUI界面

### 第三阶段：高级功能
1. 正则表达式分析
2. 批量操作
3. 数据备份恢复
4. 性能优化

### 第四阶段：用户体验
1. 界面美化
2. 快捷键支持
3. 拖拽操作
4. 帮助文档

这个详细的实现计划为开发提供了清晰的路线图和技术规范。