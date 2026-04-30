import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
import jieba
import re
from datetime import datetime, timedelta
import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import warnings

warnings.filterwarnings('ignore')

# 数据库连接配置
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}


def get_db_connection():
    """创建数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None


def fetch_news_data(herb_name=None, start_date=None, end_date=None, limit=100):
    """从数据库获取新闻数据"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 修改查询，确保使用正确的列名
        query = """
        SELECT 
            id, title, content, market_name, publish_time, 
            herb_name, 
            NULL as sentiment_score
        FROM news_info1
        WHERE 1=1
        """

        params = []
        if herb_name:
            query += " AND (title LIKE %s OR content LIKE %s OR herb_name LIKE %s)"
            params.extend([f'%{herb_name}%', f'%{herb_name}%', f'%{herb_name}%'])
        if start_date:
            query += " AND publish_time >= %s"
            params.append(start_date)
        if end_date:
            query += " AND publish_time <= %s"
            params.append(end_date)

        query += " ORDER BY publish_time DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        df = pd.DataFrame(rows)

        if df.empty:
            print("查询结果为空")
            return pd.DataFrame()

        # 重命名列以与代码其余部分保持一致
        if 'market_name' in df.columns:
            df.rename(columns={'market_name': 'source'}, inplace=True)
        if 'publish_time' in df.columns:
            df.rename(columns={'publish_time': 'publish_date'}, inplace=True)
        if 'herb_name' in df.columns:
            df.rename(columns={'herb_name': 'herb_related'}, inplace=True)

        # 确保日期是日期时间类型
        if 'publish_date' in df.columns:
            df['publish_date'] = pd.to_datetime(df['publish_date'])

        return df

    except Exception as e:
        print(f"获取新闻数据时出错: {e}")
        import traceback
        traceback.print_exc()
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


def analyze_sentiment(news_df):
    """分析新闻情感"""
    if news_df.empty:
        return None

    # 如果已经有情感分数，直接使用
    if 'sentiment_score' in news_df.columns and not news_df['sentiment_score'].isnull().all():
        # 计算平均情感分数
        avg_sentiment = news_df['sentiment_score'].mean()

        # 统计情感分布
        sentiment_counts = {
            'positive': len(news_df[news_df['sentiment_score'] > 0.1]),
            'neutral': len(news_df[(news_df['sentiment_score'] >= -0.1) & (news_df['sentiment_score'] <= 0.1)]),
            'negative': len(news_df[news_df['sentiment_score'] < -0.1])
        }

        # 计算情感趋势
        news_df = news_df.sort_values('publish_date')
        news_df['date'] = news_df['publish_date'].dt.date
        sentiment_trend = news_df.groupby('date')['sentiment_score'].mean().reset_index()

        # 提取关键词
        all_content = ' '.join(news_df['content'].fillna('').apply(preprocess_text))
        keywords = extract_keywords(all_content)

        return {
            'avg_sentiment': float(avg_sentiment),
            'sentiment_counts': sentiment_counts,
            'sentiment_trend': {
                'dates': [d.strftime('%Y-%m-%d') for d in sentiment_trend['date']],
                'scores': sentiment_trend['sentiment_score'].tolist()
            },
            'keywords': keywords
        }
    else:
        # 使用更适合中药材市场的情感分析方法
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

        # 中性词汇，这些词在中药材市场中通常不表示明显的情感倾向
        neutral_words = {
            '货源', '价格', '元', '左右', '统货', '精品', '市场', '行情', '走势',
            '供应', '需求', '产地', '批发', '零售', '采购', '销售', '交易'
        }

        # 价格相关的词汇，需要结合数字判断情感
        price_related_words = {'价格', '元', '报价', '售价', '成交价'}

        # 预处理文本
        news_df['processed_content'] = news_df['content'].fillna('').apply(preprocess_text)

        # 计算情感分数
        sentiment_scores = []
        for idx, row in news_df.iterrows():
            text = row['processed_content']
            title = row['title'] if 'title' in row and isinstance(row['title'], str) else ''

            # 结合标题和内容进行分析
            full_text = title + ' ' + text
            words = full_text.split()

            # 基础分数计算
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)

            # 提取价格信息并分析价格变化趋势
            price_trend_score = 0
            price_pattern = re.compile(r'(\d+(\.\d+)?)\s*元')
            price_matches = price_pattern.findall(row['content'] if isinstance(row['content'], str) else '')

            # 检测价格上涨或下跌的关键词
            price_up_indicators = ['上涨', '涨价', '增长', '提高', '高于']
            price_down_indicators = ['下跌', '跌价', '降低', '减少', '低于']

            has_price_up = any(indicator in row['content'] for indicator in price_up_indicators) if isinstance(
                row['content'], str) else False
            has_price_down = any(indicator in row['content'] for indicator in price_down_indicators) if isinstance(
                row['content'], str) else False

            if has_price_up:
                price_trend_score = 0.3
            elif has_price_down:
                price_trend_score = -0.3

            # 检测供需关系关键词
            supply_demand_score = 0
            supply_excess = ['供应充足', '货源充足', '供大于求', '库存充足']
            supply_shortage = ['供不应求', '货源紧张', '供应短缺', '库存不足']

            has_supply_excess = any(indicator in row['content'] for indicator in supply_excess) if isinstance(
                row['content'], str) else False
            has_supply_shortage = any(indicator in row['content'] for indicator in supply_shortage) if isinstance(
                row['content'], str) else False

            if has_supply_shortage:
                supply_demand_score = 0.2  # 供应短缺通常意味着价格上涨，对卖家是积极的
            elif has_supply_excess:
                supply_demand_score = -0.1  # 供应过剩可能导致价格下跌，但影响较小

            # 综合评分
            base_score = 0
            if positive_count > negative_count:
                base_score = min(0.5, 0.1 + (positive_count - negative_count) * 0.05)
            elif positive_count < negative_count:
                base_score = max(-0.5, -0.1 - (negative_count - positive_count) * 0.05)

            # 最终情感分数
            final_score = base_score + price_trend_score + supply_demand_score
            # 限制在 -1 到 1 之间
            final_score = max(-1, min(1, final_score))

            sentiment_scores.append(final_score)

        news_df['sentiment_score'] = sentiment_scores

        # 计算平均情感分数
        avg_sentiment = np.mean(sentiment_scores)

        # 统计情感分布
        sentiment_counts = {
            'positive': len([s for s in sentiment_scores if s > 0.1]),
            'neutral': len([s for s in sentiment_scores if -0.1 <= s <= 0.1]),
            'negative': len([s for s in sentiment_scores if s < -0.1])
        }

        # 计算情感趋势
        news_df = news_df.sort_values('publish_date')
        news_df['date'] = news_df['publish_date'].dt.date
        sentiment_trend = news_df.groupby('date')['sentiment_score'].mean().reset_index()

        # 提取关键词
        all_content = ' '.join(news_df['processed_content'])
        keywords = extract_keywords(all_content)

        return {
            'avg_sentiment': float(avg_sentiment),
            'sentiment_counts': sentiment_counts,
            'sentiment_trend': {
                'dates': [d.strftime('%Y-%m-%d') for d in sentiment_trend['date']],
                'scores': sentiment_trend['sentiment_score'].tolist()
            },
            'keywords': keywords
        }


