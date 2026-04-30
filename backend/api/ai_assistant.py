from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uvicorn
import psycopg2

app = FastAPI()

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== 你的配置 ======================
ALIYUN_API_KEY = "sk-ad95b42f4522440889b72a293ae20f99"
ALIYUN_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}
# ======================================================

class ChatRequest(BaseModel):
    content: str

# ------------------------------
# 数据库连接
# ------------------------------
def connect_db():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except:
        return None

# ------------------------------
# 从数据库读取药材数据（内部使用，不展示）
# ------------------------------
def get_herb_data(herb_name):
    conn = connect_db()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT herb_name, specification, location, price, trend,
                   week_change, month_change, year_change, source, recorded_at
            FROM herb_prices
            WHERE herb_name ILIKE %s
            LIMIT 1
        """, (f"%{herb_name}%",))
        data = cur.fetchone()
        conn.close()
        return data
    except:
        conn.close()
        return None

# ------------------------------
# ✅ 核心：AI 智能分析价格 + 给出建议（只输出建议，隐藏原始数据）
# ------------------------------
def ai_analyze_price(herb_data):
    try:
        name, spec, loc, price, trend, week, month, year, source, time = herb_data

        # 把数据库数据整理成提示词，发给 AI 分析
        prompt = f"""
你是专业中药材价格分析师，请根据以下数据，给出关于药材的专业的价格分析、趋势判断、采购与投资预警建议。

药材名称：{name}
规格：{spec}
产地：{loc}
当前价格：{price}
走势：{trend}
周涨跌幅：{week}
月涨跌幅：{month}
年涨跌幅：{year}
来源市场：{source}

请直接输出：
关于近期{name}的建议：

1. 价格走势总结
（这里写价格走势总结）

2. 涨跌原因分析
（这里写涨跌原因分析）

3. 采购/出售预警建议
（这里写采购或出售的预警建议）

4. 未来趋势预判
（这里写未来趋势预判）

要求：
- 不要不变的展示原始数据
- 不要用任何格式符号（**、###、- 等）
- 语言专业，分点清晰，纯文本输出
        """

        headers = {
            "Authorization": f"Bearer {ALIYUN_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "qwen-turbo",
            "input": {
                "messages": [
                    {"role": "user", "content": prompt.strip()}
                ]
            }
        }
        resp = requests.post(ALIYUN_URL, headers=headers, json=data)
        res = resp.json()
        reply = res["output"]["text"]

        # 最后清理一遍符号，确保干净
        reply = reply.replace("**", "").replace("###", "").replace("- ", "• ").strip()
        return reply

    except Exception as e:
        print("AI分析错误：", e)
        return "⚠️ 价格分析失败，请稍后再试"

# ------------------------------
# 普通 AI 聊天（保留原来功能）
# ------------------------------
def ai_chat(content):
    try:
        headers = {
            "Authorization": f"Bearer {ALIYUN_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "qwen-turbo",
            "input": {
                "messages": [
                    {"role": "system", "content": "你是中药材AI助手，回答简洁专业，使用友好的语气，无任何格式符号，保持回复简洁明了"},
                    {"role": "user", "content": content}
                ]
            }
        }
        resp = requests.post(ALIYUN_URL, headers=headers, json=data)
        res = resp.json()
        txt = res["output"]["text"]
        return txt.replace("**", "").replace("###", "").replace("- ", "• ").strip()
    except:
        return "⚠️ AI服务暂时不可用"

# ------------------------------
# 主接口（智能判断：聊天 / 价格分析）
# ------------------------------
@app.post("/chat")
def chat(req: ChatRequest):
    try:
        text = req.content.strip()

        # 判断是否查询价格
        price_keywords = ["价格", "行情", "多少钱", "趋势", "预警", "分析", "涨", "跌", "报价"]
        if any(k in text for k in price_keywords):
            # 匹配药材
            conn = connect_db()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT DISTINCT herb_name FROM herb_prices")
                herbs = [str(row[0]) for row in cur.fetchall()]
                conn.close()

                for herb in herbs:
                    if herb in text:
                        data = get_herb_data(herb)
                        if data:
                            return {"reply": ai_analyze_price(data)}

            return {"reply": "⚠️ 未查询到该药材的价格信息"}

        # 普通聊天
        return {"reply": ai_chat(text)}

    except:
        return {"reply": "⚠️ 服务繁忙，请稍后再试"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)