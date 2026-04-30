import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import requests
import logging
import os
import re
import time
import random


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/my_graduation_project/.log/location_mapping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('location_mapper')

# 确保日志目录存在
os.makedirs('/root/my_graduation_project/.log', exist_ok=True)

# 数据库连接配置
DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'LAPTOP-UO3FERDN',
    'host': 'localhost',
    'port': '5001'
}

# 高德地图API配置
AMAP_KEY = "b88761510d2e79d01f3a51ff9f9a75fa"  # 请替换为你的高德地图API密钥
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"

# 省份列表，用于识别地点名称中的省份前缀
PROVINCES = [
    "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江", 
    "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", 
    "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海", "台湾",
    "内蒙古", "广西", "西藏", "宁夏", "新疆", "香港", "澳门"
]

# 特殊地区后缀，可能导致查询失败
SPECIAL_SUFFIXES = [
    "自治区", "维吾尔", "回族", "壮族", "满族", "维吾尔自治区", "自治州", 
    "土家族", "苗族", "藏族", "彝族", "侗族", "瑶族", "蒙古族", "蒙古", "羌族"
]

# 地名替换映射，用于处理一些特殊地名或历史地名
LOCATION_MAPPING = {
    "湖北襄樊": "湖北襄阳",  # 襄樊已更名为襄阳
    "荷花池": "成都荷花池",  # 荷花池是成都的一个市场
    "甘肃七里河区": "兰州七里河区",  # 七里河区是兰州的一个区
    "甘肃合作": "甘肃甘南合作",  # 合作市是甘南藏族自治州的首府
    "重庆南川": "重庆南川区",  # 南川现在是重庆的一个区
    "重庆江津": "重庆江津区",  # 江津现在是重庆的一个区
    "青海辖区": "青海西宁",  # 可能是数据错误
}

# 地名别名映射，用于尝试不同的地名表达方式
LOCATION_ALIASES = {
    "湖南沅江": ["益阳沅江", "沅江市"],
    "湖南沅陵县": ["怀化沅陵", "沅陵"],
    "湖南湘潭县": ["湘潭市", "湘潭"],
    "湖南益阳": ["益阳市"],
    "湖南道县": ["永州道县"],
    "湖南邵东县": ["邵阳邵东", "邵东市"],
    "湖南邵阳县": ["邵阳市"],
    "湖南隆回县": ["邵阳隆回"],
    "甘肃华亭县": ["平凉华亭", "华亭市"],
    "甘肃宕昌县": ["陇南宕昌"],
    "甘肃岷县": ["定西岷县"],
    "甘肃景泰县": ["白银景泰"],
    "甘肃武都区": ["陇南武都"],
    "甘肃漳县": ["定西漳县"],
    "甘肃西和县": ["陇南西和"],
    "甘肃陇南": ["陇南市"],
    "甘肃陇西县": ["定西陇西"],
    "福建古田县": ["宁德古田"],
    "福建柘荣县": ["宁德柘荣"],
    "福建漳浦县": ["漳州漳浦"],
    "福建福鼎": ["宁德福鼎"],
    "贵州余庆县": ["遵义余庆"],
    "贵州兴义": ["黔西南兴义"],
    "贵州兴仁县": ["黔西南兴仁"],
    "贵州凯里": ["黔东南凯里"],
    "贵州天柱县": ["黔东南天柱"],
    "贵州威宁彝族回族苗族": ["毕节威宁"],
    "贵州施秉县": ["黔东南施秉"],
    "贵州毕节": ["毕节市"],
    "贵州黔南布依族苗族": ["黔南州"],
    "辽宁凤城": ["丹东凤城"],
    "辽宁宽甸满族": ["丹东宽甸"],
    "辽宁岫岩满族": ["鞍山岫岩"],
    "辽宁建昌县": ["葫芦岛建昌"],
    "辽宁新宾满族": ["抚顺新宾"],
    "辽宁桓仁满族": ["本溪桓仁"],
    "重庆奉节县": ["奉节县"],
    "重庆巫山县": ["巫山县"],
    "重庆巫溪县": ["巫溪县"],
    "重庆石柱土家族": ["石柱县"],
    "重庆酉阳土家族苗族": ["酉阳县"],
    "重庆铜梁县": ["铜梁区"],
    "陕西商州区": ["商洛商州"],
    "陕西宁陕县": ["安康宁陕"],
    "陕西安康": ["安康市"],
    "陕西户县": ["西安鄠邑区"],  # 户县已更名为鄠邑区
    "陕西旬阳县": ["安康旬阳"],
    "陕西柞水县": ["商洛柞水"],
    "陕西汉中": ["汉中市"],
    "陕西澄城县": ["渭南澄城"],
    "黑龙江五常": ["哈尔滨五常"],
    "黑龙江依兰县": ["哈尔滨依兰"],
    "黑龙江大同区": ["齐齐哈尔大同"],
    "黑龙江孙吴县": ["黑河孙吴"],
    "黑龙江尚志": ["哈尔滨尚志"],
    "黑龙江海伦": ["绥化海伦"],
    "黑龙江齐齐哈尔": ["齐齐哈尔市"],
}