def extract_keywords(text, top_n=20):
    """提取文本中的关键词"""
    if not text:
        return []

    # 使用TF-IDF提取关键词
    vectorizer = TfidfVectorizer(max_features=100)
    try:
        tfidf_matrix = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()

        # 获取词语的TF-IDF值
        tfidf_scores = zip(feature_names, tfidf_matrix.toarray()[0])

        # 按TF-IDF值排序
        sorted_scores = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)

        # 返回前top_n个关键词
        return [{'word': word, 'weight': float(score)} for word, score in sorted_scores[:top_n]]
    except:
        # 如果TF-IDF提取失败，使用简单的词频统计
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
        return [{'word': word, 'weight': count} for word, count in sorted_words[:top_n]]


def generate_wordcloud(keywords):
    """生成词云图"""
    if not keywords:
        return None

    # 创建词频字典
    word_freq = {item['word']: item['weight'] for item in keywords}

    try:
        # 尝试使用系统默认字体或指定备选字体
        font_path = None
        # 常见中文字体路径列表
        font_paths = [
            'simhei.ttf',  # 本地路径
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # Ubuntu/Debian
            '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc',  # CentOS/RHEL
            '/usr/share/fonts/chinese/TrueType/simhei.ttf',
            '/usr/share/fonts/dejavu/DejaVuSans.ttf',  # 非中文但常见的备选
            None  # 最后尝试不指定字体
        ]

        # 尝试找到可用的字体
        for path in font_paths:
            try:
                if path:
                    # 测试字体是否可用
                    from PIL import ImageFont
                    ImageFont.truetype(path, 12)
                font_path = path
                break
            except Exception:
                continue

        # 生成词云
        wordcloud_args = {
            'width': 800,
            'height': 400,
            'background_color': 'white',
        }

        if font_path:
            wordcloud_args['font_path'] = font_path

        wordcloud = WordCloud(**wordcloud_args).generate_from_frequencies(word_freq)

        # 保存词云图
        output_dir = os.path.join(os.path.dirname(__file__), 'static')
        os.makedirs(output_dir, exist_ok=True)

        filename = f"wordcloud_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        output_path = os.path.join(output_dir, filename)

        wordcloud.to_file(output_path)

        return f"/static/{filename}"
    except Exception as e:
        print(f"生成词云失败: {e}")
        # 如果词云生成失败，返回None但不中断整个分析过程
        return None


