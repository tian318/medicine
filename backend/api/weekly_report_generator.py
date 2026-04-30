import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json
import re
import jieba

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
    import time
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
                print(f"数据库连接失败，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
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

        # 查询一周的新闻
        query = """
        SELECT 
            id, title, content, market_name, publish_time, herb_name
        FROM news_info1
        WHERE publish_time BETWEEN %s AND %s
        ORDER BY publish_time
        """

        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()

        df = pd.DataFrame(rows)

        if df.empty:
            print("查询结果为空")
            return pd.DataFrame()

        # 确保日期是日期时间类型
        if 'publish_time' in df.columns:
            df['publish_time'] = pd.to_datetime(df['publish_time'])

        return df

    except Exception as e:
        print(f"获取新闻数据时出错: {e}")
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

        # 计算一周前的日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # 查询一周的价格数据
        query = """
        SELECT 
            herb_name, 
            specification, 
            location, 
            price, 
            trend, 
            week_change,
            recorded_at
        FROM herb_prices
        WHERE recorded_at BETWEEN %s AND %s
        ORDER BY herb_name, recorded_at DESC
        """

        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()

        df = pd.DataFrame(rows)

        if df.empty:
            print("查询价格结果为空")
            return pd.DataFrame()

        # 确保日期是日期时间类型
        if 'recorded_at' in df.columns:
            df['recorded_at'] = pd.to_datetime(df['recorded_at'])

        return df

    except Exception as e:
        print(f"获取价格数据时出错: {e}")
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

def preprocess_text(text):
    """预处理文本"""
    if not isinstance(text, str):
        return ""

    # 移除HTML标签
    text = re.sub(r'<.*?>', '', text)

    # 移除URL
    text = re.sub(r'http\S+', '', text)

    # 移除标点符号和特殊字符
    text = re.sub(r'[^\w\s]', '', text)

    # 分词
    words = jieba.cut(text)

    # 移除停用词
    stopwords = load_stopwords()
    words = [word for word in words if word not in stopwords and len(word) > 1]

    return ' '.join(words)

def load_stopwords():
    """加载停用词"""
    # 这里可以加载自定义的停用词表，或者使用默认的
    stopwords = {'的', '了', '和', '是', '在', '我', '有', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到',
                 '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    return stopwords

def extract_keywords(text, top_n=20):
    """提取文本中的关键词"""
    if not text:
        return []

    # 使用简单的词频统计
    words = text.split()
    word_counts = {}
    for word in words:
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1

    # 按词频排序
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

    # 返回前top_n个关键词
    return [{'word': word, 'count': count} for word, count in sorted_words[:top_n]]

def analyze_market_sentiment(news_df):
    """分析市场情绪"""
    if news_df.empty:
        return {
            'avg_sentiment': 0,
            'sentiment_counts': {'positive': 0, 'neutral': 0, 'negative': 0},
            'dominant_sentiment': 'neutral'
        }

    # 定义中药材市场特定的积极和消极词汇
    positive_words = {
        '充足', '稳定', '上涨', '增长', '利好', '看好', '机会', '优质', '提高', '增加',
        '热销', '畅销', '供不应求', '走俏', '抢手', '活跃', '旺销', '优良', '高产',
        '丰收', '优势', '精品', '美丽', '专业', '干净', '无异物', '无杂质'
    }

    negative_words = {
        '下跌', '减少', '利空', '看空', '风险', '低迷', '下降', '减产', '滞销',
        '库存积压', '供过于求', '疲软', '萎靡', '不景气', '走弱', '跌价', '滑坡',
        '亏损', '减产', '歉收', '劣质', '杂质', '异物', '芦头'
    }

    # 计算情感分数
    sentiment_scores = []
    for idx, row in news_df.iterrows():
        text = row['content'] if isinstance(row['content'], str) else ''
        title = row['title'] if isinstance(row['title'], str) else ''

        # 结合标题和内容进行分析
        full_text = title + ' ' + text
        words = full_text.split()

        # 基础分数计算
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        # 综合评分
        base_score = 0
        if positive_count > negative_count:
            base_score = min(0.5, 0.1 + (positive_count - negative_count) * 0.05)
        elif positive_count < negative_count:
            base_score = max(-0.5, -0.1 - (negative_count - positive_count) * 0.05)

        sentiment_scores.append(base_score)

    # 计算平均情感分数
    avg_sentiment = np.mean(sentiment_scores)

    # 统计情感分布
    sentiment_counts = {
        'positive': len([s for s in sentiment_scores if s > 0.1]),
        'neutral': len([s for s in sentiment_scores if -0.1 <= s <= 0.1]),
        'negative': len([s for s in sentiment_scores if s < -0.1])
    }

    # 确定主导情绪
    dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)

    return {
        'avg_sentiment': float(avg_sentiment),
        'sentiment_counts': sentiment_counts,
        'dominant_sentiment': dominant_sentiment
    }

def extract_hot_herbs(news_df, top_n=10):
    """提取热门药材"""
    if news_df.empty:
        return []

    # 统计药材出现次数
    herb_counts = {}
    for idx, row in news_df.iterrows():
        herb_name = row['herb_name']
        if isinstance(herb_name, str) and herb_name:
            # 处理可能的多个药材名称
            herbs = herb_name.split(',')
            for herb in herbs:
                herb = herb.strip()
                if herb:
                    if herb in herb_counts:
                        herb_counts[herb] += 1
                    else:
                        herb_counts[herb] = 1

    # 按出现次数排序
    sorted_herbs = sorted(herb_counts.items(), key=lambda x: x[1], reverse=True)

    # 返回前top_n个热门药材
    return [{'name': herb, 'count': count} for herb, count in sorted_herbs[:top_n]]

def generate_weekly_report():
    """生成中药材周报"""
    try:
        # 获取一周的新闻
        news_df = fetch_weekly_news()

        # 获取一周的价格数据
        prices_df = fetch_weekly_prices()

        if news_df.empty and prices_df.empty:
            return {
                'success': False,
                'error': '没有找到一周内的数据'
            }

        # 生成周报内容
        report = generate_new_format_report(news_df, prices_df)

        return {
            'success': True,
            'report': report
        }

    except Exception as e:
        print(f"生成周报失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_report_content(news_df, keywords, sentiment_analysis, hot_herbs):
    """生成周报内容"""
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    date_range = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"

    # 生成市场概览
    market_overview = generate_market_overview_simple(news_df, sentiment_analysis)

    # 生成价格走势分析
    price_trends = generate_price_trends_simple(news_df)

    # 生成热门药材分析
    hot_herbs_analysis = generate_hot_herbs_analysis_simple(hot_herbs)

    # 生成政策影响分析
    policy_analysis = generate_policy_analysis_simple(news_df)

    # 生成种植户建议
    grower_advice = generate_grower_advice(sentiment_analysis, hot_herbs)

    # 生成买家建议
    buyer_advice = generate_buyer_advice(sentiment_analysis, hot_herbs)

    return {
        'title': f'中药材市场周报 ({date_range})',
        'date_range': date_range,
        'market_overview': market_overview,
        'price_trends': price_trends,
        'hot_herbs': hot_herbs_analysis,
        'policy_analysis': policy_analysis,
        'grower_advice': grower_advice,
        'buyer_advice': buyer_advice
    }

def generate_market_overview(news_df, sentiment_analysis):
    """生成市场概览"""
    news_count = len(news_df)
    dominant_sentiment = sentiment_analysis['dominant_sentiment']
    sentiment_map = {
        'positive': '积极',
        'neutral': '中性',
        'negative': '消极'
    }

    overview = f"本周共收录中药材相关新闻 {news_count} 条，市场整体情绪偏{sentiment_map[dominant_sentiment]}。"
    
    # 分析新闻来源分布
    market_counts = news_df['market_name'].value_counts()
    if not market_counts.empty:
        top_markets = market_counts.head(3)
        overview += f"新闻主要来源于 {', '.join(top_markets.index.tolist())} 等市场。"
    
    return overview

def generate_price_trends(news_df):
    """生成价格走势分析"""
    # 从新闻中提取价格相关信息
    price_up_keywords = ['上涨', '涨价', '增长', '提高', '高于']
    price_down_keywords = ['下跌', '跌价', '降低', '减少', '低于']
    price_stable_keywords = ['稳定', '平稳', '不变']

    price_up_count = 0
    price_down_count = 0
    price_stable_count = 0

    for idx, row in news_df.iterrows():
        content = row['content'] if isinstance(row['content'], str) else ''
        title = row['title'] if isinstance(row['title'], str) else ''
        full_text = title + ' ' + content

        if any(keyword in full_text for keyword in price_up_keywords):
            price_up_count += 1
        elif any(keyword in full_text for keyword in price_down_keywords):
            price_down_count += 1
        elif any(keyword in full_text for keyword in price_stable_keywords):
            price_stable_count += 1

    trends = []
    if price_up_count > 0:
        trends.append(f"上涨 {price_up_count} 次")
    if price_down_count > 0:
        trends.append(f"下跌 {price_down_count} 次")
    if price_stable_count > 0:
        trends.append(f"稳定 {price_stable_count} 次")

    if trends:
        return f"本周价格走势方面，{'、'.join(trends)}。"
    else:
        return "本周未获取到明确的价格走势信息。"

def generate_hot_herbs_analysis(hot_herbs):
    """生成热门药材分析"""
    if not hot_herbs:
        return []

    # 这里简化处理，实际项目中可以结合价格数据计算涨跌幅
    return [{'name': herb['name'], 'change': round(np.random.uniform(-10, 20), 2)} for herb in hot_herbs]

def generate_market_sentiment_analysis(sentiment_analysis):
    """生成市场情绪分析"""
    avg_sentiment = sentiment_analysis['avg_sentiment']
    sentiment_counts = sentiment_analysis['sentiment_counts']

    if avg_sentiment > 0.1:
        sentiment_desc = "积极"
    elif avg_sentiment < -0.1:
        sentiment_desc = "消极"
    else:
        sentiment_desc = "中性"

    return f"本周市场情绪{sentiment_desc}，其中积极新闻 {sentiment_counts['positive']} 条，中性新闻 {sentiment_counts['neutral']} 条，消极新闻 {sentiment_counts['negative']} 条。"

def generate_predictions(sentiment_analysis, hot_herbs):
    """生成预测与建议"""
    avg_sentiment = sentiment_analysis['avg_sentiment']
    dominant_sentiment = sentiment_analysis['dominant_sentiment']

    predictions = []

    if dominant_sentiment == 'positive':
        predictions.append("预计下周市场整体将保持活跃，价格可能继续上涨。")
    elif dominant_sentiment == 'negative':
        predictions.append("预计下周市场可能较为低迷，价格可能继续下跌。")
    else:
        predictions.append("预计下周市场将保持稳定，价格波动不大。")

    if hot_herbs:
        top_herbs = [herb['name'] for herb in hot_herbs[:3]]
        predictions.append(f"建议关注 {', '.join(top_herbs)} 等热门药材的市场动态。")

    return ' '.join(predictions)


def generate_regional_analysis(news_df):
    """生成区域市场分析"""
    if news_df.empty:
        return "本周各区域市场无明显数据。"

    # 分析各区域市场的新闻数量
    regional_counts = news_df['market_name'].value_counts()
    if regional_counts.empty:
        return "本周各区域市场无明显数据。"

    # 提取前5个主要区域
    top_regions = regional_counts.head(5)
    region_analysis = "本周各区域市场活跃度分析："
    
    for region, count in top_regions.items():
        region_analysis += f"\n- {region}：{count}条新闻，活跃度较高"

    # 分析区域市场的情绪倾向
    region_sentiment = {}
    for idx, row in news_df.iterrows():
        market = row['market_name']
        if pd.isna(market):
            continue
        
        # 简单的情绪分析
        content = row['content'] if isinstance(row['content'], str) else ''
        title = row['title'] if isinstance(row['title'], str) else ''
        full_text = title + ' ' + content
        
        positive_words = {'上涨', '增长', '利好', '热销', '畅销', '活跃'}
        negative_words = {'下跌', '减少', '滞销', '低迷', '疲软'}
        
        positive_count = sum(1 for word in positive_words if word in full_text)
        negative_count = sum(1 for word in negative_words if word in full_text)
        
        if market not in region_sentiment:
            region_sentiment[market] = {'positive': 0, 'negative': 0, 'total': 0}
        
        region_sentiment[market]['positive'] += positive_count
        region_sentiment[market]['negative'] += negative_count
        region_sentiment[market]['total'] += 1

    # 分析各区域的情绪倾向
    region_analysis += "\n\n区域市场情绪倾向："
    for region, sentiment in region_sentiment.items():
        if sentiment['total'] > 0:
            net_sentiment = sentiment['positive'] - sentiment['negative']
            if net_sentiment > 0:
                region_analysis += f"\n- {region}：情绪偏向积极"
            elif net_sentiment < 0:
                region_analysis += f"\n- {region}：情绪偏向消极"
            else:
                region_analysis += f"\n- {region}：情绪相对中性"

    return region_analysis


def generate_category_analysis(news_df):
    """生成品种分类分析"""
    if news_df.empty:
        return "本周各品种分类无明显数据。"

    # 简单的药材分类
    herb_categories = {
        '根茎类': ['人参', '当归', '黄芪', '党参', '白术', '白芍', '甘草', '川芎', '地黄', '麦冬'],
        '果实种子类': ['枸杞子', '五味子', '连翘', '决明子', '菟丝子', '女贞子', '车前子', '牛蒡子', '覆盆子'],
        '花叶类': ['金银花', '菊花', '红花', '桑叶', '薄荷', '紫苏叶', '艾叶', '荷叶', '蒲公英'],
        '全草类': ['麻黄', '薄荷', '荆芥', '藿香', '佩兰', '益母草', '泽兰', '半边莲', '半枝莲'],
        '动物类': ['鹿茸', '鹿角', '龟甲', '鳖甲', '蝉蜕', '地龙', '全蝎', '蜈蚣', '水蛭'],
        '矿物类': ['石膏', '滑石', '雄黄', '朱砂', '磁石', '赭石', '炉甘石', '芒硝', '明矾']
    }

    # 统计各分类的新闻数量
    category_counts = {category: 0 for category in herb_categories.keys()}
    for idx, row in news_df.iterrows():
        herb_name = row['herb_name']
        if isinstance(herb_name, str) and herb_name:
            herbs = herb_name.split(',')
            for herb in herbs:
                herb = herb.strip()
                for category, herbs_list in herb_categories.items():
                    if herb in herbs_list:
                        category_counts[category] += 1
                        break

    # 生成分类分析
    category_analysis = "本周各品种分类关注度分析："
    total_count = sum(category_counts.values())
    
    if total_count > 0:
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories:
            if count > 0:
                percentage = (count / total_count) * 100
                category_analysis += f"\n- {category}：{count}条新闻，占比{percentage:.1f}%"
    else:
        category_analysis = "本周各品种分类无明显数据。"

    return category_analysis


def generate_policy_analysis(news_df):
    """生成政策影响分析"""
    if news_df.empty:
        return "本周无明显政策影响。"

    # 政策相关关键词
    policy_keywords = ['政策', '法规', '标准', '规范', '监管', '审批', '备案', '质量', '安全', '检验']
    policy_news = []

    for idx, row in news_df.iterrows():
        content = row['content'] if isinstance(row['content'], str) else ''
        title = row['title'] if isinstance(row['title'], str) else ''
        full_text = title + ' ' + content
        
        if any(keyword in full_text for keyword in policy_keywords):
            policy_news.append({
                'title': title,
                'content': content[:100] + '...' if len(content) > 100 else content
            })

    if not policy_news:
        return "本周无明显政策影响。"

    policy_analysis = "本周政策影响分析："
    for i, news in enumerate(policy_news[:3]):  # 只取前3条政策相关新闻
        policy_analysis += f"\n{i+1}. {news['title']}"
        policy_analysis += f"\n   {news['content']}"

    if len(policy_news) > 3:
        policy_analysis += f"\n... 等共{len(policy_news)}条政策相关新闻"

    return policy_analysis


def generate_market_overview_simple(news_df, sentiment_analysis):
    """生成简化版市场概览"""
    news_count = len(news_df)
    dominant_sentiment = sentiment_analysis['dominant_sentiment']
    sentiment_map = {
        'positive': '看好',
        'neutral': '稳定',
        'negative': '一般'
    }
    
    return f"本周市场共收录 {news_count} 条新闻，整体行情{sentiment_map[dominant_sentiment]}。"


def generate_price_trends_simple(news_df):
    """生成简化版价格走势分析"""
    price_up_keywords = ['上涨', '涨价', '增长', '提高', '高于']
    price_down_keywords = ['下跌', '跌价', '降低', '减少', '低于']
    
    price_up_count = 0
    price_down_count = 0
    
    for idx, row in news_df.iterrows():
        content = row['content'] if isinstance(row['content'], str) else ''
        title = row['title'] if isinstance(row['title'], str) else ''
        full_text = title + ' ' + content
        
        if any(keyword in full_text for keyword in price_up_keywords):
            price_up_count += 1
        elif any(keyword in full_text for keyword in price_down_keywords):
            price_down_count += 1
    
    if price_up_count > price_down_count:
        return "本周价格整体呈上涨趋势。"
    elif price_up_count < price_down_count:
        return "本周价格整体呈下跌趋势。"
    else:
        return "本周价格整体保持稳定。"


def generate_hot_herbs_analysis_simple(hot_herbs):
    """生成简化版热门药材分析"""
    if not hot_herbs:
        return []
    
    return hot_herbs[:5]


def generate_policy_analysis_simple(news_df):
    """生成简化版政策影响分析"""
    policy_keywords = ['政策', '法规', '标准', '规范', '监管']
    
    has_policy = False
    for idx, row in news_df.iterrows():
        content = row['content'] if isinstance(row['content'], str) else ''
        title = row['title'] if isinstance(row['title'], str) else ''
        full_text = title + ' ' + content
        
        if any(keyword in full_text for keyword in policy_keywords):
            has_policy = True
            break
    
    if has_policy:
        return "本周有相关政策信息，请关注政策动态对市场的影响。"
    else:
        return "本周无重大政策变化。"


def generate_grower_advice(sentiment_analysis, hot_herbs):
    """生成种植户建议"""
    advice = []
    dominant_sentiment = sentiment_analysis['dominant_sentiment']
    
    if dominant_sentiment == 'positive':
        advice.append("市场行情看好，可适当扩大种植规模。")
    elif dominant_sentiment == 'negative':
        advice.append("市场行情一般，建议控制种植规模，做好风险防范。")
    else:
        advice.append("市场保持稳定，可按原计划安排种植。")
    
    if hot_herbs:
        top_herbs = [herb['name'] for herb in hot_herbs[:3]]
        advice.append(f"建议关注 {', '.join(top_herbs)} 等热门品种的种植机会。")
    
    advice.append("注意做好田间管理，保证药材质量。")
    
    return ' '.join(advice)


def generate_buyer_advice(sentiment_analysis, hot_herbs):
    """生成买家建议"""
    advice = []
    dominant_sentiment = sentiment_analysis['dominant_sentiment']
    
    if dominant_sentiment == 'positive':
        advice.append("价格呈上涨趋势，可考虑适当备货。")
    elif dominant_sentiment == 'negative':
        advice.append("价格呈下跌趋势，建议按需采购，避免囤货。")
    else:
        advice.append("价格保持稳定，可按正常采购计划执行。")
    
    if hot_herbs:
        top_herbs = [herb['name'] for herb in hot_herbs[:3]]
        advice.append(f"热门品种 {', '.join(top_herbs)} 可重点关注。")
    
    advice.append("采购时注意鉴别药材质量，确保品质。")
    
    return ' '.join(advice)


def generate_new_format_report(news_df, prices_df):
    """生成新格式的周报"""
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    date_range = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
    
    # 分析市场整体行情
    market_overview = analyze_market_overview(news_df, prices_df)
    
    # 提取重点品种价格走势
    key_herbs_trend = analyze_key_herbs_trend(prices_df)
    
    # 分析关键资讯
    key_news = analyze_key_news(news_df)
    
    # 数据分析总结
    data_analysis = analyze_data_summary(news_df, prices_df)
    
    # 生成种植户建议
    grower_advice = generate_grower_advice_new(news_df, prices_df)
    
    # 生成买家建议
    buyer_advice = generate_buyer_advice_new(news_df, prices_df)
    
    # 下周预判
    next_week_prediction = predict_next_week(news_df, prices_df)
    
    return {
        'title': f'中药材市场周报 ({date_range})',
        'date_range': date_range,
        'market_overview': market_overview,
        'key_herbs_trend': key_herbs_trend,
        'key_news': key_news,
        'data_analysis': data_analysis,
        'grower_advice': grower_advice,
        'buyer_advice': buyer_advice,
        'next_week_prediction': next_week_prediction
    }


def analyze_market_overview(news_df, prices_df):
    """分析市场整体概况"""
    herb_count = 0
    if not prices_df.empty:
        herb_count = prices_df['herb_name'].nunique()
    
    # 分析整体市场行情
    market_sentiment = '平稳'
    if not news_df.empty:
        sentiment = analyze_market_sentiment(news_df)
        if sentiment['dominant_sentiment'] == 'positive':
            market_sentiment = '偏强'
        elif sentiment['dominant_sentiment'] == 'negative':
            market_sentiment = '偏弱'
    
    # 提取主要影响因素
    main_factors = extract_main_factors(news_df)
    
    return {
        'herb_count': herb_count,
        'market_sentiment': market_sentiment,
        'main_factors': main_factors
    }


def extract_main_factors(news_df):
    """提取主要影响因素"""
    if news_df.empty:
        return ['无明显影响因素']
    
    # 简单的关键词提取
    all_content = ' '.join(news_df['content'].fillna(''))
    keywords = extract_keywords(all_content, top_n=10)
    
    factors = [kw['word'] for kw in keywords[:5]]
    return factors if factors else ['无明显影响因素']


def analyze_key_herbs_trend(prices_df):
    """分析重点品种价格走势"""
    if prices_df.empty:
        return []
    
    # 获取最新的价格数据
    latest_prices = prices_df.groupby('herb_name').first().reset_index()
    latest_prices = latest_prices.sort_values('recorded_at', ascending=False).head(5)
    
    trends = []
    for idx, row in latest_prices.iterrows():
        herb_name = row['herb_name']
        price = row['price']
        week_change = row.get('week_change', '持平')
        
        # 解析涨跌情况
        trend = '持平'
        if week_change and '上涨' in week_change:
            trend = '上涨'
        elif week_change and '下跌' in week_change:
            trend = '下跌'
        
        trends.append({
            'herb_name': herb_name,
            'price': float(price),
            'trend': trend
        })
    
    return trends


def analyze_key_news(news_df):
    """分析关键资讯"""
    if news_df.empty:
        return {
            'production': '暂无产地动态',
            'weather': '暂无天气影响',
            'inventory': '暂无库存与货源信息',
            'policy': '暂无政策/市场消息'
        }
    
    # 分类新闻
    production_news = []
    weather_news = []
    inventory_news = []
    policy_news = []
    
    for idx, row in news_df.iterrows():
        content = row['content'] if isinstance(row['content'], str) else ''
        title = row['title'] if isinstance(row['title'], str) else ''
        full_text = title + ' ' + content
        
        # 产地动态
        if any(keyword in full_text for keyword in ['产地', '产新', '种植', '采收']):
            production_news.append(title)
        
        # 天气影响
        if any(keyword in full_text for keyword in ['天气', '降雨', '干旱', '高温', '霜冻']):
            weather_news.append(title)
        
        # 库存与货源
        if any(keyword in full_text for keyword in ['库存', '货源', '走货', '购销']):
            inventory_news.append(title)
        
        # 政策消息
        if any(keyword in full_text for keyword in ['政策', '法规', '标准', '监管']):
            policy_news.append(title)
    
    return {
        'production': production_news[0] if production_news else '暂无产地动态',
        'weather': weather_news[0] if weather_news else '暂无天气影响',
        'inventory': inventory_news[0] if inventory_news else '暂无库存与货源信息',
        'policy': policy_news[0] if policy_news else '暂无政策/市场消息'
    }


def analyze_data_summary(news_df, prices_df):
    """数据分析总结"""
    # 上涨原因
    up_reasons = []
    # 下跌原因
    down_reasons = []
    # 供需格局
    supply_demand = '供需基本平衡'
    
    if not news_df.empty:
        # 分析上涨原因
        up_keywords = ['需求增加', '库存减少', '产新推迟', '质量提升']
        for idx, row in news_df.iterrows():
            content = row['content'] if isinstance(row['content'], str) else ''
            title = row['title'] if isinstance(row['title'], str) else ''
            full_text = title + ' ' + content
            
            for keyword in up_keywords:
                if keyword in full_text and keyword not in up_reasons:
                    up_reasons.append(keyword)
        
        # 分析下跌原因
        down_keywords = ['需求疲软', '库存充足', '产新上市', '质量下降']
        for idx, row in news_df.iterrows():
            content = row['content'] if isinstance(row['content'], str) else ''
            title = row['title'] if isinstance(row['title'], str) else ''
            full_text = title + ' ' + content
            
            for keyword in down_keywords:
                if keyword in full_text and keyword not in down_reasons:
                    down_reasons.append(keyword)
    
    # 分析供需格局
    if not news_df.empty:
        supply_keywords = ['供不应求', '货源紧张', '需求旺盛']
        demand_keywords = ['供过于求', '货源充足', '需求疲软']
        
        supply_count = 0
        demand_count = 0
        
        for idx, row in news_df.iterrows():
            content = row['content'] if isinstance(row['content'], str) else ''
            title = row['title'] if isinstance(row['title'], str) else ''
            full_text = title + ' ' + content
            
            if any(keyword in full_text for keyword in supply_keywords):
                supply_count += 1
            if any(keyword in full_text for keyword in demand_keywords):
                demand_count += 1
        
        if supply_count > demand_count:
            supply_demand = '供应偏紧'
        elif demand_count > supply_count:
            supply_demand = '供应偏松'
    
    return {
        'up_reasons': up_reasons if up_reasons else ['无明显上涨原因'],
        'down_reasons': down_reasons if down_reasons else ['无明显下跌原因'],
        'supply_demand': supply_demand
    }


def generate_grower_advice_new(news_df, prices_df):
    """生成种植户建议"""
    advice = []
    
    if not news_df.empty:
        sentiment = analyze_market_sentiment(news_df)
        if sentiment['dominant_sentiment'] == 'positive':
            advice.append("市场行情看好，可适当扩大种植规模")
        elif sentiment['dominant_sentiment'] == 'negative':
            advice.append("市场行情一般，建议控制种植规模，做好风险防范")
        else:
            advice.append("市场保持稳定，可按原计划安排种植")
    
    if not prices_df.empty:
        # 获取价格上涨的品种
        up_herbs = prices_df[prices_df['week_change'].str.contains('上涨', na=False)]
        if not up_herbs.empty:
            top_up_herbs = up_herbs['herb_name'].unique()[:2]
            advice.append(f"建议关注 {', '.join(top_up_herbs)} 等价格上涨品种的种植机会")
    
    advice.append("注意做好田间管理，保证药材质量")
    
    return advice if advice else ['保持现有种植规模，关注市场动态']


def generate_buyer_advice_new(news_df, prices_df):
    """生成买家建议"""
    advice = []
    
    if not news_df.empty:
        sentiment = analyze_market_sentiment(news_df)
        if sentiment['dominant_sentiment'] == 'positive':
            advice.append("价格呈上涨趋势，可考虑适当备货")
        elif sentiment['dominant_sentiment'] == 'negative':
            advice.append("价格呈下跌趋势，建议按需采购，避免囤货")
        else:
            advice.append("价格保持稳定，可按正常采购计划执行")
    
    if not prices_df.empty:
        # 获取价格下跌的品种
        down_herbs = prices_df[prices_df['week_change'].str.contains('下跌', na=False)]
        if not down_herbs.empty:
            top_down_herbs = down_herbs['herb_name'].unique()[:2]
            advice.append(f"价格下跌品种 {', '.join(top_down_herbs)} 可重点关注")
    
    advice.append("采购时注意鉴别药材质量，确保品质")
    
    return advice if advice else ['按需采购，关注市场动态']


def predict_next_week(news_df, prices_df):
    """下周预判"""
    prediction = ""
    focus_herbs = []
    
    if not news_df.empty:
        sentiment = analyze_market_sentiment(news_df)
        if sentiment['dominant_sentiment'] == 'positive':
            prediction = "预计整体行情偏强"
        elif sentiment['dominant_sentiment'] == 'negative':
            prediction = "预计整体行情偏弱"
        else:
            prediction = "预计整体行情平稳"
    
    if not prices_df.empty:
        # 获取热门品种
        hot_herbs = prices_df['herb_name'].value_counts().head(3).index.tolist()
        focus_herbs = hot_herbs
    
    return {
        'prediction': prediction,
        'focus_herbs': focus_herbs
    }


if __name__ == "__main__":
    # 测试周报生成
    result = generate_weekly_report()
    if result['success']:
        print(f"周报生成成功:")
        print(f"标题: {result['report']['title']}")
        print(f"日期范围: {result['report']['date_range']}")
    else:
        print(f"周报生成失败: {result['error']}")