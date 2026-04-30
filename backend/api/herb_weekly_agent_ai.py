"""
中药材周报智能体 - 阿里云通义千问AI版本
功能：
1. 获取一周资讯并进行总结概括
2. 提取关键信息和关键字
3. 根据资讯和关键字分别为中药材种植户和买家提供建议
"""

import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json
import re
import requests
from typing import Dict, List, Any

# 数据库连接配置
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}

# 阿里云通义千问API配置
AI_CONFIG = {
    'API_BASE_URL': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    'API_KEY': 'sk-5bdbd09ed3084a9aadd4d852c73fc410',
    'MODEL': 'qwen-turbo',
    'TIMEOUT': 30000
}


def get_db_connection():
    """创建数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None


def fetch_weekly_news():
    """获取一周的新闻资讯"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        query = """
        SELECT id, title, content, market_name, publish_time, herb_name
        FROM news_info1
        WHERE publish_time BETWEEN %s AND %s
        ORDER BY publish_time DESC
        """
        
        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        
        df = pd.DataFrame(rows)
        
        if not df.empty and 'publish_time' in df.columns:
            df['publish_time'] = pd.to_datetime(df['publish_time'])
        
        return df
        
    except Exception as e:
        print(f"获取新闻数据出错: {e}")
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


def fetch_weekly_prices():
    """获取一周的价格数据"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        query = """
        SELECT herb_name, specification, location, price, trend, week_change, recorded_at
        FROM herb_prices
        WHERE recorded_at BETWEEN %s AND %s
        ORDER BY herb_name, recorded_at DESC
        """
        
        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        
        df = pd.DataFrame(rows)
        
        if not df.empty and 'recorded_at' in df.columns:
            df['recorded_at'] = pd.to_datetime(df['recorded_at'])
        
        return df
        
    except Exception as e:
        print(f"获取价格数据出错: {e}")
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


def call_ai_api(prompt: str, system_prompt: str = None) -> str:
    """调用阿里云通义千问API"""
    try:
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        headers = {
            'Authorization': f'Bearer {AI_CONFIG["API_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': AI_CONFIG['MODEL'],
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 2000
        }
        
        response = requests.post(
            AI_CONFIG['API_BASE_URL'],
            headers=headers,
            json=payload,
            timeout=AI_CONFIG['TIMEOUT'] / 1000
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"AI API调用失败: {response.status_code}, {response.text}")
            return ""
            
    except Exception as e:
        print(f"调用AI API出错: {e}")
        return ""


def analyze_sentiment_with_ai(news_df: pd.DataFrame) -> Dict[str, Any]:
    """使用AI分析市场情绪"""
    if news_df.empty:
        return {
            'sentiment': 'neutral',
            'score': 0,
            'positive_ratio': 0,
            'negative_ratio': 0,
            'summary': '暂无数据'
        }
    
    # 准备新闻文本
    news_texts = []
    for _, row in news_df.iterrows():
        title = row.get('title', '')
        content = row.get('content', '')
        news_texts.append(f"标题：{title}\n内容：{content}")
    
    # 限制新闻数量，避免token超限
    news_sample = news_texts[:20]
    news_summary = "\n\n".join(news_sample)
    
    system_prompt = """你是一个专业的中药材市场分析师。请分析提供的中药材市场资讯，判断市场情绪。
你需要返回JSON格式的结果，包含以下字段：
- sentiment: 市场情绪（positive/neutral/negative）
- positive_ratio: 积极情绪占比（0-1之间的小数）
- negative_ratio: 消极情绪占比（0-1之间的小数）
- summary: 市场情绪总结（一句话，不超过50字）"""
    
    prompt = f"""请分析以下中药材市场资讯的市场情绪：

{news_summary}

