import pandas as pd
import re
import psycopg2

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

def test_with_examples():
    """使用示例标题测试提取函数"""
    examples = [
        "云南省昆明市市辖区蛤蚧走动一般",
        "安国半夏 走动加快价格上涨",
        "云南普洱茯苓走势缓慢",
        "山东省临沂市费县12月31日山楂走势",
        "甘肃省张掖市民乐县 板蓝根 快讯信息",
        "甘肃省张掖市民乐县 大青叶 快讯信息",
        "云南产区茯苓因鲜货上市量增大价格小幅下跌",
        "云南产区当归干品不断增多卖货人不多",
        "云南产区天南星库存量大需求疲软",
        "云南产区龙胆产新reducible上市交易量小",
        "云南产区何首乌受市场价滑的影响行情下跌",
        "云南产区云木香交易放缓上市量继续增多",
        "贵州省毕节地区威宁彝族回族苗族自治县 半夏 走势畅快",
        "甘肃省定西市陇西县黄芪走势缓慢",
        "甘肃省定西市陇西县 党参 快讯信息",
        "2025年1月1日文山三七综合交易市场实时行情",
        "河北省邢台市内丘县 酸枣仁 走势稳定",
        "河北安国半夏价格上涨",
        "山东省临沂市费县12月31日山楂走势",
        "甘肃省定西市岷县黄芪成交价格基本稳定",
        "hawks市恩施市宣恩县黄柏行情",
        "四川省巴中市平昌县鱼腥草走势缓慢",
        "四川省巴中市平昌县 五加皮货源显缺",
        "云南省楚雄彝族自治州武定县白及驯化苗走货良好",
        "四川省广安市邻水县 土茯苓走势稳定",
        "甘肃省定西市岷县党参交易量大 走货加快",
        "河北省保定市安国市半夏走势畅快",
        "河北安国半夏小幅上扬",
        "山东省枣庄市峄城区 石榴皮 走势畅快",
        "河南省焦作市武陟县 地黄 走势缓慢",
        "四川省眉山市彭山县 泽泻开始产新",
        "浙江省金华市磐安县吴茱萸商家购进积极性不高",
        "浙江省磐安县延胡索近期行情保持稳定",
        "浙江省磐安县浙贝母走畅价升 后市行情多商看好",
        "浙江省磐安县覆盆子走动依然不畅，行情又有小幅下滑",
        "湖北省襄樊市谷城县蝉蜕行情稍有回升，有走高的势头",
        "湖北省襄阳市八角枫根走动较快，价格稳定",
        "湖北省襄阳市谷城县青风藤价格保持平稳",
        "湖北省襄阳市谷城县首乌藤走货情况稳定",
        "四川省南充市高坪区南瓜子产新结束  走动尚可",
        "河北安国半夏走向加快 农户价格上涨",
        "湖北省襄阳市谷城县白英价格稳定 产新即将结束",
        "山东省临沂市平邑县 金银花 走势缓慢",
        "安徽省亳州市谯城区白芷走销尚可",
        "hawks市恩施市大同区大青叶行情在低迷中运行",
        "hawks市恩施市大同区板蓝根可供货源充足",
        "浙江省磐安县浙八味市场覆盆子上货不多 成交量也不大"
    ]
    
    results = {}
    for example in examples:
        market = extract_location_from_title(example)
        results[example] = market
        print(f"标题: {example}")
        print(f"提取的市场名称: {market}")
        print("-" * 50)
    
    # 统计各市场名称的数量
    market_counts = {}
    for market in results.values():
        market_counts[market] = market_counts.get(market, 0) + 1
    
    print("\n各市场名称数量统计：")
    for market, count in sorted(market_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{market}: {count}")

def process_csv():
    """处理CSV文件，提取标题中的地名"""
    try:
        # 读取CSV文件
        csv_path = '/root/my_graduation_project/data/2025-04-10新闻资讯.csv'
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"成功读取CSV文件，共有 {len(df)} 条记录")
        
        # 检查是否有标题列
        if '标题' not in df.columns:
            print("CSV文件中没有'标题'列")
            return
        
        # 添加市场名称列
        df['市场名称'] = df['标题'].apply(extract_location_from_title)
        
        # 统计各市场名称的数量
        market_counts = df['市场名称'].value_counts()
        print("\n各市场名称数量统计：")
        print(market_counts)
        
        # 保存处理后的CSV文件
        output_path = '/root/my_graduation_project/data/2025-04-10新闻资讯_with_market.csv'
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n处理后的数据已保存到 {output_path}")
        
        # 输出一些示例，展示标题和提取的市场名称
        print("\n标题与提取的市场名称示例：")
        sample_size = min(10, len(df))
        for _, row in df.head(sample_size).iterrows():
            print(f"标题: {row['标题']}")
            print(f"提取的市场名称: {row['市场名称']}")
            print("-" * 50)
        
    except Exception as e:
        print(f"处理CSV文件时出错: {e}")

def update_market_names_in_db():
    """将提取的市场名称更新到数据库"""
    try:
        # 数据库连接配置
        DB_CONFIG = {
            'dbname': 'postgres',
            'user': 'postgres',
            'password': 'LAPTOP-UO3FERDN',
            'host': 'localhost',
            'port': '5432'
        }
        
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取所有news_type为'origin'的记录
        query = """
        SELECT id, title FROM news_info1 
        WHERE news_type = 'origin'
        """
        cursor.execute(query)
        records = cursor.fetchall()
        
        print(f"找到 {len(records)} 条原始资讯记录")
        
        # 更新计数器
        updated_count = 0
        
        # 遍历记录并更新
        for record_id, title in records:
            # 从标题中提取市场名称
            market_name = extract_location_from_title(title)
            
            # 更新记录
            update_query = """
            UPDATE news_info1 SET market_name = %s WHERE id = %s
            """
            cursor.execute(update_query, (market_name, record_id))
            updated_count += 1
            
            # 每100条记录打印一次进度
            if updated_count % 100 == 0:
                print(f"已处理 {updated_count}/{len(records)} 条记录")
        
        # 提交事务
        conn.commit()
        print(f"成功更新了 {updated_count} 条记录的市场名称")
        
        # 查询更新后的统计信息
        cursor.execute("SELECT market_name, COUNT(*) FROM news_info1 WHERE news_type = 'origin' GROUP BY market_name ORDER BY COUNT(*) DESC")
        market_stats = cursor.fetchall()
        
        print("\n各市场名称数量统计：")
        for market, count in market_stats:
            print(f"{market}: {count}")
        
    except Exception as e:
        print(f"更新数据库时出错: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    # 使用示例标题测试提取函数
    # test_with_examples()
    
    # 处理CSV文件
    # process_csv()
    
    # 将提取的市场名称更新到数据库
    update_market_names_in_db()