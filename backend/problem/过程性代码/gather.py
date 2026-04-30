import requests
import bs4
import pandas as pd

headers = {
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36'
    }                           #定义访问网站表头
links = []
rank_list = []
name_list = []
time_list = []
age_list = []
score_list = []
platfrom_list=[]
genre_list=[]
publisher_list=[]               #定义存储数据的列表分别为各游戏的网页链接、排名、名称、发布日期、年龄分级、Metascore评分、运行平台、游戏类型、发行商

for x in range(1,133):           #爬取排行榜中的数据不包括运行平台、游戏类型、发行商
    url = 'https://www.zyctd.com/jiage/1-0-0-'+ str(x) + '.html'
    res = requests.get(url,headers=headers)
    # print(res.text)
    db_result = bs4.BeautifulSoup(res.text, 'html.parser')
    grid = db_result.find('div',class_="price-list")
    list_item = grid.find_all('tbody')
    tds = grid.find_all('td')

    print(tds)

    list1_item = grid.find_all('div',class_="c-finderProductCard_meta")
    list2_item = grid.find_all('div',class_="c-siteReviewScore u-flexbox-column u-flexbox-alignCenter u-flexbox-justifyCenter g-text-bold c-siteReviewScore_green g-color-gray90 c-siteReviewScore_xsmall")
    for item in list_item:
        rank = item.find('span').text
        name = item.find_all('span')[1].text
        rank_list.append(rank)
        name_list.append(name)
        print("获取"+name)
    for k,item1 in enumerate(list1_item):
        time = item1.find(attrs={"class":"u-text-uppercase"})
        age = item1.text.strip()
        aage = age[-1]
        if time:
            time_list.append(time.text.replace("\n","").strip())
        if k % 2 == 0:
            if aage == '+':
                aage = age[-4:]
            elif aage not in ['E','T','M','E10+']:
                aage = '无'
            age_list.append(aage)
    for item2 in list2_item:
        score = item2.find('span').text
        score_list.append(score)
    for link in db_result.find_all('a', class_="c-finderProductCard_container g-color-gray80 u-grid"):
        href = link.get('href')
        if href:
            links.append(href)
print('排名信息获取完毕共%d条数据' %len(name_list))
print(rank_list)
print(name_list)
print("开始获取运行平台及游戏类型\n")
for y in links:                 #分别进入游戏详情爬取剩下需要的数据运行平台、游戏类型、发行商
    url = 'https://www.metacritic.com'+ str(y)
    res = requests.get(url,headers=headers)
    db_result = bs4.BeautifulSoup(res.text, 'html.parser')
    grid = db_result.find('div',class_="c-gameDetails")
    Platforms = grid.find('li',class_="c-gameDetails_listItem g-color-gray70 u-inline-block")
    Genres = grid.find('span',class_="c-globalButton_label")
    try:
        Publisher = grid.find_all('span',class_="g-outer-spacing-left-medium-fluid g-color-gray70 u-block")[1].text
    except:
        publisher = "无"
    platfrom_list.append(Platforms.text.replace("\n","").strip())
    genre_list.append(Genres.text.replace("\n","").strip())
    publisher_list.append(Publisher.replace("\n","").strip())
    print('正在获取%s..' %str(y))
print(platfrom_list)
print(genre_list)
print(publisher_list)
print("获取完成\n")

final_result = {                #将多个列表组合形成DataFrame并保存为gamerank.xlsx文件
    "游戏排名": rank_list,
    "游戏名称": name_list,
    "发布日期": time_list,
    "年龄分级": age_list,
    "Metascore评分" :score_list,
    "运行平台":platfrom_list,
    "游戏类型":genre_list,
    "发行商":publisher_list
}
final_df = pd.DataFrame(final_result)
final_df.info()
final_df.to_excel('C://Users/admin/OneDrive/桌面/R/实验/爬虫/data/gamerank.xlsx')