def predict_price_trend(sentiment_data, price_data=None):
    """基于情感分析预测价格趋势"""
    if not sentiment_data:
        return None

    avg_sentiment = sentiment_data['avg_sentiment']
    sentiment_counts = sentiment_data['sentiment_counts']

    # 计算情感比例
    total_news = sum(sentiment_counts.values())
    if total_news == 0:
        return {
            'trend': 'neutral',
            'confidence': 0,
            'explanation': '没有足够的新闻数据进行分析'
        }

    positive_ratio = sentiment_counts['positive'] / total_news
    negative_ratio = sentiment_counts['negative'] / total_news

    # 基于情感分析预测趋势
    if avg_sentiment > 0.1 and positive_ratio > 0.6:
        trend = 'up'
        confidence = min(0.9, positive_ratio)
        explanation = '市场情绪偏向积极，预计价格可能上涨'
    elif avg_sentiment < -0.1 and negative_ratio > 0.6:
        trend = 'down'
        confidence = min(0.9, negative_ratio)
        explanation = '市场情绪偏向消极，预计价格可能下跌'
    else:
        trend = 'stable'
        confidence = max(0.5, 1 - abs(positive_ratio - negative_ratio))
        explanation = '市场情绪中性，预计价格可能保持稳定'

    # 如果有价格数据，结合价格趋势进行分析
    if price_data is not None and 'trend' in price_data:
        price_trend = price_data['trend']

        if price_trend == 'up' and trend == 'up':
            confidence += 0.1
            explanation += '，且与当前价格上涨趋势一致，可信度较高'
        elif price_trend == 'down' and trend == 'down':
            confidence += 0.1
            explanation += '，且与当前价格下跌趋势一致，可信度较高'
        elif price_trend != trend:
            confidence -= 0.1
            explanation += f'，但与当前价格{price_trend}趋势不一致，存在不确定性'

    # 确保置信度在0-1之间
    confidence = max(0, min(1, confidence))

    return {
        'trend': trend,
        'confidence': float(confidence),
        'explanation': explanation
    }


def get_herb_sentiment_analysis(herb_name, start_date=None, end_date=None):
    """获取药材的市场情绪分析"""
    try:
        # 如果没有指定日期范围，默认分析最近30天的数据
        if not start_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        # 获取新闻数据
        news_df = fetch_news_data(herb_name, start_date, end_date)

        if news_df.empty:
            return {
                'success': False,
                'error': f'没有找到与{herb_name}相关的新闻数据'
            }

        # 分析情感
        sentiment_data = analyze_sentiment(news_df)

        if not sentiment_data:
            return {
                'success': False,
                'error': '情感分析失败'
            }

        # 预测价格趋势
        trend_prediction = predict_price_trend(sentiment_data)

        # 尝试生成词云，但即使失败也继续
        try:
            wordcloud_path = generate_wordcloud(sentiment_data['keywords'])
        except Exception as e:
            print(f"词云生成失败，但继续其他分析: {e}")
            wordcloud_path = None

        # 构建结果
        result = {
            'success': True,
            'herb_name': herb_name,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'news_count': len(news_df),
            'sentiment_analysis': sentiment_data,
            'trend_prediction': trend_prediction,
            'wordcloud_path': wordcloud_path
        }

        return result

    except Exception as e:
        print(f"市场情绪分析失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def get_recent_sentiment_trends():
    """获取最近的市场情绪趋势"""
    try:
        conn = get_db_connection()
        if not conn:
            return []

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 获取最近30天的整体市场情绪趋势
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # 修改查询，使用正确的列名
        query = """
        SELECT 
            id, title, content, market_name, publish_time, 
            herb_name
        FROM news_info1
        WHERE publish_time BETWEEN %s AND %s
        ORDER BY publish_time
        """

        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()

        if not rows:
            return []

        # 将查询结果转换为DataFrame
        news_df = pd.DataFrame(rows)

        # 重命名列以与代码其余部分保持一致
        if 'market_name' in news_df.columns:
            news_df.rename(columns={'market_name': 'source'}, inplace=True)
        if 'publish_time' in news_df.columns:
            news_df.rename(columns={'publish_time': 'publish_date'}, inplace=True)
        if 'herb_name' in news_df.columns:
            news_df.rename(columns={'herb_name': 'herb_related'}, inplace=True)

        # 确保日期是日期时间类型
        if 'publish_date' in news_df.columns:
            news_df['publish_date'] = pd.to_datetime(news_df['publish_date'])

        query = """
        SELECT 
            DATE(publish_date) as date,
            AVG(sentiment_score) as avg_sentiment,
            COUNT(*) as news_count
        FROM news_info1
        WHERE publish_date BETWEEN %s AND %s
        GROUP BY DATE(publish_date)
        ORDER BY date
        """

        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()

        if not rows:
            return []

        # 处理结果
        trends = []
        for row in rows:
            trends.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'avg_sentiment': float(row['avg_sentiment']) if row['avg_sentiment'] else 0,
                'news_count': row['news_count']
            })

        return trends

    except Exception as e:
        print(f"获取市场情绪趋势失败: {e}")
        return []
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