请以JSON格式返回分析结果。"""
    
    ai_response = call_ai_api(prompt, system_prompt)
    
    if not ai_response:
        return {
            'sentiment': 'neutral',
            'score': 0,
            'positive_ratio': 0.5,
            'negative_ratio': 0.5,
            'summary': '市场情绪平稳'
        }
    
    try:
        result = json.loads(ai_response)
        return {
            'sentiment': result.get('sentiment', 'neutral'),
            'score': 0 if result.get('sentiment') == 'neutral' else (1 if result.get('sentiment') == 'positive' else -1),
            'positive_ratio': result.get('positive_ratio', 0.5),
            'negative_ratio': result.get('negative_ratio', 0.5),
            'summary': result.get('summary', '市场情绪平稳')
        }
    except json.JSONDecodeError:
        return {
            'sentiment': 'neutral',
            'score': 0,
            'positive_ratio': 0.5,
            'negative_ratio': 0.5,
            'summary': '市场情绪平稳'
        }


def summarize_news_with_ai(news_df: pd.DataFrame) -> Dict[str, Any]:
    """使用AI总结一周资讯"""
    if news_df.empty:
        return {
            'total_count': 0,
            'summary': '本周暂无资讯数据',
            'key_events': [],
            'hot_herbs': [],
            'active_markets': []
        }
    
    total_count = len(news_df)
    
    # 提取热门药材
    herb_counter = {}
    for _, row in news_df.iterrows():
        herb_name = row.get('herb_name', '')
        if herb_name and isinstance(herb_name, str):
            herbs = [h.strip() for h in herb_name.split(',') if h.strip()]
            for herb in herbs:
                herb_counter[herb] = herb_counter.get(herb, 0) + 1
    
    hot_herbs = sorted(herb_counter.items(), key=lambda x: x[1], reverse=True)[:5]
    hot_herbs = [{'name': name, 'count': count} for name, count in hot_herbs]
    
    # 活跃市场
    market_counter = {}
    for market in news_df['market_name'].dropna():
        market_counter[market] = market_counter.get(market, 0) + 1
    
    active_markets = sorted(market_counter.items(), key=lambda x: x[1], reverse=True)[:5]
    active_markets = [{'name': name, 'count': count} for name, count in active_markets]
    
    # 使用AI提取关键事件和生成总结
    news_sample = news_df.head(15)
    news_texts = []
    for _, row in news_sample.iterrows():
        title = row.get('title', '')
        publish_time = row.get('publish_time')
        time_str = publish_time.strftime('%m-%d') if pd.notna(publish_time) else ''
        news_texts.append(f"[{time_str}] {title}")
    
    news_summary_text = "\n".join(news_texts)
    
    system_prompt = """你是一个专业的中药材市场分析师。请分析提供的中药材市场资讯，提取关键事件并生成总结。
你需要返回JSON格式的结果，包含以下字段：
- summary: 本周资讯总结（不超过100字）
- key_events: 关键事件列表，每个事件包含title（事件标题，不超过50字）、date（日期，格式MM-DD）、type（事件类型，如产新、涨价、天气、政策等）"""
    
    prompt = f"""请分析以下中药材市场资讯，提取关键事件并生成总结：

{news_summary_text}

请以JSON格式返回分析结果。"""
    
    ai_response = call_ai_api(prompt, system_prompt)
    
    key_events = []
    summary = f"本周共发布{total_count}条中药材相关资讯。"
    
    if hot_herbs:
        summary += f"最受关注的品种为{', '.join([h['name'] for h in hot_herbs[:3]])}。"
    
    if active_markets:
        summary += f"主要资讯来源市场包括{', '.join([m['name'] for m in active_markets[:3]])}。"
    
    if ai_response:
        try:
            result = json.loads(ai_response)
            if 'summary' in result:
                summary = result['summary']
            if 'key_events' in result:
                key_events = result['key_events'][:5]
        except json.JSONDecodeError:
            pass
    
    return {
        'total_count': total_count,
        'summary': summary,
        'key_events': key_events,
        'hot_herbs': hot_herbs,
        'active_markets': active_markets
    }


def extract_keywords_with_ai(news_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """使用AI提取关键词"""
    if news_df.empty:
        return []
    
    # 准备文本
    all_text = ' '.join(news_df['content'].fillna('').astype(str).tolist()[:10])
    
    system_prompt = """你是一个专业的中药材市场分析师。请从提供的中药材市场资讯中提取关键词。
你需要返回JSON格式的结果，包含以下字段：
- keywords: 关键词列表，每个关键词包含word（词语）和weight（权重，0-1之间的小数，表示重要性）"""
    
    prompt = f"""请从以下中药材市场资讯中提取15个最重要的关键词：

{all_text}

