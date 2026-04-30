from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import re
import sys
# 导入预测模块
from price_prediction_api import (
    predict_herb_price,
    get_available_herbs,
    get_specifications,
)

# 导入情绪分析模块
from sentiment_analysis_api import (
    fetch_news_data,
    analyze_sentiment,
    get_herb_names_from_db,
)

# 导入价格趋势聚类分析模块
from price_trend_clustering import analyze_price_trends


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 数据库连接配置
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}


def get_db_connection(max_retries=3, retry_delay=1):
    """创建数据库连接，带重试机制"""
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return conn
            except:
                conn.close()
                raise Exception("Connection validation failed")
        except Exception as e:
            if attempt < max_retries - 1:
                import time
                print(f"数据库连接失败，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                import traceback
                print(f"数据库连接失败: {e}")
                print(traceback.format_exc())
    return None


@app.route("/api/db-health", methods=["GET"])
def db_health_check():
    """数据库健康检查端点"""
    try:
        print("接收到数据库健康检查请求")
        conn = get_db_connection()
        if not conn:
            return jsonify({
                "status": "error",
                "message": "数据库连接失败"
            }), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 检查所有关键表
        table_status = {}
        key_tables = ['herb_prices', 'herb_data', 'location_mapping', 'news_info1', 'weather_data']
        
        for table in key_tables:
            try:
                # 检查表是否存在
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name = %s AND table_schema = 'public'
                """, (table,))
                table_exists = cursor.fetchone() is not None
                
                if table_exists:
                    # 检查表中的记录数
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()['count']
                    
                    # 检查表结构
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = %s AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """, (table,))
                    columns = cursor.fetchall()
                    
                    table_status[table] = {
                        "exists": True,
                        "record_count": count,
                        "columns": [{"name": col['column_name'], "type": col['data_type']} for col in columns]
                    }
                else:
                    table_status[table] = {
                        "exists": False,
                        "record_count": 0,
                        "columns": []
                    }
            except Exception as table_error:
                table_status[table] = {
                    "exists": False,
                    "error": str(table_error)
                }
        
        cursor.close()
        conn.close()
        
        # 检查是否有缺失的关键表
        missing_tables = [table for table, status in table_status.items() if not status.get('exists', False)]
        
        return jsonify({
            "status": "ok",
            "message": "数据库连接正常",
            "tables": table_status,
            "missing_tables": missing_tables
        })
        
    except Exception as e:
        import traceback
        print(f"数据库健康检查失败: {e}")
        print(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": str(e),
            "stack_trace": traceback.format_exc()
        }), 500


@app.route("/api/herbs", methods=["GET"])
def get_herbs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        # 修改为中文字段名
        cursor.execute('SELECT DISTINCT "药材名称" FROM herb_data ORDER BY "药材名称"')
        herbs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify([herb['药材名称'] for herb in herbs])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/herbs-data", methods=["GET"])
def get_herbs_data():
    """获取所有中药材数据"""
    print("接收到获取中药材数据的请求")
    conn = get_db_connection()
    if not conn:
        print("数据库连接失败")
        return jsonify({"error": "数据库连接失败"}), 500

    try:
        print("数据库连接成功")
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 先检查表结构
        print("检查herb_data表结构")
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'herb_data' AND table_schema = 'public'
        """)
        columns = [row['column_name'] for row in cursor.fetchall()]
        print(f"herb_data表字段: {columns}")
        
        # 尝试使用不同的字段名组合
        print("执行SQL查询: SELECT * FROM herb_data LIMIT 5")
        cursor.execute("SELECT * FROM herb_data LIMIT 5")
        sample_data = cursor.fetchall()
        print(f"示例数据: {sample_data}")
        
        # 根据实际字段名调整查询
        if 'herb_name' in columns:
            print("使用字段名: herb_name, pinyin_initial, variety_characteristics, distribution_area")
            cursor.execute("""
                SELECT herb_name as name, pinyin_initial as initial, variety_characteristics as efficacy, distribution_area as distribution
                FROM herb_data 
                ORDER BY pinyin_initial, herb_name
            """)
        elif 'name' in columns:
            print("使用字段名: name, initial, efficacy, distribution")
            cursor.execute("""
                SELECT name, initial, efficacy, distribution
                FROM herb_data 
                ORDER BY initial, name
            """)
        elif '药材名称' in columns:
            print("使用中文字段名: 药材名称, 拼音首字母, 品种特点, 分布区域")
            cursor.execute("""
                SELECT "药材名称" as name, "拼音首字母" as initial, "品种特点" as efficacy, "分布区域" as distribution
                FROM herb_data 
                ORDER BY "拼音首字母", "药材名称"
            """)
        else:
            print("使用通用查询: SELECT *")
            cursor.execute("""
                SELECT * FROM herb_data ORDER BY 1, 2
            """)
        
        print("SQL查询执行成功")
        herbs = cursor.fetchall()
        print(f"查询到 {len(herbs)} 条中药材数据")
        
        # 为每条记录添加 id 和 pinyin 字段（前端需要）
        result = []
        for i, herb in enumerate(herbs):
            try:
                # 适应不同的字段名
                if 'name' in herb:
                    name = herb.get('name', '')
                    initial = herb.get('initial', '')
                    efficacy = herb.get('efficacy', '')
                    distribution = herb.get('distribution', '')
                elif 'herb_name' in herb:
                    name = herb.get('herb_name', '')
                    initial = herb.get('pinyin_initial', '')
                    efficacy = herb.get('variety_characteristics', '')
                    distribution = herb.get('distribution_area', '')
                elif '药材名称' in herb:
                    name = herb.get('药材名称', '')
                    initial = herb.get('拼音首字母', '')
                    efficacy = herb.get('品种特点', '')
                    distribution = herb.get('分布区域', '')
                else:
                    # 尝试使用第一个字段作为名称
                    name = list(herb.values())[0] if herb else ''
                    initial = herb.get(list(herb.keys())[1], '') if len(herb) > 1 else ''
                    efficacy = herb.get(list(herb.keys())[2], '') if len(herb) > 2 else ''
                    distribution = herb.get(list(herb.keys())[3], '') if len(herb) > 3 else ''
                
                herb_dict = {
                    'id': i + 1,
                    'name': name,
                    'initial': initial,
                    'efficacy': efficacy,
                    'distribution': distribution,
                    'pinyin': initial if initial else ''
                }
                result.append(herb_dict)
            except Exception as item_error:
                print(f"处理单条药材数据失败: {item_error}")
                continue
        
        print(f"处理完成，返回 {len(result)} 条数据")
        return jsonify(result)
    except Exception as e:
        import traceback
        print(f"获取中药材数据失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
        print("数据库连接已关闭")


# @app.route("/api/herbs-data1", methods=["GET"])
# def get_herbs_data1():
#     """获取所有中药材数据（备用端点）"""
#     print("接收到获取中药材数据的请求（备用端点）")
#     conn = get_db_connection()
#     if not conn:
#         print("数据库连接失败")
#         return jsonify({"error": "数据库连接失败"}), 500

#     try:
#         print("数据库连接成功")
#         cursor = conn.cursor(cursor_factory=RealDictCursor)
#         print("执行SQL查询: SELECT id, name, pinyin, efficacy, initial FROM herb_data ORDER BY initial, name")
#         cursor.execute("""
#             SELECT id, name, pinyin, efficacy, initial 
#             FROM herb_data 
#             ORDER BY initial, name
#         """)
#         print("SQL查询执行成功")
#         herbs = cursor.fetchall()
#         print(f"查询到 {len(herbs)} 条中药材数据")
#         return jsonify(herbs)
#     except Exception as e:
#         import traceback
#         print(f"获取中药材数据失败: {e}")
#         print(traceback.format_exc())
#         return jsonify({"error": str(e)}), 500
#     finally:
#         conn.close()
#         print("数据库连接已关闭")


