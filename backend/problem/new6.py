import requests
import bs4
import pandas as pd
import datetime
import os
import sys
import time
import random
import psycopg2
from psycopg2.extras import execute_values
from dateutil import parser

# 添加utils目录到Python路径
utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils'))
if utils_path not in sys.path:
    sys.path.append(utils_path)

try:
    from my_log import Mail_log
except ImportError:
    print("无法导入Mail_log，请确保my_log.py文件存在于utils目录中")

# 数据库连接配置
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}

def get_latest_news_time(news_type='market'):
    """获取数据库中最新的市场资讯时间"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询最新的新闻时间，固定news_type为'market'
        query = "SELECT publish_time FROM news_info1 WHERE news_type = 'market' ORDER BY publish_time DESC LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            latest_time = result[0]
            print(f"数据库中最新的市场资讯时间: {latest_time}")
            return latest_time
        else:
            print("数据库中没有市场资讯记录，将爬取所有新闻")
            return None
            
    except Exception as e:
        print(f"查询最新新闻时间时出错: {e}")
        return None
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

def save_to_database(df):
    """保存数据到数据库"""
    try:
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 添加recorded_at列和news_type列
        df['recorded_at'] = datetime.datetime.now()
        df['news_type'] = 'market'  # 标记为市场资讯
        
        # 重命名列
        column_mapping = {
            '标题': 'title',
            '发布时间': 'publish_time',
            '品种': 'herb_name',
            '内容': 'content',
            '市场名称': 'market_name'  # 新增市场名称列
        }
        df = df.rename(columns=column_mapping)
        
        # 填补空的发布时间，使用前一条新闻的时间
        # 修改为使用ffill()方法代替fillna(method='ffill')
        df['publish_time'] = df['publish_time'].ffill()
        
        # 处理"未知时间"的情况
        df['publish_time'] = df['publish_time'].apply(
            lambda x: None if x == "未知时间" or not x else x
        )
        
        # 转换发布时间为datetime格式
        df['publish_time'] = pd.to_datetime(df['publish_time'], errors='coerce')
        
        # 再次使用前值填充可能出现的NaT值
        # 修改为使用ffill()方法代替fillna(method='ffill')
        df['publish_time'] = df['publish_time'].ffill()
        
        # 按发布时间排序，处理NaT值
        df = df.sort_values(by='publish_time', na_position='last')
        
        # 准备数据并插入
        columns = ['title', 'publish_time', 'herb_name', 'content', 'market_name', 'news_type', 'recorded_at']
        values = [tuple(row) for row in df[columns].values]
        
        insert_query = f"""
        INSERT INTO news_info1 ({', '.join(columns)})
        VALUES %s
        """
        
        execute_values(cursor, insert_query, values)
        conn.commit()
        
        print(f"成功保存 {len(df)} 条记录到数据库")
        return True
        
    except Exception as e:
        print(f"保存数据到数据库时出错: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

def crawl_news():
    """爬取中药材天地网市场资讯"""
    # 创建邮件日志对象
    mail_logger = Mail_log("中药材市场资讯爬虫")
    
    try:
        # 获取当前日期
        current_date = datetime.date.today()
        print(f"开始爬取日期: {current_date}")
        
        # 获取数据库中最新的市场资讯时间
        latest_news_time = get_latest_news_time('market')
        
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36'
        }

        # 定义存储数据的列表
        news_data = []
        
        # 爬取前5页数据，可以根据需要调整页数
        for page in range(1, 268):
            try:
                url = f'https://www.zyctd.com/zixun/200-{page}.html'  # 修改为市场资讯的URL
                print(f"正在爬取第{page}页市场资讯列表")
                
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                news_list = soup.find('div', class_='zixun-list')
                
                if not news_list:
                    mail_logger.log(f"页面 {page} 未找到新闻列表", "warning")
                    continue
                
                # 获取所有新闻项
                news_items = news_list.find_all('div', class_='zixun-item-box')
                
                # 标记是否所有新闻都已经存在于数据库中
                all_news_exist = True
                
                for item in news_items:
                    try:
                        # 获取新闻标题和链接
                        title_element = item.find('div', class_='zixun-item-title').find('a')
                        title = title_element.text.strip()
                        link = title_element['href']
                        
                        # 获取品种信息
                        herb_name = "未知品种"
                        footer_mbs = item.find('span', class_='g-fr footer-mbs')
                        if footer_mbs:
                            hover_mbs = footer_mbs.find('div', class_='hover-mbs')
                            if hover_mbs and hover_mbs.find('a'):
                                herb_name = hover_mbs.find('a').text.strip()
                        
                        # 爬取新闻详情页
                        print(f"正在爬取市场资讯: {title}")
                        article_content, publish_time, market_name = crawl_article_content(link, headers)
                        
                        # 转换文章时间为datetime对象
                        try:
                            article_datetime = parser.parse(publish_time)
                            
                            # 如果有最新新闻时间，且当前文章时间不比最新时间新，则跳过
                            if latest_news_time and article_datetime <= latest_news_time:
                                print(f"跳过已存在的市场资讯: {title} ({publish_time})")
                                continue
                            
                            # 标记有新的新闻
                            all_news_exist = False
                            
                        except Exception as e:
                            print(f"解析文章时间出错: {e}")
                            # 如果无法解析时间，仍然添加到数据列表
                        
                        # 添加到数据列表
                        news_data.append({
                            '标题': title,
                            '发布时间': publish_time,
                            '品种': herb_name,
                            '内容': article_content,
                            '市场名称': market_name
                        })
                        
                        # 随机延时，避免请求过于频繁
                        time.sleep(random.uniform(1, 3))
                        
                    except Exception as e:
                        mail_logger.log(f"爬取新闻项时出错: {str(e)}", "error")
                        continue
                
                # 如果当前页所有新闻都已存在，且不是第一页，则停止爬取
                if all_news_exist and page > 1:
                    print("没有发现新的市场资讯，停止爬取")
                    break
                
            except requests.RequestException as e:
                mail_logger.log(f"爬取第 {page} 页时发生网络错误: {str(e)}", "error")
                continue
            except Exception as e:
                mail_logger.log(f"爬取第 {page} 页时发生未知错误: {str(e)}", "error")
                continue
        
        # 检查是否成功爬取到数据
        if not news_data:
            mail_logger.log("未能成功爬取任何市场资讯数据或没有新的市场资讯", "info")
            return

        # 创建DataFrame
        df = pd.DataFrame(news_data)
        print(f"共爬取 {len(df)} 条市场资讯")
        
        try:
            # 保存到CSV
            csv_path = f'/root/my_graduation_project/data/{current_date}市场资讯.csv'
            df.to_csv(csv_path, index=False, encoding='utf-8')
            mail_logger.log(f"成功保存CSV文件到: {csv_path}", "info")
            
            # 保存到数据库
            save_to_database(df)
            mail_logger.log("成功保存数据到数据库", "info")
            
        except Exception as e:
            mail_logger.log(f"保存数据时发生错误: {str(e)}", "error")
            mail_logger.mail_send("dingryl@foxmail.com", "中药材市场资讯爬虫数据保存异常")
            return
        
    except Exception as e:
        mail_logger.log(f"爬虫运行过程中发生严重错误: {str(e)}", "error")
        mail_logger.mail_send("dingryl@foxmail.com", "中药材市场资讯爬虫运行异常")
        return
    
    # 将日志发送邮件通知
    if mail_logger.mail_text:
        mail_logger.mail_send("dingryl@foxmail.com", "中药材市场资讯爬虫运行日志")

def crawl_article_content(url, headers):
    """爬取文章详情内容"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        
        # 查找文章标题
        title_element = soup.find('div', class_='info-title').find('h1')
        title = title_element.text.strip() if title_element else "无标题"
        
        # 查找文章发布时间和市场名称（从author区域）
        publish_time = "未知时间"
        market_name = "未知市场"
        
        # 查找author区域
        author_div = soup.find('div', class_='author')
        if author_div:
            # 提取时间
            time_span = author_div.find('span')
            if time_span:
                publish_time = time_span.text.strip()
            
            # 提取市场名称（作者）
            info_author_span = author_div.find('span', class_='info-author')
            if info_author_span:
                market_name = info_author_span.text.strip()
            
            # 如果没有找到info-author类，尝试其他方法
            if market_name == "未知市场":
                # 尝试从作者文本中提取市场名称
                author_text = author_div.text.strip()
                if "作者:" in author_text or "作者：" in author_text:
                    parts = author_text.replace("作者:", "作者：").split("作者：")
                    if len(parts) > 1:
                        # 提取作者后面的文本，直到下一个空格或特殊字符
                        author_part = parts[1].strip().split()[0]
                        if author_part:
                            market_name = author_part
        
        # 查找文章内容区域
        article_content_div = soup.find('div', class_='info-content')
        
        if not article_content_div:
            return "无法获取文章内容", publish_time, market_name
        
        # 移除声明部分
        announcement = article_content_div.find('p', class_='detail-anounce')
        if announcement:
            announcement.decompose()
        
        # 获取所有段落
        paragraphs = article_content_div.find_all('p')
        content = ""
        
        for p in paragraphs:
            content += p.text.strip() + "\n\n"
        
        # 如果从页面中无法提取市场名称，尝试从内容中提取
        if market_name == "未知市场":
            # 尝试从内容中提取市场名称
            content_lines = content.split('\n')
            for line in content_lines:
                if "市场" in line and len(line) < 30:  # 假设市场名称所在行不会太长
                    market_name = line.strip()
                    break
        
        return content.strip(), publish_time, market_name
    
    except Exception as e:
        print(f"爬取文章内容时出错: {e}")
        return f"爬取失败: {str(e)}", "未知时间", "未知市场"

if __name__ == "__main__":
    crawl_news()