def get_top_herbs_by_sentiment(limit=10, sentiment_type='positive'):
    """获取情感分析排名靠前的药材"""
    try:
        conn = get_db_connection()
        if not conn:
            return []

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 获取最近30天的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # 修改查询，使用正确的列名
        query = """
        SELECT 
            id, title, content, market_name, publish_time, 
            herb_name
        FROM news_info1
        WHERE publish_time BETWEEN %s AND %s
        AND herb_name IS NOT NULL
        ORDER BY publish_time
        """

        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()

        if not rows:
            return []

        # 将查询结果转换为DataFrame
        news_df = pd.DataFrame(rows)

        # 重命名列以与代码其余部分保持一致
        if 'market_name' in news_df.columns:
            news_df.rename(columns={'market_name': 'source'}, inplace=True)
        if 'publish_time' in news_df.columns:
            news_df.rename(columns={'publish_time': 'publish_date'}, inplace=True)
        if 'herb_name' in news_df.columns:
            news_df.rename(columns={'herb_name': 'herb_related'}, inplace=True)

        # 确保日期是日期时间类型
        if 'publish_date' in news_df.columns:
            news_df['publish_date'] = pd.to_datetime(news_df['publish_date'])

        # 根据情感类型构建查询条件
        sentiment_condition = ""
        if sentiment_type == 'positive':
            sentiment_condition = "sentiment_score > 0.1"
        elif sentiment_type == 'negative':
            sentiment_condition = "sentiment_score < -0.1"
        else:  # neutral
            sentiment_condition = "sentiment_score BETWEEN -0.1 AND 0.1"

        query = f"""
        WITH herb_sentiment AS (
            SELECT 
                unnest(string_to_array(herb_related, ',')) as herb_name,
                sentiment_score
            FROM news_info1
            WHERE publish_date BETWEEN %s AND %s
            AND herb_related IS NOT NULL
            AND {sentiment_condition}
        )
        SELECT 
            herb_name,
            AVG(sentiment_score) as avg_sentiment,
            COUNT(*) as news_count
        FROM herb_sentiment
        GROUP BY herb_name
        ORDER BY 
            CASE WHEN %s = 'positive' THEN avg_sentiment END DESC,
            CASE WHEN %s = 'negative' THEN avg_sentiment END ASC,
            news_count DESC
        LIMIT %s
        """

        cursor.execute(query, (start_date, end_date, sentiment_type, sentiment_type, limit))
        rows = cursor.fetchall()

        if not rows:
            return []

        # 处理结果
        herbs = []
        for row in rows:
            herbs.append({
                'herb_name': row['herb_name'],
                'avg_sentiment': float(row['avg_sentiment']) if row['avg_sentiment'] else 0,
                'news_count': row['news_count']
            })

        return herbs

    except Exception as e:
        print(f"获取情感分析排名靠前的药材失败: {e}")
        return []
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


def get_herb_names_from_db():
    """从数据库中获取所有药材名称"""
    try:
        conn = get_db_connection()
        if not conn:
            return []

        cursor = conn.cursor()

        # 查询数据库中的所有药材名称，去重
        query = """
        SELECT DISTINCT herb_name 
        FROM news_info1 
        WHERE herb_name IS NOT NULL AND herb_name != ''
        ORDER BY herb_name
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        # 提取药材名称
        herb_names = [row[0] for row in rows if row[0]]

        return herb_names

    except Exception as e:
        print(f"获取药材名称列表失败: {e}")
        return []
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    # 测试情感分析
    herb_name = "黄连"
    result = get_herb_sentiment_analysis(herb_name)

    if result['success']:
        print(f"\n{herb_name}的市场情绪分析结果:")
        print(f"新闻数量: {result['news_count']}")
        print(f"平均情感分数: {result['sentiment_analysis']['avg_sentiment']}")
        print(f"情感分布: {result['sentiment_analysis']['sentiment_counts']}")
        print(f"价格趋势预测: {result['trend_prediction']['trend']}")
        print(f"预测置信度: {result['trend_prediction']['confidence']}")
        print(f"预测解释: {result['trend_prediction']['explanation']}")
    else:
        print(f"分析失败: {result['error']}")