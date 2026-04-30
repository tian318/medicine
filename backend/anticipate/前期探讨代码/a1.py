import pandas as pd
import numpy as np
# 数据库连接
import psycopg2
from psycopg2.extras import RealDictCursor
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from prophet import Prophet
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# 数据库连接配置
DB_CONFIG = {
     "dbname": "postgres",
    "user": "postgres",
    "password": "Zhangzetian0.",
    "host": "59.110.216.114",
    "port": "5432",
}

def fetch_price_data(herb_name=None, specification=None):
    """从数据库获取价格数据"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        # 创建游标（RealDictCursor让结果以字典返回，方便转DataFrame）
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT herb_name, specification, location, price, trend, 
               week_change, month_change, year_change, source, recorded_at
        FROM herb_prices
        WHERE source = 'market'
        """
        
        params = []
        if herb_name:
            query += " AND herb_name = %s"
            params.append(herb_name)
        if specification:
            query += " AND specification = %s"
            params.append(specification)
            
        query += " ORDER BY recorded_at ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows)
        
        # 处理百分比字段
        for col in ['week_change', 'month_change', 'year_change']:
            df[col] = df[col].str.rstrip('%').astype('float') / 100
            
        # 确保价格是数值类型
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        return df
        
    except Exception as e:
        print(f"获取数据时出错: {e}")
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

def fetch_weather_data():
    """获取气象数据（模拟）"""
    # 这里模拟获取气象数据，实际应从数据库或API获取
    date_range = pd.date_range(start='2024-01-01', end='2025-04-01', freq='D')
    weather_df = pd.DataFrame({
        'date': date_range,
        'temperature': np.random.normal(20, 5, len(date_range)),
        'rainfall': np.random.exponential(5, len(date_range)),
        'humidity': np.random.normal(60, 10, len(date_range))
    })
    return weather_df

def fetch_policy_data():
    """获取政策关键词频率数据（模拟）"""
    # 这里模拟获取政策数据，实际应从文本分析结果中获取
    date_range = pd.date_range(start='2024-01-01', end='2025-04-01', freq='D')
    policy_df = pd.DataFrame({
        'date': date_range,
        'regulation_freq': np.random.poisson(2, len(date_range)),
        'support_freq': np.random.poisson(3, len(date_range)),
        'market_control_freq': np.random.poisson(1, len(date_range))
    })
    return policy_df

def create_time_features(df):
    """创建时间特征"""
    # 确保recorded_at是日期时间类型
    df['recorded_at'] = pd.to_datetime(df['recorded_at'])
    
    # 提取日期部分作为索引
    df['date'] = df['recorded_at'].dt.date
    
    # 创建时间特征
    df['year'] = df['recorded_at'].dt.year
    df['month'] = df['recorded_at'].dt.month
    df['day'] = df['recorded_at'].dt.day
    df['dayofweek'] = df['recorded_at'].dt.dayofweek
    df['quarter'] = df['recorded_at'].dt.quarter
    df['is_month_start'] = df['recorded_at'].dt.is_month_start.astype(int)
    df['is_month_end'] = df['recorded_at'].dt.is_month_end.astype(int)
    
    return df

def create_lag_features(df, lag_days=[1, 3, 7, 14, 30]):
    """创建滞后特征"""
    # 按药材名称和规格分组
    grouped = df.groupby(['herb_name', 'specification'])
    
    for lag in lag_days:
        df[f'price_lag_{lag}'] = grouped['price'].shift(lag)
    
    return df

def create_rolling_features(df, windows=[3, 7, 14, 30]):
    """创建滑动窗口特征"""
    # 按药材名称和规格分组
    grouped = df.groupby(['herb_name', 'specification'])
    
    for window in windows:
        df[f'price_rolling_mean_{window}'] = grouped['price'].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean())
        df[f'price_rolling_std_{window}'] = grouped['price'].transform(
            lambda x: x.rolling(window=window, min_periods=1).std())
        df[f'price_rolling_max_{window}'] = grouped['price'].transform(
            lambda x: x.rolling(window=window, min_periods=1).max())
        df[f'price_rolling_min_{window}'] = grouped['price'].transform(
            lambda x: x.rolling(window=window, min_periods=1).min())
    
    return df

