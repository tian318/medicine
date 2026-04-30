import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import time
import logging
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/my_graduation_project/.log/weather_data_filler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('weather_data_filler')

# 确保日志目录存在
os.makedirs('/root/my_graduation_project/.log', exist_ok=True)

# 数据库连接配置
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'LAPTOP-UO3FERDN',
    'host': 'localhost',
    'port': '5432'
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

def get_records_with_nulls():
    """获取包含空值的天气记录"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT location, date, latitude, longitude,
               temperature, temperature_min, temperature_max, 
               precipitation, humidity, wind_speed, sunshine_duration
        FROM weather_data
        WHERE temperature IS NULL 
           OR temperature_min IS NULL 
           OR temperature_max IS NULL 
           OR precipitation IS NULL 
           OR humidity IS NULL 
           OR wind_speed IS NULL 
           OR sunshine_duration IS NULL
        ORDER BY location, date
        """
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        logger.error(f"获取包含空值的记录失败: {e}")
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

def fetch_weather_data(latitude, longitude, date, retry_count=0):
    """从Open-Meteo API获取特定日期的天气数据"""
    try:
        # 使用相同的日期作为开始和结束日期，只获取一天的数据
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': date.strftime('%Y-%m-%d'),
            'end_date': date.strftime('%Y-%m-%d'),
            'daily': 'temperature_2m_mean,temperature_2m_min,temperature_2m_max,precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_mean,sunshine_duration',
            'timezone': 'Asia/Shanghai'
        }
        
        session = create_requests_session()
        
        # 计算当前重试的延迟时间
        delay = min(BASE_DELAY * (BACKOFF_FACTOR ** retry_count), MAX_DELAY)
        logger.info(f"请求延迟: {delay}秒")
        time.sleep(delay)
        
        response = session.get(OPEN_METEO_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429 and retry_count < 5:  # 如果遇到限流
            retry_count += 1
            logger.warning(f"API请求被限流，第{retry_count}次重试...")
            time.sleep(delay * 2)  # 增加更长的延迟
            return fetch_weather_data(latitude, longitude, date, retry_count)
        else:
            logger.error(f"API请求失败: {response.status_code} - {response.text}")
            return None
                
    except Exception as e:
        logger.error(f"获取天气数据失败: {e}")
        if retry_count < 5:
            retry_count += 1
            logger.warning(f"发生错误，第{retry_count}次重试...")
            time.sleep(delay * 2)
            return fetch_weather_data(latitude, longitude, date, retry_count)
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
    
    return df

def update_weather_record(record, weather_data):
    """更新单条天气记录"""
    if weather_data.empty:
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # 从weather_data中获取第一行（应该只有一行）
        data_row = weather_data.iloc[0]
        
        # 将numpy类型转换为Python原生类型
        temperature = float(data_row['temperature']) if pd.notna(data_row['temperature']) else None
        temperature_min = float(data_row['temperature_min']) if pd.notna(data_row['temperature_min']) else None
        temperature_max = float(data_row['temperature_max']) if pd.notna(data_row['temperature_max']) else None
        precipitation = float(data_row['precipitation']) if pd.notna(data_row['precipitation']) else None
        humidity = float(data_row['humidity']) if pd.notna(data_row['humidity']) else None
        wind_speed = float(data_row['wind_speed']) if pd.notna(data_row['wind_speed']) else None
        sunshine_duration = float(data_row['sunshine_duration']) if pd.notna(data_row['sunshine_duration']) else None
        recorded_at = data_row['recorded_at']
        
        # 更新查询
        query = """
        UPDATE weather_data
        SET temperature = %s,
            temperature_min = %s,
            temperature_max = %s,
            precipitation = %s,
            humidity = %s,
            wind_speed = %s,
            sunshine_duration = %s,
            recorded_at = %s
        WHERE location = %s AND date = %s
        """
        
        cursor.execute(query, (
            temperature,
            temperature_min,
            temperature_max,
            precipitation,
            humidity,
            wind_speed,
            sunshine_duration,
            recorded_at,
            record['location'],
            record['date']
        ))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"更新天气记录失败: {e}")
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    logger.info("开始补全天气数据")
    
    # 获取包含空值的记录
    null_records = get_records_with_nulls()
    if null_records.empty:
        logger.info("没有找到包含空值的记录，程序退出")
        return
    
    logger.info(f"找到 {len(null_records)} 条包含空值的记录")
    
    # 获取地点映射（用于可能缺少经纬度的情况）
    location_map = get_location_mappings()
    
    # 逐条处理记录
    success_count = 0
    for idx, record in null_records.iterrows():
        location = record['location']
        date = record['date']
        
        # 获取经纬度，优先使用记录中的值，如果为空则从映射中获取
        latitude = record['latitude']
        longitude = record['longitude']
        
        if pd.isna(latitude) or pd.isna(longitude):
            if location in location_map:
                latitude = location_map[location]['latitude']
                longitude = location_map[location]['longitude']
            else:
                logger.warning(f"无法获取 {location} 的经纬度，跳过")
                continue
        
        logger.info(f"处理 {location} 在 {date} 的天气数据 ({idx+1}/{len(null_records)})")
        
        # 获取天气数据
        weather_data = fetch_weather_data(latitude, longitude, date)
        
        if weather_data:
            # 处理数据
            df = process_weather_data(weather_data, location)
            
            if not df.empty:
                # 更新记录
                if update_weather_record(record, df):
                    success_count += 1
                    logger.info(f"成功更新 {location} 在 {date} 的天气数据")
                else:
                    logger.warning(f"更新 {location} 在 {date} 的天气数据失败")
            else:
                logger.warning(f"处理 {location} 在 {date} 的天气数据失败，返回空数据")
        else:
            logger.warning(f"获取 {location} 在 {date} 的天气数据失败")
        
        # 添加随机延迟，避免API限流
        delay = BASE_DELAY + (idx % 5)  # 基础延迟加一些变化
        logger.info(f"等待 {delay} 秒后继续...")
        time.sleep(delay)
    
    logger.info(f"天气数据补全完成，成功更新 {success_count}/{len(null_records)} 条记录")

if __name__ == "__main__":
    main()