def get_db_connection():
    """创建数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

def get_missing_locations():
    """获取缺少经纬度映射的地点"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        query = """
        SELECT DISTINCT hp.location
        FROM herb_prices hp
        LEFT JOIN location_mapping lm ON hp.location = lm.location_name
        WHERE lm.id IS NULL
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        
        # 获取所有缺失的地点
        missing_locations = [row[0] for row in cursor.fetchall()]
        return missing_locations
    except Exception as e:
        logger.error(f"获取缺失地点失败: {e}")
        return []
    finally:
        conn.close()

def normalize_location_name(location_name):
    """规范化地点名称，去除特殊字符和不必要的后缀"""
    # 去除特殊后缀
    for suffix in SPECIAL_SUFFIXES:
        if suffix in location_name:
            location_name = location_name.replace(suffix, "")
    
    # 去除多余的空格
    location_name = location_name.strip()
    
    return location_name

def extract_province_and_city(location_name):
    """从地点名称中提取省份和城市/县名"""
    province = None
    city = location_name
    
    # 尝试从地点名称中提取省份
    for p in PROVINCES:
        if location_name.startswith(p):
            province = p
            city = location_name[len(p):]
            break
    
    return province, city

def geocode_location(location_name):
    """使用高德地图API获取地点的经纬度，包含重试逻辑"""
    original_name = location_name
    
    # 检查是否有预定义的地名映射
    if location_name in LOCATION_MAPPING:
        mapped_name = LOCATION_MAPPING[location_name]
        logger.info(f"使用预定义映射: '{location_name}' -> '{mapped_name}'")
        geo_data = try_geocode(mapped_name)
        if geo_data:
            return geo_data
    
    # 第一步：尝试使用原始地点名称
    geo_data = try_geocode(location_name)
    if geo_data:
        return geo_data
    
    # 第二步：规范化地点名称并重试
    normalized_name = normalize_location_name(location_name)
    if normalized_name != location_name:
        logger.info(f"尝试使用规范化名称: '{normalized_name}'")
        geo_data = try_geocode(normalized_name)
        if geo_data:
            return geo_data
    
    # 第三步：提取省份和城市，仅使用城市名称重试
    province, city = extract_province_and_city(normalized_name)
    if province and city:
        logger.info(f"尝试仅使用城市/县名: '{city}'")
        geo_data = try_geocode(city)
        if geo_data:
            # 如果成功，确保保留省份信息
            if not geo_data.get('province'):
                geo_data['province'] = province
            return geo_data
        
        # 第四步：如果城市名称包含"县"或"市"等后缀，尝试去除后缀
        if any(suffix in city for suffix in ["县", "市", "区", "旗"]):
            simple_city = re.sub(r'[县市区旗]$', '', city)
            if simple_city != city:
                logger.info(f"尝试使用简化城市名: '{simple_city}'")
                geo_data = try_geocode(simple_city)
                if geo_data:
                    if not geo_data.get('province'):
                        geo_data['province'] = province
                    return geo_data
    
    # 第五步：尝试使用别名
    if location_name in LOCATION_ALIASES:
        for alias in LOCATION_ALIASES[location_name]:
            logger.info(f"尝试使用别名: '{alias}'")
            geo_data = try_geocode(alias)
            if geo_data:
                return geo_data
    
    # 第六步：尝试添加"市"或"县"后缀
    if province and city and not any(suffix in city for suffix in ["县", "市", "区", "旗"]):
        for suffix in ["市", "县"]:
            city_with_suffix = f"{city}{suffix}"
            logger.info(f"尝试添加后缀: '{city_with_suffix}'")
            geo_data = try_geocode(city_with_suffix)
            if geo_data:
                if not geo_data.get('province'):
                    geo_data['province'] = province
                return geo_data
    
    # 第七步：尝试使用省份+城市的组合
    if province and city:
        # 尝试不同的分隔符
        for separator in ["", " "]:
            combined = f"{province}{separator}{city}"
            if combined != location_name:
                logger.info(f"尝试使用组合名称: '{combined}'")
                geo_data = try_geocode(combined)
                if geo_data:
                    return geo_data
    
    logger.warning(f"所有尝试都失败，无法获取 '{original_name}' 的地理编码")
    return None