def merge_external_data(price_df, weather_df, policy_df):
    """合并外部数据"""
    # 确保日期格式一致
    price_df['date'] = pd.to_datetime(price_df['date'])
    weather_df['date'] = pd.to_datetime(weather_df['date'])
    policy_df['date'] = pd.to_datetime(policy_df['date'])
    
    # 合并数据
    merged_df = price_df.merge(weather_df, on='date', how='left')
    merged_df = merged_df.merge(policy_df, on='date', how='left')
    
    # 填充缺失值
    merged_df = merged_df.fillna(method='ffill')
    
    return merged_df

def prepare_data_for_model(herb_name, specification=None):
    """准备模型训练数据"""
    # 获取价格数据
    price_df = fetch_price_data(herb_name, specification)
    if price_df.empty:
        print(f"未找到{herb_name}的价格数据")
        return None
    
    # 创建时间特征
    price_df = create_time_features(price_df)
    
    # 创建滞后特征
    price_df = create_lag_features(price_df)
    
    # 创建滑动窗口特征
    price_df = create_rolling_features(price_df)
    
    # 获取外部数据
    weather_df = fetch_weather_data()
    policy_df = fetch_policy_data()
    
    # 合并所有数据
    full_df = merge_external_data(price_df, weather_df, policy_df)
    
    # 删除缺失值
    full_df = full_df.dropna()
    
    return full_df




# ... 前面的代码 ...

def build_prophet_model(df, herb_name, specification, forecast_days=30):
    """使用Prophet构建预测模型"""
    # 准备Prophet所需的数据格式
    prophet_df = df[['date', 'price']].copy()
    prophet_df.columns = ['ds', 'y']
    
    # 添加外部回归因子
    external_features = ['temperature', 'rainfall', 'humidity', 
                         'regulation_freq', 'support_freq', 'market_control_freq']
    
    # 初始化模型
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode='multiplicative'
    )
    
    # 添加外部回归因子
    for feature in external_features:
        if feature in df.columns:
            model.add_regressor(feature)
    
    # 拟合模型
    model.fit(prophet_df)
    
    # 创建未来数据框
    future = model.make_future_dataframe(periods=forecast_days)
    
    # 添加未来的外部回归因子值
    for feature in external_features:
        if feature in df.columns:
            # 这里使用简单的方法填充未来值，实际应使用更复杂的方法
            future[feature] = np.mean(df[feature])
    
    # 预测
    forecast = model.predict(future)
    
    # 可视化结果
    fig = model.plot(forecast)
    plt.title(f'{herb_name} {specification} 价格预测 (Prophet)')
    plt.savefig(f'/root/my_graduation_project/output/{herb_name}_{specification}_prophet.png')
    
    # 组件分析
    fig_comp = model.plot_components(forecast)
    plt.savefig(f'/root/my_graduation_project/output/{herb_name}_{specification}_prophet_components.png')
    
    # 返回预测结果
    return forecast




    # ... 前面的代码 ...

