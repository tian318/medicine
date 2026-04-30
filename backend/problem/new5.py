import requests
import bs4
import pandas as pd
import datetime
import os
import sys
import time
import random
import psycopg2
import re
from psycopg2.extras import execute_values
from dateutil import parser

# 添加utils目录到Python路径
utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils'))
print(f"Utils path: {utils_path}")
print(f"Utils directory exists: {os.path.exists(utils_path)}")
print(f"my_log.py exists: {os.path.exists(os.path.join(utils_path, 'my_log.py'))}")

if utils_path not in sys.path:
    sys.path.append(utils_path)
    print(f"Added utils path to sys.path: {utils_path}")

print(f"Sys.path: {sys.path}")

try:
    from my_log import Mail_log  # type: ignore
    print("Successfully imported Mail_log from my_log")
except ImportError as e:
    print(f"无法导入Mail_log: {e}")
    print("请确保my_log.py文件存在于utils目录中")
    
# 创建一个简易的日志类替代，避免程序崩溃
class Mail_log:
    def __init__(self, name):
        self.name = name
        self.mail_text = ""

    def log(self, msg, level):
        print(f"[{level}] {msg}")
        self.mail_text += f"[{level}] {msg}\n"

    def mail_send(self, to_email, subject):
        print(f"邮件发送提醒: 收件人={to_email}, 主题={subject}")
        print("注意：使用的是替代日志类，未实际发送邮件")


# 数据库连接配置
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}

# 常见的中药材市场地名列表
common_locations = [
    '安国', '亳州', '成都', '玉林', '广州', '昆明', '重庆', '普洱',
    '西安', '北京', '上海', '杭州', '南京', '武汉', '长沙', '郑州',
    '石家庄', '太原', '济南', '合肥', '南宁', '贵阳', '福州', '兰州',
    '西宁', '银川', '乌鲁木齐', '拉萨', '南昌', '哈尔滨', '长春',
    '沈阳', '天津', '呼和浩特', '海口', '深圳', '青岛', '大连', '宁波',
    '陇西', '文山', '河北', '山东', '江苏', '浙江', '安徽', '江西',
    '福建', '湖北', '湖南', '河南', '广东', '广西', '海南', '四川',
    '贵州', '云南', '陕西', '甘肃', '青海', '内蒙古', '黑龙江', '吉林',
    '辽宁', '山西', '宁夏', '新疆', '西藏', '磐安', '谷城', '平邑', '谯城'
]


def extract_location_from_title(title):
    """从标题中提取地名"""
    if not title or not isinstance(title, str):
        return "未知市场"

    # 四个特定市场的匹配
    specific_markets = {
        '安国': '安国市场',
        '亳州': '亳州市场',
        '玉林': '玉林市场',
        '荷花池': '荷花池市场'
    }

    # 先检查是否是四个特定市场之一
    for market_name, market_full_name in specific_markets.items():
        if market_name in title[:15]:
            return market_full_name

    # 匹配省市县模式
    province_city_pattern = re.compile(r'([\u4e00-\u9fa5]+省[\u4e00-\u9fa5]+市[\u4e00-\u9fa5]+[县区])')
    match = province_city_pattern.search(title)
    if match:
        return match.group(1)

    # 匹配省县模式（如浙江省磐安县）
    province_county_pattern = re.compile(r'([\u4e00-\u9fa5]+省[\u4e00-\u9fa5]+[县市区])')
    match = province_county_pattern.search(title)
    if match:
        return match.group(1)

    # 匹配省市模式
    province_pattern = re.compile(r'([\u4e00-\u9fa5]+省[\u4e00-\u9fa5]+市)')
    match = province_pattern.search(title)
    if match:
        return match.group(1)

    # 匹配自治州模式
    autonomous_pattern = re.compile(r'([\u4e00-\u9fa5]+自治州[\u4e00-\u9fa5]+[县市])')
    match = autonomous_pattern.search(title)
    if match:
        return match.group(1)

    # 匹配"XX产区"模式
    area_pattern = re.compile(r'([\u4e00-\u9fa5]+产区)')
    match = area_pattern.search(title)
    if match:
        return match.group(1)

    # 检查标题的前几个字符是否匹配已知地名
    for location in common_locations:
        if location in title[:15] and location not in specific_markets:
            return location

    return "未知市场"


