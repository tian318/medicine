import pandas as pd
import mysql.connector

# 读取CSV文件
file_path_1 = '/root/my_graduation_project/data/2025-01-02产地价格.csv'  # 请替换为实际文件路径
file_path_2 = '/root/my_graduation_project/data/2025-01-02市场价格.csv'  # 请替换为实际文件路径

# 读取数据
df_origin = pd.read_csv(file_path_1)
df_market = pd.read_csv(file_path_2)

# 连接到MySQL数据库
db_connection = mysql.connector.connect(
    host="localhost",  # 替换为数据库主机地址
    user="root",  # 替换为数据库用户名
    password="7#Gk@9!zLpX2&",  # 替换为数据库密码
    database="product_prices"  # 替换为数据库名称
)

# 创建游标对象
cursor = db_connection.cursor()

# 创建Product表（如果尚未创建）
cursor.execute("""
CREATE TABLE IF NOT EXISTS Product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    spec VARCHAR(255) NOT NULL
)
""")

# 创建OriginPrice表（如果尚未创建）
cursor.execute("""
CREATE TABLE IF NOT EXISTS OriginPrice (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    price DECIMAL(10, 2),
    date DATE,
    FOREIGN KEY (product_id) REFERENCES Product(id)
)
""")

# 创建MarketPrice表（如果尚未创建）
cursor.execute("""
CREATE TABLE IF NOT EXISTS MarketPrice (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    price DECIMAL(10, 2),
    market VARCHAR(255),
    date DATE,
    FOREIGN KEY (product_id) REFERENCES Product(id)
)
""")

# 提交表创建操作
db_connection.commit()

# 将产品信息插入Product表（避免重复插入）
product_data = [(name, spec) for name, spec in zip(df_origin['名称'], df_origin['规格'])]
cursor.executemany("INSERT IGNORE INTO Product (name, spec) VALUES (%s, %s)", product_data)

# 提交产品信息数据
db_connection.commit()

# 将产地价格数据插入OriginPrice表
for _, row in df_origin.iterrows():
    cursor.execute("""
    INSERT INTO OriginPrice (product_id, price, date) 
    SELECT id, %s, %s FROM Product WHERE name = %s AND spec = %s
    """, (row['近期价格'], '2025-01-02', row['名称'], row['规格']))

# 将市场价格数据插入MarketPrice表
for _, row in df_market.iterrows():
    cursor.execute("""
    INSERT INTO MarketPrice (product_id, price, market, date) 
    SELECT id, %s, %s, %s FROM Product WHERE name = %s AND spec = %s
    """, (row['近期价格'], row['市场'], '2025-01-02', row['名称'], row['规格']))

# 提交所有数据插入
db_connection.commit()

# 关闭数据库连接
cursor.close()
db_connection.close()

print("数据已成功导入到MySQL数据库！")