def build_xgboost_model(df, herb_name, specification, forecast_days=30):
    """使用XGBoost构建预测模型"""
    # 准备特征和目标变量
    feature_cols = [col for col in df.columns if col not in 
                   ['herb_name', 'specification', 'location', 'price', 'trend', 
                    'source', 'recorded_at', 'date']]
    
    X = df[feature_cols]
    y = df['price']
    
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 定义时间序列交叉验证
    tscv = TimeSeriesSplit(n_splits=5)
    
    # 定义参数网格
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.05, 0.1],
        'subsample': [0.8, 0.9, 1.0],
        'colsample_bytree': [0.8, 0.9, 1.0]
    }
    
    # 初始化XGBoost回归器
    xgb_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    
    # 使用网格搜索进行超参数调优
    grid_search = GridSearchCV(
        estimator=xgb_model,
        param_grid=param_grid,
        cv=tscv,
        scoring='neg_mean_squared_error',
        verbose=1,
        n_jobs=-1
    )
    
    # 拟合模型
    grid_search.fit(X_train, y_train)
    
    # 获取最佳模型
    best_model = grid_search.best_estimator_
    
    # 在测试集上评估模型
    y_pred = best_model.predict(X_test)
    
    # 计算评估指标
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print(f"最佳参数: {grid_search.best_params_}")
    print(f"MAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R²: {r2:.2f}")
    
    # 特征重要性可视化
    plt.figure(figsize=(10, 6))
    xgb.plot_importance(best_model, max_num_features=20)
    plt.title(f'{herb_name} {specification} 特征重要性')
    plt.savefig(f'/root/my_graduation_project/output/{herb_name}_{specification}_feature_importance.png')
    
    # 预测未来价格
    # 为简化起见，这里使用最后一行数据复制并修改日期来预测未来
    last_row = X.iloc[-1:].copy()
    future_predictions = []
    
    for i in range(forecast_days):
        # 预测下一天
        next_price = best_model.predict(last_row)[0]
        future_predictions.append(next_price)
        
        # 更新最后一行数据用于下一次预测
        # 这里需要根据实际特征进行更新，这只是一个简化示例
        for lag in range(30, 1, -1):
            if f'price_lag_{lag-1}' in last_row.columns:
                last_row[f'price_lag_{lag}'] = last_row[f'price_lag_{lag-1}']
        
        last_row['price_lag_1'] = next_price
        
        # 更新滑动平均等特征
        # 这里简化处理，实际应根据特征定义更新
    
    # 创建预测结果数据框
    last_date = df['date'].max()
    future_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
    forecast_df = pd.DataFrame({
        'date': future_dates,
        'predicted_price': future_predictions
    })
    
    # 可视化预测结果
    plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['price'], label='历史价格')
    plt.plot(forecast_df['date'], forecast_df['predicted_price'], label='预测价格', linestyle='--')
    plt.title(f'{herb_name} {specification} 价格预测 (XGBoost)')
    plt.xlabel('日期')
    plt.ylabel('价格')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'/root/my_graduation_project/output/{herb_name}_{specification}_xgboost_forecast.png')
    
    return forecast_df, best_model

def ensemble_prediction(prophet_forecast, xgboost_forecast, weights=[0.5, 0.5]):
    """集成两个模型的预测结果"""
    # 准备数据
    prophet_df = prophet_forecast[['ds', 'yhat']].copy()
    prophet_df.columns = ['date', 'prophet_pred']
    prophet_df['date'] = pd.to_datetime(prophet_df['date'])
    
    xgb_df = xgboost_forecast[['date', 'predicted_price']].copy()
    xgb_df.columns = ['date', 'xgb_pred']
    
    # 合并预测结果
    ensemble_df = prophet_df.merge(xgb_df, on='date', how='inner')
    
    # 加权平均
    ensemble_df['ensemble_pred'] = (
        weights[0] * ensemble_df['prophet_pred'] + 
        weights[1] * ensemble_df['xgb_pred']
    )
    
    return ensemble_df

def evaluate_models(df, prophet_forecast, xgboost_forecast, ensemble_forecast):
    """评估各个模型的性能"""
    # 准备实际值
    actual = df[['date', 'price']].copy()
    actual['date'] = pd.to_datetime(actual['date'])
    
    # 准备Prophet预测值
    prophet_pred = prophet_forecast[['ds', 'yhat']].copy()
    prophet_pred.columns = ['date', 'prophet_pred']
    prophet_pred['date'] = pd.to_datetime(prophet_pred['date'])
    
    # 合并数据
    eval_df = actual.merge(prophet_pred, on='date', how='inner')
    eval_df = eval_df.merge(ensemble_forecast[['date', 'xgb_pred', 'ensemble_pred']], on='date', how='inner')
    
    # 计算评估指标
    results = {}
    for model in ['prophet_pred', 'xgb_pred', 'ensemble_pred']:
        mae = mean_absolute_error(eval_df['price'], eval_df[model])
        rmse = np.sqrt(mean_squared_error(eval_df['price'], eval_df[model]))
        r2 = r2_score(eval_df['price'], eval_df[model])
        
        results[model] = {
            'MAE': mae,
            'RMSE': rmse,
            'R²': r2
        }
    
    # 打印评估结果
    print("\n模型评估结果:")
    for model, metrics in results.items():
        print(f"\n{model}:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.4f}")
    
    # 可视化比较
    plt.figure(figsize=(14, 7))
    plt.plot(eval_df['date'], eval_df['price'], label='实际价格', marker='o')
    plt.plot(eval_df['date'], eval_df['prophet_pred'], label='Prophet预测', linestyle='--')
    plt.plot(eval_df['date'], eval_df['xgb_pred'], label='XGBoost预测', linestyle='-.')
    plt.plot(eval_df['date'], eval_df['ensemble_pred'], label='集成预测', linestyle=':')
    plt.title('各模型预测结果比较')
    plt.xlabel('日期')
    plt.ylabel('价格')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'/root/my_graduation_project/output/model_comparison.png')
    
    return results, eval_df


