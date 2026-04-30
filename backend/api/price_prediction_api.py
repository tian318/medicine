import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import os
from statsmodels.tsa.arima.model import ARIMA

# 配置 TensorFlow 日志级别，减少冗余输出
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# 创建输出目录
if not os.path.exists('output'):
    os.makedirs('output')

# 仅导入Prophet但增加异常处理，避免导入失败影响整体程序
try:
    from prophet import Prophet

    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    import tensorflow as tf  # type: ignore
    from tensorflow.keras.models import Sequential  # type: ignore
    from tensorflow.keras.layers import LSTM, Dense, Dropout  # type: ignore
    from tensorflow.keras.callbacks import EarlyStopping  # type: ignore
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    tf = None
    Sequential = None
    LSTM = None
    Dense = None
    Dropout = None
    EarlyStopping = None

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


def fetch_price_data(herb_name=None, specification=None, start_date=None, end_date=None):
    """从数据库获取价格数据"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
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
        if start_date:
            query += " AND recorded_at::date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND recorded_at::date <= %s"
            params.append(end_date)

        query += " ORDER BY recorded_at ASC"

        print(f"执行查询: {query}")
        print(f"参数: {params}")

        cursor.execute(query, params)
        rows = cursor.fetchall()

        print(f"查询结果: 找到{len(rows)}条记录")

        df = pd.DataFrame(rows)

        if df.empty:
            print("查询结果为空")
            return pd.DataFrame()

        # 处理百分比字段
        for col in ['week_change', 'month_change', 'year_change']:
            if col in df.columns:
                df[col] = df[col].str.rstrip('%').astype('float') / 100

        # 确保价格是数值类型
        df['price'] = pd.to_numeric(df['price'], errors='coerce')

        # 确保日期是日期时间类型
        df['recorded_at'] = pd.to_datetime(df['recorded_at'])

        # 基础数据清洗：去除价格为空/0的记录
        df = df.dropna(subset=['price'])
        df = df[df['price'] > 0]

        return df

    except Exception as e:
        print(f"获取数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


def prepare_time_series_data(df):
    """准备时间序列数据（增强版：增加异常值处理）"""
    # 按日期分组并计算平均价格
    daily_prices = df.groupby(df['recorded_at'].dt.date)['price'].mean().reset_index()
    daily_prices.columns = ['date', 'price']
    daily_prices['date'] = pd.to_datetime(daily_prices['date'])

    # 按日期排序
    daily_prices = daily_prices.sort_values('date')

    # 检查是否有缺失日期，如果有则进行插值
    date_range = pd.date_range(start=daily_prices['date'].min(), end=daily_prices['date'].max(), freq='D')
    full_date_df = pd.DataFrame({'date': date_range})
    daily_prices = full_date_df.merge(daily_prices, on='date', how='left')

    # 使用线性插值填充缺失值
    daily_prices['price'] = daily_prices['price'].interpolate(method='linear')

    # 异常值处理：使用IQR方法去除极端值
    Q1 = daily_prices['price'].quantile(0.25)
    Q3 = daily_prices['price'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # 替换异常值为边界值（避免直接删除导致数据缺失）
    daily_prices['price'] = np.where(daily_prices['price'] < lower_bound, lower_bound, daily_prices['price'])
    daily_prices['price'] = np.where(daily_prices['price'] > upper_bound, upper_bound, daily_prices['price'])

    # 最终清洗：确保无空值
    daily_prices = daily_prices.dropna(subset=['price'])

    return daily_prices


def train_arima_model(data, forecast_days=30):
    """训练ARIMA模型并预测"""
    # 尝试不同的ARIMA参数
    best_aic = float('inf')
    best_order = None
    best_model = None

    # 简化的网格搜索
    p_values = range(0, 3)
    d_values = range(0, 2)
    q_values = range(0, 3)

    for p in p_values:
        for d in d_values:
            for q in q_values:
                try:
                    model = ARIMA(data['price'], order=(p, d, q))
                    model_fit = model.fit()

                    if model_fit.aic < best_aic:
                        best_aic = model_fit.aic
                        best_order = (p, d, q)
                        best_model = model_fit
                except:
                    continue

    if best_model is None:
        # 如果所有组合都失败，使用简单的默认值
        try:
            best_model = ARIMA(data['price'], order=(1, 1, 1)).fit()
            best_order = (1, 1, 1)
        except:
            return None, None, None

    # 预测未来价格
    forecast_result = best_model.forecast(steps=forecast_days)

    # 创建预测日期
    last_date = data['date'].iloc[-1]
    forecast_dates = [last_date + timedelta(days=i + 1) for i in range(forecast_days)]

    # 创建预测数据框
    forecast_df = pd.DataFrame({
        'date': forecast_dates,
        'predicted_price': forecast_result
    })

    # 计算训练集上的评估指标
    train_pred = best_model.fittedvalues
    train_metrics = {
        'mae': mean_absolute_error(data['price'][len(data) - len(train_pred):], train_pred),
        'rmse': np.sqrt(mean_squared_error(data['price'][len(data) - len(train_pred):], train_pred)),
        'r2': r2_score(data['price'][len(data) - len(train_pred):], train_pred)
    }

    return forecast_df, best_order, train_metrics


def train_prophet_model(data, forecast_days=30):
    """训练Prophet模型并预测（终极降级版：最小化复杂度）"""
    if not PROPHET_AVAILABLE:
        print("Prophet库未安装，跳过Prophet模型训练")
        return None, None, None

    try:
        # 准备Prophet所需的数据格式
        prophet_df = data[['date', 'price']].copy()
        prophet_df.columns = ['ds', 'y']

        # 确保无空值
        prophet_df = prophet_df.dropna(subset=['ds', 'y'])

        # 数据量检查：至少需要30个数据点（提高阈值，增加稳定性）
        if len(prophet_df) < 30:
            print("数据量不足，无法训练Prophet模型")
            return None, None, None

        # 初始化极简模型（最大化兼容性）
        model = Prophet(
            yearly_seasonality=False,  # 关闭年度季节性，减少计算
            weekly_seasonality=False,
            daily_seasonality=False,
            interval_width=0.95,
            n_changepoints=2,  # 极少的变点，最小化计算
            changepoint_prior_scale=0.01
        )

        # 拟合模型（终极异常捕获）
        try:
            model.fit(prophet_df)
        except Exception as e1:
            print(f"Prophet模型训练失败，已自动跳过: {e1}")
            return None, None, None

        # 创建未来数据框
        future = model.make_future_dataframe(periods=forecast_days)

        # 预测
        forecast = model.predict(future)

        # 提取预测结果
        forecast_df = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_days).copy()
        forecast_df.columns = ['date', 'predicted_price', 'lower_bound', 'upper_bound']

        # 确保预测价格为正数
        forecast_df['predicted_price'] = np.maximum(forecast_df['predicted_price'], 0.01)
        forecast_df['lower_bound'] = np.maximum(forecast_df['lower_bound'], 0.01)
        forecast_df['upper_bound'] = np.maximum(forecast_df['upper_bound'], 0.01)

        # 计算训练集上的评估指标
        train_pred = forecast[forecast['ds'].isin(prophet_df['ds'])]['yhat'].values
        train_metrics = {
            'mae': mean_absolute_error(prophet_df['y'], train_pred),
            'rmse': np.sqrt(mean_squared_error(prophet_df['y'], train_pred)),
            'r2': r2_score(prophet_df['y'], train_pred)
        }

        return forecast_df, model, train_metrics

    except Exception as e:
        print(f"Prophet模型训练失败，已自动跳过: {e}")
        return None, None, None


def train_lstm_model(data, forecast_days=30, look_back=10):
    """训练LSTM模型并预测（修复维度不匹配错误）"""
    if not TENSORFLOW_AVAILABLE:
        print("TensorFlow库未安装，跳过LSTM模型训练")
        return None, None, None
    
    try:
        # 确保数据足够长
        if len(data) <= look_back + 5:  # 至少需要look_back+5个数据点
            print(f"数据点数量不足，LSTM模型需要至少{look_back + 5}个数据点，当前只有{len(data)}个")
            return None, None, None

        # 准备LSTM所需的数据
        prices = data['price'].values.reshape(-1, 1)

        # 归一化数据
        scaler = MinMaxScaler(feature_range=(0, 1))
        prices_scaled = scaler.fit_transform(prices)

        # 创建时间序列数据集
        X, y = [], []
        for i in range(len(prices_scaled) - look_back):
            X.append(prices_scaled[i:i + look_back, 0])
            y.append(prices_scaled[i + look_back, 0])

        X, y = np.array(X), np.array(y)
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))

        # 确保有足够的数据进行训练
        if len(X) < 10:  # 至少需要10个样本
            print("样本数量不足，无法训练LSTM模型")
            return None, None, None

        # 划分训练集和测试集
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]

        # 构建LSTM模型（优化结构，减少过拟合）
        model = Sequential()
        model.add(LSTM(50, return_sequences=True, input_shape=(look_back, 1), dropout=0.2, recurrent_dropout=0.2))
        model.add(LSTM(50, return_sequences=False, dropout=0.2, recurrent_dropout=0.2))
        model.add(Dense(25))
        model.add(Dense(1))

        # 编译模型
        model.compile(optimizer='adam', loss='mean_squared_error')

        # 训练模型（增加早停机制）
        if EarlyStopping is not None:
            early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        else:
            early_stop = None

        model.fit(
            X_train, y_train,
            epochs=100,
            batch_size=32,
            verbose=0,
            validation_data=(X_test, y_test),
            callbacks=[early_stop]
        )

        # 评估模型
        train_pred = model.predict(X_train, verbose=0)
        test_pred = model.predict(X_test, verbose=0)

        # 反归一化
        train_pred = scaler.inverse_transform(train_pred)
        y_train_inv = scaler.inverse_transform(y_train.reshape(-1, 1))
        test_pred = scaler.inverse_transform(test_pred)
        y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1))

        # 计算评估指标
        train_metrics = {
            'mae': mean_absolute_error(y_train_inv, train_pred),
            'rmse': np.sqrt(mean_squared_error(y_train_inv, train_pred)),
            'r2': r2_score(y_train_inv, train_pred)
        }

        # 预测未来价格（修复维度不匹配问题）
        last_sequence = prices_scaled[-look_back:].reshape(1, look_back, 1)
        future_predictions = []

        for _ in range(forecast_days):
            next_pred = model.predict(last_sequence, verbose=0)[0, 0]
            future_predictions.append(next_pred)

            # 修复：确保新增值的维度和原序列一致
            next_pred_reshaped = np.array(next_pred).reshape(1, 1, 1)
            last_sequence = np.append(last_sequence[:, 1:, :], next_pred_reshaped, axis=1)

        # 反归一化预测结果
        future_predictions = np.array(future_predictions).reshape(-1, 1)
        future_predictions = scaler.inverse_transform(future_predictions)

        # 确保预测价格为正数
        future_predictions = np.maximum(future_predictions, 0.01)

        # 创建预测日期
        last_date = data['date'].iloc[-1]
        forecast_dates = [last_date + timedelta(days=i + 1) for i in range(forecast_days)]

        # 创建预测数据框
        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'predicted_price': future_predictions.flatten()
        })

        return forecast_df, model, train_metrics
    except Exception as e:
        print(f"LSTM模型训练过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def train_xgboost_model(data, forecast_days=30, look_back=10):
    """训练XGBoost模型并预测（增强版：增加数据检查）"""
    try:
        # 数据量检查
        if len(data) <= look_back + 5:
            print(f"数据点数量不足，XGBoost模型需要至少{look_back + 5}个数据点")
            return None, None, None

        # 创建特征
        X, y = [], []
        prices = data['price'].values

        for i in range(len(prices) - look_back):
            X.append(prices[i:i + look_back])
            y.append(prices[i + look_back])

        if len(X) < 10:
            print("样本数量不足，无法训练XGBoost模型")
            return None, None, None

        X, y = np.array(X), np.array(y)

        # 划分训练集和测试集
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]

        # 训练XGBoost模型（增加早停）
        model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            early_stopping_rounds=10
        )

        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

        # 评估模型
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)

        # 计算评估指标
        train_metrics = {
            'mae': mean_absolute_error(y_train, train_pred),
            'rmse': np.sqrt(mean_squared_error(y_train, train_pred)),
            'r2': r2_score(y_train, train_pred)
        }

        # 预测未来价格
        last_sequence = prices[-look_back:].reshape(1, -1)
        future_predictions = []

        for _ in range(forecast_days):
            next_pred = model.predict(last_sequence)[0]
            # 确保预测价格为正数
            next_pred = max(next_pred, 0.01)
            future_predictions.append(next_pred)

            # 更新序列
            last_sequence = np.append(last_sequence[:, 1:], [[next_pred]], axis=1)

        # 创建预测日期
        last_date = data['date'].iloc[-1]
        forecast_dates = [last_date + timedelta(days=i + 1) for i in range(forecast_days)]

        # 创建预测数据框
        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'predicted_price': future_predictions
        })

        return forecast_df, model, train_metrics
    except Exception as e:
        print(f"XGBoost模型训练失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def predict_herb_price(herb_name, specification=None, forecast_days=30, start_date=None, end_date=None,
                       by_market=False):
    """预测药材价格（最终版：Prophet失败自动跳过）"""
    try:
        # 获取价格数据
        df = fetch_price_data(
            herb_name=herb_name,
            specification=specification,
            start_date=start_date,
            end_date=end_date
        )

        if df.empty:
            print(f"没有找到{herb_name}的价格数据")
            return {'success': False, 'error': '没有找到价格数据'}

        # 检查数据点数量
        if len(df) < 30:
            print(f"数据点数量不足，至少需要30个数据点，当前只有{len(df)}个")
            return {'success': False, 'error': f'数据点数量不足，至少需要30个，当前{len(df)}个'}

        # 按市场分别预测
        if by_market:
            markets = df['location'].unique().tolist()
            market_predictions = {}

            for market in markets:
                market_df = df[df['location'] == market].copy()
                if len(market_df) < 30:
                    print(f"{market}市场数据点数量不足，跳过")
                    continue

                market_ts_data = prepare_time_series_data(market_df)
                predictions = {}

                # ARIMA模型（核心保底模型）
                arima_forecast, arima_order, arima_metrics = train_arima_model(market_ts_data, forecast_days)
                if arima_forecast is not None:
                    predictions['ARIMA'] = {
                        'forecast': {
                            'date': arima_forecast['date'].dt.strftime('%Y-%m-%d').tolist(),
                            'predicted_price': arima_forecast['predicted_price'].tolist()
                        },
                        'model_params': {'order': arima_order},
                        'metrics': arima_metrics
                    }

                # Prophet模型（失败自动跳过）
                prophet_forecast, prophet_model, prophet_metrics = train_prophet_model(market_ts_data, forecast_days)
                if prophet_forecast is not None:
                    predictions['Prophet'] = {
                        'forecast': {
                            'date': prophet_forecast['date'].dt.strftime('%Y-%m-%d').tolist(),
                            'predicted_price': prophet_forecast['predicted_price'].tolist(),
                            'lower_bound': prophet_forecast['lower_bound'].tolist(),
                            'upper_bound': prophet_forecast['upper_bound'].tolist()
                        },
                        'metrics': prophet_metrics
                    }

                # LSTM模型
                lstm_forecast, lstm_model, lstm_metrics = train_lstm_model(market_ts_data, forecast_days)
                if lstm_forecast is not None:
                    predictions['LSTM'] = {
                        'forecast': {
                            'date': lstm_forecast['date'].dt.strftime('%Y-%m-%d').tolist(),
                            'predicted_price': lstm_forecast['predicted_price'].tolist()
                        },
                        'metrics': lstm_metrics
                    }

                # XGBoost模型
                xgb_forecast, xgb_model, xgb_metrics = train_xgboost_model(market_ts_data, forecast_days)
                if xgb_forecast is not None:
                    predictions['XGBoost'] = {
                        'forecast': {
                            'date': xgb_forecast['date'].dt.strftime('%Y-%m-%d').tolist(),
                            'predicted_price': xgb_forecast['predicted_price'].tolist()
                        },
                        'metrics': xgb_metrics
                    }

                # 集成模型（至少2个模型才集成）
                if len(predictions) >= 2:
                    ensemble_forecast = ensemble_predictions(predictions, None)
                    if ensemble_forecast is not None:
                        predictions['Ensemble'] = {
                            'forecast': {
                                'date': ensemble_forecast['date'].tolist(),
                                'predicted_price': ensemble_forecast['predicted_price'].tolist()
                            },
                            'weights': {model: 1 / len(predictions) for model in predictions}
                        }

                if predictions:
                    market_predictions[market] = {
                        'predictions': predictions,
                        'historical_data': {
                            'date': market_ts_data['date'].dt.strftime('%Y-%m-%d').tolist(),
                            'price': market_ts_data['price'].tolist()
                        }
                    }

            if not market_predictions:
                return {'success': False, 'error': '所有市场的数据都不足以进行预测'}

            # 保存预测结果
            save_prediction_result(herb_name, specification, market_predictions, by_market=True)

            return {
                'success': True,
                'herb_name': herb_name,
                'specification': specification,
                'forecast_days': forecast_days,
                'by_market': True,
                'market_predictions': market_predictions
            }

        else:
            # 整体预测
            ts_data = prepare_time_series_data(df)
            predictions = {}

            # ARIMA模型（核心保底模型）
            arima_forecast, arima_order, arima_metrics = train_arima_model(ts_data, forecast_days)
            if arima_forecast is not None:
                predictions['ARIMA'] = {
                    'forecast': {
                        'date': arima_forecast['date'].dt.strftime('%Y-%m-%d').tolist(),
                        'predicted_price': arima_forecast['predicted_price'].tolist()
                    },
                    'model_params': {'order': arima_order},
                    'metrics': arima_metrics
                }

            # Prophet模型（失败自动跳过）
            prophet_forecast, prophet_model, prophet_metrics = train_prophet_model(ts_data, forecast_days)
            if prophet_forecast is not None:
                predictions['Prophet'] = {
                    'forecast': {
                        'date': prophet_forecast['date'].dt.strftime('%Y-%m-%d').tolist(),
                        'predicted_price': prophet_forecast['predicted_price'].tolist(),
                        'lower_bound': prophet_forecast['lower_bound'].tolist(),
                        'upper_bound': prophet_forecast['upper_bound'].tolist()
                    },
                    'metrics': prophet_metrics
                }

            # LSTM模型
            lstm_forecast, lstm_model, lstm_metrics = train_lstm_model(ts_data, forecast_days)
            if lstm_forecast is not None:
                predictions['LSTM'] = {
                    'forecast': {
                        'date': lstm_forecast['date'].dt.strftime('%Y-%m-%d').tolist(),
                        'predicted_price': lstm_forecast['predicted_price'].tolist()
                    },
                    'metrics': lstm_metrics
                }

            # XGBoost模型
            xgb_forecast, xgb_model, xgb_metrics = train_xgboost_model(ts_data, forecast_days)
            if xgb_forecast is not None:
                predictions['XGBoost'] = {
                    'forecast': {
                        'date': xgb_forecast['date'].dt.strftime('%Y-%m-%d').tolist(),
                        'predicted_price': xgb_forecast['predicted_price'].tolist()
                    },
                    'metrics': xgb_metrics
                }

            # 集成模型
            if len(predictions) >= 2:
                ensemble_forecast = ensemble_predictions(predictions, None)
                if ensemble_forecast is not None:
                    predictions['Ensemble'] = {
                        'forecast': {
                            'date': ensemble_forecast['date'].tolist(),
                            'predicted_price': ensemble_forecast['predicted_price'].tolist()
                        },
                        'weights': {model: 1 / len(predictions) for model in predictions}
                    }

            if not predictions:
                return {'success': False, 'error': '所有模型都无法成功预测'}

            # 保存预测结果
            result_data = {
                'herb_name': herb_name,
                'specification': specification,
                'forecast_days': forecast_days,
                'by_market': False,
                'predictions': predictions,
                'historical_data': {
                    'date': ts_data['date'].dt.strftime('%Y-%m-%d').tolist(),
                    'price': ts_data['price'].tolist()
                }
            }
            save_prediction_result(herb_name, specification, result_data)

            return {
                'success': True,
                **result_data
            }

    except Exception as e:
        error_msg = f"预测过程中出错: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': error_msg}


def ensemble_predictions(predictions_dict, weights=None):
    """集成多个模型的预测结果"""
    try:
        model_names = list(predictions_dict.keys())
        if len(model_names) < 2:
            return None

        first_model = model_names[0]
        dates = predictions_dict[first_model]['forecast']['date']

        # 验证所有模型的日期长度一致
        for model in model_names:
            if len(predictions_dict[model]['forecast']['date']) != len(dates):
                print(f"{model}模型预测长度不一致，跳过集成")
                return None

        # 均等权重
        if weights is None:
            weights = {model: 1 / len(model_names) for model in model_names}

        # 计算加权平均
        ensemble_pred = np.zeros(len(dates))
        for model in model_names:
            model_pred = np.array(predictions_dict[model]['forecast']['predicted_price'])
            ensemble_pred += weights[model] * model_pred

        # 确保预测价格为正数
        ensemble_pred = np.maximum(ensemble_pred, 0.01)

        # 创建集成预测数据框
        ensemble_df = pd.DataFrame({
            'date': dates,
            'predicted_price': ensemble_pred
        })

        return ensemble_df
    except Exception as e:
        print(f"集成预测失败: {e}")
        return None


def save_prediction_result(herb_name, specification, result_data, by_market=False):
    """保存预测结果到JSON文件"""
    try:
        # 清理文件名特殊字符
        clean_herb = herb_name.replace('/', '_').replace('\\', '_')
        clean_spec = specification.replace('/', '_').replace('\\', '_') if specification else '无规格'

        filename = f"output/{clean_herb}_{clean_spec}_forecast.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        print(f"预测完成，结果已保存到 {os.path.abspath(filename)}")
    except Exception as e:
        print(f"保存预测结果失败: {e}")


def get_available_herbs():
    """获取数据库中可用的药材列表"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = """
        SELECT DISTINCT herb_name
        FROM herb_prices
        WHERE price > 0 AND price IS NOT NULL
        ORDER BY herb_name
        """

        cursor.execute(query)
        herbs = [row[0] for row in cursor.fetchall()]

        return herbs

    except Exception as e:
        print(f"获取药材列表时出错: {e}")
        return []
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


def get_specifications(herb_name):
    """获取指定药材的规格列表"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = """
        SELECT DISTINCT specification
        FROM herb_prices
        WHERE herb_name = %s AND specification IS NOT NULL AND price > 0
        ORDER BY specification
        """

        cursor.execute(query, (herb_name,))
        specifications = [row[0] for row in cursor.fetchall()]

        return specifications

    except Exception as e:
        print(f"获取规格列表时出错: {e}")
        return []
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    # 示例：预测丁香价格
    herb_name = "丁香"
    specification = "统 进口"
    forecast_days = 30

    # 获取当前日期
    current_date = datetime.now()
    start_date = (current_date - timedelta(days=365)).strftime('%Y-%m-%d')  # 用1年数据，增加稳定性
    end_date = current_date.strftime('%Y-%m-%d')

    # 执行预测
    result = predict_herb_price(
        herb_name=herb_name,
        specification=specification,
        forecast_days=forecast_days,
        start_date=start_date,
        end_date=end_date
    )

    if result.get("success", False):
        print("\n✅ 预测成功!")

        # 打印评估指标
        print("\n📊 模型评估指标:")
        if result.get('by_market', False):
            for market, market_data in result['market_predictions'].items():
                print(f"\n=== {market} ===")
                for model, data in market_data['predictions'].items():
                    if model != "Ensemble" and "metrics" in data:
                        print(f"\n{model}模型:")
                        for metric, value in data["metrics"].items():
                            print(f"  {metric}: {value:.4f}")
        else:
            for model, data in result["predictions"].items():
                if model != "Ensemble" and "metrics" in data:
                    print(f"\n{model}模型:")
                    for metric, value in data["metrics"].items():
                        print(f"  {metric}: {value:.4f}")
    else:
        print(f"\n❌ 预测失败: {result.get('error', '未知错误')}")