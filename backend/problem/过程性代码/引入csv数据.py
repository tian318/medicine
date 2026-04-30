import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import os
import re

# 数据库连接配置
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'LAPTOP-UO3FERDN',
    'host': 'localhost',
    'port': '5432'
}

def get_source_from_filename(filename):
    """从文件名判断数据来源"""
    if '产地价格' in filename:
        return 'origin'
    elif '市场价格' in filename:
        return 'market'
    return None

def get_date_from_filename(filename):
    """从文件名提取日期"""
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return match.group(1)
    return None

def process_percentage(value):
    """处理百分比字符串"""
    if pd.isna(value) or value == '0' or value == '':
        return '0%'
    return value if '%' in value else f"{value}%"

def import_price_data(file_path):
    """导入价格数据"""
    try:
        # 获取文件名
        filename = os.path.basename(file_path)
        
        # 获取数据来源和日期
        source = get_source_from_filename(filename)
        date_str = get_date_from_filename(filename)
        
        if not source or not date_str:
            print(f"错误: 无法从文件名 '{filename}' 解析数据来源或日期")
            return False
            
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 重命名列
        column_mapping = {
            '名称': 'herb_name',
            '规格': 'specification',
            '市场': 'location',
            '近期价格': 'price',
            '走势': 'trend',
            '周涨跌': 'week_change',
            '月涨跌': 'month_change',
            '年涨跌': 'year_change'
        }
        df = df.rename(columns=column_mapping)
        
        # 处理百分比数据
        for col in ['week_change', 'month_change', 'year_change']:
            df[col] = df[col].apply(process_percentage)
        
        # 添加source和recorded_at列
        df['source'] = source
        df['recorded_at'] = pd.to_datetime(date_str)
        
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 准备数据并插入
        columns = ['herb_name', 'specification', 'location', 'price', 'trend', 
                  'week_change', 'month_change', 'year_change', 'source', 'recorded_at']
        values = [tuple(row) for row in df[columns].values]
        
        insert_query = f"""
        INSERT INTO herb_prices ({', '.join(columns)})
        VALUES %s
        """
        
        execute_values(cursor, insert_query, values)
        conn.commit()
        
        print(f"成功导入 {len(df)} 条记录，来源: {source}")
        return True
        
    except Exception as e:
        print(f"导入数据错误: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

def process_daily_files(date_str):
    """处理指定日期的价格文件"""
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    file_patterns = [
        f"/root/my_graduation_project/data/{date_str}产地价格.csv",
        f"/root/my_graduation_project/data/{date_str}市场价格.csv"
    ]
    
    for pattern in file_patterns:
        file_path = os.path.join(base_dir, pattern)
        if os.path.exists(file_path):
            print(f"正在处理文件: {file_path}")
            import_price_data(file_path)
        else:
            print(f"警告: 文件不存在 - {file_path}")

def process_all_files():
    """处理data目录下所有的价格数据文件"""
    data_dir = "/root/my_graduation_project/data"
    
    # 获取所有CSV文件
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv') and ('产地价格' in f or '市场价格' in f)]
    # 按日期排序
    csv_files.sort()
    
    for filename in csv_files:
        file_path = os.path.join(data_dir, filename)
        print(f"正在处理文件: {file_path}")
        import_price_data(file_path)

def main():
    """主函数"""
    choice = input("请选择导入模式:\n1. 导入指定日期的数据\n2. 导入所有历史数据\n请输入选择(1或2): ")
    
    if choice == '1':
        date_input = input("请输入要处理的数据日期 (YYYY-MM-DD): ")
        process_daily_files(date_input)
    elif choice == '2':
        process_all_files()
    else:
        print("无效的选择")

if __name__ == "__main__":
    main()