请以JSON格式返回关键词列表。"""
    
    ai_response = call_ai_api(prompt, system_prompt)
    
    if not ai_response:
        return []
    
    try:
        result = json.loads(ai_response)
        if 'keywords' in result:
            return result['keywords'][:15]
    except json.JSONDecodeError:
        pass
    
    return []


def analyze_price_trends_with_ai(prices_df: pd.DataFrame) -> Dict[str, Any]:
    """使用AI分析价格趋势"""
    if prices_df.empty:
        return {
            'trend_summary': '暂无价格数据',
            'up_herbs': [],
            'down_herbs': [],
            'stable_herbs': []
        }
    
    up_herbs = []
    down_herbs = []
    stable_herbs = []
    
    for herb_name in prices_df['herb_name'].unique():
        herb_data = prices_df[prices_df['herb_name'] == herb_name]
        
        if herb_data.empty:
            continue
        
        latest = herb_data.iloc[0]
        week_change = latest.get('week_change', '')
        
        herb_info = {
            'name': herb_name,
            'price': latest.get('price'),
            'specification': latest.get('specification', ''),
            'location': latest.get('location', '')
        }
        
        if week_change and '上涨' in str(week_change):
            up_herbs.append(herb_info)
        elif week_change and '下跌' in str(week_change):
            down_herbs.append(herb_info)
        else:
            stable_herbs.append(herb_info)
    
    trend_parts = []
    if up_herbs:
        trend_parts.append(f"上涨品种{len(up_herbs)}个")
    if down_herbs:
        trend_parts.append(f"下跌品种{len(down_herbs)}个")
    if stable_herbs:
        trend_parts.append(f"价格稳定品种{len(stable_herbs)}个")
    
    trend_summary = '，'.join(trend_parts) if trend_parts else '价格波动较小'
    
    return {
        'trend_summary': trend_summary,
        'up_herbs': up_herbs[:5],
        'down_herbs': down_herbs[:5],
        'stable_herbs': stable_herbs[:5]
    }


def generate_grower_advice_with_ai(sentiment_analysis: Dict, news_summary: Dict, 
                                  price_analysis: Dict, keywords: List) -> List[str]:
    """使用AI为种植户生成建议"""
    system_prompt = """你是一个专业的中药材种植专家。请根据提供的市场数据为中药材种植户提供专业建议。
你需要返回JSON格式的结果，包含以下字段：
- advice: 建议列表，每条建议不超过100字，至少5条建议"""
    
    # 准备数据
    sentiment = sentiment_analysis.get('sentiment', 'neutral')
    sentiment_summary = sentiment_analysis.get('summary', '')
    hot_herbs = [h['name'] for h in news_summary.get('hot_herbs', [])[:5]]
    up_herbs = [h['name'] for h in price_analysis.get('up_herbs', [])[:5]]
    keyword_str = '、'.join([k['word'] for k in keywords[:10]])
    
    prompt = f"""请根据以下市场数据为中药材种植户提供专业建议：

市场情绪：{sentiment}（{sentiment_summary}）
热门药材：{', '.join(hot_herbs) if hot_herbs else '无'}
价格上涨品种：{', '.join(up_herbs) if up_herbs else '无'}
本周关键词：{keyword_str}

请提供至少5条针对种植户的专业建议，包括种植决策、品种选择、田间管理、采收准备、品质提升等方面。

请以JSON格式返回建议列表。"""
    
    ai_response = call_ai_api(prompt, system_prompt)
    
    if not ai_response:
        return ["市场行情平稳，建议按计划进行种植，关注后续市场变化。"]
    
    try:
        result = json.loads(ai_response)
        if 'advice' in result:
            return result['advice'][:8]
    except json.JSONDecodeError:
        pass
    
    return ["市场行情平稳，建议按计划进行种植，关注后续市场变化。"]


def generate_buyer_advice_with_ai(sentiment_analysis: Dict, news_summary: Dict, 
                                 price_analysis: Dict, keywords: List) -> List[str]:
    """使用AI为买家生成建议"""
    system_prompt = """你是一个专业的中药材采购专家。请根据提供的市场数据为中药材采购商/买家提供专业建议。
