import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from tslearn.clustering import TimeSeriesKMeans
from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from datetime import datetime, timedelta
import json
import os
import re

# 数据库连接配置
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}

# 趋势类型定义
TREND_TYPES = {
    0: "小幅震荡/平稳",
    1: "先稳后涨",
    2: "先稳后跌",
    3: "先涨后跌",
    4: "涨-平-涨",
    5: "平-涨-平",
    6: "先跌后涨",
    7: "先涨后稳",
    8: "震荡下跌",
    9: "平-跌-平",
    10: "先跌后稳",
    11: "震荡上涨",
    12: "连续上涨",
    13: "连续下跌"
}


def fetch_all_herbs_price_data(start_date=None, end_date=None):
    """从数据库获取所有药材的价格数据"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
        SELECT herb_name, specification, location, price, recorded_at
        FROM herb_prices
        WHERE source = 'market'
        """

        params = []
        if start_date:
            query += " AND recorded_at::date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND recorded_at::date <= %s"
            params.append(end_date)

        query += " ORDER BY herb_name, specification, location, recorded_at ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        df = pd.DataFrame(rows)

        if df.empty:
            return pd.DataFrame()

        # 确保价格是数值类型
        df['price'] = pd.to_numeric(df['price'], errors='coerce')

        # 确保日期是日期时间类型
        df['recorded_at'] = pd.to_datetime(df['recorded_at'])

        return df

    except Exception as e:
        print(f"获取数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


def prepare_time_series_data_for_clustering(df):
    """准备用于聚类的时间序列数据，合并不同规格和产地的药材价格"""
    # 只按药材名称和日期分组，忽略规格和产地，计算平均价格
    daily_prices = df.groupby(['herb_name', df['recorded_at'].dt.date])['price'].mean().reset_index()
    daily_prices.columns = ['herb_name', 'date', 'price']
    daily_prices['date'] = pd.to_datetime(daily_prices['date'])

    # 获取所有唯一的药材名称
    herb_names = daily_prices['herb_name'].unique()

    # 创建一个字典来存储每个药材的时间序列数据
    herb_time_series = {}

    for herb_name in herb_names:
        herb_data = daily_prices[daily_prices['herb_name'] == herb_name].sort_values('date')

        # 检查数据点数量是否足够
        if len(herb_data) < 30:  # 至少需要30个数据点
            continue

        # 检查是否有缺失日期，如果有则进行插值
        date_range = pd.date_range(start=herb_data['date'].min(), end=herb_data['date'].max(), freq='D')
        full_date_df = pd.DataFrame({'date': date_range})
        herb_data = full_date_df.merge(herb_data, on='date', how='left')

        # 使用线性插值填充缺失值
        herb_data['price'] = herb_data['price'].interpolate(method='linear')

        # 填充herb_name
        herb_data['herb_name'] = herb_name

        # 存储时间序列数据
        herb_time_series[herb_name] = herb_data

    return herb_time_series


def extract_trend_features(time_series_dict):
    """提取价格趋势特征"""
    features = []
    herb_names = []

    for herb_name, data in time_series_dict.items():
        # 确保数据足够长
        if len(data) < 30:
            continue

        # 提取价格序列
        prices = data['price'].values

        # 归一化价格
        scaler = MinMaxScaler(feature_range=(0, 1))
        normalized_prices = scaler.fit_transform(prices.reshape(-1, 1)).flatten()

        # 将时间序列分为三段
        segment_size = len(normalized_prices) // 3
        segments = [
            normalized_prices[:segment_size],
            normalized_prices[segment_size:2 * segment_size],
            normalized_prices[2 * segment_size:]
        ]

        # 计算每段的趋势特征
        segment_features = []
        for segment in segments:
            # 线性回归斜率
            x = np.arange(len(segment))
            slope = np.polyfit(x, segment, 1)[0]

            # 波动性（标准差）
            volatility = np.std(segment)

            # 最大值和最小值
            max_val = np.max(segment)
            min_val = np.min(segment)

            # 添加特征
            segment_features.extend([slope, volatility, max_val, min_val])

        # 添加整体特征
        overall_slope = np.polyfit(np.arange(len(normalized_prices)), normalized_prices, 1)[0]
        overall_volatility = np.std(normalized_prices)

        # 组合所有特征
        all_features = segment_features + [overall_slope, overall_volatility]

        features.append(all_features)
        herb_names.append(herb_name)

    return np.array(features), herb_names


def cluster_price_trends(features, herb_names, n_clusters=14):
    """对价格趋势进行聚类"""
    # 使用K-means聚类
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(features)

    # 创建结果字典
    result = {}
    for i, herb_name in enumerate(herb_names):
        cluster_id = int(clusters[i])
        if cluster_id not in result:
            result[cluster_id] = []
        result[cluster_id].append(herb_name)

    return result


def get_representative_herbs(cluster_dict, time_series_dict, original_df, n_representatives=5):
    """获取每个聚类的代表性药材，包含原始规格和产地信息"""
    representatives = {}

    for cluster_id, herb_names in cluster_dict.items():
        # 计算每个药材与聚类中心的距离
        cluster_herbs = []

        for herb_name in herb_names:
            if herb_name in time_series_dict:
                herb_data = time_series_dict[herb_name]

                # 获取该药材的所有规格和产地组合
                herb_specs = original_df[original_df['herb_name'] == herb_name].groupby(
                    ['specification', 'location']).size().reset_index()

                # 如果有多个规格和产地组合，选择数据量最多的一个
                if len(herb_specs) > 0:
                    # 对于每个规格和产地组合，计算数据量
                    for _, row in herb_specs.iterrows():
                        spec = row['specification']
                        location = row['location']

                        # 提取价格数据
                        prices = herb_data['price'].values
                        dates = herb_data['date'].dt.strftime('%Y-%m-%d').tolist()

                        cluster_herbs.append({
                            'herb_id': herb_name,  # 使用药材名称作为ID
                            'herb_name': herb_name,
                            'specification': spec,
                            'location': location,
                            'prices': prices.tolist(),
                            'dates': dates
                        })

                        # 只添加一个规格和产地组合作为代表
                        break

        # 选择代表性药材（最多n_representatives个）
        representatives[cluster_id] = cluster_herbs[:min(n_representatives, len(cluster_herbs))]

    return representatives


def analyze_price_trends(start_date=None, end_date=None, save_result=False):
    """分析药材价格趋势并进行聚类"""
    # 获取所有药材的价格数据
    df = fetch_all_herbs_price_data(start_date, end_date)

    if df.empty:
        return {"error": "没有找到价格数据"}

    # 准备时间序列数据（合并不同规格和产地）
    time_series_dict = prepare_time_series_data_for_clustering(df)

    if not time_series_dict:
        return {"error": "没有足够的时间序列数据进行聚类"}

    # 提取趋势特征
    features, herb_names = extract_trend_features(time_series_dict)

    if len(features) == 0:
        return {"error": "无法提取趋势特征"}

    # 聚类分析
    cluster_dict = cluster_price_trends(features, herb_names)

    # 获取代表性药材（保留规格和产地信息）
    representatives = get_representative_herbs(cluster_dict, time_series_dict, df)

    # 准备结果
    result = {
        "trend_types": TREND_TYPES,
        "clusters": {},
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date_range": {
            "start_date": start_date,
            "end_date": end_date
        }
    }

    for cluster_id, herbs in representatives.items():
        trend_type = TREND_TYPES.get(cluster_id, f"类别 {cluster_id}")
        result["clusters"][cluster_id] = {
            "trend_type": trend_type,
            "herbs": herbs,
            "total_herbs": len(cluster_dict.get(cluster_id, [])),
            "all_herb_names": cluster_dict.get(cluster_id, [])  # 添加该聚类中的所有药材名称
        }

    # 如果需要保存结果
    if save_result:
        save_clustering_result(result, start_date, end_date)

    return result


