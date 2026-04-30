import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os
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

def fetch_price_data(herb_name=None, specification=None, source=None, days=365):
    """从数据库获取价格数据"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT herb_name, specification, location, price, trend, 
               week_change, month_change, year_change, source, recorded_at
        FROM herb_prices
        WHERE recorded_at >= NOW() - INTERVAL '%s days'
        """
        
        params = [days]
        
        if herb_name:
            query += " AND herb_name = %s"
            params.append(herb_name)
        if specification:
            query += " AND specification = %s"
            params.append(specification)
        if source:
            query += " AND source = %s"
            params.append(source)
            
        query += " ORDER BY recorded_at ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows)
        
        if df.empty:
            print(f"未找到符合条件的数据")
            return None
            
        # 处理百分比字段
        for col in ['week_change', 'month_change', 'year_change']:
            if col in df.columns:
                df[col] = df[col].str.rstrip('%').astype('float') / 100
            
        # 确保价格是数值类型
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        # 确保日期是日期时间类型
        df['recorded_at'] = pd.to_datetime(df['recorded_at'])
        
        return df
        
    except Exception as e:
        print(f"获取数据时出错: {e}")
        return None
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

def prepare_time_series_data(df, herb_name, specification, source):
    """准备时间序列数据"""
    # 筛选特定药材和规格的数据
    filtered_df = df[(df['herb_name'] == herb_name) & 
                     (df['specification'] == specification) &
                     (df['source'] == source)]
    
    if filtered_df.empty:
        print(f"未找到 {herb_name} {specification} 的数据")
        return None
    
    # 按日期分组并计算平均价格
    daily_prices = filtered_df.groupby('recorded_at')['price'].mean().reset_index()
    
    # 设置日期为索引
    daily_prices.set_index('recorded_at', inplace=True)
    
    # 重采样为日频率并填充缺失值
    daily_prices = daily_prices.resample('D').mean()
    daily_prices = daily_prices.interpolate(method='linear')
    
    return daily_prices

def analyze_price_trend(price_series, window=7):
    """分析价格趋势"""
    # 计算移动平均
    ma7 = price_series.rolling(window=window).mean()
    ma30 = price_series.rolling(window=30).mean()
    
    # 计算价格变化率
    price_change = price_series.pct_change() * 100
    
    # 计算波动性
    volatility = price_series.rolling(window=window).std() / price_series.rolling(window=window).mean()
    
    # 季节性分解
    try:
        if len(price_series) >= 2 * 365:  # 至少需要两年的数据进行季节性分解
            decomposition = seasonal_decompose(price_series, model='additive', period=365)
            trend = decomposition.trend
            seasonal = decomposition.seasonal
            residual = decomposition.resid
        else:
            trend = ma30
            seasonal = None
            residual = price_series - trend
    except Exception as e:
        print(f"季节性分解失败: {e}")
        trend = ma30
        seasonal = None
        residual = price_series - trend
    
    return {
        'ma7': ma7,
        'ma30': ma30,
        'price_change': price_change,
        'volatility': volatility,
        'trend': trend,
        'seasonal': seasonal,
        'residual': residual
    }

def build_arima_model(price_series, forecast_days=30):
    """构建ARIMA模型"""
    # 尝试不同的ARIMA参数
    best_aic = float('inf')
    best_order = None
    best_model = None
    
    # 简化起见，只尝试几组参数
    p_values = [1, 2]
    d_values = [0, 1]
    q_values = [0, 1]
    
    for p in p_values:
        for d in d_values:
            for q in q_values:
                try:
                    model = ARIMA(price_series, order=(p, d, q))
                    model_fit = model.fit()
                    
                    if model_fit.aic < best_aic:
                        best_aic = model_fit.aic
                        best_order = (p, d, q)
                        best_model = model_fit
                except Exception as e:
                    continue
    
    if best_model is None:
        print("ARIMA模型拟合失败，尝试使用默认参数")
        try:
            model = ARIMA(price_series, order=(1, 1, 0))
            best_model = model.fit()
            best_order = (1, 1, 0)
        except Exception as e:
            print(f"ARIMA模型构建失败: {e}")
            return None, None
    
    print(f"最佳ARIMA参数: {best_order}")
    
    # 预测未来价格
    forecast = best_model.forecast(steps=forecast_days)
    forecast_index = pd.date_range(start=price_series.index[-1] + timedelta(days=1), periods=forecast_days)
    forecast_series = pd.Series(forecast, index=forecast_index)
    
    return best_model, forecast_series

