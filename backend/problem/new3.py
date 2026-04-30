import requests
import bs4
import pandas as pd
import datetime
import time
import random
import sys
import os
import psycopg2
from psycopg2.extras import execute_values

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

def save_to_database(df, source='ecommerce'):
    """保存数据到数据库"""
    try:
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 添加source和recorded_at列
        df['source'] = source
        df['recorded_at'] = datetime.datetime.now()
        
        # 重命名列
        column_mapping = {
            '品名': 'herb_name',
            '规格': 'specification',
            '产地': 'location',
            '近期价格（元）': 'price',
            '店铺': 'shop_name',
            '详情': 'details'
        }
        df = df.rename(columns=column_mapping)
        
        # 准备数据并插入
        columns = ['herb_name', 'specification', 'location', 'price', 'shop_name', 'details', 'source', 'recorded_at']
        values = [tuple(row) for row in df[columns].values]
        
        insert_query = f"""
        INSERT INTO ecommerce_prices ({', '.join(columns)})
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



def make_request_with_retry(url, headers, max_retries=3, base_delay=2):
    """发送请求并实现重试机制"""
    for attempt in range(max_retries):
        try:
            # 添加随机延迟，避免请求过于规律
            delay = base_delay + random.uniform(1, 3)
            time.sleep(delay)
            
            # 发送请求
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            return res
        except requests.RequestException as e:
            # 如果不是最后一次尝试，则等待后重试
            if attempt < max_retries - 1:
                # 指数退避策略，每次重试增加等待时间
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"请求失败，{wait_time:.2f}秒后重试: {e}")
                time.sleep(wait_time)
            else:
                # 最后一次尝试也失败，抛出异常
                raise

def crawl_and_save():
    """爬取数据并保存的主函数"""
    # 创建邮件日志对象
    mail_logger = Mail_log("中药材电商价格爬虫")
    
    try:
        # 获取当前日期
        current_date = datetime.date.today()
        print(current_date)
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36'
        }

        # 获取总页数
        url = 'https://www.zyctd.com/jiage/ds0-0.html'
        response = make_request_with_retry(url, headers)
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        page_info = soup.find('li', class_='page').find('span').text
        total_pages = int(page_info.split(' / ')[1])    # 获取总共需要爬取的页数
        print("总共需要爬取%d页数据" % total_pages)
        pages = total_pages + 1            

        # 定义存储数据的列表
        data = []
        # 定义列名
        columns = ["品名", "规格", "产地", "近期价格（元）", "店铺", '详情']

        # 改进后的代码，开始爬取数据
        for x in range(1, pages):
            try:
                url = 'https://www.zyctd.com/jiage/ds0-0-' + str(x) + '.html'
                res = make_request_with_retry(url, headers)
                
                db_result = bs4.BeautifulSoup(res.text, 'html.parser')
                grid = db_result.find('tbody')  # 直接找到tbody标签
                
                if not grid:
                    mail_logger.log(f"页面 {x} 未找到数据表格", "warning")
                    continue
                    
                print("正在爬取第%d页数据" % x)  # 打印当前爬取的页数

                # 使用find_all找到所有包含数据的行
                rows = grid.find_all('tr')

                for row in rows:
                    tds = row.find_all('td')
                    row_data = []
                    for td in tds:
                        # 提取名称和规格时，从span属性中获取完整内容
                        if td.find('span'):
                            a_tag = td.find('span')
                            row_data.append(a_tag['title'].strip() if 'title' in a_tag.attrs else a_tag.text.strip())
                        else:
                            # 检查td是否有title属性，如果有则使用title的值
                            row_data.append(td['title'].strip() if 'title' in td.attrs else td.text.strip())
                    # 当行数据达到列数时，添加到数据列表
                    if len(row_data) == len(columns):
                        data.append(row_data)
                    else:
                        mail_logger.log(f"页面 {x} 中发现数据格式异常: {row_data}", "warning")
                        
            except requests.RequestException as e:
                mail_logger.log(f"爬取第 {x} 页时发生网络错误: {str(e)}", "error")
                continue
            except Exception as e:
                mail_logger.log(f"爬取第 {x} 页时发生未知错误: {str(e)}", "error")
                continue

        # 检查是否成功爬取到数据
        if not data:
            mail_logger.log("未能成功爬取任何数据", "error")
            mail_logger.mail_send("dingryl@foxmail.com", "中药材电商价格爬虫运行异常")
            return

        # 创建DataFrame
        df = pd.DataFrame(data, columns=columns)
        df.info()

        try:
            # 保存到CSV
            csv_path = f'/root/my_graduation_project/data/{current_date}电商价格.csv'
            df.to_csv(csv_path, index=False, encoding='utf-8')
            mail_logger.log(f"成功保存CSV文件到: {csv_path}", "info")

            # 保存到数据库
            # save_to_database(df)
            # mail_logger.log("成功保存数据到数据库", "info")

        except Exception as e:
            mail_logger.log(f"保存数据时发生错误: {str(e)}", "error")
            mail_logger.mail_send("dingryl@foxmail.com", "中药材电商价格爬虫数据保存异常")
            return

    except Exception as e:
        mail_logger.log(f"爬虫运行过程中发生严重错误: {str(e)}", "error")
        mail_logger.mail_send("dingryl@foxmail.com", "中药材电商价格爬虫运行异常")
        return

    # 将日志发送邮件通知
    if mail_logger.mail_text:
        mail_logger.mail_send("dingryl@foxmail.com", "中药材电商价格爬虫运行日志")

if __name__ == "__main__":
    crawl_and_save()