@app.route("/api/herb-detail", methods=["GET"])
def get_herb_detail():
    """获取单个中药材详情"""
    herb_name = request.args.get("herb_name")
    if not herb_name:
        return jsonify({"error": "缺少药材名称参数"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "数据库连接失败"}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 先检查表结构，确定使用哪个字段名
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'herb_data' AND table_schema = 'public'
        """)
        columns = [row['column_name'] for row in cursor.fetchall()]
        
        # 根据字段名确定查询条件
        if 'herb_name' in columns:
            cursor.execute(
                "SELECT * FROM herb_data WHERE herb_name = %s",
                (herb_name,),
            )
        elif '药材名称' in columns:
            cursor.execute(
                'SELECT * FROM herb_data WHERE "药材名称" = %s',
                (herb_name,),
            )
        else:
            return jsonify({"error": "表结构不匹配"}), 500
        
        herb = cursor.fetchone()
        
        if not herb:
            return jsonify({"error": "未找到该中药材"}), 404
        
        # 为了前端使用方便，统一字段名
        # 尝试多种字段名映射
        if 'herb_name' in herb:
            result = {
                "initial": herb.get("pinyin_initial"),
                "name": herb.get("herb_name"),
                "characteristics": herb.get("variety_characteristics"),
                "distribution": herb.get("distribution_area"),
                "harvest_season": herb.get("collection_time"),
                "usage_method": herb.get("usage_dosage"),
                "taboo": herb.get("toxicity"),
                "medicinal_effects": herb.get("indications"),
                "shengzhanghuanjing": herb.get("growth_environment"),
                "xingtaitezheng": herb.get("morphological_features"),
                "zaipeijishu": herb.get("cultivation_technique")
            }
        elif '药材名称' in herb:
            result = {
                "initial": herb.get("拼音首字母"),
                "name": herb.get("药材名称"),
                "characteristics": herb.get("品种特点"),
                "distribution": herb.get("分布区域"),
                "harvest_season": herb.get("采集时间"),
                "usage_method": herb.get("用量"),
                "taboo": herb.get("毒性"),
                "medicinal_effects": herb.get("针对症状"),
                "shengzhanghuanjing": herb.get("生长环境"),
                "xingtaitezheng": herb.get("形态特征"),
                "zaipeijishu": herb.get("栽培技术")
            }
        else:
            # 使用通用映射
            result = {}
            for key, value in herb.items():
                result[key] = value
        
        return jsonify(result)
    except Exception as e:
        import traceback
        print(f"获取中药材详情失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/specifications", methods=["GET"])
def get_specifications():
    """获取指定药材的所有规格"""
    herb_name = request.args.get("herb_name")
    if not herb_name:
        return jsonify({"error": "缺少药材名称参数"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "数据库连接失败"}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT DISTINCT specification FROM herb_prices WHERE herb_name = %s ORDER BY specification",
            (herb_name,),
        )
        specs = [row["specification"] for row in cursor.fetchall()]
        return jsonify(specs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/price-trend", methods=["GET"])
def get_price_trend():
    """获取药材价格pip趋势数据"""
    herb_name = request.args.get("herb_name")
    specification = request.args.get("specification")
    location = request.args.get("location")  # 可选地点参数
    start_date = request.args.get("start_date")  # 开始日期
    end_date = request.args.get("end_date")  # 结束日期
    days = request.args.get("days", default=90, type=int)

    if not herb_name or not specification:
        return jsonify({"error": "缺少必要参数"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "数据库连接失败"}), 500

    try:
        # 计算日期范围
        if start_date and end_date:
            # 使用提供的日期范围
            query_start_date = start_date
            query_end_date = end_date
        else:
            # 使用天数计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            query_start_date = start_date
            query_end_date = end_date

        # 查询价格数据
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
        SELECT 
            recorded_at::date as date, 
            AVG(price::numeric) as avg_price,
            MIN(price::numeric) as min_price,
            MAX(price::numeric) as max_price
        FROM herb_prices
        WHERE herb_name = %s 
          AND specification = %s
        """

        params = [herb_name, specification]

        # 如果提供了地点，则按地点筛选，否则不筛选地点
        if location:
            query += " AND location = %s"
            params.append(location)

        # 添加日期范围条件
        if isinstance(query_start_date, str):
            query += " AND recorded_at::date >= %s AND recorded_at::date <= %s"
        else:
            query += " AND recorded_at >= %s AND recorded_at <= %s"

        params.extend([query_start_date, query_end_date])

        query += """
        GROUP BY recorded_at::date
        ORDER BY recorded_at::date
        """

        cursor.execute(query, params)
        results = cursor.fetchall()

        # 准备返回数据
        dates = []
        avg_prices = []
        min_prices = []
        max_prices = []

        for row in results:
            dates.append(row["date"].strftime("%Y-%m-%d"))
            avg_prices.append(float(row["avg_price"]) if row["avg_price"] else None)
            min_prices.append(float(row["min_price"]) if row["min_price"] else None)
            max_prices.append(float(row["max_price"]) if row["max_price"] else None)

        result = {
            "dates": dates,
            "avg_prices": avg_prices,
            "min_prices": min_prices,
            "max_prices": max_prices,
        }

        return jsonify(result)
    except Exception as e:
        import traceback

        print(f"价格趋势数据查询失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/market-comparison", methods=["GET"])
def get_market_comparison():
    """获取不同市场的价格比较数据"""
    herb_name = request.args.get("herb_name")
    specification = request.args.get("specification")

    if not herb_name or not specification:
        return jsonify({"error": "缺少必要参数"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "数据库连接失败"}), 500

    try:
        # 查询最近一个月各市场的平均价格
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
        SELECT 
            location, 
            AVG(price::numeric) as avg_price
        FROM herb_prices
        WHERE herb_name = %s 
          AND specification = %s
          AND recorded_at >= NOW() - INTERVAL '30 days'
        GROUP BY location
        ORDER BY avg_price DESC
        LIMIT 10
        """

        cursor.execute(query, (herb_name, specification))
        results = cursor.fetchall()

        # 准备返回数据
        locations = []
        prices = []

        for row in results:
            locations.append(row["location"])
            prices.append(float(row["avg_price"]) if row["avg_price"] else None)

        result = {"locations": locations, "prices": prices}

        return jsonify(result)
    except Exception as e:
        import traceback

        print(f"市场比较数据查询失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/weather-price-correlation", methods=["GET"])
def get_weather_price_correlation():
    """获取天气与价格的相关性数据"""
    herb_name = request.args.get("herb_name")
    specification = request.args.get("specification")
    location = request.args.get("location")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not herb_name or not specification:
        return jsonify({"error": "缺少必要参数"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "数据库连接失败"}), 500

    try:
        # 查询价格和天气数据
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
        SELECT 
            hp.recorded_at::date as date,
            AVG(hp.price::numeric) as avg_price,
            AVG(wd.temperature) as avg_temp,
            AVG(wd.precipitation) as avg_precip
        FROM herb_prices hp
        LEFT JOIN weather_data wd ON hp.location = wd.location AND hp.recorded_at::date = wd.date
        WHERE hp.herb_name = %s 
          AND hp.specification = %s
        """

        params = [herb_name, specification]

        if location:
            query += " AND hp.location = %s"
            params.append(location)

        # 添加日期范围条件
        if start_date and end_date:
            query += " AND hp.recorded_at::date BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        else:
            query += " AND hp.recorded_at >= NOW() - INTERVAL '90 days'"

        query += """
        GROUP BY hp.recorded_at::date
        ORDER BY hp.recorded_at::date
        """

        cursor.execute(query, params)
        results = cursor.fetchall()

        if not results:
            return jsonify({"error": "没有找到匹配的数据"}), 404

        # 准备返回数据
        dates = []
        prices = []
        temperatures = []
        precipitations = []

        for row in results:
            dates.append(row["date"].strftime("%Y-%m-%d"))
            prices.append(float(row["avg_price"]) if row["avg_price"] else None)
            temperatures.append(float(row["avg_temp"]) if row["avg_temp"] else None)
            precipitations.append(
                float(row["avg_precip"]) if row["avg_precip"] else None
            )

        result = {
            "dates": dates,
            "prices": prices,
            "temperatures": temperatures,
            "precipitations": precipitations,
        }

        return jsonify(result)
    except Exception as e:
        import traceback

        print(f"天气价格相关性数据查询失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/locations", methods=["GET"])
def get_locations():
    """获取所有地点信息（市场和产地）"""
    print("接收到获取地点信息的请求")
    conn = get_db_connection()
    if not conn:
        print("数据库连接失败")
        return jsonify({"error": "数据库连接失败"}), 500

    try:
        print("数据库连接成功")
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 先检查表结构
        print("检查location_mapping表结构")
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'location_mapping' AND table_schema = 'public'
        """)
        columns = [row['column_name'] for row in cursor.fetchall()]
        print(f"location_mapping表字段: {columns}")
        
        # 尝试使用不同的字段名组合
        print("执行SQL查询: SELECT * FROM location_mapping LIMIT 5")
        cursor.execute("SELECT * FROM location_mapping LIMIT 5")
        sample_data = cursor.fetchall()
        print(f"示例数据: {sample_data}")
        
        # 根据实际字段名调整查询
        if 'location_name' in columns:
            print("使用字段名: id, location_name, latitude, longitude, province, city, is_market")
            query = """
            SELECT 
                id, 
                location_name, 
                latitude, 
                longitude, 
                province, 
                city, 
                is_market
            FROM location_mapping
            ORDER BY province, city, location_name
            """
        else:
            print("使用通用查询: SELECT *")
            query = "SELECT * FROM location_mapping ORDER BY 1"
        
        cursor.execute(query)
        locations = cursor.fetchall()
        print(f"查询到 {len(locations)} 条地点数据")

        # 转换为前端需要的格式
        result = []
        for i, loc in enumerate(locations):
            try:
                # 适应不同的字段名
                if 'location_name' in loc:
                    location_name = loc.get('location_name', '')
                    latitude = loc.get('latitude', 0.0)
                    longitude = loc.get('longitude', 0.0)
                    province = loc.get('province', '')
                    city = loc.get('city', '')
                    is_market = loc.get('is_market', False)
                    id = loc.get('id', i + 1)
                else:
                    # 尝试使用通用字段名
                    location_name = loc.get(list(loc.keys())[1], '') if len(loc) > 1 else ''
                    latitude = loc.get(list(loc.keys())[2], 0.0) if len(loc) > 2 else 0.0
                    longitude = loc.get(list(loc.keys())[3], 0.0) if len(loc) > 3 else 0.0
                    province = loc.get(list(loc.keys())[4], '') if len(loc) > 4 else ''
                    city = loc.get(list(loc.keys())[5], '') if len(loc) > 5 else ''
                    is_market = loc.get(list(loc.keys())[6], False) if len(loc) > 6 else False
                    id = loc.get(list(loc.keys())[0], i + 1) if loc else i + 1
                
                # 判断是否为四大市场之一
                is_major_market = False
                if is_market and location_name in ["安国", "亳州", "玉林", "荷花池"]:
                    is_major_market = True

                # 安全地转换经纬度为浮点数
                try:
                    latitude = float(latitude) if latitude else 0.0
                    longitude = float(longitude) if longitude else 0.0
                except (ValueError, TypeError):
                    latitude = 0.0
                    longitude = 0.0

                result.append(
                    {
                        "id": id,
                        "location_name": location_name,
                        "latitude": latitude,
                        "longitude": longitude,
                        "province": province or "",
                        "city": city or "",
                        "is_market": bool(is_market),
                        "is_major_market": is_major_market,
                    }
                )
            except Exception as item_error:
                print(f"处理单条地点数据失败: {item_error}")
                continue

        print(f"处理完成，返回 {len(result)} 条数据")
        return jsonify(result)
    except Exception as e:
        import traceback

        print(f"获取地点信息失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
        print("数据库连接已关闭")


@app.route("/api/location-herbs", methods=["GET"])
def get_location_herbs():
    """获取指定地点的药材列表"""
    location = request.args.get("location")

    if not location:
        return jsonify({"error": "缺少地点参数"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "数据库连接失败"}), 500

    try:
        cursor = conn.cursor()

        # 查询该地点有价格记录的所有药材
        query = """
        SELECT DISTINCT herb_name
        FROM herb_prices
        WHERE location = %s
        ORDER BY herb_name
        """

        cursor.execute(query, (location,))
        herbs = [row[0] for row in cursor.fetchall()]

        return jsonify(herbs)
    except Exception as e:
        import traceback

        print(f"获取地点药材列表失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/location-prices", methods=["GET"])
def get_location_prices():
    """获取指定地点的药材价格信息"""
    location = request.args.get("location")
    herb_name = request.args.get("herb_name")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "数据库连接失败"}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 构建查询条件
        query = """
        SELECT 
            herb_name,
            specification,
            price,
            trend,
            week_change,
            month_change,
            recorded_at
        FROM herb_prices
        """

        params = []

        # 如果提供了地点，则按地点筛选
        if location and location.strip():
            query += " WHERE location = %s"
            params.append(location)
        else:
            query += " WHERE 1=1"

        # 如果提供了药材名称，则按药材名称筛选
        if herb_name:
            query += " AND herb_name = %s"
            params.append(herb_name)

        # 如果提供了日期范围，则按日期范围筛选
        if start_date and end_date:
            query += " AND recorded_at::date BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        else:
            # 否则获取最近的数据
            if location and location.strip():
                query += " AND recorded_at >= (SELECT MAX(recorded_at) - INTERVAL '3 days' FROM herb_prices WHERE location = %s)"
                params.append(location)
            else:
                query += " AND recorded_at >= (SELECT MAX(recorded_at) - INTERVAL '3 days' FROM herb_prices)"


        query += " ORDER BY herb_name, specification, recorded_at DESC"

        cursor.execute(query, params)
        prices = cursor.fetchall()

        # 处理结果，确保每个药材规格组合只返回最新的一条记录
        result = {}
        for row in prices:
            key = f"{row['herb_name']}_{row['specification']}"
            if key not in result:
                result[key] = {
                    "herb_name": row["herb_name"],
                    "specification": row["specification"],
                    "price": float(row["price"]),
                    "trend": row["trend"],
                    "week_change": row["week_change"],
                    "month_change": row["month_change"],
                    "recorded_at": row["recorded_at"].isoformat(),
                }

        return jsonify(list(result.values()))
    except Exception as e:
        import traceback

        print(f"获取地点价格信息失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/price-heatmap", methods=["GET"])
def get_price_heatmap():
    """获取价格热力图数据（按地点和时间）"""
    herb_name = request.args.get("herb_name")
    specification = request.args.get("specification")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    time_interval = request.args.get("time_interval", "month")  # 'week' 或 'month'

    if not herb_name:
        return jsonify({"error": "缺少药材名称参数"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "数据库连接失败"}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 根据时间间隔选择不同的日期格式化方式
        if time_interval == "week":
            date_format = "TO_CHAR(recorded_at, 'YYYY-WW')"
            date_label = "第WW周"
        else:  # 默认按月
            date_format = "TO_CHAR(recorded_at, 'YYYY-MM')"
            date_label = "MM月"

        # 构建查询
        query = f"""
        SELECT 
            location,
            {date_format} AS time_period,
            AVG(price::numeric) AS avg_price
        FROM herb_prices
        WHERE herb_name = %s
        """

        params = [herb_name]

        # 添加规格条件
        if specification:
            query += " AND specification = %s"
            params.append(specification)

        # 添加日期范围条件
        if start_date and end_date:
            query += " AND recorded_at::date BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        else:
            # 默认查询最近6个月的数据
            query += " AND recorded_at >= NOW() - INTERVAL '6 months'"

        query += f"""
        GROUP BY location, {date_format}
        ORDER BY location, {date_format}
        """

        cursor.execute(query, params)
        results = cursor.fetchall()

        if not results:
            return jsonify({"error": "没有找到匹配的数据"}), 404

        # 处理数据，转换为热力图所需的格式
        locations = set()
        time_periods = set()
        data_map = {}

        for row in results:
            location = row["location"]
            time_period = row["time_period"]
            avg_price = float(row["avg_price"]) if row["avg_price"] else 0

            locations.add(location)
            time_periods.add(time_period)
            data_map[(location, time_period)] = avg_price

        # 转换为有序列表
        locations = sorted(list(locations))
        time_periods = sorted(list(time_periods))

        # 构建热力图数据
        heatmap_data = []
        for i, location in enumerate(locations):
            for j, time_period in enumerate(time_periods):
                value = data_map.get((location, time_period), 0)
                if value > 0:  # 只包含有数据的点
                    heatmap_data.append([j, i, value])

        result = {
            "locations": locations,
            "time_periods": time_periods,
            "data": heatmap_data,
            "time_interval": time_interval,
        }

        return jsonify(result)
    except Exception as e:
        import traceback

        print(f"获取热力图数据失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# 添加价格预测相关API
@app.route("/api/price-prediction", methods=["POST"])
def predict_price():
    """执行价格预测"""
    try:
        data = request.json
        herb_name = data.get("herb_name")
        specification = data.get("specification")
        forecast_days = data.get("forecast_days", 30)
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        by_market = data.get("by_market", False)

        if not herb_name:
            return jsonify({"error": "缺少药材名称参数"}), 400

        # 确保规格参数为None或有效字符串
        if specification == "":
            specification = None

        # 首先检查数据库中是否有该药材和规格的数据
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "数据库连接失败"}), 500

        try:
            cursor = conn.cursor()
            query = """
            SELECT COUNT(*) FROM herb_prices 
            WHERE herb_name = %s
            """
            params = [herb_name]

            if specification:
                query += " AND specification = %s"
                params.append(specification)

            if start_date and end_date:
                query += " AND recorded_at::date BETWEEN %s AND %s"
                params.extend([start_date, end_date])

            cursor.execute(query, params)
            count = cursor.fetchone()[0]

            if count == 0:
                date_range_msg = (
                    f"在{start_date}至{end_date}期间" if start_date and end_date else ""
                )
                spec_msg = f"规格'{specification}'" if specification else "任何规格"
                return (
                    jsonify(
                        {
                            "error": f"没有找到{herb_name}的{spec_msg}价格数据{date_range_msg}。请尝试其他药材、规格或日期范围。"
                        }
                    ),
                    404,
                )

            print(f"找到{count}条{herb_name}的价格数据记录")

        finally:
            cursor.close()
            conn.close()

        # 执行预测
        result = predict_herb_price(
            herb_name=herb_name,
            specification=specification,
            forecast_days=forecast_days,
            start_date=start_date,
            end_date=end_date,
            by_market=by_market,
        )

        if not result:
            return (
                jsonify(
                    {
                        "error": "预测失败，可能是数据不足或格式不适合预测。请尝试其他药材、规格或日期范围。"
                    }
                ),
                400,
            )

        # 保存预测结果到文件
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{herb_name}"
        if specification:
            filename += f"_{specification}"
        filename += "_forecast.json"

        output_path = os.path.join(output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"预测完成，结果已保存到 {output_path}")

        return jsonify(result)

    except Exception as e:
        import traceback

        print(f"预测失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/api/actual-vs-predicted", methods=["GET"])
def get_actual_vs_predicted():
    """获取真实价格与预测价格比对数据"""
    try:
        herb_name = request.args.get("herb_name")
        prediction_date = request.args.get("prediction_date")
        specification = request.args.get("specification")

        if not herb_name or not prediction_date:
            return jsonify({"success": False, "error": "缺少必要参数"}), 400

        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 查询预测日期之后的实际价格数据
        query = """
        SELECT location, recorded_at::date as date, AVG(price) as price
        FROM herb_prices
        WHERE herb_name = %s
          AND recorded_at::date >= %s
        """

        params = [herb_name, prediction_date]

        # 只有当specification参数存在且不为空时，才添加到查询条件中
        if specification and specification.strip():
            query += " AND specification = %s"
            params.append(specification)

        query += """
        GROUP BY location, recorded_at::date
        ORDER BY location, recorded_at::date
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # 按市场分组
        market_data = {}
        for row in rows:
            market = row["location"]
            date = row["date"].strftime("%Y-%m-%d")
            price = float(row["price"])

            if market not in market_data:
                market_data[market] = {"dates": [], "prices": []}

            market_data[market]["dates"].append(date)
            market_data[market]["prices"].append(price)

        return jsonify({"success": True, "actual_data": market_data})

    except Exception as e:
        print(f"获取实际价格数据失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if "conn" in locals() and conn:
            cursor.close()
            conn.close()


@app.route("/api/prediction-results/<herb_name>", methods=["GET"])
def get_prediction_results(herb_name):
    """获取已保存的预测结果"""
    specification = request.args.get("specification")

    try:
        # 构建文件名
        filename = (
            f"{herb_name}_{specification}_forecast.json"
            if specification
            else f"{herb_name}_forecast.json"
        )
        filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "output", filename
        )

        # 检查文件是否存在
        if not os.path.exists(filepath):
            return jsonify({"error": "未找到预测结果"}), 404

        # 读取预测结果
        with open(filepath, "r", encoding="utf-8") as f:
            result = json.load(f)

        return jsonify(result)
    except Exception as e:
        import traceback

        print(f"获取预测结果失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/api/prediction-history", methods=["GET"])
def get_prediction_history():
    """获取所有历史预测记录"""
    try:
        output_dir = os.path.join(os.path.dirname(__file__), "output")

        # 确保目录存在
        if not os.path.exists(output_dir):
            return jsonify([])

        # 获取所有json文件
        prediction_files = [
            f for f in os.listdir(output_dir) if f.endswith("_forecast.json")
        ]

        # 提取预测信息
        predictions = []
        for file in prediction_files:
            file_path = os.path.join(output_dir, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 提取基本信息
                herb_name = data.get("herb_name", "")
                specification = data.get("specification", "")
                by_market = data.get("by_market", False)
                forecast_days = data.get("forecast_days", 0)

                # 获取预测日期范围
                date_range = []
                if by_market and "market_predictions" in data:
                    # 获取第一个市场的第一个模型的预测日期
                    first_market = list(data["market_predictions"].keys())[0]
                    first_model = list(
                        data["market_predictions"][first_market]["predictions"].keys()
                    )[0]
                    dates = data["market_predictions"][first_market]["predictions"][
                        first_model
                    ]["forecast"]["date"]
                    if dates:
                        date_range = [dates[0], dates[-1]]
                elif not by_market and "predictions" in data:
                    # 获取第一个模型的预测日期
                    first_model = list(data["predictions"].keys())[0]
                    dates = data["predictions"][first_model]["forecast"]["date"]
                    if dates:
                        date_range = [dates[0], dates[-1]]

                # 获取文件修改时间
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                predictions.append(
                    {
                        "filename": file,
                        "herb_name": herb_name,
                        "specification": specification or "全部规格",
                        "by_market": by_market,
                        "forecast_days": forecast_days,
                        "date_range": date_range,
                        "created_at": mod_time,
                    }
                )

            except Exception as e:
                print(f"读取预测文件 {file} 时出错: {e}")

        # 按修改时间排序，最新的在前
        predictions.sort(key=lambda x: x["created_at"], reverse=True)

        return jsonify(predictions)

    except Exception as e:
        print(f"获取预测历史记录失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/prediction-result/<filename>", methods=["GET"])
def get_prediction_result(filename):
    """获取指定预测文件的内容"""
    try:
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        file_path = os.path.join(output_dir, filename)

        if not os.path.exists(file_path):
            return jsonify({"error": "预测文件不存在"}), 404

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return jsonify(data)

    except Exception as e:
        print(f"获取预测结果失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/prediction-models", methods=["GET"])
def get_prediction_models():
    """获取可用的预测模型列表"""
    models = [
        {
            "id": "ARIMA",
            "name": "ARIMA模型",
            "description": "自回归综合移动平均模型，适合短期预测",
        },
        {
            "id": "Prophet",
            "name": "Prophet模型",
            "description": "Facebook开发的时间序列预测模型，能处理季节性和节假日效应",
        },
        {
            "id": "LSTM",
            "name": "LSTM神经网络",
            "description": "长短期记忆网络，深度学习模型，适合捕捉长期依赖关系",
        },
        {
            "id": "XGBoost",
            "name": "XGBoost模型",
            "description": "梯度提升树模型，强大的机器学习算法",
        },
        {
            "id": "Ensemble",
            "name": "集成模型",
            "description": "综合多个模型的预测结果，通常表现更稳定",
        },
    ]
    return jsonify(models)


@app.route("/api/price-ranking", methods=["GET"])
def get_price_ranking():
    """获取药材价格涨幅排行榜数据"""
    ranking_type = request.args.get("ranking_type", "week_change")  # 默认按周涨幅排序
    limit = request.args.get("limit", default=10, type=int)  # 默认返回10条记录
    positive_only = (
        request.args.get("positive_only", "true").lower() == "true"
    )  # 是否只返回正的涨幅

    # 验证排序字段
    valid_ranking_types = ["week_change", "month_change", "year_change"]
    if ranking_type not in valid_ranking_types:
        return (
            jsonify(
                {"error": f"无效的排序字段，有效值为: {', '.join(valid_ranking_types)}"}
            ),
            400,
        )

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "数据库连接失败"}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 构建查询
        query = f"""
            SELECT 
                herb_name,
                specification,
                location,
                price,
                trend,
                {ranking_type},
                recorded_at
            FROM herb_prices
            WHERE {ranking_type} IS NOT NULL
            """

        # 如果只需要正的涨幅，使用类型转换
        if positive_only:
            # 修复：使用双百分号来表示实际的百分号，避免格式化问题
            query += f"""
            AND (
                CASE 
                    WHEN {ranking_type} LIKE '%%' THEN CAST(REPLACE({ranking_type}, '%', '') AS FLOAT) > 0
                    ELSE CAST({ranking_type} AS FLOAT) > 0
                END
            )
            """

        # 添加排序和限制
        query += f"""
        ORDER BY 
            CASE 
                WHEN {ranking_type} LIKE '%%' THEN CAST(REPLACE({ranking_type}, '%', '') AS FLOAT)
                ELSE CAST({ranking_type} AS FLOAT)
            END DESC
        LIMIT {limit}
        """

        # 修改：直接在查询字符串中使用limit值，不使用参数占位符
        cursor.execute(query)
        results = cursor.fetchall()

        # 处理结果
        ranking_data = []
        for row in results:
            ranking_data.append(
                {
                    "herb_name": row["herb_name"],
                    "specification": row["specification"],
                    "location": row["location"],
                    "price": float(row["price"]),
                    "trend": row["trend"],
                    "week_change": row.get("week_change"),
                    "month_change": row.get("month_change"),
                    "year_change": row.get(
                        "year_change"
                    ),  # 使用get方法，因为可能不存在
                    "recorded_at": (
                        row["recorded_at"].isoformat() if row["recorded_at"] else None
                    ),
                }
            )

        return jsonify(ranking_data)
    except Exception as e:
        import traceback

        print(f"获取价格涨幅排行榜失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# 获取药材列表
@app.route("/api/herbs/list", methods=["GET"])
def get_herbs_list():
    """获取所有药材名称列表"""
    herb_names = get_herb_names_from_db()
    return jsonify(herb_names)


# 情感分析
@app.route("/api/sentiment-analysis", methods=["GET"])
def analyze_herb_sentiment():
    """分析药材市场情绪"""
    herb_name = request.args.get("herb_name")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not herb_name:
        return jsonify({"success": False, "error": "缺少药材名称参数"}), 400

    result = get_herb_sentiment_analysis(herb_name, start_date, end_date)
    return jsonify(result)


def get_herb_sentiment_analysis(herb_name, start_date=None, end_date=None):
    """获取药材的市场情绪分析结果"""
    try:
        # 获取相关新闻数据
        news_df = fetch_news_data(
            herb_name=herb_name, start_date=start_date, end_date=end_date, limit=100
        )

        if news_df.empty:
            return {"success": False, "error": f"未找到与{herb_name}相关的新闻数据"}

        # 分析情感
        sentiment_result = analyze_sentiment(news_df)

        if not sentiment_result:
            return {"success": False, "error": "情感分析失败"}

        # 构建返回结果
        result = {
            "success": True,
            "herb_name": herb_name,
            "date_range": {
                "start_date": (
                    start_date
                    if start_date
                    else news_df["publish_date"].min().strftime("%Y-%m-%d")
                ),
                "end_date": (
                    end_date
                    if end_date
                    else news_df["publish_date"].max().strftime("%Y-%m-%d")
                ),
            },
            "news_count": len(news_df),
            "sentiment_analysis": sentiment_result,
        }

        # 添加趋势预测
        avg_sentiment = sentiment_result.get("avg_sentiment", 0)
        result["trend_prediction"] = {
            "trend": (
                "up"
                if avg_sentiment > 0.1
                else ("down" if avg_sentiment < -0.1 else "stable")
            ),
            "confidence": min(0.9, 0.5 + abs(avg_sentiment) * 0.5),
            "explanation": get_trend_explanation(avg_sentiment),
        }

        return result

    except Exception as e:
        import traceback

        print(f"情感分析失败: {e}")
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}


def get_trend_explanation(sentiment_score):
    """根据情感分数生成趋势解释"""
    if sentiment_score > 0.3:
        return "市场情绪非常积极，预计价格可能显著上涨"
    elif sentiment_score > 0.1:
        return "市场情绪偏向积极，预计价格可能上涨"
    elif sentiment_score < -0.3:
        return "市场情绪非常消极，预计价格可能显著下跌"
    elif sentiment_score < -0.1:
        return "市场情绪偏向消极，预计价格可能下跌"
    else:
        return "市场情绪中性，预计价格可能保持稳定"


@app.route("/api/price-trend-clustering", methods=["GET"])
def get_price_trend_clustering():
    """获取价格趋势聚类分析结果"""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    save_result = request.args.get("save_result", "false").lower() == "true"

    try:
        # 调用聚类分析函数
        result = analyze_price_trends(start_date, end_date, save_result)

        if "error" in result:
            return jsonify({"error": result["error"]}), 400

        return jsonify(result)
    except Exception as e:
        import traceback

        print(f"价格趋势聚类分析失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/api/save-clustering-result", methods=["POST"])
def save_clustering_result_api():  # 修改函数名，避免与导入的函数同名
    """保存聚类分析结果到文件"""
    try:
        # 从请求体获取聚类结果数据
        clustering_data = request.json

        if not clustering_data:
            return jsonify({"error": "缺少聚类数据"}), 400

        # 获取日期范围
        date_range = clustering_data.get("date_range", {})
        start_date = date_range.get("start_date")
        end_date = date_range.get("end_date")

        # 导入并调用 price_trend_clustering.py 中的函数
        from price_trend_clustering import save_clustering_result

        file_path = save_clustering_result(clustering_data, start_date, end_date)

        if file_path:
            return jsonify(
                {"success": True, "message": "聚类结果保存成功", "file_path": file_path}
            )
        else:
            return jsonify({"error": "保存聚类结果失败"}), 500
    except Exception as e:
        import traceback

        print(f"保存聚类结果失败: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/api/price-trend-clustering/history", methods=["GET"])
def get_clustering_history():
    """获取历史聚类结果文件列表"""
    from price_trend_clustering import get_clustering_history_files

    history_files = get_clustering_history_files()
    return jsonify(history_files)


@app.route("/api/price-trend-clustering/load/<filename>", methods=["GET"])
def load_clustering_file(filename):
    """加载指定的聚类结果文件"""
    from price_trend_clustering import load_clustering_result

    result = load_clustering_result(filename)
    return jsonify(result)


@app.route("/api/today-news", methods=["GET"])
def get_today_news():
    """获取当天新闻资讯"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "数据库连接失败"}), 500

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查询最近的10条新闻
        query = """
        SELECT 
            id, title, content, market_name, publish_time, herb_name
        FROM news_info1
        ORDER BY publish_time DESC
        LIMIT 10
        """

        cursor.execute(query)
        news = cursor.fetchall()

        # 导入标签提取模块
        from news_tagging import enrich_news_with_tags
        
        # 为新闻添加标签
        news_with_tags = enrich_news_with_tags(news)

        return jsonify(news_with_tags)
    except Exception as e:
        print(f"获取当天新闻失败: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


@app.route("/api/generate-weekly-report", methods=["GET"])
def generate_weekly_report_api():
    """生成中药材周报"""
    try:
        # 导入周报生成模块
        from weekly_report_generator import generate_weekly_report
        
        # 生成周报
        result = generate_weekly_report()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({"error": result['error']}), 400
    except Exception as e:
        print(f"生成周报失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/herb-weekly-report", methods=["GET"])
def generate_herb_weekly_report_api():
    """生成中药材周报（智能体版本）"""
    try:
        # 导入AI版本的周报智能体模块
        from herb_weekly_agent_ai import generate_weekly_report
        
        # 生成周报
        result = generate_weekly_report()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({"error": result['error']}), 400
    except Exception as e:
        print(f"生成周报失败: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


import threading

# 用于存储后台任务状态
background_tasks = {}

def check_port_in_use(port):
    """检查端口是否被占用"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except Exception:
        return False

def run_ai_assistant_in_background():
    """在后台线程中运行AI助手服务"""
    import subprocess
    import os
    import sys

    try:
        # 检查端口8000是否已被占用
        if check_port_in_use(8000):
            print("[启动] 端口8000已被占用，AI助手服务可能已经在运行，跳过启动")
            return

        print("[启动] 正在启动AI助手服务...")

        # 构建ai_assistant.py的绝对路径
        # 使用 os.path.abspath 确保获得绝对路径，而不是依赖 __file__
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ai_assistant_path = os.path.join(script_dir, 'ai_assistant.py')

        # 验证 ai_assistant.py 文件是否存在
        if not os.path.exists(ai_assistant_path):
            print(f"[启动] 错误: ai_assistant.py 文件不存在于 {ai_assistant_path}")
            return

        # 使用当前 Python 解释器（虚拟环境中的 python）执行脚本
        python_executable = sys.executable

        # 验证 Python 解释器是否存在，如果不存在或为空，使用虚拟环境中的 python
        if not python_executable or not os.path.exists(python_executable):
            print(f"[启动] 错误: Python 解释器无效: {repr(python_executable)}")
            # 尝试使用虚拟环境中的 python（与启动 Flask 相同的虚拟环境）
            venv_python = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'bin', 'python')
            if os.path.exists(venv_python):
                python_executable = venv_python
                print(f"[启动] 使用虚拟环境 Python: {python_executable}")
            else:
                # 最后尝试系统 python3
                python_executable = 'python3'
                print(f"[启动] 回退到系统 python3")

        # 使用列表形式传递参数，避免 shell=True 的安全风险和路径解析问题
        command = [python_executable, ai_assistant_path]
        print(f"[启动] 运行命令: {' '.join(command)}")

        # 详细调试信息
        print(f"[启动] 调试信息:")
        print(f"  - python_executable = {repr(python_executable)}")
        print(f"  - ai_assistant_path = {repr(ai_assistant_path)}")
        print(f"  - command = {repr(command)}")
        print(f"  - cwd = {repr(script_dir)}")

        # 运行脚本，不设置 shell=True，并指定工作目录
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=script_dir
        )

        print(f"[启动] AI助手服务返回码: {result.returncode}")
        if result.stdout:
            print(f"[启动] AI助手服务输出: {result.stdout}")
        if result.stderr:
            print(f"[启动] AI助手服务错误: {result.stderr}")

    except Exception as e:
        print(f"[启动] 启动AI助手服务异常: {e}")
        import traceback
        print(traceback.format_exc())

