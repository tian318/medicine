from flask import Flask, jsonify, request
from flask_cors import CORS  # 解决跨域问题
import pymysql

app = Flask(__name__)
CORS(app)  # 允许跨域请求，方便Vue前端调用

# 数据库连接配置（请根据你的实际情况修改）
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # 你的数据库用户名
    'password': '123456',  # 你的数据库密码
    'database': 'zhongyaocai',  # 数据库名
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    conn = pymysql.connect(**DB_CONFIG)
    return conn

# ========== 新增登录接口 ==========
@app.route('/api/user/login', methods=['POST'])
def user_login():
    """
    用户登录接口
    请求参数：username (用户名), password (密码)
    """
    # 获取前端传递的JSON数据
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    # 校验参数是否为空
    if not username or not password:
        return jsonify({
            'code': 400,
            'message': '用户名和密码不能为空',
            'data': None
        })

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # 查询users表中是否存在该用户
        sql = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(sql, (username, password))
        user = cursor.fetchone()

        if user:
            # 登录成功
            return jsonify({
                'code': 200,
                'message': '登录成功',
                'data': {
                    'username': user['username'],
                    # 可扩展返回用户ID、角色等信息
                    'userId': user.get('id', '')
                }
            })
        else:
            # 登录失败（用户名或密码错误）
            return jsonify({
                'code': 401,
                'message': '登录失败，请先注册',
                'data': None
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'服务器错误：{str(e)}',
            'data': None
        })
    finally:
        cursor.close()
        conn.close()

# ========== 原有接口 ==========
@app.route('/api/herbs/filter', methods=['GET'])
def filter_herbs_by_initial():
    """
    按首字母筛选中药材接口
    参数: initial (可选) - 拼音首字母，如 'A', 'B'
    不传则返回所有中药材
    """
    initial = request.args.get('initial', '').upper()  # 统一转大写
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)  # 返回字典格式数据

    try:
        if initial:
            # 按拼音首字母筛选
            sql = """
                SELECT 
                    拼音首字母 AS initial,
                    药材名称 AS name,
                    拼音 AS pinyin,
                    功效 AS efficacy,
                    品种特点 AS features,
                    分布区域 AS distribution
                FROM herb_data
                WHERE 拼音首字母 = %s
                ORDER BY 药材名称 ASC
            """
            cursor.execute(sql, (initial,))
        else:
            # 返回所有中药材
            sql = """
                SELECT 
                    拼音首字母 AS initial,
                    药材名称 AS name,
                    拼音 AS pinyin,
                    功效 AS efficacy,
                    品种特点 AS features,
                    分布区域 AS distribution
                FROM herb_data
                ORDER BY 拼音首字母 ASC, 药材名称 ASC
            """
            cursor.execute(sql)

        herbs = cursor.fetchall()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': herbs,
            'total': len(herbs)
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'查询失败: {str(e)}',
            'data': []
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/herbs/count', methods=['GET'])
def get_herbs_count():
    """获取所有中药材总数"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM herb_data")
        count = cursor.fetchone()[0]
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': count
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'查询失败: {str(e)}',
            'data': 0
        })
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)