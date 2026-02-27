"""
组合模式字典生成模块
支持多区域内容的笛卡尔积组合生成
"""
import logging
import json
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime, timedelta
from itertools import product

from .database import db_manager


class CombinationGenerator:
    """组合模式字典生成器"""
    
    def __init__(self):
        """初始化组合生成器"""
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def generate_date_range(self, start_year: int, end_year: int, date_format: str = "YYYY") -> List[str]:
        """
        生成日期范围
        
        Args:
            start_year: 开始年份
            end_year: 结束年份
            date_format: 日期格式 (YYYY, MM, DD, YYYYMMDD等)
            
        Returns:
            List[str]: 日期字符串列表
        """
        dates = []
        
        if date_format == "YYYY":
            # 年份格式
            for year in range(start_year, end_year + 1):
                dates.append(str(year))
        elif date_format == "YY":
            # 两位年份格式
            for year in range(start_year, end_year + 1):
                dates.append(str(year)[-2:])
        elif date_format == "MM":
            # 月份格式
            for month in range(1, 13):
                dates.append(f"{month:02d}")
        elif date_format == "DD":
            # 日期格式
            for day in range(1, 32):
                dates.append(f"{day:02d}")
        elif date_format == "YYYYMMDD":
            # 完整日期格式
            start_date = datetime(start_year, 1, 1)
            end_date = datetime(end_year, 12, 31)
            current_date = start_date
            
            while current_date <= end_date:
                dates.append(current_date.strftime("%Y%m%d"))
                current_date += timedelta(days=1)
        elif date_format == "MMDD":
            # 月日格式
            for month in range(1, 13):
                for day in range(1, 32):
                    try:
                        # 验证日期有效性
                        datetime(2000, month, day)
                        dates.append(f"{month:02d}{day:02d}")
                    except ValueError:
                        continue
        
        return dates
    
    def generate_number_sequence(self, start: int, end: int, format_str: str = "{:d}") -> List[str]:
        """
        生成数字序列
        
        Args:
            start: 开始数字
            end: 结束数字
            format_str: 格式字符串，如 "{:02d}" 表示两位数字补零
            
        Returns:
            List[str]: 数字字符串列表
        """
        return [format_str.format(i) for i in range(start, end + 1)]
    
    def parse_custom_input(self, input_text: str) -> List[str]:
        """
        解析自定义输入
        
        Args:
            input_text: 输入文本，支持换行分隔或逗号分隔
            
        Returns:
            List[str]: 解析后的字符串列表
        """
        if not input_text.strip():
            return []
        
        # 先按换行分割，再按逗号分割
        items = []
        for line in input_text.strip().split('\n'):
            line = line.strip()
            if line:
                if ',' in line:
                    items.extend([item.strip() for item in line.split(',') if item.strip()])
                else:
                    items.append(line)
        
        return list(set(items))  # 去重
    
    def get_dictionary_words(self, dictionary_ids: List[int]) -> List[str]:
        """
        获取字典中的词条
        
        Args:
            dictionary_ids: 字典ID列表
            
        Returns:
            List[str]: 词条列表
        """
        if not dictionary_ids:
            return []
        
        try:
            placeholders = ','.join(['?'] * len(dictionary_ids))
            query = f"""
                SELECT DISTINCT word 
                FROM words 
                WHERE dictionary_id IN ({placeholders})
                ORDER BY word
            """
            
            rows = self.db.fetch_all(query, dictionary_ids)
            return [row['word'] for row in rows]
            
        except Exception as e:
            self.logger.error(f"获取字典词条失败: {e}")
            return []
    
    def generate_combinations(self, config: Dict[str, Any]) -> Iterator[str]:
        """
        生成组合字典
        
        Args:
            config: 组合配置
                {
                    'area_a': {'type': 'custom', 'data': ['admin', 'user']},
                    'area_b': {'type': 'dictionary', 'data': [1, 2]},
                    'area_c': {'type': 'date', 'data': {'start_year': 2020, 'end_year': 2024, 'format': 'YYYY'}},
                    'connector': '_',
                    'areas_enabled': ['a', 'b', 'c']
                }
                
        Yields:
            str: 生成的组合字符串
        """
        try:
            areas_data = {}
            areas_enabled = config.get('areas_enabled', ['a', 'b', 'c'])
            connector = config.get('connector', '')
            
            # 处理A区域（自定义输入）
            if 'a' in areas_enabled and 'area_a' in config:
                area_a_config = config['area_a']
                if area_a_config['type'] == 'custom':
                    areas_data['a'] = self.parse_custom_input(area_a_config['data'])
                elif area_a_config['type'] == 'text':
                    areas_data['a'] = [area_a_config['data']] if area_a_config['data'] else []
            
            # 处理B区域（字典选择）
            if 'b' in areas_enabled and 'area_b' in config:
                area_b_config = config['area_b']
                if area_b_config['type'] == 'dictionary':
                    dictionary_ids = area_b_config['data']
                    areas_data['b'] = self.get_dictionary_words(dictionary_ids)
                elif area_b_config['type'] == 'custom':
                    areas_data['b'] = self.parse_custom_input(area_b_config['data'])
            
            # 处理C区域（日期/数字序列）
            if 'c' in areas_enabled and 'area_c' in config:
                area_c_config = config['area_c']
                if area_c_config['type'] == 'date':
                    date_config = area_c_config['data']
                    areas_data['c'] = self.generate_date_range(
                        date_config['start_year'],
                        date_config['end_year'],
                        date_config.get('format', 'YYYY')
                    )
                elif area_c_config['type'] == 'number':
                    number_config = area_c_config['data']
                    areas_data['c'] = self.generate_number_sequence(
                        number_config['start'],
                        number_config['end'],
                        number_config.get('format', '{:d}')
                    )
                elif area_c_config['type'] == 'custom':
                    areas_data['c'] = self.parse_custom_input(area_c_config['data'])
            
            # 过滤空的区域
            valid_areas = {k: v for k, v in areas_data.items() if v}
            
            if not valid_areas:
                self.logger.warning("没有有效的区域数据")
                return
            
            # 生成笛卡尔积组合
            area_keys = sorted(valid_areas.keys())
            area_values = [valid_areas[key] for key in area_keys]
            
            for combination in product(*area_values):
                if connector:
                    yield connector.join(combination)
                else:
                    yield ''.join(combination)
                    
        except Exception as e:
            self.logger.error(f"生成组合失败: {e}")
            return
    
    def save_combination_config(self, name: str, config: Dict[str, Any]) -> int:
        """
        保存组合配置
        
        Args:
            name: 配置名称
            config: 配置数据
            
        Returns:
            int: 配置ID
        """
        try:
            config_json = json.dumps(config, ensure_ascii=False)
            
            cursor = self.db.execute_query(
                """INSERT INTO combination_configs (name, config_data, created_at, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (name, config_json, datetime.now(), datetime.now())
            )
            
            config_id = cursor.lastrowid
            self.logger.info(f"保存组合配置成功: {name} (ID: {config_id})")
            return config_id
            
        except Exception as e:
            self.logger.error(f"保存组合配置失败: {e}")
            raise
    
    def load_combination_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        """
        加载组合配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        try:
            row = self.db.fetch_one(
                "SELECT * FROM combination_configs WHERE id = ?",
                (config_id,)
            )
            
            if row:
                config = json.loads(row['config_data'])
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'config': config,
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"加载组合配置失败: {e}")
            return None
    
    def get_all_combination_configs(self) -> List[Dict[str, Any]]:
        """
        获取所有组合配置
        
        Returns:
            List[Dict[str, Any]]: 配置列表
        """
        try:
            rows = self.db.fetch_all(
                "SELECT * FROM combination_configs ORDER BY created_at DESC"
            )
            
            configs = []
            for row in rows:
                try:
                    config = json.loads(row['config_data'])
                    configs.append({
                        'id': row['id'],
                        'name': row['name'],
                        'config': config,
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                except json.JSONDecodeError:
                    self.logger.warning(f"配置数据解析失败: ID {row['id']}")
                    continue
            
            return configs
            
        except Exception as e:
            self.logger.error(f"获取组合配置列表失败: {e}")
            return []
    
    def delete_combination_config(self, config_id: int) -> bool:
        """
        删除组合配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            cursor = self.db.execute_query(
                "DELETE FROM combination_configs WHERE id = ?",
                (config_id,)
            )
            
            success = cursor.rowcount > 0
            if success:
                self.logger.info(f"删除组合配置成功: ID {config_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"删除组合配置失败: {e}")
            return False
    
    def estimate_combination_count(self, config: Dict[str, Any]) -> int:
        """
        估算组合数量
        
        Args:
            config: 组合配置
            
        Returns:
            int: 估算的组合数量
        """
        try:
            areas_enabled = config.get('areas_enabled', ['a', 'b', 'c'])
            total_count = 1
            
            # 计算每个区域的数量
            for area in areas_enabled:
                area_key = f'area_{area}'
                if area_key not in config:
                    continue
                
                area_config = config[area_key]
                area_count = 0
                
                if area_config['type'] == 'custom':
                    area_count = len(self.parse_custom_input(area_config['data']))
                elif area_config['type'] == 'text':
                    area_count = 1 if area_config['data'] else 0
                elif area_config['type'] == 'dictionary':
                    dictionary_ids = area_config['data']
                    area_count = len(self.get_dictionary_words(dictionary_ids))
                elif area_config['type'] == 'date':
                    date_config = area_config['data']
                    date_list = self.generate_date_range(
                        date_config['start_year'],
                        date_config['end_year'],
                        date_config.get('format', 'YYYY')
                    )
                    area_count = len(date_list)
                elif area_config['type'] == 'number':
                    number_config = area_config['data']
                    area_count = number_config['end'] - number_config['start'] + 1
                
                if area_count > 0:
                    total_count *= area_count
                else:
                    return 0  # 如果任何区域为空，总数为0
            
            return total_count
            
        except Exception as e:
            self.logger.error(f"估算组合数量失败: {e}")
            return 0


# 全局组合生成器实例
combination_generator = CombinationGenerator()


if __name__ == "__main__":
    # 测试组合生成功能
    logging.basicConfig(level=logging.INFO)
    
    # 测试配置
    test_config = {
        'area_a': {'type': 'custom', 'data': 'admin\nuser\ntest'},
        'area_b': {'type': 'custom', 'data': 'login,panel,dashboard'},
        'area_c': {'type': 'date', 'data': {'start_year': 2023, 'end_year': 2024, 'format': 'YYYY'}},
        'connector': '_',
        'areas_enabled': ['a', 'b', 'c']
    }
    
    # 估算数量
    count = combination_generator.estimate_combination_count(test_config)
    print(f"估算组合数量: {count}")
    
    # 生成组合（限制输出数量）
    combinations = list(combination_generator.generate_combinations(test_config))
    print(f"实际生成数量: {len(combinations)}")
    print("前10个组合:")
    for i, combo in enumerate(combinations[:10]):
        print(f"  {i+1}: {combo}")