你需要返回JSON格式的结果，包含以下字段：
- advice: 建议列表，每条建议不超过100字，至少5条建议"""
    
    # 准备数据
    sentiment = sentiment_analysis.get('sentiment', 'neutral')
    sentiment_summary = sentiment_analysis.get('summary', '')
    up_herbs = [h['name'] for h in price_analysis.get('up_herbs', [])[:5]]
    down_herbs = [h['name'] for h in price_analysis.get('down_herbs', [])[:5]]
    keyword_str = '、'.join([k['word'] for k in keywords[:10]])
    
    prompt = f"""请根据以下市场数据为中药材采购商/买家提供专业建议：

市场情绪：{sentiment}（{sentiment_summary}）
价格上涨品种：{', '.join(up_herbs) if up_herbs else '无'}
价格下跌品种：{', '.join(down_herbs) if down_herbs else '无'}
本周关键词：{keyword_str}

请提供至少5条针对采购商/买家的专业建议，包括采购策略、价格关注、采购机会、质量把控、货源把握等方面。

请以JSON格式返回建议列表。"""
    
    ai_response = call_ai_api(prompt, system_prompt)
    
    if not ai_response:
        return ["市场走势平稳，可按正常计划进行采购，保持合理库存。"]
    
    try:
        result = json.loads(ai_response)
        if 'advice' in result:
            return result['advice'][:8]
    except json.JSONDecodeError:
        pass
    
    return ["市场走势平稳，可按正常计划进行采购，保持合理库存。"]


def generate_weekly_report():
    """生成完整的周报（AI版本）"""
    try:
        print("开始获取数据...")
        news_df = fetch_weekly_news()
        prices_df = fetch_weekly_prices()
        
        print(f"获取到新闻数据：{len(news_df)}条")
        print(f"获取到价格数据：{len(prices_df)}条")
        
        if news_df.empty:
            return {
                'success': False,
                'error': '暂无新闻数据'
            }
        
        print("开始AI分析...")
        
        # 使用AI分析数据
        print("1. 分析市场情绪...")
        sentiment_analysis = analyze_sentiment_with_ai(news_df)
        
        print("2. 总结资讯...")
        news_summary = summarize_news_with_ai(news_df)
        
        print("3. 分析价格趋势...")
        price_analysis = analyze_price_trends_with_ai(prices_df)
        
        print("4. 提取关键词...")
        keywords = extract_keywords_with_ai(news_df)
        
        print("5. 生成种植户建议...")
        grower_advice = generate_grower_advice_with_ai(sentiment_analysis, news_summary, price_analysis, keywords)
        
        print("6. 生成买家建议...")
        buyer_advice = generate_buyer_advice_with_ai(sentiment_analysis, news_summary, price_analysis, keywords)
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_range = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        
        # 组装周报
        report = {
            'title': '中药材市场周报',
            'date_range': date_range,
            'summary': {
                'overview': news_summary['summary'],
                'sentiment': sentiment_analysis['summary'],
                'price_trend': price_analysis['trend_summary']
            },
            'news_summary': news_summary,
            'sentiment_analysis': sentiment_analysis,
            'price_analysis': price_analysis,
            'keywords': keywords,
            'grower_advice': grower_advice,
            'buyer_advice': buyer_advice
        }
        
        print("周报生成完成！")
        
        return {
            'success': True,
            'report': report
        }
        
    except Exception as e:
        print(f"生成周报失败: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    print("正在生成中药材周报（AI版本）...")
    result = generate_weekly_report()
    
    if result['success']:
        print("\n" + "=" * 60)
        print("周报生成成功！")
        print("=" * 60 + "\n")
        
        report = result['report']
        print(f"标题：{report['title']}")
        print(f"日期范围：{report['date_range']}")
        print(f"\n本周概况：{report['summary']['overview']}")
        print(f"市场情绪：{report['summary']['sentiment']}")
        print(f"价格走势：{report['summary']['price_trend']}")
        print(f"\n热门药材：{[h['name'] for h in report['news_summary']['hot_herbs']]}")
        print(f"关键词：{[k['word'] for k in report['keywords']]}")
        print(f"\n种植户建议：{len(report['grower_advice'])}条")
        print(f"买家建议：{len(report['buyer_advice'])}条")
    else:
        print(f"周报生成失败：{result['error']}")
