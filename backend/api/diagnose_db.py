#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库诊断脚本 - 检查PostgreSQL数据库中的表和数据
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

# 数据库连接配置
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}

def check_database_connection():
    """检查数据库连接"""
    print("=" * 60)
    print("检查数据库连接...")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ 数据库连接成功！")
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def check_tables(conn):
    """检查数据库中的表"""
    print("\n" + "=" * 60)
    print("检查数据库中的表...")
    print("=" * 60)
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 获取所有表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        
        print(f"\n数据库中共有 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table}")
        
        # 检查关键表
        required_tables = ['herb_prices', 'herb_data', 'location_mapping', 'news_info1', 'weather_data']
        print("\n" + "-" * 60)
        print("检查关键表是否存在:")
        
        missing_tables = []
        for table in required_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - 表不存在")
                missing_tables.append(table)
        
        return tables, missing_tables
        
    except Exception as e:
        print(f"❌ 检查表失败: {e}")
        import traceback
        traceback.print_exc()
        return [], []

def check_table_data(conn, table_name):
    """检查表中的数据"""
    print(f"\n" + "-" * 60)
    print(f"检查表 {table_name} 的数据...")
    print("-" * 60)
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 检查记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()['count']
        print(f"  记录数: {count}")
        
        # 检查表结构
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        columns = cursor.fetchall()
        
        print(f"  字段数: {len(columns)}")
        print("  字段列表:")
        for col in columns:
            print(f"    - {col['column_name']} ({col['data_type']})")
        
        # 显示示例数据
        if count > 0:
            print(f"\n  示例数据（前3条）:")
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            samples = cursor.fetchall()
            for i, sample in enumerate(samples, 1):
                print(f"    记录 {i}: {dict(sample)}")
        
        return count > 0
        
    except Exception as e:
        print(f"  ❌ 检查表数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("PostgreSQL数据库诊断工具")
    print("=" * 60)
    
    # 检查连接
    conn = check_database_connection()
    if not conn:
        print("\n❌ 无法连接到数据库，诊断终止")
        sys.exit(1)
    
    try:
        # 检查表
        tables, missing_tables = check_tables(conn)
        
        # 检查每个关键表的数据
        print("\n" + "=" * 60)
        print("检查关键表的数据...")
        print("=" * 60)
        
        key_tables = ['herb_prices', 'herb_data', 'location_mapping', 'news_info1']
        for table in key_tables:
            if table in tables:
                check_table_data(conn, table)
        
        # 总结
        print("\n" + "=" * 60)
        print("诊断总结")
        print("=" * 60)
        
        if missing_tables:
            print(f"\n❌ 缺少以下关键表: {', '.join(missing_tables)}")
            print("  这些表是应用正常运行所必需的！")
        else:
            print("\n✅ 所有关键表都存在")
        
        print("\n诊断完成！")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