# def try_geocode(location_name, attempt=1, max_attempts=5, backoff_factor=0.1):
#     """尝试使用高德地图API获取地点的经纬度"""
#     try:
#         params = {
#             'address': location_name,
#             'key': AMAP_KEY,
#             'output': 'JSON'
#         }
        
#         response = requests.get(AMAP_GEOCODE_URL, params=params)
        
#         if response.status_code == 200:
#             data = response.json()
            
#             if data['status'] == '1' and data['count'] != '0':
#                 # 获取第一个结果
#                 result = data['geocodes'][0]
                
#                 # 解析经纬度
#                 lng, lat = result['location'].split(',')
                
#                 # 解析省市信息
#                 province = result.get('province', '')
#                 city = result.get('city', '')
                
#                 return {
#                     'latitude': float(lat),
#                     'longitude': float(lng),
#                     'province': province,
#                     'city': city
#                 }
#             else:
#                 return None
#         else:
#             logger.error(f"API请求失败: {response.status_code} - {response.text}")
#             return None
#     except Exception as e:
#         logger.error(f"地理编码请求失败: {e}")
#         return None

def try_geocode(location_name, attempt=1, max_attempts=5, backoff_factor=0.1):
    """尝试使用高德地图API获取地点的经纬度，包含重试逻辑"""
    if attempt > max_attempts:
        logger.error(f"达到最大重试次数，无法获取 '{location_name}' 的地理编码")
        return None
    
    try:
        params = {
            'address': location_name,
            'key': AMAP_KEY,
            'output': 'JSON'
        }
        
        response = requests.get(AMAP_GEOCODE_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == '1' and data['count'] != '0':
                # 获取第一个结果
                result = data['geocodes'][0]
                
                # 解析经纬度
                lng, lat = result['location'].split(',')
                
                # 解析省市信息
                province = result.get('province', '')
                city = result.get('city', '')
                
                return {
                    'latitude': float(lat),
                    'longitude': float(lng),
                    'province': province,
                    'city': city
                }
            else:
                # 如果没有找到结果，增加延迟并重试
                delay = backoff_factor * (2 ** (attempt - 1)) + random.uniform(0, 0.1)
                logger.warning(f"未找到结果，将在 {delay:.2f} 秒后重试（尝试 {attempt}/{max_attempts}）")
                time.sleep(delay)
                return try_geocode(location_name, attempt + 1, max_attempts, backoff_factor)
        else:
            logger.error(f"API请求失败: {response.status_code} - {response.text}")
            # 如果请求失败，增加延迟并重试
            delay = backoff_factor * (2 ** (attempt - 1)) + random.uniform(0, 0.1)
            logger.warning(f"请求失败，将在 {delay:.2f} 秒后重试（尝试 {attempt}/{max_attempts}）")
            time.sleep(delay)
            return try_geocode(location_name, attempt + 1, max_attempts, backoff_factor)
    except Exception as e:
        logger.error(f"地理编码请求失败: {e}")
        # 如果发生异常，增加延迟并重试
        delay = backoff_factor * (2 ** (attempt - 1)) + random.uniform(0, 0.1)
        logger.warning(f"发生异常，将在 {delay:.2f} 秒后重试（尝试 {attempt}/{max_attempts}）")
        time.sleep(delay)
        return try_geocode(location_name, attempt + 1, max_attempts, backoff_factor)

def save_location_mapping(location_name, geo_data):
    """保存地点映射到数据库"""
    if not geo_data:
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        query = """
        INSERT INTO location_mapping 
        (location_name, latitude, longitude, province, city, is_market)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (location_name) DO NOTHING
        """
        
        # 假设所有地点都是市场
        is_market = True
        
        cursor.execute(
            query, 
            (
                location_name, 
                geo_data['latitude'], 
                geo_data['longitude'], 
                geo_data['province'], 
                geo_data['city'], 
                is_market
            )
        )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"保存地点映射失败: {e}")
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    logger.info("开始更新地点映射")
    
    # 获取缺失映射的地点
    missing_locations = get_missing_locations()
    logger.info(f"发现 {len(missing_locations)} 个缺失映射的地点")
    
    # 为每个地点获取地理编码
    success_count = 0
    for location in missing_locations:
        logger.info(f"正在获取 '{location}' 的地理编码")
        
        geo_data = geocode_location(location)
        if geo_data:
            if save_location_mapping(location, geo_data):
                success_count += 1
                logger.info(f"成功保存 '{location}' 的地理编码")
            else:
                logger.warning(f"保存 '{location}' 的地理编码失败")
        else:
            logger.warning(f"无法获取 '{location}' 的地理编码")
        
        # 添加短暂延迟，避免API请求过于频繁
        time.sleep(0.1)
    
    logger.info(f"地点映射更新完成，成功更新 {success_count}/{len(missing_locations)} 个地点")

if __name__ == "__main__":
    main()