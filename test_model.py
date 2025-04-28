#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
# 导入LightGBM
import lightgbm as lgb
from sklearn.model_selection import train_test_split, KFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
import pickle  # 导入pickle模块用于模型序列化
import sqlite3

# 设置matplotlib中文字体支持
try:
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
except Exception as e:
    print(f"警告: 未能设置中文字体，图表中的中文可能无法正确显示: {e}")

def connect_to_database():
    """连接到数据库并获取数据"""
    try:
        # 导入数据库模块并使用应用上下文
        import models
        from models import app
        
        # 使用Flask应用上下文
        with app.app_context():
            # 使用与Flask应用相同的数据库引擎
            sql_command = 'select * from XinXi'
            df = pd.read_sql(sql_command, models.db.engine)
            print(f"从数据库加载了 {len(df)} 条记录")
            return df
    except Exception as e:
        print(f"数据库连接失败: {e}")
        # 尝试从CSV文件加载（如果数据库连接失败）
        try:
            df = pd.read_csv('data_backup.csv')
            print(f"从备份CSV加载了 {len(df)} 条记录")
            return df
        except Exception as ex:
            print(f"无法从数据库或备份文件加载数据: {ex}")
            return None

def prepare_data(df):
    """准备数据处理"""
    if df is None or len(df) == 0:
        print("没有可用数据进行处理")
        return None
    
    # 去除包含 NaN 的行并创建副本避免SettingWithCopyWarning
    df = df.dropna().copy()
    print(f"去除NaN后剩余 {len(df)} 条记录")

    # 处理无限值和剩余的NaN值
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # 确保数值列是浮点数类型
    if '分数线' in df.columns:
        df['分数线'] = pd.to_numeric(df['分数线'], errors='coerce')
    
    # 改进：使用更健壮的异常值处理方法 - 修改为均值±3倍标准差
    if '分数线' in df.columns:
        # 计算分数线的均值和标准差
        mean_score = df['分数线'].mean()
        std_score = df['分数线'].std()
        
        # 定义异常值界限
        lower_bound = mean_score - 3 * std_score
        upper_bound = mean_score + 3 * std_score
        
        # 输出异常值界限
        print(f"分数线异常值界限: 下界={lower_bound:.2f}, 上界={upper_bound:.2f}")
        
        # 标记异常值
        outliers = df[(df['分数线'] < lower_bound) | (df['分数线'] > upper_bound)]
        if len(outliers) > 0:
            print(f"检测到 {len(outliers)} 个异常值")
            
            # 更复杂的异常值处理：对异常值使用均值替换而不是边界值
            df.loc[df['分数线'] < lower_bound, '分数线'] = mean_score
            df.loc[df['分数线'] > upper_bound, '分数线'] = mean_score
            print("已将异常值替换为均值")
    
    # 再次检查并删除NaN值
    df = df.dropna().reset_index(drop=True)
    print(f"清理后剩余 {len(df)} 条记录")
    
    return df

def save_to_csv_if_needed(df):
    """将数据保存到CSV备份文件"""
    # 移除CSV备份功能，仅保留.pkl文件
    pass
    # try:
    #     if df is not None and len(df) > 0:
    #         df.to_csv('data_backup.csv', index=False, encoding='utf-8')
    #         print("数据已备份到 data_backup.csv")
    # except Exception as e:
    #     print(f"数据备份失败: {e}")