def run_new5_in_background(task_id):
    """在后台线程中运行new5.py"""
    import subprocess
    import os
    import sys
    import shlex

    try:
        background_tasks[task_id] = {"status": "running", "output": "", "error": ""}

        # 构建new5.py的绝对路径，使用 os.path.abspath 确保路径正确
        script_dir = os.path.dirname(os.path.abspath(__file__))
        new5_path = os.path.join(script_dir, '..', 'problem', 'new5.py')
        new5_path = os.path.abspath(new5_path)  # 转换为绝对路径
        project_root = os.path.dirname(script_dir)

        # 验证 new5.py 文件是否存在
        if not os.path.exists(new5_path):
            print(f"错误: new5.py 文件不存在于 {new5_path}")
            background_tasks[task_id] = {
                "status": "error",
                "output": "",
                "error": f"文件不存在: {new5_path}"
            }
            return

        # 使用当前 Python 解释器（虚拟环境中的 python）执行脚本
        python_executable = sys.executable

        # 验证 Python 解释器是否存在
        if not python_executable or not os.path.exists(python_executable):
            print(f"错误: Python 解释器无效: {python_executable}")
            python_executable = 'python3'
            if not os.path.exists(python_executable):
                python_executable = 'python'

        # 使用列表形式传递参数，避免 shell=True 的安全风险和路径解析问题
        command = [python_executable, new5_path]
        print(f"运行命令: {' '.join(command)}")

        # 运行脚本，不设置 shell=True，并指定工作目录
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(new5_path),
            timeout=600  # 10分钟超时
        )

        print(f"new5.py返回码: {result.returncode}")
        if result.stdout:
            print(f"new5.py输出: {result.stdout}")
        if result.stderr:
            print(f"new5.py错误: {result.stderr}")

        background_tasks[task_id] = {
            "status": "completed" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "error": result.stderr
        }

    except subprocess.TimeoutExpired:
        print("new5.py执行超时")
        background_tasks[task_id] = {
            "status": "timeout",
            "output": "",
            "error": "脚本执行超时（超过10分钟）"
        }
    except Exception as e:
        print(f"运行new5.py异常: {e}")
        import traceback
        print(traceback.format_exc())
        background_tasks[task_id] = {
            "status": "error",
            "output": "",
            "error": str(e)
        }

