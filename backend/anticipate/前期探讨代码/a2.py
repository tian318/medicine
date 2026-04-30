import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint, uniform

def add_seasonal_features(df):
    """添加季节性特征"""
    # 中药材采收季节特征
    df['is_harvest_season'] = 0
    
    # 根据不同药材设置采收季节
    # 这里需要根据实际情况定义不同药材的采收季节
    herb_seasons = {
        '黄连': [9, 10, 11],  # 秋季采收
        '白术': [10, 11],     # 秋末冬初采收
        '党参': [9, 10],      # 秋季采收
        # 添加更多药材的采收季节
    }
    
    for herb, seasons in herb_seasons.items():
        mask = (df['herb_name'] == herb) & (df['recorded_at'].dt.month.isin(seasons))
        df.loc[mask, 'is_harvest_season'] = 1
    
    # 添加节气特征
    # 简化处理，实际应根据具体日期计算二十四节气
    df['is_major_solar_term'] = 0
    
    # 定义重要节气日期（简化）
    major_terms = [
        # (月, 日) 近似值
        (2, 4),   # 立春
        (5, 6),   # 立夏
        (8, 8),   # 立秋
        (11, 7),  # 立冬
    ]
    
    for month, day in major_terms:
        mask = (df['recorded_at'].dt.month == month) & (df['recorded_at'].dt.day.between(day-3, day+3))
        df.loc[mask, 'is_major_solar_term'] = 1
    
    return df

def add_market_features(df):
    """添加市场特征"""
    # 计算各市场的价格差异
    market_avg = df.groupby(['date', 'herb_name', 'specification'])['price'].transform('mean')
    df['market_price_ratio'] = df['price'] / market_avg
    
    # 计算各市场的价格波动性
    df['price_volatility'] = df.groupby(['location', 'herb_name', 'specification'])['price'].transform(
        lambda x: x.rolling(window=7, min_periods=1).std() / x.rolling(window=7, min_periods=1).mean()
    )
    
    return df

def add_text_sentiment_features(df, policy_data):
    """添加文本情感分析特征"""
    # 这里假设policy_data包含了情感分析结果
    # 实际应从文本分析结果中获取
    
    # 合并情感分析数据
    df = df.merge(
        policy_data[['date', 'positive_sentiment', 'negative_sentiment', 'neutral_sentiment']], 
        on='date', 
        how='left'
    )
    
    # 计算情感得分
    df['sentiment_score'] = df['positive_sentiment'] - df['negative_sentiment']
    
    # 填充缺失值
    df = df.fillna(method='ffill')
    
    return df

def feature_selection_and_engineering(df):
    """特征选择与工程"""
    # 标准化数值特征
    num_features = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    num_features = [f for f in num_features if f != 'price']  # 排除目标变量
    
    scaler = StandardScaler()
    df[num_features] = scaler.fit_transform(df[num_features])
    
    # 主成分分析降维（可选）
    # pca = PCA(n_components=0.95)  # 保留95%的方差
    # df_pca = pca.fit_transform(df[num_features])
    # pca_cols = [f'PC{i+1}' for i in range(df_pca.shape[1])]
    # df[pca_cols] = df_pca
    
    # 特征交互
    # 创建一些重要特征的交互项
    important_features = ['price_lag_1', 'price_rolling_mean_7', 'temperature', 'rainfall']
    for i in range(len(important_features)):
        for j in range(i+1, len(important_features)):
            feat1 = important_features[i]
            feat2 = important_features[j]
            if feat1 in df.columns and feat2 in df.columns:
                df[f'{feat1}_{feat2}_interaction'] = df[feat1] * df[feat2]
    
    return df