def create_time_series_features(df):
    """创建时间序列特征"""
    if df is None or len(df) == 0 or '年份' not in df.columns:
        print("没有可用数据进行时间序列特征工程")
        return df
    
    print("\n=== 开始时间序列特征工程 ===")
    df_ts = df.copy()
    
    # 尝试将年份转换为日期类型
    is_date_type = False
    try:
        if isinstance(df_ts['年份'].iloc[0], str):
            df_ts['年份'] = pd.to_datetime(df_ts['年份'])
            print("已将年份转换为日期类型")
            is_date_type = True
    except Exception as e:
        print(f"年份格式转换失败，创建数值型时间特征: {e}")
        # 确保年份是数值型
        if not pd.api.types.is_numeric_dtype(df_ts['年份']):
            try:
                df_ts['年份'] = pd.to_numeric(df_ts['年份'])
            except Exception as e:
                print(f"无法将年份转换为数值，跳过时间特征创建: {e}")
                return df
    
    # 如果是日期类型，添加日期组件特征
    if is_date_type:
        df_ts['year'] = df_ts['年份'].dt.year
        df_ts['month'] = df_ts['年份'].dt.month
        df_ts['quarter'] = df_ts['年份'].dt.quarter
        print("已创建日期型时间特征")
    
    # 按地区排序数据
    if '地区' in df_ts.columns:
        df_ts = df_ts.sort_values(['地区', '年份'])
        
        # 创建时间序列特征（适用于所有年份类型）
        if '分数线' in df_ts.columns:
            print("创建按地区分组的时间序列特征")
            # 创建滞后特征
            df_ts['分数线_滞后1年'] = df_ts.groupby('地区')['分数线'].shift(1)
            df_ts['分数线_滞后2年'] = df_ts.groupby('地区')['分数线'].shift(2)
            df_ts['分数线_滞后3年'] = df_ts.groupby('地区')['分数线'].shift(3)
            
            # 创建窗口统计特征
            df_ts['分数线_3年均值'] = df_ts.groupby('地区')['分数线'].transform(
                lambda x: x.rolling(3, min_periods=1).mean())
            df_ts['分数线_5年均值'] = df_ts.groupby('地区')['分数线'].transform(
                lambda x: x.rolling(5, min_periods=1).mean())
            df_ts['分数线_3年标准差'] = df_ts.groupby('地区')['分数线'].transform(
                lambda x: x.rolling(3, min_periods=1).std())
            df_ts['分数线_3年最大值'] = df_ts.groupby('地区')['分数线'].transform(
                lambda x: x.rolling(3, min_periods=1).max())
            df_ts['分数线_3年最小值'] = df_ts.groupby('地区')['分数线'].transform(
                lambda x: x.rolling(3, min_periods=1).min())
            
            # 创建差分特征
            df_ts['分数线_年度变化'] = df_ts.groupby('地区')['分数线'].diff()
            df_ts['分数线_年度变化率'] = df_ts.groupby('地区')['分数线'].pct_change()
            df_ts['分数线_年度加速度'] = df_ts.groupby('地区')['分数线_年度变化'].diff()
    
    # 创建与报考人数相关的时间特征
    if '报考人数' in df_ts.columns and '地区' in df_ts.columns:
        # 按年度计算平均报考人数
        df_ts['报考人数_3年均值'] = df_ts.groupby('地区')['报考人数'].transform(
            lambda x: x.rolling(3, min_periods=1).mean())
        
        # 计算报考人数的年度变化
        df_ts['报考人数_年度变化'] = df_ts.groupby('地区')['报考人数'].diff()
        df_ts['报考人数_年度变化率'] = df_ts.groupby('地区')['报考人数'].pct_change()
        
        # 竞争比计算
        if '招考人数' in df_ts.columns:
            df_ts['竞争比'] = df_ts['报考人数'] / df_ts['招考人数'].replace(0, 1)  # 避免除零
            df_ts['竞争比_3年均值'] = df_ts.groupby('地区')['竞争比'].transform(
                lambda x: x.rolling(3, min_periods=1).mean())
            df_ts['竞争比_年度变化'] = df_ts.groupby('地区')['竞争比'].diff()
    
    # 填充缺失值
    numeric_cols = df_ts.select_dtypes(include=['float64', 'int64']).columns
    df_ts[numeric_cols] = df_ts[numeric_cols].fillna(df_ts[numeric_cols].mean())
    
    # 检查是否成功创建了时间特征
    time_features = [col for col in df_ts.columns if '滞后' in col or '均值' in col or '变化' in col or '标准差' in col]
    print(f"创建了 {len(time_features)} 个时间序列特征: {', '.join(time_features[:5])}...")
    
    print("=== 时间序列特征工程完成 ===\n")
    return df_ts

def get_feature_list(df_clean):
    """获取特征列表"""
    # 基础特征
    features = []
    for col in ['地区_encoded', '部门名称_encoded', '职位_encoded', 
                '学历_encoded', '专业_encoded', '招考人数', '报考人数']:
        if col in df_clean.columns:
            features.append(col)
    
    # 添加时间序列特征
    time_features = [col for col in df_clean.columns if '滞后' in col 
                     or '均值' in col or '变化' in col or '标准差' in col
                     or '最大值' in col or '最小值' in col or '竞争比' in col
                     or '加速度' in col]
    features.extend(time_features)
    
    return features