def visualize_prediction(price_series, forecast_series, analysis_results, herb_name, specification, source):
    """可视化预测结果"""
    # 创建输出目录
    output_dir = '/root/my_graduation_project/output'
    os.makedirs(output_dir, exist_ok=True)
    
    # 设置图表样式
    plt.style.use('seaborn-v0_8')
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制历史价格
    ax.plot(price_series.index, price_series.values, label='历史价格', color='blue')
    
    # 绘制移动平均线
    ax.plot(analysis_results['ma7'].index, analysis_results['ma7'].values, label='7日移动平均', color='green', linestyle='--')
    ax.plot(analysis_results['ma30'].index, analysis_results['ma30'].values, label='30日移动平均', color='purple', linestyle='-.')
    
    # 绘制预测价格
    ax.plot(forecast_series.index, forecast_series.values, label='预测价格', color='red', linestyle='-')
    
    # 添加预测区域的阴影
    ax.axvspan(price_series.index[-1], forecast_series.index[-1], alpha=0.2, color='gray')
    
    # 添加图表标题和标签
    ax.set_title(f'{herb_name} {specification} ({source}) 价格预测', fontsize=16)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('价格', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 保存图表
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{herb_name}_{specification}_{source}_prediction.png', dpi=300)
    
    # 创建趋势分析图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # 绘制价格变化率
    ax1.plot(analysis_results['price_change'].index, analysis_results['price_change'].values, label='价格变化率(%)', color='orange')
    ax1.set_title(f'{herb_name} {specification} 价格变化率', fontsize=14)
    ax1.set_xlabel('日期', fontsize=12)
    ax1.set_ylabel('变化率(%)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # 绘制波动性
    ax2.plot(analysis_results['volatility'].index, analysis_results['volatility'].values, label='价格波动性', color='purple')
    ax2.set_title(f'{herb_name} {specification} 价格波动性', fontsize=14)
    ax2.set_xlabel('日期', fontsize=12)
    ax2.set_ylabel('波动性', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # 保存趋势分析图表
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{herb_name}_{specification}_{source}_trend_analysis.png', dpi=300)
    
    # 如果有季节性分解结果，创建季节性分解图表
    if analysis_results['seasonal'] is not None:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        
        # 绘制趋势
        ax1.plot(analysis_results['trend'].index, analysis_results['trend'].values, label='趋势', color='blue')
        ax1.set_title('趋势', fontsize=14)
        ax1.grid(True, alpha=0.3)
        
        # 绘制季节性
        ax2.plot(analysis_results['seasonal'].index, analysis_results['seasonal'].values, label='季节性', color='green')
        ax2.set_title('季节性', fontsize=14)
        ax2.grid(True, alpha=0.3)
        
        # 绘制残差
        ax3.plot(analysis_results['residual'].index, analysis_results['residual'].values, label='残差', color='red')
        ax3.set_title('残差', fontsize=14)
        ax3.grid(True, alpha=0.3)
        
        # 保存季节性分解图表
        plt.tight_layout()
        plt.savefig(f'{output_dir}/{herb_name}_{specification}_{source}_seasonal_decomposition.png', dpi=300)
    
    plt.close('all')

def predict_price(herb_name, specification, source='market', forecast_days=30):
    """预测药材价格"""
    print(f"开始预测 {herb_name} {specification} ({source}) 的价格...")
    
    # 获取价格数据
    df = fetch_price_data(herb_name, specification, source)
    if df is None:
        return None
    
    # 准备时间序列数据
    price_series = prepare_time_series_data(df, herb_name, specification, source)
    if price_series is None:
        return None
    
    print(f"获取到 {len(price_series)} 条价格记录")
    
    # 分析价格趋势
    analysis_results = analyze_price_trend(price_series)
    
    # 构建ARIMA模型
    model, forecast_series = build_arima_model(price_series, forecast_days)
    if model is None:
        return None
    
    # 可视化预测结果
    visualize_prediction(price_series, forecast_series, analysis_results, herb_name, specification, source)
    
    # 计算预测准确性指标
    if len(price_series) > 30:
        # 使用最后30天的数据作为测试集
        train = price_series[:-30]
        test = price_series[-30:]
        
        # 使用训练集构建模型
        test_model, test_forecast = build_arima_model(train, forecast_days=30)
        
        if test_model is not None:
            # 计算评估指标
            mae = mean_absolute_error(test, test_forecast[:30])
            rmse = np.sqrt(mean_squared_error(test, test_forecast[:30]))
            mape = np.mean(np.abs((test - test_forecast[:30]) / test)) * 100
            
            print("\n模型评估指标:")
            print(f"平均绝对误差 (MAE): {mae:.2f}")
            print(f"均方根误差 (RMSE): {rmse:.2f}")
            print(f"平均绝对百分比误差 (MAPE): {mape:.2f}%")
    
    # 保存预测结果
    forecast_df = pd.DataFrame({
        'date': forecast_series.index,
        'predicted_price': forecast_series.values
    })
    
    output_dir = '/root/my_graduation_project/output'
    os.makedirs(output_dir, exist_ok=True)
    forecast_df.to_csv(f'{output_dir}/{herb_name}_{specification}_{source}_forecast.csv', index=False)
    
    print(f"预测完成，结果已保存到 {output_dir}/{herb_name}_{specification}_{source}_forecast.csv")
    
    return forecast_series

def compare_models(herb_name, specification, source='market', forecast_days=30):
    """比较不同预测模型的性能"""
    print(f"开始比较 {herb_name} {specification} 的不同预测模型...")
    
    # 获取价格数据
    df = fetch_price_data(herb_name, specification, source)
    if df is None:
        return None
    
    # 准备时间序列数据
    price_series = prepare_time_series_data(df, herb_name, specification, source)
    if price_series is None:
        return None
    
    # 划分训练集和测试集
    train_size = int(len(price_series) * 0.8)
    train = price_series[:train_size]
    test = price_series[train_size:]
    
    # 创建输出目录
    output_dir = '/root/my_graduation_project/output'
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. ARIMA模型
    print("训练ARIMA模型...")
    arima_model, arima_forecast = build_arima_model(train, forecast_days=len(test))
    
    # 2. 简单移动平均模型
    print("计算移动平均预测...")
    ma_forecast = train.rolling(window=7).mean().iloc[-1]
    ma_forecast = pd.Series([ma_forecast] * len(test), index=test.index)
    
    # 3. 指数平滑模型
    print("训练指数平滑模型...")
    try:
        exp_model = ExponentialSmoothing(
            train, 
            trend='add', 
            seasonal='add', 
            seasonal_periods=30
        ).fit()
        exp_forecast = exp_model.forecast(len(test))
    except Exception as e:
        print(f"指数平滑模型训练失败: {e}")
        exp_forecast = None
    
    # 计算评估指标
    results = {}
    
    if arima_model is not None:
        arima_mae = mean_absolute_error(test, arima_forecast[:len(test)])
        arima_rmse = np.sqrt(mean_squared_error(test, arima_forecast[:len(test)]))
        results['ARIMA'] = {'MAE': arima_mae, 'RMSE': arima_rmse}
    
    ma_mae = mean_absolute_error(test, ma_forecast)
    ma_rmse = np.sqrt(mean_squared_error(test, ma_forecast))
    results['移动平均'] = {'MAE': ma_mae, 'RMSE': ma_rmse}
    
    if exp_forecast is not None:
        exp_mae = mean_absolute_error(test, exp_forecast)
        exp_rmse = np.sqrt(mean_squared_error(test, exp_forecast))
        results['指数平滑'] = {'MAE': exp_mae, 'RMSE': exp_rmse}
    
    # 打印评估结果
    print("\n模型评估结果:")
    for model_name, metrics in results.items():
        print(f"\n{model_name}:")
        for metric_name, value in metrics.items():
            print(f"  {metric_name}: {value:.4f}")
    
    # 可视化比较
    plt.figure(figsize=(12, 6))
    plt.plot(test.index, test.values, label='实际价格', color='blue', marker='o')
    
    if arima_model is not None:
        plt.plot(test.index, arima_forecast[:len(test)], label='ARIMA预测', linestyle='--')
    
    plt.plot(test.index, ma_forecast, label='移动平均预测', linestyle='-.')
    
    if exp_forecast is not None:
        plt.plot(test.index, exp_forecast, label='指数平滑预测', linestyle=':')
    
    plt.title(f'{herb_name} {specification} 不同模型预测比较', fontsize=16)
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('价格', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{herb_name}_{specification}_{source}_model_comparison.png', dpi=300)
    
    # 使用最佳模型预测未来价格
    best_model = min(results.items(), key=lambda x: x[1]['RMSE'])[0]
    print(f"\n最佳模型: {best_model}")
    
    # 使用全部数据重新训练最佳模型并预测未来
    if best_model == 'ARIMA':
        _, future_forecast = build_arima_model(price_series, forecast_days)
    elif best_model == '指数平滑' and exp_forecast is not None:
        try:
            exp_model = ExponentialSmoothing(
                price_series, 
                trend='add', 
                seasonal='add', 
                seasonal_periods=30
            ).fit()
            future_dates = pd.date_range(start=price_series.index[-1] + timedelta(days=1), periods=forecast_days)
            future_forecast = pd.Series(exp_model.forecast(forecast_days), index=future_dates)
        except Exception as e:
            print(f"使用全部数据训练指数平滑模型失败: {e}")
            _, future_forecast = build_arima_model(price_series, forecast_days)
    else:
        # 默认使用ARIMA
        _, future_forecast = build_arima_model(price_series, forecast_days)
    
    # 可视化最终预测
    plt.figure(figsize=(12, 6))
    plt.plot(price_series.index, price_series.values, label='历史价格', color='blue')
    plt.plot(future_forecast.index, future_forecast.values, label='预测价格', color='red', linestyle='--')
    plt.axvspan(price_series.index[-1], future_forecast.index[-1], alpha=0.2, color='gray')
    
    plt.title(f'{herb_name} {specification} 价格预测 (使用{best_model}模型)', fontsize=16)
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('价格', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{herb_name}_{specification}_{source}_best_model_forecast.png', dpi=300)
    
    # 保存预测结果
    forecast_df = pd.DataFrame({
        'date': future_forecast.index,
        'predicted_price': future_forecast.values,
        'model': best_model
    })
    
    forecast_df.to_csv(f'{output_dir}/{herb_name}_{specification}_{source}_best_forecast.csv', index=False)
    
    print(f"比较完成，最佳预测结果已保存到 {output_dir}/{herb_name}_{specification}_{source}_best_forecast.csv")
    
    return results, future_forecast

if __name__ == "__main__":
    print("中药材价格预测系统")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 单一模型预测")
        print("2. 多模型比较预测")
        print("3. 退出")
        
        choice = input("请输入选项 (1-3): ")
        
        if choice == '1':
            herb_name = input("请输入要预测的药材名称 (例如: 黄连): ")
            specification = input("请输入药材规格 (例如: 鸡爪统): ")
            source = input("请输入价格来源 (market 或 origin): ")
            forecast_days = int(input("请输入预测天数: "))
            
            predict_price(herb_name, specification, source, forecast_days)
            
        elif choice == '2':
            herb_name = input("请输入要预测的药材名称 (例如: 黄连): ")
            specification = input("请输入药材规格 (例如: 鸡爪统): ")
            source = input("请输入价格来源 (market 或 origin): ")
            forecast_days = int(input("请输入预测天数: "))
            
            compare_models(herb_name, specification, source, forecast_days)
            
        elif choice == '3':
            print("感谢使用中药材价格预测系统！")
            break
            
        else:
            print("无效选项，请重新输入。")