def build_stacked_model(df, herb_name, specification, forecast_days=30):
    """构建堆叠模型"""
    # 准备特征和目标变量
    feature_cols = [col for col in df.columns if col not in 
                   ['herb_name', 'specification', 'location', 'price', 'trend', 
                    'source', 'recorded_at', 'date']]
    
    X = df[feature_cols]
    y = df['price']
    
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 定义基础模型
    base_models = {
        'rf': RandomForestRegressor(random_state=42),
        'svr': SVR(),
        'mlp': MLPRegressor(random_state=42)
    }
    
    # 定义参数空间
    param_spaces = {
        'rf': {
            'n_estimators': randint(50, 300),
            'max_depth': randint(3, 15),
            'min_samples_split': randint(2, 20),
            'min_samples_leaf': randint(1, 10)
        },
        'svr': {
            'C': uniform(0.1, 10),
            'gamma': uniform(0.01, 1),
            'epsilon': uniform(0.01, 0.5)
        },
        'mlp': {
            'hidden_layer_sizes': [(50,), (100,), (50, 50), (100, 50)],
            'alpha': uniform(0.0001, 0.01),
            'learning_rate_init': uniform(0.001, 0.1)
        }
    }
    
    # 训练基础模型
    trained_models = {}
    base_predictions = {}
    
    for name, model in base_models.items():
        print(f"训练 {name} 模型...")
        
        # 随机搜索最佳参数
        random_search = RandomizedSearchCV(
            estimator=model,
            param_distributions=param_spaces[name],
            n_iter=20,
            cv=5,
            scoring='neg_mean_squared_error',
            random_state=42,
            n_jobs=-1
        )
        
        random_search.fit(X_train, y_train)
        best_model = random_search.best_estimator_
        trained_models[name] = best_model
        
        # 生成预测
        base_predictions[name] = best_model.predict(X_test)
        
        # 评估模型
        mae = mean_absolute_error(y_test, base_predictions[name])
        rmse = np.sqrt(mean_squared_error(y_test, base_predictions[name]))
        r2 = r2_score(y_test, base_predictions[name])
        
        print(f"{name} 模型评估结果:")
        print(f"  MAE: {mae:.4f}")
        print(f"  RMSE: {rmse:.4f}")
        print(f"  R²: {r2:.4f}")
    
    # 创建元特征
    meta_features = np.column_stack([base_predictions[name] for name in base_models.keys()])
    
    # 训练元模型
    meta_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    meta_model.fit(meta_features, y_test)
    
    # 生成最终预测
    final_predictions = meta_model.predict(meta_features)
    
    # 评估堆叠模型
    mae = mean_absolute_error(y_test, final_predictions)
    rmse = np.sqrt(mean_squared_error(y_test, final_predictions))
    r2 = r2_score(y_test, final_predictions)
    
    print("\n堆叠模型评估结果:")
    print(f"  MAE: {mae:.4f}")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  R²: {r2:.4f}")
    
    # 预测未来价格
    future_predictions = []
    last_row = X.iloc[-1:].copy()
    
    for i in range(forecast_days):
        # 使用基础模型生成预测
        base_preds = {}
        for name, model in trained_models.items():
            base_preds[name] = model.predict(last_row)[0]
        
        # 使用元模型生成最终预测
        meta_input = np.array([[base_preds[name] for name in base_models.keys()]])
        next_price = meta_model.predict(meta_input)[0]
        
        future_predictions.append(next_price)
        
        # 更新特征用于下一次预测
        # 这里需要根据实际特征进行更新
        for lag in range(30, 1, -1):
            if f'price_lag_{lag-1}' in last_row.columns:
                last_row[f'price_lag_{lag}'] = last_row[f'price_lag_{lag-1}']
        
        last_row['price_lag_1'] = next_price
        
        # 更新其他特征
        # 这里简化处理，实际应根据特征定义更新
    
    # 创建预测结果数据框
    last_date = df['date'].max()
    future_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
    forecast_df = pd.DataFrame({
        'date': future_dates,
        'predicted_price': future_predictions
    })
    
    return forecast_df, trained_models, meta_model

def incorporate_weather_data(df, weather_df):
    """整合气象数据"""
    # 确保日期格式一致
    df['date'] = pd.to_datetime(df['date'])
    weather_df['date'] = pd.to_datetime(weather_df['date'])
    
    # 合并数据
    merged_df = df.merge(weather_df, on='date', how='left')
    
    # 创建气象相关特征
    # 计算温度变化率
    merged_df['temp_change'] = merged_df.groupby(['herb_name', 'specification'])['temperature'].diff()
    
    # 计算降水累积量
    merged_df['rainfall_7d_sum'] = merged_df.groupby(['herb_name', 'specification'])['rainfall'].transform(
        lambda x: x.rolling(window=7, min_periods=1).sum())
    
    # 创建极端天气指标
    merged_df['extreme_temp'] = ((merged_df['temperature'] > merged_df['temperature'].quantile(0.95)) | 
                                (merged_df['temperature'] < merged_df['temperature'].quantile(0.05))).astype(int)
    
    merged_df['heavy_rain'] = (merged_df['rainfall'] > merged_df['rainfall'].quantile(0.9)).astype(int)
    
    # 填充缺失值
    merged_df = merged_df.fillna(method='ffill')
    
    return merged_df

