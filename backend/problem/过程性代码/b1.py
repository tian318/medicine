import sqlalchemy as sa
from sqlalchemy import inspect
import pandas as pd

def get_database_info(connection_string):
    """
    获取数据库中所有表的详细信息
    
    参数:
        connection_string: 数据库连接字符串，例如 'postgresql://username:password@localhost:5432/dbname'
    
    返回:
        包含所有表信息的字典
    """
    # 创建引擎
    engine = sa.create_engine(connection_string)
    
    # 获取检查器
    inspector = inspect(engine)
    
    # 获取所有表名
    table_names = inspector.get_table_names()
    
    # 存储所有表信息的字典
    all_tables_info = {}
    
    # 遍历每个表
    for table_name in table_names:
        print(f"表名: {table_name}")
        
        # 获取表的列信息
        columns = inspector.get_columns(table_name)
        print("列信息:")
        for column in columns:
            print(f"  - {column['name']}: {column['type']} (可空: {column.get('nullable', True)})")
        
        # 获取主键信息
        pk = inspector.get_pk_constraint(table_name)
        print(f"主键: {pk['constrained_columns']}")
        
        # 获取外键信息
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            print("外键:")
            for fk in fks:
                print(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        
        # 获取索引信息
        indexes = inspector.get_indexes(table_name)
        if indexes:
            print("索引:")
            for index in indexes:
                print(f"  - {index['name']}: {index['column_names']} (唯一: {index['unique']})")
        
        print("\n" + "-"*50 + "\n")
        
        # 存储表信息
        all_tables_info[table_name] = {
            'columns': columns,
            'primary_key': pk,
            'foreign_keys': fks,
            'indexes': indexes
        }
    
    return all_tables_info

def get_table_row_counts(connection_string):
    """
    获取数据库中所有表的行数
    """
    engine = sa.create_engine(connection_string)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    row_counts = {}
    with engine.connect() as conn:
        for table_name in table_names:
            result = conn.execute(sa.text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            row_counts[table_name] = count
            print(f"表 {table_name} 有 {count} 行数据")
    
    return row_counts

# 使用示例
if __name__ == "__main__":
    # 替换为您的数据库连接字符串
    connection_string = 'postgresql://postgres:LAPTOP-UO3FERDN@localhost:5001/postgres'
    
    # 获取并打印所有表信息
    tables_info = get_database_info(connection_string)
    
    # 获取所有表的行数
    row_counts = get_table_row_counts(connection_string)
    
    # 导出数据库结构到Excel
    # export_schema_to_excel(connection_string)