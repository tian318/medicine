import requests
import bs4
import pandas as pd
import datetime

# try:
    # 获取当前日期
current_date = datetime.date.today()
print(current_date)
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36'
}  # 定义访问网站表头

# 定义存储数据的列表
data = []

# 定义列名
columns = ["名称", "规格", "市场", "近期价格", "走势", "周涨跌", "月涨跌", "年涨跌"]

# 改进后的代码，开始爬取数据
for x in range(1,37):  # 假设我们要爬取前两页的数据
    url = 'https://www.zyctd.com/jiage/8-0-0-' + str(x) + '.html'
    res = requests.get(url, headers=headers)
    db_result = bs4.BeautifulSoup(res.text, 'html.parser')
    grid = db_result.find('div', class_="price-list")
    print("正在爬取%d页数据" % x) # 打印当前爬取的页数
    # 使用find_all找到所有包含数据的行
    rows = grid.find_all('tr')[1:]  # 跳过表头行

    for row in rows:
        tds = row.find_all('td')
        row_data = []
        for td in tds:
            # 跳过价格图标列
            if td.find('img'):
                continue
            # 提取名称和规格时，从title属性中获取完整内容
            if td.find('a'):
                a_tag = td.find('a')
                row_data.append(a_tag['title'].strip() if 'title' in a_tag.attrs else a_tag.text.strip())
            else:
                row_data.append(td.text.strip())
        
        # 当行数据达到列数时，添加到数据列表
        if len(row_data) == len(columns):
            data.append(row_data)

# 创建DataFrame
df = pd.DataFrame(data, columns=columns)
df.info()

# 保存数据
df.to_csv('/root/my_graduation_project/data/' + str(current_date) +'产地价格.csv', index=False, encoding='utf-8')
# except:
#     print("代码报错，new2")