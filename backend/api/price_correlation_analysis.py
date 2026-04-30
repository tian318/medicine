import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json

def get_db_connection():
    """创建数据库连接"""
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='LAPTOP-UO3FERDN',
            host='39.104.55.114',
            port='5001'
        )
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def analyze_price_correlation(cluster_id=None, start_date=None, end_date=None, top_n=3):
    """
    分析药材价格走势的相关性
    
    参数:
    - cluster_id: 聚类ID，如果提供则只分析该聚类中的药材
    - start_date: 开始日期
    - end_date: 结束日期
    - top_n: 返回相关性最高的前N个药材对
    
    返回:
    - 正相关和负相关的药材对列表
    """
    try:
        conn = get_db_connection()
        if not conn:
            return {"error": "数据库连接失败"}
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 如果没有提供日期范围，默认使用最近6个月
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        
        # 获取所有药材的价格数据
        query = """
        SELECT 
            herb_name,
            specification,
            location,
            recorded_at::date as date,
            AVG(price::numeric) as avg_price
        FROM herb_prices
        WHERE recorded_at::date BETWEEN %s AND %s
        """
        
        params = [start_date, end_date]
        
        # 如果提供了聚类ID，则从聚类结果中获取药材列表
        herb_list = []
        if cluster_id is not None:
            # 这里需要根据您的聚类结果存储方式进行调整
            # 假设聚类结果存储在clustering_results表中
            cluster_query = """
            SELECT herb_names FROM clustering_results 
            WHERE cluster_id = %s AND analysis_date = (
                SELECT MAX(analysis_date) FROM clustering_results
            )
            """
            try:
                cursor.execute(cluster_query, [cluster_id])
                result = cursor.fetchone()
                if result and result['herb_names']:
                    herb_list = result['herb_names']
                    query += " AND herb_name = ANY(%s)"
                    params.append(herb_list)
            except Exception as e:
                print(f"获取聚类药材列表失败: {e}")
                # 如果获取聚类药材失败，则不添加药材筛选条件
        
        query += """
        GROUP BY herb_name, specification, location, recorded_at::date
        ORDER BY herb_name, specification, location, recorded_at::date
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if not results:
            return {"error": "没有找到匹配的数据"}
        
        # 将数据转换为DataFrame
        df = pd.DataFrame(results)
        
        # 创建药材标识符（药材名称+规格+产地）
        df['herb_id'] = df['herb_name'] + ' (' + df['specification'] + ') - ' + df['location']
        
        # 数据透视表，行为日期，列为药材标识符，值为价格
        pivot_df = df.pivot_table(index='date', columns='herb_id', values='avg_price')
        
        # 计算相关性矩阵
        corr_matrix = pivot_df.corr(method='pearson')
        
        # 提取相关性对
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                herb1 = corr_matrix.columns[i]
                herb2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                
                # 只保留有足够数据点的药材对
                if not np.isnan(corr_value):
                    herb1_parts = herb1.split(' (')
                    herb2_parts = herb2.split(' (')
                    
                    herb1_name = herb1_parts[0]
                    herb1_spec = herb1_parts[1].split(') - ')[0]
                    herb1_loc = herb1_parts[1].split(') - ')[1]
                    
                    herb2_name = herb2_parts[0]
                    herb2_spec = herb2_parts[1].split(') - ')[0]
                    herb2_loc = herb2_parts[1].split(') - ')[1]
                    
                    corr_pairs.append({
                        'herb1': {
                            'name': herb1_name,
                            'specification': herb1_spec,
                            'location': herb1_loc
                        },
                        'herb2': {
                            'name': herb2_name,
                            'specification': herb2_spec,
                            'location': herb2_loc
                        },
                        'correlation': round(corr_value, 3)
                    })
        
        # 按相关性绝对值排序
        corr_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        # 分离正相关和负相关
        positive_corr = [pair for pair in corr_pairs if pair['correlation'] > 0]
        negative_corr = [pair for pair in corr_pairs if pair['correlation'] < 0]
        
        # 获取前N个正相关和负相关对
        top_positive = positive_corr[:top_n]
        top_negative = negative_corr[:top_n]
        
        # 为每个药材对获取价格数据
        for pairs in [top_positive, top_negative]:
            for pair in pairs:
                herb1_id = f"{pair['herb1']['name']} ({pair['herb1']['specification']}) - {pair['herb1']['location']}"
                herb2_id = f"{pair['herb2']['name']} ({pair['herb2']['specification']}) - {pair['herb2']['location']}"
                
                # 获取这两个药材的价格数据
                herb_data = pivot_df[[herb1_id, herb2_id]].dropna()
                
                # 转换为列表格式
                dates = herb_data.index.strftime('%Y-%m-%d').tolist()
                herb1_prices = herb_data[herb1_id].tolist()
                herb2_prices = herb_data[herb2_id].tolist()
                
                # 添加到结果中
                pair['dates'] = dates
                pair['herb1_prices'] = herb1_prices
                pair['herb2_prices'] = herb2_prices
        
        return {
            'positive_correlation': top_positive,
            'negative_correlation': top_negative
        }
    
    except Exception as e:
        import traceback
        print(f"分析价格相关性失败: {e}")
        print(traceback.format_exc())
        return {"error": str(e)}
    finally:
        if conn:
            conn.close()