def optimize_ensemble_weights(eval_df):
    """优化集成模型的权重"""
    best_rmse = float('inf')
    best_weights = [0.5, 0.5]
    
    for w1 in np.arange(0, 1.01, 0.05):
        w2 = 1 - w1
        eval_df['test_ensemble'] = w1 * eval_df['prophet_pred'] + w2 * eval_df['xgb_pred']
        
        rmse = np.sqrt(mean_squared_error(eval_df['price'], eval_df['test_ensemble']))
        
        if rmse < best_rmse:
            best_rmse = rmse
            best_weights = [w1, w2]
    
    print(f"最优权重: Prophet={best_weights[0]:.2f}, XGBoost={best_weights[1]:.2f}")
    print(f"最优RMSE: {best_rmse:.4f}")
    
    return best_weights

def predict_herb_price(herb_name, specification=None, forecast_days=30):
    """预测指定药材的价格"""
    print(f"开始预测 {herb_name} {specification} 的价格...")
    
    # 准备数据
    df = prepare_data_for_model(herb_name, specification)
    if df is None:
        return None
    
    print(f"数据准备完成，共 {len(df)} 条记录")
    
    # 构建Prophet模型
    print("构建Prophet模型...")
    prophet_forecast = build_prophet_model(df, herb_name, specification, forecast_days)
    
    # 构建XGBoost模型
    print("构建XGBoost模型...")
    xgboost_forecast, xgb_model = build_xgboost_model(df, herb_name, specification, forecast_days)
    
    # 初始集成预测
    print("进行集成预测...")
    ensemble_forecast = ensemble_prediction(prophet_forecast, xgboost_forecast)
    
    # 评估模型
    print("评估模型性能...")
    results, eval_df = evaluate_models(df, prophet_forecast, xgboost_forecast, ensemble_forecast)
    
    # 优化集成权重
    print("优化集成模型权重...")
    best_weights = optimize_ensemble_weights(eval_df)
    
    # 使用最优权重重新进行集成预测
    final_ensemble = ensemble_prediction(prophet_forecast, xgboost_forecast, best_weights)
    
    # 可视化最终预测结果
    plt.figure(figsize=(14, 7))
    plt.plot(df['date'], df['price'], label='历史价格', marker='o')
    
    # 获取未来日期的预测
    future_dates = final_ensemble['date'][final_ensemble['date'] > df['date'].max()]
    future_preds = final_ensemble['ensemble_pred'][final_ensemble['date'] > df['date'].max()]
    
    plt.plot(future_dates, future_preds, label='预测价格', linestyle='--', color='red')
    plt.axvline(x=df['date'].max(), color='gray', linestyle=':', label='预测起点')
    
    plt.title(f'{herb_name} {specification} 价格预测（最优集成模型）')
    plt.xlabel('日期')
    plt.ylabel('价格')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'/root/my_graduation_project/output/{herb_name}_{specification}_final_forecast.png')
    
    # 保存预测结果
    future_forecast = final_ensemble[final_ensemble['date'] > df['date'].max()]
    future_forecast.to_csv(f'/root/my_graduation_project/output/{herb_name}_{specification}_forecast.csv', index=False)
    
    print(f"预测完成，结果已保存到 /root/my_graduation_project/output/{herb_name}_{specification}_forecast.csv")
    
    return future_forecast

if __name__ == "__main__":
    # 创建输出目录
    import os
    os.makedirs('/root/my_graduation_project/output', exist_ok=True)
    
    # 示例：预测黄连价格
    herb_name = "黄连"
    specification = "鸡爪统"
    forecast_days = 60
    
    forecast = predict_herb_price(herb_name, specification, forecast_days)
    
    if forecast is not None:
        print("\n未来30天价格预测:")
        print(forecast[['date', 'ensemble_pred']].head(30))