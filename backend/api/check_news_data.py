
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DB_CONFIG = {
    "dbname": "public",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}

def check_news_data():
    """检查新闻数据"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== 检查数据库中的新闻数据 ===\n")
        
        # 查询最近20条新闻
        query = """
        SELECT id, title, publish_time, herb_name, market_name
        FROM news_info1
        ORDER BY publish_time DESC
        LIMIT 20
        """
        
        cursor.execute(query)
        news_list = cursor.fetchall()
        
        print(f"最近20条新闻（按发布时间降序）：\n")
        for news in news_list:
            print(f"ID: {news['id']}")
            print(f"标题: {news['title']}")
            print(f"发布时间: {news['publish_time']}")
            print(f"药材: {news['herb_name']}")
            print(f"市场: {news['market_name']}")
            print("-" * 50)
        
        # 检查日期字段
        print(f"\n\n=== 日期字段检查 ===\n")
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"今天的日期: {today}")
        
        # 查询今天的新闻
        query_today = """
        SELECT COUNT(*) as count
        FROM news_info1
        WHERE DATE(publish_time) = %s
        """
        
        cursor.execute(query_today, (today,))
        result = cursor.fetchone()
        print(f"今天的新闻数量: {result['count']}")
        
        # 查询所有日期的分布
        print(f"\n\n=== 新闻日期分布 ===\n")
        query_dates = """
        SELECT DATE(publish_time) as date, COUNT(*) as count
        FROM news_info1
        GROUP BY DATE(publish_time)
        ORDER BY DATE(publish_time) DESC
        LIMIT 10
        """
        
        cursor.execute(query_dates)
        dates = cursor.fetchall()
        
        print("最近10天的新闻数量：")
        for date_info in dates:
            print(f"{date_info['date']}: {date_info['count']}条")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"检查新闻数据时出错: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    check_news_data()