def train_lightgbm_model(df):
    """训练LightGBM回归模型"""
    print("\n=== 开始LightGBM模型训练 ===\n")
    
    # 创建时间序列特征
    df_clean = create_time_series_features(df)
    
    # 特征编码
    encoders = {}
    for col in ['地区', '部门名称', '职位', '学历', '专业']:
        if col in df_clean.columns:
            encoders[col] = LabelEncoder()
            df_clean[col+'_encoded'] = encoders[col].fit_transform(df_clean[col])
    
    # 获取特征列表
    features = get_feature_list(df_clean)
    print(f"使用特征: {', '.join(features[:5])}... (共{len(features)}个特征)")
    
    
    # 训练测试集分割
    X = df_clean[features]
    y = df_clean['分数线']
    
    # 使用时间序列交叉验证而不是简单随机分割
    X_train, X_test, y_train, y_test = split_data_by_time(df_clean, X, y)
    
    # 标准化数值特征
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # 训练LightGBM模型
    print("训练LightGBM模型...")
    
    # 优化LightGBM参数
    lgb_params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'n_jobs': -1,  # 使用所有CPU核心
        'min_data_in_leaf': 20,  # 防止过拟合
        'max_depth': -1,  # 不限制树的深度
        'reg_alpha': 0.1,  # L1正则化
        'reg_lambda': 0.1   # L2正则化
    }
    
    # 设置交叉验证
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    lgb_models = []
    cv_scores = []
    feature_importance_list = []
    
    # 交叉验证并保存模型
    for fold, (train_idx, val_idx) in enumerate(kf.split(X_train)):
        print(f"\n训练折叠 {fold+1}/5...")
        # 划分训练和验证集
        X_tr, X_val = X_train[train_idx], X_train[val_idx]
        y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
        
        # 创建LightGBM数据集
        train_data = lgb.Dataset(X_tr, label=y_tr)
        valid_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        # 训练LightGBM模型
        model = lgb.train(
            params=lgb_params,
            train_set=train_data,
            num_boost_round=1000,
            valid_sets=[valid_data],
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
        )
        
        # 验证集评估
        val_pred = model.predict(X_val)
        val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
        cv_scores.append(val_rmse)
        
        # 保存模型和特征重要性
        lgb_models.append(model)
        feature_importance_list.append(dict(zip(features, model.feature_importance())))
        
        print(f"折叠 {fold+1} RMSE: {val_rmse:.4f}")
    
    print(f"\n交叉验证RMSE: {np.mean(cv_scores):.4f} (±{np.std(cv_scores):.4f})")
    
    # 创建最终模型（使用全部训练数据）
    train_data = lgb.Dataset(X_train, label=y_train)
    final_model = lgb.train(
        params=lgb_params,
        train_set=train_data,
        num_boost_round=1000
    )
    
    # 测试集评估和可视化
    model_metrics = evaluate_model(final_model, X_test, y_test, features)
    
    # 保存模型为pickle格式
    model_path = save_model_as_pickle(final_model, encoders, scaler, features, model_metrics, feature_importance=model_metrics['feature_importance'])
    
    # 构建和返回结果字典
    result = {
        'model': final_model,
        'model_path': model_path,
        'encoders': encoders,
        'scaler': scaler,
        'features': features,
        'test_rmse': model_metrics['test_rmse'],
        'test_mae': model_metrics['test_mae'],
        'test_r2': model_metrics['test_r2'],
        'accuracy': model_metrics['accuracy'],
        'confidence': model_metrics['confidence'],
        'feature_importance': model_metrics['feature_importance'],
        'models': lgb_models  # 保存所有交叉验证模型
    }
    
    print("\n=== LightGBM模型训练完成 ===\n")
    return result

def split_data_by_time(df_clean, X, y):
    """根据时间序列或随机方式分割数据"""
    if '年份' in df_clean.columns:
        try:
            # 按时间排序数据
            df_sorted = df_clean.sort_values('年份')
            train_size = int(len(df_sorted) * 0.8)
            X_train = df_sorted[X.columns].iloc[:train_size]
            y_train = df_sorted['分数线'].iloc[:train_size]
            X_test = df_sorted[X.columns].iloc[train_size:]
            y_test = df_sorted['分数线'].iloc[train_size:]
            print("使用时间序列分割方法")
        except Exception as e:
            # 回退到随机分割
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            print(f"时间序列分割失败，使用随机分割方法: {e}")
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        print("使用随机分割方法")
    
    return X_train, X_test, y_train, y_test

