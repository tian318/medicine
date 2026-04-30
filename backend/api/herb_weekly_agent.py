"""
中药材周报智能体
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
import jieba
import jieba.analyse
from collections import Counter

# 数据库连接配置
DB_CONFIG = {
    "dbname": "public",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}

# 中药材专业词典（用于jieba分词）
HERB_KEYWORDS = {
    '种植相关': ['种植', '播种', '育苗', '田间管理', '病虫害', '施肥', '灌溉', '采收', '产新', '产量', '种植面积'],
    '价格相关': ['价格', '行情', '涨价', '跌价', '上涨', '下跌', '稳定', '波动', '走势'],
    '市场相关': ['市场', '交易', '购销', '走货', '货源', '库存', '供应', '需求', '销量'],
    '天气相关': ['天气', '气候', '降雨', '干旱', '高温', '低温', '霜冻', '冰雹', '台风'],
    '政策相关': ['政策', '法规', '标准', '监管', '认证', 'GAP', 'GMP', '药典'],
    '品质相关': ['质量', '品质', '规格', '等级', '含量', '农残', '重金属', '真伪']
}

# 情感词典
POSITIVE_WORDS = ['上涨', '增长', '利好', '热销', '畅销', '活跃', '看好', '强劲', '旺盛', '紧缺', '供不应求']
NEGATIVE_WORDS = ['下跌', '跌价', '滞销', '低迷', '疲软', '过剩', '看淡', '疲软', '充足', '供过于求']


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
        
        # 计算一周前的日期
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


def preprocess_text(text):
    """文本预处理"""
    if not isinstance(text, str):
        return ""
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除URL
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    # 移除特殊字符
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)
    return text.strip()


def extract_keywords_tfidf(text, top_n=10):
    """使用TF-IDF提取关键词"""
    if not text:
        return []
    
    # 添加自定义词典
    for category, words in HERB_KEYWORDS.items():
        for word in words:
            jieba.add_word(word)
    
    keywords = jieba.analyse.extract_tags(text, topK=top_n, withWeight=True)
    return [{'word': word, 'weight': round(weight, 4)} for word, weight in keywords]


def analyze_sentiment(news_df):
    """分析市场情绪"""
    if news_df.empty:
        return {'sentiment': 'neutral', 'score': 0, 'summary': '暂无数据'}
    
    positive_count = 0
    negative_count = 0
    
    for _, row in news_df.iterrows():
        content = preprocess_text(row.get('content', ''))
        title = preprocess_text(row.get('title', ''))
        full_text = title + ' ' + content
        
        pos_score = sum(1 for word in POSITIVE_WORDS if word in full_text)
        neg_score = sum(1 for word in NEGATIVE_WORDS if word in full_text)
        
        if pos_score > neg_score:
            positive_count += 1
        elif neg_score > pos_score:
            negative_count += 1
    
    total = len(news_df)
    if total == 0:
        return {'sentiment': 'neutral', 'score': 0, 'summary': '暂无数据'}
    
    sentiment_score = (positive_count - negative_count) / total
    
    if sentiment_score > 0.1:
        sentiment = 'positive'
        summary = '市场情绪积极，整体看好'
    elif sentiment_score < -0.1:
        sentiment = 'negative'
        summary = '市场情绪消极，需谨慎对待'
    else:
        sentiment = 'neutral'
        summary = '市场情绪平稳，观望为主'
    
    return {
        'sentiment': sentiment,
        'score': round(sentiment_score, 3),
        'positive_ratio': round(positive_count / total, 3),
        'negative_ratio': round(negative_count / total, 3),
        'summary': summary
    }


def summarize_news(news_df):
    """总结一周资讯"""
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
    herb_counter = Counter()
    for _, row in news_df.iterrows():
        herb_name = row.get('herb_name', '')
        if herb_name and isinstance(herb_name, str):
            herbs = [h.strip() for h in herb_name.split(',') if h.strip()]
            herb_counter.update(herbs)
    
    hot_herbs = [{'name': name, 'count': count} 
                 for name, count in herb_counter.most_common(5)]
    
    # 活跃市场
    market_counter = Counter(news_df['market_name'].dropna())
    active_markets = [{'name': name, 'count': count} 
                      for name, count in market_counter.most_common(5)]
    
    # 提取关键事件（基于标题关键词）
    key_events = []
    event_keywords = ['产新', '涨价', '跌价', '天气', '政策', '库存', '需求']
    
    for _, row in news_df.iterrows():
        title = row.get('title', '')
        for keyword in event_keywords:
            if keyword in title and title not in [e['title'] for e in key_events]:
                key_events.append({
                    'title': title[:50] + '...' if len(title) > 50 else title,
                    'date': row.get('publish_time').strftime('%m-%d') if pd.notna(row.get('publish_time')) else '',
                    'type': keyword
                })
                break
        if len(key_events) >= 5:
            break
    
    # 生成总结文本
    summary_parts = [f"本周共发布{total_count}条中药材相关资讯。"]
    
    if hot_herbs:
        summary_parts.append(f"最受关注的品种为{', '.join([h['name'] for h in hot_herbs[:3]])}。")
    
    if active_markets:
        summary_parts.append(f"主要资讯来源市场包括{', '.join([m['name'] for m in active_markets[:3]])}。")
    
    return {
        'total_count': total_count,
        'summary': ''.join(summary_parts),
        'key_events': key_events,
        'hot_herbs': hot_herbs,
        'active_markets': active_markets
    }


def analyze_price_trends(prices_df):
    """分析价格趋势"""
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
    
    # 按药材分组分析
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
    
    # 生成趋势总结
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


def generate_grower_advice(sentiment_analysis, news_summary, price_analysis, keywords):
    """为种植户生成建议"""
    advice = []
    
    # 基于市场情绪的建议
    sentiment = sentiment_analysis.get('sentiment', 'neutral')
    if sentiment == 'positive':
        advice.append("【种植决策】市场行情向好，可关注价格上涨品种的种植机会，适当增加种植面积。")
    elif sentiment == 'negative':
        advice.append("【种植决策】市场行情偏弱，建议谨慎扩种，优先保障现有药材的田间管理质量。")
    else:
        advice.append("【种植决策】市场走势平稳，建议按计划进行种植，关注后续市场变化。")
    
    # 基于热门药材的建议
    hot_herbs = news_summary.get('hot_herbs', [])
    if hot_herbs:
        hot_names = [h['name'] for h in hot_herbs[:3]]
        advice.append(f"【品种选择】近期{', '.join(hot_names)}等品种关注度较高，如有种植条件可适当关注。")
    
    # 基于价格趋势的建议
    up_herbs = price_analysis.get('up_herbs', [])
    if up_herbs:
        up_names = [h['name'] for h in up_herbs[:3]]
        advice.append(f"【价格关注】{', '.join(up_names)}等品种价格上涨，如已种植可把握销售时机。")
    
    # 基于关键词的建议
    keyword_str = ' '.join([k['word'] for k in keywords[:5]])
    
    if '天气' in keyword_str or '气候' in keyword_str:
        advice.append("【田间管理】近期天气变化可能影响药材生长，请加强田间管理，做好防灾准备。")
    
    if '病虫害' in keyword_str:
        advice.append("【病虫害防治】注意防范病虫害，及时采取防治措施，保证药材品质。")
    
    if '产新' in keyword_str:
        advice.append("【采收准备】部分药材即将进入产新期，请提前做好采收和加工准备。")
    
    if '质量' in keyword_str or '品质' in keyword_str:
        advice.append("【品质提升】市场对药材质量要求提高，建议加强质量管理，提升产品竞争力。")
    
    # 通用建议
    advice.append("【长期建议】持续关注市场动态，合理安排种植结构，避免盲目跟风种植。")
    
    return advice


def generate_buyer_advice(sentiment_analysis, news_summary, price_analysis, keywords):
    """为买家生成建议"""
    advice = []
    
    # 基于市场情绪的建议
    sentiment = sentiment_analysis.get('sentiment', 'neutral')
    if sentiment == 'positive':
        advice.append("【采购策略】市场行情上涨，如有急需可适当备货，但需控制库存成本。")
    elif sentiment == 'negative':
        advice.append("【采购策略】市场行情下行，建议按需采购，避免大量囤货，等待更好的采购时机。")
    else:
        advice.append("【采购策略】市场走势平稳，可按正常计划进行采购，保持合理库存。")
    
    # 基于价格上涨品种的建议
    up_herbs = price_analysis.get('up_herbs', [])
    if up_herbs:
        up_names = [h['name'] for h in up_herbs[:3]]
        advice.append(f"【价格关注】{', '.join(up_names)}等品种价格上涨明显，如有库存可适时出货。")
    
    # 基于价格下跌品种的建议
    down_herbs = price_analysis.get('down_herbs', [])
    if down_herbs:
        down_names = [h['name'] for h in down_herbs[:3]]
        advice.append(f"【采购机会】{', '.join(down_names)}等品种价格下跌，如有需求可适当增加采购。")
    
    # 基于关键词的建议
    keyword_str = ' '.join([k['word'] for k in keywords[:5]])
    
    if '库存' in keyword_str or '货源' in keyword_str:
        advice.append("【货源把握】市场货源情况变化，建议密切关注供应情况，及时调整采购计划。")
    
    if '质量' in keyword_str or '品质' in keyword_str:
        advice.append("【质量把控】采购时重点关注药材质量，选择信誉良好的供应商，确保药材品质。")
    
    if '政策' in keyword_str:
        advice.append("【政策关注】近期有相关政策出台，请关注政策对市场和价格的影响。")
    
    if '天气' in keyword_str:
        advice.append("【供应预判】天气因素可能影响后续供应，建议提前规划采购，确保货源稳定。")
    
    # 通用建议
    advice.append("【长期建议】建立稳定的供应渠道，关注产地动态，合理安排采购节奏。")
    
    return advice


def generate_weekly_report():
    """生成完整的周报"""
    try:
        # 获取数据
        news_df = fetch_weekly_news()
        prices_df = fetch_weekly_prices()
        
        # 分析数据
        sentiment_analysis = analyze_sentiment(news_df)
        news_summary = summarize_news(news_df)
        price_analysis = analyze_price_trends(prices_df)
        
        # 提取关键词
        all_text = ' '.join(news_df['content'].fillna('').astype(str)) + ' ' + \
                   ' '.join(news_df['title'].fillna('').astype(str))
        keywords = extract_keywords_tfidf(preprocess_text(all_text), top_n=15)
        
        # 生成建议
        grower_advice = generate_grower_advice(sentiment_analysis, news_summary, price_analysis, keywords)
        buyer_advice = generate_buyer_advice(sentiment_analysis, news_summary, price_analysis, keywords)
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_range = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        
        # 组装周报
        report = {
            'title': f'中药材市场周报 ({date_range})',
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


def format_report_text(report):
    """将周报格式化为文本"""
    lines = []
    
    lines.append("=" * 60)
    lines.append(report['title'])
    lines.append("=" * 60)
    lines.append("")
    
    # 总体概况
    lines.append("【本周概况】")
    lines.append(report['summary']['overview'])
    lines.append(report['summary']['sentiment'])
    lines.append(f"价格走势：{report['summary']['price_trend']}")
    lines.append("")
    
    # 热门药材
    hot_herbs = report['news_summary']['hot_herbs']
    if hot_herbs:
        lines.append("【热门药材】")
        for herb in hot_herbs:
            lines.append(f"  • {herb['name']}：{herb['count']}条相关资讯")
        lines.append("")
    
    # 价格涨跌
    price_analysis = report['price_analysis']
    if price_analysis['up_herbs']:
        lines.append("【价格上涨品种】")
        for herb in price_analysis['up_herbs']:
            lines.append(f"  • {herb['name']}：{herb['price']}元/公斤")
        lines.append("")
    
    if price_analysis['down_herbs']:
        lines.append("【价格下跌品种】")
        for herb in price_analysis['down_herbs']:
            lines.append(f"  • {herb['name']}：{herb['price']}元/公斤")
        lines.append("")
    
    # 关键事件
    key_events = report['news_summary']['key_events']
    if key_events:
        lines.append("【本周关键事件】")
        for event in key_events:
            lines.append(f"  • [{event['date']}] {event['title']}")
        lines.append("")
    
    # 种植户建议
    lines.append("【对种植户的建议】")
    for advice in report['grower_advice']:
        lines.append(f"  {advice}")
    lines.append("")
    
    # 买家建议
    lines.append("【对采购商/买家的建议】")
    for advice in report['buyer_advice']:
        lines.append(f"  {advice}")
    lines.append("")
    
    # 关键词
    keywords = report['keywords']
    if keywords:
        lines.append("【本周关键词】")
        keyword_str = '、'.join([k['word'] for k in keywords[:10]])
        lines.append(f"  {keyword_str}")
    
    lines.append("")
    lines.append("=" * 60)
    lines.append("报告生成时间：" + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    lines.append("=" * 60)
    
    return '\n'.join(lines)


if __name__ == "__main__":
    # 测试周报生成
    print("正在生成中药材周报...")
    result = generate_weekly_report()
    
    if result['success']:
        report = result['report']
        print("\n" + "=" * 60)
        print("周报生成成功！")
        print("=" * 60 + "\n")
        
        # 打印格式化后的周报
        formatted_report = format_report_text(report)
        print(formatted_report)
        
        # 保存到文件
        filename = f"中药材周报_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(formatted_report)
        print(f"\n周报已保存到文件：{filename}")
    else:
        print(f"周报生成失败：{result['error']}")
