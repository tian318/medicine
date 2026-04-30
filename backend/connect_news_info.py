import mysql.connector
from mysql.connector import Error

class NewsInfoDB:
    def __init__(self, host="localhost", user="root", password="7#Gk@9!zLpX2&", database="zhongyaocai"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """连接到MySQL数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("成功连接到MySQL数据库")
                self.cursor = self.connection.cursor()
                return True
        except Error as e:
            print(f"连接数据库时出错: {e}")
            return False
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("数据库连接已关闭")
    
    def get_news_list(self, limit=10):
        """获取新闻列表"""
        try:
            query = "SELECT id, title, publish_time, herb_name, news_type FROM news_info1 ORDER BY publish_time DESC LIMIT %s"
            self.cursor.execute(query, (limit,))
            result = self.cursor.fetchall()
            return result
        except Error as e:
            print(f"查询新闻列表时出错: {e}")
            return []
    
    def get_news_by_id(self, news_id):
        """根据ID获取新闻详情"""
        try:
            query = "SELECT * FROM news_info1 WHERE id = %s"
            self.cursor.execute(query, (news_id,))
            result = self.cursor.fetchone()
            return result
        except Error as e:
            print(f"查询新闻详情时出错: {e}")
            return None
    
    def get_news_by_herb(self, herb_name, limit=10):
        """根据中药材名称获取相关新闻"""
        try:
            query = "SELECT id, title, publish_time, news_type FROM news_info1 WHERE herb_name LIKE %s ORDER BY publish_time DESC LIMIT %s"
            self.cursor.execute(query, (f"%{herb_name}%", limit))
            result = self.cursor.fetchall()
            return result
        except Error as e:
            print(f"查询中药材相关新闻时出错: {e}")
            return []
    
    def insert_news(self, title, publish_time, herb_name, content, news_type, market_name):
        """插入新闻数据"""
        try:
            query = """
            INSERT INTO news_info1 (title, publish_time, herb_name, content, news_type, recorded_at, market_name)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s)
            """
            self.cursor.execute(query, (title, publish_time, herb_name, content, news_type, market_name))
            self.connection.commit()
            print("新闻插入成功")
            return self.cursor.lastrowid
        except Error as e:
            print(f"插入新闻时出错: {e}")
            self.connection.rollback()
            return None
    
    def update_news(self, news_id, title=None, content=None, news_type=None):
        """更新新闻数据"""
        try:
            update_fields = []
            update_values = []
            
            if title:
                update_fields.append("title = %s")
                update_values.append(title)
            if content:
                update_fields.append("content = %s")
                update_values.append(content)
            if news_type:
                update_fields.append("news_type = %s")
                update_values.append(news_type)
            
            if update_fields:
                update_values.append(news_id)
                query = f"UPDATE news_info1 SET {', '.join(update_fields)} WHERE id = %s"
                self.cursor.execute(query, update_values)
                self.connection.commit()
                print("新闻更新成功")
                return True
            else:
                print("没有需要更新的字段")
                return False
        except Error as e:
            print(f"更新新闻时出错: {e}")
            self.connection.rollback()
            return False
    
    def delete_news(self, news_id):
        """删除新闻数据"""
        try:
            query = "DELETE FROM news_info1 WHERE id = %s"
            self.cursor.execute(query, (news_id,))
            self.connection.commit()
            print("新闻删除成功")
            return True
        except Error as e:
            print(f"删除新闻时出错: {e}")
            self.connection.rollback()
            return False

# 示例代码
if __name__ == "__main__":
    # 创建数据库连接实例
    db = NewsInfoDB()
    
    # 连接数据库
    if db.connect():
        # 获取新闻列表
        print("\n最新10条新闻:")
        news_list = db.get_news_list(10)
        for news in news_list:
            print(f"ID: {news[0]}, 标题: {news[1]}, 发布时间: {news[2]}, 中药材: {news[3]}, 类型: {news[4]}")
        
        # 示例：根据ID获取新闻详情
        if news_list:
            news_id = news_list[0][0]
            print(f"\nID为{news_id}的新闻详情:")
            news_detail = db.get_news_by_id(news_id)
            if news_detail:
                print(f"ID: {news_detail[0]}")
                print(f"标题: {news_detail[1]}")
                print(f"发布时间: {news_detail[2]}")
                print(f"中药材: {news_detail[3]}")
                print(f"内容: {news_detail[4][:100]}...")  # 只显示前100个字符
                print(f"类型: {news_detail[5]}")
                print(f"记录时间: {news_detail[6]}")
                print(f"市场名称: {news_detail[7]}")
        
        # 示例：根据中药材名称查询新闻
        herb_name = "三七"
        print(f"\n关于'{herb_name}'的新闻:")
        herb_news = db.get_news_by_herb(herb_name, 5)
        for news in herb_news:
            print(f"ID: {news[0]}, 标题: {news[1]}, 发布时间: {news[2]}, 类型: {news[3]}")
        
        # 示例：插入新闻
        # new_news_id = db.insert_news(
        #     title="测试新闻",
        #     publish_time="2026-03-11 10:00:00",
        #     herb_name="三七",
        #     content="这是一条测试新闻内容",
        #     news_type="市场动态",
        #     market_name="亳州中药材市场"
        # )
        # print(f"\n新插入的新闻ID: {new_news_id}")
        
        # 示例：更新新闻
        # if new_news_id:
        #     db.update_news(new_news_id, title="更新后的测试新闻", news_type="行业资讯")
        
        # 示例：删除新闻
        # if new_news_id:
        #     db.delete_news(new_news_id)
        
        # 关闭数据库连接
        db.disconnect()
    else:
        print("数据库连接失败")