def incorporate_policy_data(df, policy_df):
    """整合政策数据"""
    # 确保日期格式一致
    df['date'] = pd.to_datetime(df['date'])
    policy_df['date'] = pd.to_datetime(policy_df['date'])
    
    # 合并数据
    merged_df = df.merge(policy_df, on='date', how='left')
    
    # 创建政策影响滞后特征
    for lag in [1, 3, 7, 14, 30]:
        for col in ['regulation_freq', 'support_freq', 'market_control_freq']:
            if col in merged_df.columns:
                merged_df[f'{col}_lag_{lag}'] = merged_df.groupby(['herb_name', 'specification'])[col].shift(lag)
    
    # 创建政策累积影响
    for window in [7, 14, 30]:
        for col in ['regulation_freq', 'support_freq', 'market_control_freq']:
            if col in merged_df.columns:
                merged_df[f'{col}_sum_{window}d'] = merged_df.groupby(['herb_name', 'specification'])[col].transform(
                    lambda x: x.rolling(window=window, min_periods=1).sum())
    
    # 填充缺失值
    merged_df = merged_df.fillna(0)
    
    return merged_df

def detect_price_anomalies(df):
    """检测价格异常值"""
    # 计算价格的Z分数
    df['price_zscore'] = df.groupby(['herb_name', 'specification'])['price'].transform(
        lambda x: (x - x.mean()) / x.std())
    
    # 标记异常值
    df['is_price_anomaly'] = (abs(df['price_zscore']) > 3).astype(int)
    
    # 创建异常值特征
    df['recent_anomalies'] = df.groupby(['herb_name', 'specification'])['is_price_anomaly'].transform(
        lambda x: x.rolling(window=30, min_periods=1).sum())
    
    return df

def create_market_cycle_features(df):
    """创建市场周期特征"""
    # 使用傅里叶变换检测周期性
    from scipy import signal
    
    def detect_cycles(series, sampling_freq=1):
        if len(series) < 10:
            return 0
        
        # 去除趋势
        detrended = signal.detrend(series.dropna())
        
        # 计算功率谱
        freqs, psd = signal.welch(detrended, fs=sampling_freq)
        
        # 找到主要周期
        if len(psd) > 1:
            main_freq = freqs[np.argmax(psd[1:]) + 1]
            if main_freq > 0:
                return 1 / main_freq
        return 0
    
    # 按药材和规格分组
    for name, group in df.groupby(['herb_name', 'specification']):
        if len(group) >= 60:  # 需要足够的数据点
            # 检测价格周期
            cycle_length = detect_cycles(group['price'])
            
            if cycle_length > 0:
                # 创建周期特征
                herb, spec = name
                mask = (df['herb_name'] == herb) & (df['specification'] == spec)
                
                # 添加周期位置特征
                df.loc[mask, 'days_in_cycle'] = np.arange(len(group)) % int(cycle_length)
                df.loc[mask, 'cycle_position'] = np.sin(2 * np.pi * df.loc[mask, 'days_in_cycle'] / cycle_length)
                
                print(f"{herb} {spec} 检测到周期长度: {cycle_length:.1f} 天")
    
    # 填充缺失值
    df['days_in_cycle'] = df['days_in_cycle'].fillna(0)
    df['cycle_position'] = df['cycle_position'].fillna(0)
    
    return df