def run_new4_in_background(task_id):
    """在后台线程中运行new4.py（天气数据爬虫）"""
    import subprocess
    import os
    import sys
    
    try:
        background_tasks[task_id] = {"status": "running", "output": "", "error": ""}
        
        # 构建new4.py的路径
        new4_path = os.path.join(os.path.dirname(__file__), '..', 'problem', 'new4.py')
        
        # 使用当前 Python 解释器（虚拟环境中的 python）执行脚本
        python_executable = sys.executable
        
        # 使用列表形式传递参数，避免 shell=True 的安全风险和路径解析问题
        command = [python_executable, new4_path]
        print(f"运行命令: {' '.join(command)}")
        
        # 运行new4.py脚本，设置超时时间为20分钟（天气数据获取可能需要更长时间）
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(new4_path),
            timeout=1200  # 20分钟超时
        )
        
        print(f"new4.py返回码: {result.returncode}")
        if result.stdout:
            print(f"new4.py输出: {result.stdout}")
        if result.stderr:
            print(f"new4.py错误: {result.stderr}")
        
        background_tasks[task_id] = {
            "status": "completed" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "error": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        print("new4.py执行超时")
        background_tasks[task_id] = {
            "status": "timeout",
            "output": "",
            "error": "脚本执行超时（超过20分钟）"
        }
    except Exception as e:
        print(f"运行new4.py异常: {e}")
        import traceback
        print(traceback.format_exc())
        background_tasks[task_id] = {
            "status": "error",
            "output": "",
            "error": str(e)
        }

def run_new2_in_background(task_id):
    """在后台线程中运行new2.py（中药材价格爬虫）"""
    import subprocess
    import os
    import sys
    
    try:
        background_tasks[task_id] = {"status": "running", "output": "", "error": ""}
        
        # 构建new2.py的路径
        new2_path = os.path.join(os.path.dirname(__file__), '..', 'problem', 'new2.py')
        
        # 使用当前 Python 解释器（虚拟环境中的 python）执行脚本
        python_executable = sys.executable
        
        # 使用列表形式传递参数，避免 shell=True 的安全风险和路径解析问题
        command = [python_executable, new2_path]
        print(f"运行命令: {' '.join(command)}")
        
        # 运行脚本，不设置 shell=True，并指定工作目录
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(new2_path),
            timeout=1800  # 30分钟超时
        )
        
        print(f"new2.py返回码: {result.returncode}")
        if result.stdout:
            print(f"new2.py输出: {result.stdout}")
        if result.stderr:
            print(f"new2.py错误: {result.stderr}")
        
        background_tasks[task_id] = {
            "status": "completed" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "error": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        print("new2.py执行超时")
        background_tasks[task_id] = {
            "status": "timeout",
            "output": "",
            "error": "脚本执行超时（超过30分钟）"
        }
    except Exception as e:
        print(f"运行new2.py异常: {e}")
        import traceback
        print(traceback.format_exc())
        background_tasks[task_id] = {
            "status": "error",
            "output": "",
            "error": str(e)
        }


@app.route("/api/run-new5", methods=["GET"])
def run_new5():
    """在后台运行new5.py脚本爬取数据（非阻塞）"""
    import uuid
    try:
        task_id = str(uuid.uuid4())
        
        # 在后台线程中运行
        thread = threading.Thread(target=run_new5_in_background, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "message": "爬虫已在后台启动",
            "task_id": task_id
        })
    except Exception as e:
        print(f"启动new5.py失败: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/api/run-new5/status/<task_id>", methods=["GET"])