def save_clustering_result(result, start_date=None, end_date=None):
    """保存聚类结果到JSON文件"""
    try:
        # 创建保存目录
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data",
                                "clustering_results")
        os.makedirs(save_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if start_date and end_date:
            filename = f"price_trend_clustering_{start_date}_to_{end_date}_{timestamp}.json"
        else:
            filename = f"price_trend_clustering_{timestamp}.json"

        file_path = os.path.join(save_dir, filename)

        # 保存为JSON文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"聚类结果已保存到: {file_path}")
        return file_path
    except Exception as e:
        print(f"保存聚类结果失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_clustering_history_files():
    """获取历史聚类结果文件列表"""
    try:
        # 获取保存目录
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data",
                                "clustering_results")

        # 检查目录是否存在
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
            return []

        # 获取所有JSON文件
        json_files = [f for f in os.listdir(save_dir) if
                      f.endswith('.json') and f.startswith('price_trend_clustering_')]

        # 按修改时间排序（最新的在前）
        json_files.sort(key=lambda x: os.path.getmtime(os.path.join(save_dir, x)), reverse=True)

        # 提取文件信息
        file_info_list = []
        for filename in json_files:
            file_path = os.path.join(save_dir, filename)
            file_info = {
                'filename': filename,
                'file_path': file_path,
                'created_time': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                'file_size': os.path.getsize(file_path) // 1024  # 转换为KB
            }

            # 尝试从文件名中提取日期范围
            date_range_match = re.search(r'(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})', filename)
            if date_range_match:
                file_info['start_date'] = date_range_match.group(1)
                file_info['end_date'] = date_range_match.group(2)

            file_info_list.append(file_info)

        return file_info_list
    except Exception as e:
        print(f"获取历史聚类文件列表失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def load_clustering_result(filename):
    """加载指定的聚类结果文件"""
    try:
        # 获取保存目录
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data",
                                "clustering_results")
        file_path = os.path.join(save_dir, filename)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {"error": f"文件不存在: {filename}"}

        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            result = json.load(f)

        return result
    except Exception as e:
        print(f"加载聚类结果失败: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"加载聚类结果失败: {str(e)}"}