def evaluate_model(model, X_test, y_test, features):
    """评估模型并保存可视化结果"""
    # 预测并计算指标
    test_pred = model.predict(X_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    test_mae = mean_absolute_error(y_test, test_pred)
    test_r2 = r2_score(y_test, test_pred)
    
    # 计算模型置信度 (1 - 平均相对误差)
    mape = np.mean(np.abs((y_test - test_pred) / y_test)) * 100
    confidence = 100 - mape
    
    # 输出评估指标
    print(f"\n测试集评估:")
    print(f"  RMSE: {test_rmse:.4f}")
    print(f"  MAE: {test_mae:.4f}")
    print(f"  R²: {test_r2:.4f}")
    print(f"  模型置信度: {confidence:.2f}%")
    
    # 计算特征重要性
    feature_importance = dict(zip(features, model.feature_importance()))
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # 输出特征重要性
    print("\n最重要的10个特征:")
    for feature, importance in top_features:
        print(f"  {feature}: {importance}")
    
    # 计算模型准确率 - 基于预测误差在一定阈值内的比例
    accuracy_threshold = 5.0  # 5分内算准确
    accuracy = np.mean(np.abs(y_test - test_pred) <= accuracy_threshold) * 100
    print(f"\n模型准确率（误差≤{accuracy_threshold}分）: {accuracy:.2f}%")
    
    # 返回指标
    return {
        'test_rmse': test_rmse,
        'test_mae': test_mae,
        'test_r2': test_r2,
        'confidence': confidence,
        'accuracy': accuracy,
        'feature_importance': feature_importance
    }

def generate_visualizations(model, y_test, test_pred, features):
    """生成和保存可视化图表"""
    # 该函数不再生成图表文件
    pass
    # # 1. 特征重要性图
    # plt.figure(figsize=(12, 8))
    # lgb.plot_importance(model, max_num_features=20, figsize=(12, 8))
    # plt.title('LightGBM 特征重要性')
    # plt.tight_layout()
    # plt.savefig('lgb_feature_importance.png', dpi=300)
    # print("已保存特征重要性图表到 lgb_feature_importance.png")
    # 
    # # 2. 预测与实际值对比图
    # plt.figure(figsize=(12, 8))
    # plt.scatter(y_test, test_pred, alpha=0.6)
    # plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
    # plt.xlabel('实际值')
    # plt.ylabel('预测值')
    # plt.title('LightGBM 测试集预测结果')
    # plt.tight_layout()
    # plt.savefig('lgb_test_predictions.png', dpi=300)
    # print("已保存测试集预测结果图表到 lgb_test_predictions.png")
    # 
    # # 3. 误差分布图
    # plt.figure(figsize=(12, 8))
    # errors = y_test - test_pred
    # plt.hist(errors, bins=50, alpha=0.7)
    # plt.axvline(x=0, color='r', linestyle='--')
    # plt.xlabel('预测误差')
    # plt.ylabel('频率')
    # plt.title('LightGBM 预测误差分布')
    # plt.grid(True, alpha=0.3)
    # plt.tight_layout()
    # plt.savefig('lgb_error_distribution.png', dpi=300)
    # print("已保存预测误差分布图表到 lgb_error_distribution.png")

def save_model_as_pickle(model, encoders, scaler, features, metrics, feature_importance):
    """将模型和元数据保存为pickle文件"""
    pickle_path = 'lgb_model.pkl'
    
    # 创建包含模型和元数据的字典
    model_data = {
        'model': model,
        'encoders': encoders,
        'scaler': scaler,
        'features': features,
        'metrics': {
            'test_rmse': metrics['test_rmse'],
            'test_mae': metrics['test_mae'],
            'test_r2': metrics['test_r2'],
            'accuracy': metrics['accuracy'],
            'confidence': metrics['confidence']
        },
        'feature_importance': feature_importance
    }
    
    # 保存为pickle文件
    with open(pickle_path, 'wb') as f:
        pickle.dump(model_data, f)
    print(f"已保存模型和元数据到pickle文件: {pickle_path}")
    
    return pickle_path  # 返回保存的文件路径

def load_model_from_pickle(model_path):
    try:
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        print(f"已成功从{model_path}加载模型")
        return model_data
    except Exception as e:
        print(f"加载模型时出错: {e}")
        return None

def main():
    """主函数"""
    print("\n=== 开始模型测试程序 ===\n")
    
    # 1. 加载数据
    df = connect_to_database()
    
    if df is not None and len(df) > 0:
        # 2. 备份数据
        save_to_csv_if_needed(df)
        
        # 3. 准备数据
        df = prepare_data(df)
        
        # 4. 训练LightGBM模型
        lgb_result = train_lightgbm_model(df)
        
        # 5. 展示最终结果
        print("\n=================== 最终测试结果 ===================")
        print(f"LightGBM模型置信度: {lgb_result['confidence']:.2f}%")
        print(f"LightGBM模型准确率: {lgb_result['accuracy']:.2f}%")
        print(f"RMSE: {lgb_result['test_rmse']:.4f}")
        print(f"MAE: {lgb_result['test_mae']:.4f}")
        print(f"R²: {lgb_result['test_r2']:.4f}")
        
        # 输出特征重要性
        print("\n最重要的5个特征:")
        top_features = sorted(lgb_result['feature_importance'].items(), 
                             key=lambda x: x[1], reverse=True)[:5]
        for feature, importance in top_features:
            print(f"  {feature}: {importance}")
        
        # 6. 演示如何加载和使用保存的模型(可选)
        print("\n=== 演示加载保存的模型 ===")
        if os.path.exists('lgb_model.pkl'):
            loaded_model_data = load_model_from_pickle('lgb_model.pkl')
            if loaded_model_data is not None:
                print("模型加载成功，可以用于预测")
        else:
            print("未找到保存的模型文件，请先训练模型")
        
        print("\n=== 模型测试完成 ===")
    else:
        print("无法获取数据，测试终止")

if __name__ == "__main__":
    main() 