def check_new5_status(task_id):
    """检查后台任务状态"""
    if task_id in background_tasks:
        return jsonify(background_tasks[task_id])
    else:
        return jsonify({"status": "not_found"}), 404


# @app.route('/api/price-correlation', methods=['GET'])
# def get_price_correlation():


@app.route("/api/ai-assistant", methods=["POST"])
def ai_assistant():
    """AI智能对话助手"""
    try:
        data = request.json
        message = data.get("message")
        
        if not message:
            return jsonify({"error": "缺少消息参数"}), 400
        
        # 简单的回复，因为AI助手现在是独立服务
        return jsonify({"response": "AI助手服务已迁移到独立的FastAPI服务，请使用http://localhost:8000/chat接口"})
    except Exception as e:
        import traceback
        print(f"AI助手API出错: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# 添加用户认证相关API
@app.route("/api/user/login", methods=["POST"])
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return jsonify({
                "code": 400,
                "message": "用户名和密码不能为空"
            }), 400
        
        # 连接数据库，验证用户信息
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 验证用户（使用 password_hash 字段）
            cursor.execute("SELECT id, username, phone FROM users WHERE username = %s AND password_hash = %s", (username, password))
            user = cursor.fetchone()
            
            if user:
                # 登录成功后运行 new5.py 文件
                import uuid
                task_id = str(uuid.uuid4())
                # 在后台线程中运行
                import threading
                thread = threading.Thread(target=run_new5_in_background, args=(task_id,))
                thread.daemon = True
                thread.start()
                
                return jsonify({
                    "code": 200,
                    "message": "登录成功，爬虫已在后台启动",
                    "data": {
                        "username": username,
                        "token": "dummy_token_123456",
                        "crawler_task_id": task_id
                    }
                })
            else:
                return jsonify({
                    "code": 401,
                    "message": "用户名或密码错误"
                }), 401
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": str(e)
        }), 500

