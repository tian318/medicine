"""
新闻标签生成器
功能：
1. 为新闻自动生成标签
2. 支持按标签筛选新闻
"""

import re
from collections import Counter

# 标签规则定义
TAG_RULES = {
    '价格上涨': ['上涨', '涨价', '走高', '上扬', '攀升', '猛涨', '大涨', '暴涨', '跳涨', '劲涨'],
    '价格下跌': ['下跌', '跌价', '下滑', '下降', '回落', '暴跌', '大跌', '狂跌'],
    '价格稳定': ['稳定', '平稳', '持平', '不变', '维稳'],
    '走货情况': ['走货', '交易', '购销', '销售', '出货', '成交', '交易量'],
    '库存情况': ['库存', '库存充足', '库存紧张', '库存积压', '库存消化'],
    '供需情况': ['供应', '需求', '供不应求', '供过于求', '供需平衡'],
    '产新动态': ['产新', '产新期', '新货', '新产', '采收', '收获'],
    '种植情况': ['种植', '播种', '种植面积', '栽培', '田间管理'],
    '天气影响': ['天气', '气候', '降雨', '干旱', '高温', '低温', '霜冻', '冰雹'],
    '政策法规': ['政策', '法规', '标准', '监管', '认证', 'GAP', 'GMP'],
    '品质质量': ['质量', '品质', '规格', '等级', '含量', '农残', '重金属'],
    '市场动态': ['市场', '行情', '走势', '趋势', '预测', '分析']
}

# 药材名称列表（用于识别药材相关新闻）
HERB_NAMES = [
    '黄芪', '当归', '党参', '白术', '白芍', '川芎', '茯苓', '甘草', '麦冬', '半夏',
    '枸杞', '菊花', '金银花', '连翘', '板蓝根', '地黄', '桔梗', '防风', '柴胡', '黄芩',
    '黄连', '黄柏', '苦参', '龙胆草', '何首乌', '杜仲', '厚朴', '肉桂', '五味子', '山茱萸',
    '酸枣仁', '柏子仁', '桃仁', '杏仁', '红花', '丹参', '益母草', '泽兰', '车前子', '泽泻',
    '薏苡仁', '芡实', '莲子', '山药', '百合', '玉竹', '黄精', '天麻', '灵芝', '猪苓'
]

def extract_tags(title, content):
    """从新闻标题和内容中提取标签"""
    tags = []
    full_text = (title or '') + ' ' + (content or '')
    
    # 提取价格标签
    for tag, keywords in TAG_RULES.items():
        for keyword in keywords:
            if keyword in full_text:
                tags.append(tag)
                break
    
    # 提取药材标签
    for herb_name in HERB_NAMES:
        if herb_name in full_text:
            tags.append(f'药材-{herb_name}')
    
    # 去重
    tags = list(set(tags))
    
    # 限制标签数量
    if len(tags) > 5:
        # 优先保留价格和市场相关标签
        priority_tags = ['价格上涨', '价格下跌', '价格稳定', '走货情况', '库存情况', '供需情况']
        priority_tags_in = [tag for tag in tags if tag in priority_tags]
        other_tags = [tag for tag in tags if tag not in priority_tags]
        tags = priority_tags_in + other_tags[:5 - len(priority_tags_in)]
    
    return tags

def get_tag_categories():
    """获取标签分类"""
    categories = {
        '价格相关': ['价格上涨', '价格下跌', '价格稳定'],
        '市场相关': ['走货情况', '库存情况', '供需情况', '市场动态'],
        '生产相关': ['产新动态', '种植情况', '天气影响'],
        '其他相关': ['政策法规', '品质质量']
    }
    return categories

def filter_news_by_tags(news_list, selected_tags):
    """按标签筛选新闻"""
    if not selected_tags:
        return news_list
    
    filtered_news = []
    for news in news_list:
        news_tags = news.get('tags', [])
        # 检查是否有任何一个选中的标签匹配
        if any(tag in news_tags for tag in selected_tags):
            filtered_news.append(news)
    
    return filtered_news

def enrich_news_with_tags(news_list):
    """为新闻列表添加标签"""
    for news in news_list:
        title = news.get('title', '')
        content = news.get('content', '')
        news['tags'] = extract_tags(title, content)
    return news_list

if __name__ == "__main__":
    # 测试标签提取
    test_news = [
        {
            'title': '黄芪价格上涨，市场走货加快',
            'content': '近期黄芪价格持续上涨，市场走货加快，库存紧张。'
        },
        {
            'title': '当归产新期临近，价格有所回落',
            'content': '当归产新期临近，新货即将上市，价格有所回落。'
        },
        {
            'title': '党参种植面积增加，预计供应充足',
            'content': '今年党参种植面积明显增加，预计未来供应充足。'
        }
    ]
    
    enriched_news = enrich_news_with_tags(test_news)
    for news in enriched_news:
        print(f"标题: {news['title']}")
        print(f"标签: {news['tags']}")
        print('-' * 50)
