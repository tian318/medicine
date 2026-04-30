import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import time
import logging
import os
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志
# 使用相对路径作为日志文件路径
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'weather_data.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('weather_fetcher')

# 数据库连接配置
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}

# Open-Meteo API配置
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

# 请求延迟配置（秒）
BASE_DELAY = 3
MAX_DELAY = 30
BACKOFF_FACTOR = 2

def get_db_connection():
    """创建数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

def get_location_mappings():
    """从数据库获取地点映射信息"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        query = "SELECT location_name, latitude, longitude FROM location_mapping"
        df = pd.read_sql(query, conn)
        
        # 创建地点名称到经纬度的映射字典
        location_map = {}
        for _, row in df.iterrows():
            location_map[row['location_name']] = {
                'latitude': row['latitude'],
                'longitude': row['longitude']
            }
        
        return location_map
    except Exception as e:
        logger.error(f"获取地点映射失败: {e}")
        return {}
    finally:
        conn.close()

def get_unique_locations_and_dates():
    """从herb_prices表获取唯一的地点和日期组合"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        query = """
        SELECT DISTINCT location, DATE(recorded_at) as date
        FROM herb_prices
        ORDER BY location, date
        """
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        logger.error(f"获取唯一地点和日期失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_existing_weather_data():
    """获取已存在的天气数据记录，用于避免重复获取"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT location, date, 
               (temperature IS NOT NULL AND 
                temperature_min IS NOT NULL AND 
                temperature_max IS NOT NULL AND 
                precipitation IS NOT NULL AND 
                humidity IS NOT NULL AND 
                wind_speed IS NOT NULL AND 
                sunshine_duration IS NOT NULL) as is_complete
        FROM weather_data
        """
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        logger.error(f"获取已存在的天气数据失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def create_requests_session():
    """创建带有重试机制的请求会话"""
    session = requests.Session()
    
    # 配置重试策略
    retries = Retry(
        total=5,  # 最大重试次数
        backoff_factor=1,  # 重试间隔时间
        status_forcelist=[500, 502, 503, 504],  # 需要重试的HTTP状态码
        allowed_methods=["GET"]  # 允许重试的请求方法
    )
    
    # 将重试策略应用到会话
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def fetch_weather_data(latitude, longitude, start_date, end_date, retry_count=0):
    """从Open-Meteo API获取天气数据"""
    try:
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': start_date,
            'end_date': end_date,
            'daily': 'temperature_2m_mean,temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_mean,sunshine_duration',
            'timezone': 'Asia/Shanghai'
        }
        
        session = create_requests_session()
        
        # 计算当前重试的延迟时间
        delay = min(BASE_DELAY * (BACKOFF_FACTOR ** retry_count), MAX_DELAY)
        # 添加随机变化，避免固定间隔请求
        jitter = random.uniform(0, 2)
        actual_delay = delay + jitter
        
        logger.info(f"请求延迟: {actual_delay:.2f}秒")
        time.sleep(actual_delay)
        
        response = session.get(OPEN_METEO_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429 and retry_count < 5:  # 如果遇到限流
            retry_count += 1
            logger.warning(f"API请求被限流，第{retry_count}次重试...")
            time.sleep(delay * 2)  # 增加更长的延迟
            return fetch_weather_data(latitude, longitude, start_date, end_date, retry_count)
        else:
            logger.error(f"API请求失败: {response.status_code} - {response.text}")
            return None
                
    except Exception as e:
        logger.error(f"获取天气数据失败: {e}")
        if retry_count < 5:
            retry_count += 1
            logger.warning(f"发生错误，第{retry_count}次重试...")
            time.sleep(delay * 2)
            return fetch_weather_data(latitude, longitude, start_date, end_date, retry_count)
        return None

def process_weather_data(data, location):
    """处理API返回的天气数据"""
    if not data or 'daily' not in data:
        return pd.DataFrame()
    
    daily = data['daily']
    
    # 创建数据框并处理数值范围
    df = pd.DataFrame({
        'location': location,
        'latitude': data['latitude'],
        'longitude': data['longitude'],
        'date': daily['time'],
        'temperature': pd.Series(daily.get('temperature_2m_mean', [None] * len(daily['time']))).round(2),
        'temperature_min': pd.Series(daily.get('temperature_2m_min', [None] * len(daily['time']))).round(2),
        'temperature_max': pd.Series(daily.get('temperature_2m_max', [None] * len(daily['time']))).round(2),
        'precipitation': pd.Series(daily.get('precipitation_sum', [None] * len(daily['time']))).round(2),
        'humidity': pd.Series(daily.get('relative_humidity_2m_mean', [None] * len(daily['time']))).round(2),
        'wind_speed': pd.Series(daily.get('wind_speed_10m_mean', [None] * len(daily['time']))).round(2),
        'sunshine_duration': pd.Series(daily.get('sunshine_duration', [None] * len(daily['time']))).div(3600).round(2),  # 转换为小时
        'recorded_at': datetime.now()
    })
    
    # 将 NaN 转换为 None，避免数据库插入问题
    df = df.where(pd.notnull(df), None)
    
    return df

def save_weather_data(df):
    """将天气数据保存到数据库"""
    if df.empty:
        return 0
    
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        
        # 准备数据，确保所有数值都是Python原生类型
        data = []
        for _, row in df.iterrows():
            # 安全转换函数，处理可能的NaN和None
            def safe_convert(value):
                if pd.isna(value) or value is None:
                    return None
                return float(value)
                
            data.append((
                row['location'], 
                float(row['latitude']) if row['latitude'] is not None else None, 
                float(row['longitude']) if row['longitude'] is not None else None, 
                row['date'], 
                safe_convert(row['temperature']), 
                safe_convert(row['temperature_min']), 
                safe_convert(row['temperature_max']), 
                safe_convert(row['precipitation']), 
                safe_convert(row['humidity']),
                safe_convert(row['wind_speed']), 
                safe_convert(row['sunshine_duration']), 
                row['recorded_at']
            ))
        
        # 插入数据
        query = """
        INSERT INTO weather_data 
        (location, latitude, longitude, date, temperature, temperature_min, 
         temperature_max, precipitation, humidity, wind_speed, sunshine_duration, recorded_at)
        VALUES %s
        ON CONFLICT (location, date) 
        DO UPDATE SET
            temperature = COALESCE(EXCLUDED.temperature, weather_data.temperature),
            temperature_min = COALESCE(EXCLUDED.temperature_min, weather_data.temperature_min),
            temperature_max = COALESCE(EXCLUDED.temperature_max, weather_data.temperature_max),
            precipitation = COALESCE(EXCLUDED.precipitation, weather_data.precipitation),
            humidity = COALESCE(EXCLUDED.humidity, weather_data.humidity),
            wind_speed = COALESCE(EXCLUDED.wind_speed, weather_data.wind_speed),
            sunshine_duration = COALESCE(EXCLUDED.sunshine_duration, weather_data.sunshine_duration),
            recorded_at = EXCLUDED.recorded_at
        """
        
        execute_values(cursor, query, data)
        conn.commit()
        
        return len(data)
    except Exception as e:
        conn.rollback()
        logger.error(f"保存天气数据失败: {e}")
        return 0
    finally:
        conn.close()

def main():
    """主函数"""
    logger.info("开始获取天气数据")
    
    # 获取地点映射
    location_map = get_location_mappings()
    if not location_map:
        logger.error("无法获取地点映射，程序退出")
        return
    
    # 获取需要查询天气数据的地点和日期
    locations_dates = get_unique_locations_and_dates()
    if locations_dates.empty:
        logger.error("无法获取地点和日期信息，程序退出")
        return
    
    # 获取已存在的天气数据记录
    existing_data = get_existing_weather_data()
    if not existing_data.empty:
        logger.info(f"已有 {len(existing_data)} 条天气记录，其中完整记录 {existing_data['is_complete'].sum()} 条")
    
    # 创建地点-日期的完整记录集合，用于跳过已有完整数据的记录
    complete_records = set()
    if not existing_data.empty:
        for _, row in existing_data[existing_data['is_complete']].iterrows():
            complete_records.add((row['location'], row['date'].strftime('%Y-%m-%d')))
    
    # 按地点分组处理
    total_saved = 0
    for location, group in locations_dates.groupby('location'):
        if location not in location_map:
            logger.warning(f"地点 '{location}' 未在映射表中找到，跳过")
            continue
        
        coords = location_map[location]
        
        # 获取该地点的日期范围
        min_date = group['date'].min()
        max_date = group['date'].max()
        
        # 为了减少API调用次数，按月份分批获取数据
        current_date = min_date
        while current_date <= max_date:
            # 计算当前批次的结束日期（当月最后一天或max_date中较小的一个）
            next_month = current_date.replace(day=28) + timedelta(days=4)
            end_of_month = next_month - timedelta(days=next_month.day)
            batch_end = min(end_of_month, max_date)
            
            # 检查该批次是否有需要获取的数据
            batch_dates = pd.date_range(current_date, batch_end)
            need_fetch = False
            
            for date in batch_dates:
                date_str = date.strftime('%Y-%m-%d')
                if (location, date_str) not in complete_records:
                    need_fetch = True
                    break
            
            if not need_fetch:
                logger.info(f"跳过 {location} 从 {current_date} 到 {batch_end} 的天气数据，已有完整记录")
                current_date = batch_end + timedelta(days=1)
                continue
            
            logger.info(f"获取 {location} 从 {current_date} 到 {batch_end} 的天气数据")
            
            # 获取天气数据
            weather_data = fetch_weather_data(
                coords['latitude'], 
                coords['longitude'],
                current_date.strftime('%Y-%m-%d'),
                batch_end.strftime('%Y-%m-%d')
            )
            
            if weather_data:
                # 处理并保存数据
                df = process_weather_data(weather_data, location)
                saved = save_weather_data(df)
                total_saved += saved
                logger.info(f"成功保存 {saved} 条天气记录")
            
            # 移动到下一个月
            current_date = batch_end + timedelta(days=1)
            
            # 添加随机延迟，避免API请求过于频繁
            delay = random.uniform(BASE_DELAY, BASE_DELAY * 2)
            logger.info(f"等待 {delay:.2f} 秒后继续...")
            time.sleep(delay)
    
    logger.info(f"天气数据获取完成，共保存 {total_saved} 条记录")

if __name__ == "__main__":
    main()