def advanced_price_prediction(herb_name, specification=None, forecast_days=30):
    """高级价格预测流程"""
    # 创建输出目录
    os.makedirs('/root/my_graduation_project/output', exist_ok=True)
    
    print(f"开始高级预测 {herb_name} {specification} 的价格...")
    
    # 1. 准备基础数据
    df = prepare_data_for_model(herb_name, specification)
    if df is None:
        return None
    
    # 2. 添加季节性特征
    df = add_seasonal_features(df)
    
    # 3. 添加市场特征
    df = add_market_features(df)
    
    # 4. 获取并整合气象数据
    weather_df = fetch_weather_data()
    df = incorporate_weather_data(df, weather_df)
    
    # 5. 获取并整合政策数据
    policy_df = fetch_policy_data()
    df = incorporate_policy_data(df, policy_df)
    
    # 6. 添加文本情感分析特征
    df = add_text_sentiment_features(df, policy_df)
    
    # 7. 检测价格异常值
    df = detect_price_anomalies(df)
    
    # 8. 创建市场周期特征
    df = create_market_cycle_features(df)
    
    # 9. 特征选择与工程
    df = feature_selection_and_engineering(df)
    
    print(f"高级特征工程完成，特征数量: {df.shape[1]}")
    
    # 10. 构建堆叠模型
    print("构建堆叠模型...")
    stacked_forecast, base_models, meta_model = build_stacked_model(df, herb_name, specification, forecast_days)
    
    # 11. 构建Prophet模型
    print("构建Prophet模型...")
    prophet_forecast = build_prophet_model(df, herb_name, specification, forecast_days)
    
    # 12. 构建XGBoost模型
    print("构建XGBoost模型...")
    xgboost_forecast, xgb_model = build_xgboost_model(df, herb_name, specification, forecast_days)
    
    # 13. 集成所有模型
    print("集成所有模型预测...")
    # 准备各模型预测结果
    prophet_df = prophet_forecast[['ds', 'yhat']].copy()
    prophet_df.columns = ['date', 'prophet_pred']
    prophet_df['date'] = pd.to_datetime(prophet_df['date'])
    
    xgb_df = xgboost_forecast[['date', 'predicted_price']].copy()
    xgb_df.columns = ['date', 'xgb_pred']
    
    stacked_df = stacked_forecast.copy()
    stacked_df.columns = ['date', 'stacked_pred']
    
    # 合并预测结果
    ensemble_df = prophet_df.merge(xgb_df, on='date', how='outer')
    ensemble_df = ensemble_df.merge(stacked_df, on='date', how='outer')
    
    # 加权平均 (可以通过交叉验证优化权重)
    weights = [0.3, 0.3, 0.4]  # Prophet, XGBoost, Stacked
    ensemble_df['final_pred'] = (
        weights[0] * ensemble_df['prophet_pred'].fillna(0) + 
        weights[1] * ensemble_df['xgb_pred'].fillna(0) + 
        weights[2] * ensemble_df['stacked_pred'].fillna(0)
    )
    
    # 14. 可视化最终预测结果
    plt.figure(figsize=(16, 8))
    
    # 绘制历史价格
    plt.plot(df['date'], df['price'], label='历史价格', marker='o', alpha=0.7)
    
    # 获取未来日期的预测
    future_dates = ensemble_df['date'][ensemble_df['date'] > df['date'].max()]
    
    # 绘制各模型预测结果
    plt.plot(future_dates, ensemble_df.loc[ensemble_df['date'].isin(future_dates), 'prophet_pred'], 
             label='Prophet预测', linestyle='--', alpha=0.6)
    plt.plot(future_dates, ensemble_df.loc[ensemble_df['date'].isin(future_dates), 'xgb_pred'], 
             label='XGBoost预测', linestyle='-.', alpha=0.6)
    plt.plot(future_dates, ensemble_df.loc[ensemble_df['date'].isin(future_dates), 'stacked_pred'], 
             label='堆叠模型预测', linestyle=':', alpha=0.6)
    
    # 绘制最终集成预测
    plt.plot(future_dates, ensemble_df.loc[ensemble_df['date'].isin(future_dates), 'final_pred'], 
             label='最终集成预测', linestyle='-', linewidth=2.5, color='red')
    
    # 添加预测起点标记
    plt.axvline(x=df['date'].max(), color='gray', linestyle=':', label='预测起点')
    
    # 添加图表标题和标签
    plt.title(f'{herb_name} {specification} 价格高级预测', fontsize=16)
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('价格', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # 保存图表
    plt.savefig(f'/root/my_graduation_project/output/{herb_name}_{specification}_advanced_forecast.png', dpi=300)
    
    # 15. 保存预测结果
    future_forecast = ensemble_df[ensemble_df['date'] > df['date'].max()]
    future_forecast.to_csv(f'/root/my_graduation_project/output/{herb_name}_{specification}_advanced_forecast.csv', index=False)
    
    print(f"高级预测完成，结果已保存到 /root/my_graduation_project/output/{herb_name}_{specification}_advanced_forecast.csv")
    
    # 16. 返回预测结果
    return future_forecast, base_models, meta_model, xgb_model

def analyze_feature_importance(df, models, herb_name, specification):
    """分析特征重要性"""
    # 准备特征列
    feature_cols = [col for col in df.columns if col not in 
                   ['herb_name', 'specification', 'location', 'price', 'trend', 
                    'source', 'recorded_at', 'date']]
    
    # 获取XGBoost模型的特征重要性
    xgb_model = models['xgb_model']
    xgb_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': xgb_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    # 获取随机森林模型的特征重要性
    if 'rf' in models['base_models']:
        rf_model = models['base_models']['rf']
        rf_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
    else:
        rf_importance = pd.DataFrame()
    
    # 可视化XGBoost特征重要性
    plt.figure(figsize=(12, 8))
    top_n = 20
    sns.barplot(x='importance', y='feature', data=xgb_importance.head(top_n))
    plt.title(f'{herb_name} {specification} XGBoost模型特征重要性 (Top {top_n})')
    plt.tight_layout()
    plt.savefig(f'/root/my_graduation_project/output/{herb_name}_{specification}_xgb_importance.png')
    
    # 如果有随机森林模型，也可视化其特征重要性
    if not rf_importance.empty:
        plt.figure(figsize=(12, 8))
        sns.barplot(x='importance', y='feature', data=rf_importance.head(top_n))
        plt.title(f'{herb_name} {specification} 随机森林模型特征重要性 (Top {top_n})')
        plt.tight_layout()
        plt.savefig(f'/root/my_graduation_project/output/{herb_name}_{specification}_rf_importance.png')
    
    # 返回特征重要性数据
    return {
        'xgb_importance': xgb_importance,
        'rf_importance': rf_importance if not rf_importance.empty else None
    }

def evaluate_prediction_accuracy(df, forecast, herb_name, specification):
    """评估预测准确性"""
    # 如果有真实数据可以比较
    if 'actual_price' in forecast.columns:
        # 计算评估指标
        mae = mean_absolute_error(forecast['actual_price'], forecast['final_pred'])
        rmse = np.sqrt(mean_squared_error(forecast['actual_price'], forecast['final_pred']))
        mape = np.mean(np.abs((forecast['actual_price'] - forecast['final_pred']) / forecast['actual_price'])) * 100
        r2 = r2_score(forecast['actual_price'], forecast['final_pred'])
        
        print(f"\n{herb_name} {specification} 预测准确性评估:")
        print(f"平均绝对误差 (MAE): {mae:.2f}")
        print(f"均方根误差 (RMSE): {rmse:.2f}")
        print(f"平均绝对百分比误差 (MAPE): {mape:.2f}%")
        print(f"决定系数 (R²): {r2:.4f}")
        
        # 可视化预测vs实际
        plt.figure(figsize=(14, 7))
        plt.plot(forecast['date'], forecast['actual_price'], label='实际价格', marker='o')
        plt.plot(forecast['date'], forecast['final_pred'], label='预测价格', linestyle='--')
        plt.title(f'{herb_name} {specification} 预测vs实际价格')
        plt.xlabel('日期')
        plt.ylabel('价格')
        plt.legend()
        plt.grid(True)
        plt.savefig(f'/root/my_graduation_project/output/{herb_name}_{specification}_prediction_vs_actual.png')
        
        return {
            'MAE': mae,
            'RMSE': rmse,
            'MAPE': mape,
            'R2': r2
        }
    else:
        print("无法评估预测准确性：缺少实际价格数据")
        return None

if __name__ == "__main__":
    # 导入必要的库
    import os
    import matplotlib.pyplot as plt
    import seaborn as sns
    from datetime import timedelta
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    import xgboost as xgb
    
    # 创建输出目录
    os.makedirs('/root/my_graduation_project/output', exist_ok=True)
    
    # 示例：预测黄连价格
    herb_name = "黄连"
    specification = "鸡爪统"
    forecast_days = 60
    
    # 运行高级预测
    forecast, base_models, meta_model, xgb_model = advanced_price_prediction(
        herb_name, specification, forecast_days)
    
    # 分析特征重要性
    models = {
        'base_models': base_models,
        'meta_model': meta_model,
        'xgb_model': xgb_model
    }
    
    importance_analysis = analyze_feature_importance(
        prepare_data_for_model(herb_name, specification), models, herb_name, specification)
    
    # 打印预测结果
    if forecast is not None:
        print("\n未来30天价格预测:")
        print(forecast[['date', 'final_pred']].head(30))