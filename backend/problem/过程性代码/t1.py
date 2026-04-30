import pandas as pd
import datetime
import psycopg2
from psycopg2.extras import execute_values

# 数据库连接配置
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'LAPTOP-UO3FERDN',
    'host': 'localhost',
    'port': '5432'
}

def process_and_save_csv():
    """处理CSV文件中的空值并保存到数据库"""
    try:
        # 读取CSV文件
        csv_path = '/root/my_graduation_project/data/2025-04-10新闻资讯.csv'
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"成功读取CSV文件，共有 {len(df)} 条记录")
        
        # 检查是否有空值
        null_counts = df.isnull().sum()
        print("各列空值数量：")
        print(null_counts)
        
        # 填补空的发布时间，使用前一条新闻的时间
        df['发布时间'] = df['发布时间'].fillna(method='ffill')
        
        # 处理"未知时间"的情况
        df['发布时间'] = df['发布时间'].apply(
            lambda x: None if x == "未知时间" or not x else x
        )
        
        # 填补空的品种名称
        df['品种'] = df['品种'].fillna("未知品种")
        
        # 检查处理后的空值
        null_counts_after = df.isnull().sum()
        print("处理后各列空值数量：")
        print(null_counts_after)
        
        # 保存到数据库
        save_to_database(df)
        
        # 保存处理后的CSV文件（可选）
        processed_csv_path = '/root/my_graduation_project/data/2025-04-10新闻资讯_processed.csv'
        df.to_csv(processed_csv_path, index=False, encoding='utf-8')
        print(f"处理后的数据已保存到 {processed_csv_path}")
        
        return True
        
    except Exception as e:
        print(f"处理CSV文件时出错: {e}")
        return False

def save_to_database(df):
    """保存数据到数据库"""
    try:
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 添加recorded_at列和news_type列
        df['recorded_at'] = datetime.datetime.now()
        df['news_type'] = 'origin'  # 标记为产地资讯
        
        # 重命名列
        column_mapping = {
            '标题': 'title',
            '发布时间': 'publish_time',
            '品种': 'herb_name',
            '内容': 'content'
        }
        df = df.rename(columns=column_mapping)
        
        # 转换发布时间为datetime格式
        df['publish_time'] = pd.to_datetime(df['publish_time'], errors='coerce')
        
        # 再次使用前向填充来处理可能出现的NaT值
        df['publish_time'] = df['publish_time'].fillna(method='ffill')
        
        # 按发布时间排序
        df = df.sort_values(by='publish_time', na_position='last')
        
        # 准备数据并插入
        columns = ['title', 'publish_time', 'herb_name', 'content', 'news_type', 'recorded_at']
        values = [tuple(row) for row in df[columns].values]
        
        insert_query = f"""
        INSERT INTO news_info1 ({', '.join(columns)})
        VALUES %s
        """
        
        execute_values(cursor, insert_query, values)
        conn.commit()
        
        print(f"成功保存 {len(df)} 条记录到数据库")
        return True
        
    except Exception as e:
        print(f"保存数据到数据库时出错: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    process_and_save_csv()