@app.route("/api/user/register", methods=["POST"])
def register():
    """用户注册"""
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")
        phone = data.get("phone")
        
        if not username or not password:
            return jsonify({
                "code": 400,
                "message": "用户名和密码不能为空"
            }), 400
        
        # 连接数据库，保存用户信息
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({
                    "code": 400,
                    "message": "用户名已存在"
                }), 400
            
            # 插入新用户（使用 password_hash 字段）
            cursor.execute(
                "INSERT INTO users (username, password_hash, phone, created_at) VALUES (%s, %s, %s, %s)",
                (username, password, phone, datetime.now())
            )
            conn.commit()
            
            return jsonify({
                "code": 200,
                "message": "注册成功",
                "data": {
                    "username": username
                }
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": str(e)
        }), 500

def run_crawlers_on_startup():
    """在应用启动时自动运行爬虫脚本"""
    import uuid
    try:
        # 启动new5.py（新闻爬虫）
        new5_task_id = str(uuid.uuid4())
        print(f"[启动] 正在启动新闻爬虫任务，任务ID: {new5_task_id}")
        new5_thread = threading.Thread(target=run_new5_in_background, args=(new5_task_id,))
        new5_thread.daemon = True
        new5_thread.start()
        
        # 启动new4.py（天气数据爬虫）
        new4_task_id = str(uuid.uuid4())
        print(f"[启动] 正在启动天气数据爬虫任务，任务ID: {new4_task_id}")
        new4_thread = threading.Thread(target=run_new4_in_background, args=(new4_task_id,))
        new4_thread.daemon = True
        new4_thread.start()
        
        # 启动new2.py（中药材价格爬虫）
        new2_task_id = str(uuid.uuid4())
        print(f"[启动] 正在启动中药材价格爬虫任务，任务ID: {new2_task_id}")
        new2_thread = threading.Thread(target=run_new2_in_background, args=(new2_task_id,))
        new2_thread.daemon = True
        new2_thread.start()
        
        print(f"[启动] 所有爬虫任务已在后台启动")
        return {"new5_task_id": new5_task_id, "new4_task_id": new4_task_id, "new2_task_id": new2_task_id}
    except Exception as e:
        print(f"[启动] 启动爬虫任务失败: {e}")
        import traceback
        print(traceback.format_exc())
        return None


if __name__ == "__main__":
    # 在Flask应用启动前运行爬虫脚本
    print("=" * 50)
    print("Flask应用启动中...")
    print("=" * 50)
    
    # 启动时自动运行所有爬虫（新闻和天气数据）
    run_crawlers_on_startup()
    
    # 启动时自动运行AI助手服务
    print("[启动] 准备启动AI助手服务...")
    ai_assistant_thread = threading.Thread(target=run_ai_assistant_in_background)
    ai_assistant_thread.daemon = True  # 设置为守护线程，当主线程结束时自动结束
    ai_assistant_thread.start()
    print("[启动] AI助手服务线程已启动")
    
    # 启动Flask应用
    app.run(debug=True, host="0.0.0.0", port=5002)