def check_news_exists(title, publish_time):
    """
    检查数据库中是否已存在该新闻（按标题+发布时间）
    :param title: 新闻标题
    :param publish_time: 发布时间字符串
    :return: True（存在）/False（不存在）
    """
    conn = None
    cursor = None
    try:
        # 连接数据库（添加超时和保活参数，防止连接中断）
        conn = psycopg2.connect(
            **DB_CONFIG,
            connect_timeout=30,
            keepalives=1,
            keepalives_idle=60,
            keepalives_interval=10,
            keepalives_count=5
        )
        cursor = conn.cursor()

        # 转换发布时间为datetime（兼容不同格式）
        try:
            publish_time_dt = pd.to_datetime(publish_time, errors='coerce')
            if pd.isna(publish_time_dt):
                # 若时间转换失败，仅按标题匹配（降低匹配精度）
                query = "SELECT 1 FROM news_info1 WHERE title = %s LIMIT 1"
                cursor.execute(query, (title,))
            else:
                # 按标题+发布时间精确匹配（时间精确到天，避免秒级差异）
                query = """
                SELECT 1 FROM news_info1 
                WHERE title = %s 
                AND DATE(publish_time) = %s 
                LIMIT 1
                """
                cursor.execute(query, (title, publish_time_dt.date()))

            result = cursor.fetchone()
            return result is not None

        except Exception as e:
            print(f"检查新闻是否存在时出错: {e}")
            return False

    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False  # 连接失败时默认视为不存在，继续爬取

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def save_to_database(df):
    """保存数据到数据库（移除ON CONFLICT，仅代码层去重）"""
    try:
        # 连接数据库（添加超时和保活参数）
        conn = psycopg2.connect(
            **DB_CONFIG,
            connect_timeout=30,
            keepalives=1,
            keepalives_idle=60,
            keepalives_interval=10,
            keepalives_count=5
        )
        cursor = conn.cursor()

        # 添加recorded_at列和news_type列
        df['recorded_at'] = datetime.datetime.now()
        df['news_type'] = 'origin'  # 标记为产地资讯

        # 从标题中提取市场名称
        df['market_name'] = df['标题'].apply(extract_location_from_title)

        # 重命名列
        column_mapping = {
            '标题': 'title',
            '发布时间': 'publish_time',
            '品种': 'herb_name',
            '内容': 'content'
        }
        df = df.rename(columns=column_mapping)

        # 处理"未知时间"的情况
        df['publish_time'] = df['publish_time'].apply(
            lambda x: None if x == "未知时间" or not x else x
        )

        # 转换发布时间为datetime格式
        df['publish_time'] = pd.to_datetime(df['publish_time'], errors='coerce')

        # 前向填充空值（兼容所有pandas版本）
        df['publish_time'] = df['publish_time'].ffill()
        # 后向填充（防止开头空值）
        df['publish_time'] = df['publish_time'].bfill()

        # 按发布时间排序
        df = df.sort_values(by='publish_time', na_position='last')

        # 去重：按标题+发布时间去重（代码层最终去重）
        df = df.drop_duplicates(subset=['title', 'publish_time'], keep='first')

        # 无数据则直接返回
        if df.empty:
            print("无新数据需要插入数据库")
            return True

        # 准备数据并单独插入，处理主键冲突
        columns = ['title', 'publish_time', 'herb_name', 'content', 'news_type', 'recorded_at', 'market_name']
        values = [tuple(row) for row in df[columns].values]

        # 构建插入语句
        insert_query = f"""
        INSERT INTO news_info1 ({', '.join(columns)})
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        # 单独插入每条记录，处理主键冲突
        inserted_count = 0
        for i, row in enumerate(values):
            try:
                cursor.execute(insert_query, row)
                conn.commit()
                inserted_count += 1
            except psycopg2.IntegrityError:
                # 跳过重复记录
                conn.rollback()
                continue
            except Exception as e:
                # 处理其他错误
                print(f"插入第{i+1}条记录时出错: {e}")
                conn.rollback()
                continue

        print(f"\n各市场名称数量统计：")
        print(df['market_name'].value_counts())
        print(f"成功保存 {inserted_count} 条新记录到数据库（总待插入 {len(df)} 条）")

        return inserted_count > 0

    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


def normalize_url(url):
    """标准化URL，补充缺失的协议头"""
    if url.startswith('//'):
        return 'https:' + url
    elif url.startswith('/'):
        return 'https://www.zyctd.com' + url
    elif not url.startswith(('http://', 'https://')):
        return 'https://www.zyctd.com/' + url
    return url


def crawl_article_content(url, headers):
    """爬取文章详情内容"""
    try:
        # 标准化URL
        full_url = normalize_url(url)
        print(f"访问文章链接: {full_url}")

        response = requests.get(full_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = bs4.BeautifulSoup(response.text, 'html.parser')

        # 查找文章发布时间
        time_element = soup.find('div', class_='author').find('span')
        publish_time = time_element.text.strip() if time_element else "未知时间"

        # 查找文章内容区域
        article_content_div = soup.find('div', class_='info-content')
        if not article_content_div:
            return "无法获取文章内容", publish_time

        # 移除声明部分
        announcement = article_content_div.find('p', class_='detail-anounce')
        if announcement:
            announcement.decompose()

        # 拼接内容
        content = "\n\n".join([p.text.strip() for p in article_content_div.find_all('p')])
        return content.strip(), publish_time

    except Exception as e:
        print(f"爬取文章内容时出错: {e}")
        return f"爬取失败: {str(e)}", "未知时间"


def crawl_news(start_page=1, end_page=10):
    """
    爬取中药材天地网产地资讯（指定页面+只爬取当天新闻+跳过已存在数据）
    :param start_page: 起始页码
    :param end_page: 结束页码
    """
    mail_logger = Mail_log("中药材产地资讯爬虫")

    try:
        # 校验页码
        if start_page < 1 or end_page < start_page:
            print("页码参数错误：起始页码≥1，结束页码≥起始页码")
            return

        current_date = datetime.date.today()
        print(f"开始爬取日期: {current_date}")
        print(f"爬取页码范围: {start_page} - {end_page}")
        print("模式：指定页面爬取 + 只爬取当天新闻 + 跳过数据库已存在的新闻")

        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
            'referer': 'https://www.zyctd.com/',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }

        # 存储新数据（仅未存在的）
        news_data = []
        total_skipped = 0  # 统计跳过的数量

        # 爬取指定页码
        total_pages = end_page - start_page + 1
        for page in range(start_page, end_page + 1):
            progress = page - start_page + 1
            print(f"\n=== 爬取第{page}页 (进度: {progress}/{total_pages}) ===")

            # 页面延时
            time.sleep(random.uniform(3, 5))

            try:
                # 请求列表页
                url = f'https://www.zyctd.com/zixun/201-{page}.html'
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                news_list = soup.find('div', class_='zixun-list')

                if not news_list:
                    mail_logger.log(f"第{page}页未找到新闻列表", "warning")
                    continue

                news_items = news_list.find_all('div', class_='zixun-item-box')
                print(f"第{page}页找到 {len(news_items)} 条新闻")

                # 遍历每条新闻
                for idx, item in enumerate(news_items, 1):
                    try:
                        # 提取标题和链接
                        title_elem = item.find('div', class_='zixun-item-title').find('a')
                        if not title_elem:
                            print(f"  第{idx}条无标题/链接，跳过")
                            continue

                        title = title_elem.text.strip()
                        link = title_elem['href']

                        # 爬取详情页
                        print(f"  处理第{idx}条: {title[:50]}..." if len(title) > 50 else f"  处理第{idx}条: {title}")
                        article_content, article_time = crawl_article_content(link, headers)

                        # 检查是否为最近7天的新闻
                        try:
                            article_date = pd.to_datetime(article_time, errors='coerce').date()
                            # 计算日期差
                            days_diff = (current_date - article_date).days
                            if days_diff > 7:
                                print(f"  → 不是最近7天的新闻 ({article_time})，跳过")
                                continue
                            print(f"  → 是最近{days_diff}天的新闻，保留")
                        except:
                            print(f"  → 时间格式错误 ({article_time})，跳过")
                            continue

                        # 核心逻辑：检查是否已存在（代码层去重）
                        if check_news_exists(title, article_time):
                            print(f"  → 该新闻已存在，跳过")
                            total_skipped += 1
                            continue

                        # 仅添加新数据
                        news_data.append({
                            '标题': title,
                            '发布时间': article_time,
                            '品种': item.find('span', class_='g-fr footer-mbs').find('div', class_='hover-mbs').find(
                                'a').text.strip() if item.find('span', class_='g-fr footer-mbs') else "未知品种",
                            '内容': article_content
                        })

                        # 单条延时
                        time.sleep(random.uniform(1, 3))

                    except Exception as e:
                        mail_logger.log(f"第{page}页第{idx}条处理失败: {e}", "error")
                        continue

            except requests.RequestException as e:
                mail_logger.log(f"第{page}页请求失败: {e}", "error")
                time.sleep(random.uniform(5, 8))
                continue
            except Exception as e:
                mail_logger.log(f"第{page}页处理异常: {e}", "error")
                continue

        # 爬取完成统计
        print(f"\n=== 爬取结束 ===")
        print(f"总计跳过已存在新闻: {total_skipped} 条")
        print(f"总计获取新新闻: {len(news_data)} 条")

        if not news_data:
            mail_logger.log("无新数据需要保存", "info")
            return

        # 保存数据
        df = pd.DataFrame(news_data)

        # 保存CSV
        save_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(save_dir, exist_ok=True)
        csv_path = os.path.join(save_dir, f'{current_date}_新数据_页码{start_page}-{end_page}.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"新数据已保存到CSV: {csv_path}")

        # 保存数据库
        if save_to_database(df):
            mail_logger.log("新数据成功入库", "info")
        else:
            mail_logger.log("新数据入库失败", "error")

    except Exception as e:
        mail_logger.log(f"爬虫整体异常: {e}", "error")
        mail_logger.mail_send("dingryl@foxmail.com", "爬虫运行失败")
    finally:
        if mail_logger.mail_text:
            mail_logger.mail_send("dingryl@foxmail.com", "爬虫运行完成")


if __name__ == "__main__":
    # 爬取第249页，自动跳过已存在数据
    crawl_news(start_page=1, end_page=3)