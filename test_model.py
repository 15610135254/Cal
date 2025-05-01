#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
# 改为导入简单模型
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import VotingRegressor
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
import pickle  # 导入pickle模块用于模型序列化
# 不再使用SQLite
# import sqlite3

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
    
    # 改进：使用更精确的异常值处理方法 - IQR方法
    if '分数线' in df.columns:
        Q1 = df['分数线'].quantile(0.25)
        Q3 = df['分数线'].quantile(0.75)
        IQR = Q3 - Q1
        
        # 定义异常值界限
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # 输出异常值界限
        print(f"分数线异常值界限(IQR方法): 下界={lower_bound:.2f}, 上界={upper_bound:.2f}")
        
        # 标记异常值
        outliers = df[(df['分数线'] < lower_bound) | (df['分数线'] > upper_bound)]
        if len(outliers) > 0:
            print(f"检测到 {len(outliers)} 个异常值")
            
            # 使用分位数替换而不是均值
            df.loc[df['分数线'] < lower_bound, '分数线'] = Q1
            df.loc[df['分数线'] > upper_bound, '分数线'] = Q3
            print("已将异常值替换为对应四分位数")
    
    # 再次检查并删除NaN值
    df = df.dropna().reset_index(drop=True)
    print(f"清理后剩余 {len(df)} 条记录")
    
    return df

def save_to_csv_if_needed(df):
    """将数据保存到CSV备份文件"""
    # 移除CSV备份功能，仅保留.pkl文件
    pass

def create_basic_features(df):
    """创建简单的时间序列特征"""
    if df is None or len(df) == 0 or '年份' not in df.columns:
        print("没有可用数据进行特征工程")
        return df
    
    print("\n=== 开始基础特征工程 ===")
    df_ts = df.copy()
    
    # 尝试将年份转换为数值型
    try:
        if not pd.api.types.is_numeric_dtype(df_ts['年份']):
            df_ts['年份'] = pd.to_numeric(df_ts['年份'])
            print("已将年份转换为数值类型")
    except Exception as e:
        print(f"年份格式转换失败: {e}")
    
    # 按地区排序数据
    if '地区' in df_ts.columns:
        df_ts = df_ts.sort_values(['地区', '年份'])
        
        # 创建增强的时间序列特征
        if '分数线' in df_ts.columns:
            print("创建增强的时间序列特征")
            # 创建滞后特征
            df_ts['分数线_上一年'] = df_ts.groupby('地区')['分数线'].shift(1)
            df_ts['分数线_前年'] = df_ts.groupby('地区')['分数线'].shift(2)
            
            # 创建移动平均特征
            df_ts['分数线_3年平均'] = df_ts.groupby('地区')['分数线'].transform(
                lambda x: x.rolling(3, min_periods=1).mean())
            df_ts['分数线_5年平均'] = df_ts.groupby('地区')['分数线'].transform(
                lambda x: x.rolling(5, min_periods=1).mean())
            
            # 创建趋势特征
            df_ts['分数线_3年趋势'] = df_ts['分数线'] - df_ts['分数线_3年平均']
            df_ts['分数线_同比增长'] = (df_ts['分数线'] - df_ts['分数线_上一年']) / df_ts['分数线_上一年']
    
    # 创建与报考相关的增强特征
    if '报考人数' in df_ts.columns and '招考人数' in df_ts.columns:
        # 计算基础竞争比
        df_ts['竞争比'] = df_ts['报考人数'] / df_ts['招考人数'].replace(0, 1)
        
        # 计算地区平均竞争比
        df_ts['地区平均竞争比'] = df_ts.groupby('地区')['竞争比'].transform('mean')
        
        # 计算相对竞争压力
        df_ts['相对竞争压力'] = df_ts['竞争比'] / df_ts['地区平均竞争比']
    
    # 填充缺失值
    numeric_cols = df_ts.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        if df_ts[col].isnull().any():
            # 对时间序列特征使用前向填充
            if '分数线' in col or '竞争' in col:
                df_ts[col] = df_ts.groupby('地区')[col].fillna(method='ffill')
            # 其他特征使用中位数填充
            df_ts[col] = df_ts[col].fillna(df_ts[col].median())
    
    # 检查是否成功创建了时间特征
    new_features = [col for col in df_ts.columns if col not in df.columns]
    print(f"创建了 {len(new_features)} 个新特征: {', '.join(new_features)}")
    
    print("=== 基础特征工程完成 ===\n")
    return df_ts

def get_feature_list(df_clean):
    """获取特征列表"""
    # 基础特征
    features = []
    for col in ['地区_encoded', '部门名称_encoded', '职位_encoded', 
                '学历_encoded', '专业_encoded', '招考人数', '报考人数', '年份']:
        if col in df_clean.columns:
            features.append(col)
    
    # 添加创建的特征
    new_features = [col for col in df_clean.columns if 
                   '上一年' in col or '平均' in col or '竞争比' in col]
    features.extend(new_features)
    
    return features

def train_simple_models(df):
    """训练简单的回归模型组合"""
    print("\n=== 开始简单模型训练 ===\n")
    
    # 创建基本特征
    df_clean = create_basic_features(df)
    
    # 特征编码
    encoders = {}
    for col in ['地区', '部门名称', '职位', '学历', '专业']:
        if col in df_clean.columns:
            encoders[col] = LabelEncoder()
            df_clean[col+'_encoded'] = encoders[col].fit_transform(df_clean[col])
    
    # 获取特征列表
    features = get_feature_list(df_clean)
    print(f"使用特征: {', '.join(features)}")
    
    # 训练测试集分割
    X = df_clean[features]
    y = df_clean['分数线']
    
    # 使用简单的随机分割
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"训练集: {X_train.shape[0]} 条记录, 测试集: {X_test.shape[0]} 条记录")
    
    # 标准化数值特征
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 创建简单模型
    print("训练线性回归模型...")
    lr_model = LinearRegression()
    lr_model.fit(X_train_scaled, y_train)
    
    print("训练决策树模型...")
    dt_model = DecisionTreeRegressor(max_depth=5, random_state=42)  # 限制深度，防止过拟合
    dt_model.fit(X_train_scaled, y_train)
    
    # 创建组合模型 (简单平均)
    ensemble_model = VotingRegressor([
        ('lr', lr_model),
        ('dt', dt_model)
    ])
    ensemble_model.fit(X_train_scaled, y_train)
    
    # 评估各个模型
    models = {
        "线性回归": lr_model,
        "决策树(深度=5)": dt_model,
        "组合模型": ensemble_model
    }
    
    print("\n各模型表现:")
    best_model = None
    best_score = -float('inf')
    
    for name, model in models.items():
        # 训练集评分
        train_pred = model.predict(X_train_scaled)
        train_r2 = r2_score(y_train, train_pred)
        
        # 测试集评分
        test_pred = model.predict(X_test_scaled)
        test_r2 = r2_score(y_test, test_pred)
        test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
        
        # 计算模型置信度 (1 - 平均相对误差)
        mape = np.mean(np.abs((y_test - test_pred) / y_test)) * 100
        confidence = 100 - mape
        
        print(f"{name}:")
        print(f"  训练集 R²: {train_r2:.4f}")
        print(f"  测试集 R²: {test_r2:.4f}")
        print(f"  测试集 RMSE: {test_rmse:.4f}")
        print(f"  模型置信度: {confidence:.2f}%")
        
        # 记录最佳模型
        if test_r2 > best_score:
            best_score = test_r2
            best_model = model
    
    # 使用最佳模型进行特征重要性分析和最终评估
    if best_model is models["决策树(深度=5)"]:
        # 决策树有特征重要性
        feature_importance = dict(zip(features, best_model.feature_importances_))
    else:
        # 线性回归使用系数绝对值作为特征重要性
        if best_model is models["线性回归"]:
            feature_importance = dict(zip(features, np.abs(best_model.coef_)))
        else:
            # 组合模型使用决策树部分的特征重要性
            feature_importance = dict(zip(features, models["决策树(深度=5)"].feature_importances_))
    
    # 输出特征重要性
    print("\n最重要的5个特征:")
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
    for feature, importance in top_features:
        print(f"  {feature}: {importance}")
    
    # 计算最佳模型的最终测试集性能
    final_pred = best_model.predict(X_test_scaled)
    final_rmse = np.sqrt(mean_squared_error(y_test, final_pred))
    final_mae = mean_absolute_error(y_test, final_pred)
    final_r2 = r2_score(y_test, final_pred)
    
    # 计算模型准确率 - 基于预测误差在一定阈值内的比例
    accuracy_threshold = 5.0  # 5分内算准确
    accuracy = np.mean(np.abs(y_test - final_pred) <= accuracy_threshold) * 100
    
    # 计算置信度
    mape = np.mean(np.abs((y_test - final_pred) / y_test)) * 100
    confidence = 100 - mape
    
    # 保存最佳模型
    model_name = [name for name, model in models.items() if model is best_model][0]
    print(f"\n最佳模型: {model_name}")
    
    # 保存模型为pickle格式
    model_data = {
        'model': best_model,
        'model_name': model_name,
        'encoders': encoders,
        'scaler': scaler,
        'features': features,
        'metrics': {
            'test_rmse': final_rmse,
            'test_mae': final_mae,
            'test_r2': final_r2,
            'accuracy': accuracy,
            'confidence': confidence
        },
        'feature_importance': feature_importance
    }
    
    with open('simple_model.pkl', 'wb') as f:
        pickle.dump(model_data, f)
    print(f"已保存最佳模型到 simple_model.pkl")
    
    print("\n=== 简单模型训练完成 ===\n")
    return model_data

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
    print("\n=== 开始使用已保存的模型进行预测 ===\n")
    
    # 1. 加载数据
    df = connect_to_database()
    
    if df is not None and len(df) > 0:
        # 2. 准备数据
        df = prepare_data(df)
        
        # 3. 加载已保存的模型
        try:
            model_data = load_model_from_pickle('simple_model.pkl')
            if model_data is None:
                print("无法加载模型，程序终止")
                return
            
            print(f"成功加载模型: {model_data['model_name']}")
            
            # 4. 创建特征
            df = create_basic_features(df)
            
            # 5. 对分类特征进行编码
            for col, encoder in model_data['encoders'].items():
                if col in df.columns:
                    print(f"编码特征: {col}")
                    df[col+'_encoded'] = encoder.transform(df[col])
            
            # 6. 准备预测数据
            features = model_data['features']
            print(f"\n使用特征: {', '.join(features)}")
            
            X = df[features]
            y = df['分数线']
            
            # 7. 标准化数据
            X_scaled = model_data['scaler'].transform(X)
            
            # 8. 进行预测
            predictions = model_data['model'].predict(X_scaled)
            
            # 9. 计算预测指标
            rmse = np.sqrt(mean_squared_error(y, predictions))
            mae = mean_absolute_error(y, predictions)
            r2 = r2_score(y, predictions)
            
            # 计算准确率（5分以内的预测）
            accuracy = np.mean(np.abs(y - predictions) <= 5.0) * 100
            
            # 计算置信度
            mape = np.mean(np.abs((y - predictions) / y)) * 100
            confidence = 100 - mape
            
            # 10. 输出结果
            print("\n=================== 预测结果 ===================")
            print(f"模型名称: {model_data['model_name']}")
            print(f"模型置信度: {confidence:.2f}%")
            print(f"模型准确率: {accuracy:.2f}%")
            print(f"RMSE: {rmse:.4f}")
            print(f"MAE: {mae:.4f}")
            print(f"R²: {r2:.4f}")
            
            # 11. 输出特征重要性
            print("\n最重要的3个特征:")
            top_features = sorted(model_data['feature_importance'].items(), 
                                key=lambda x: x[1], reverse=True)[:3]
            for feature, importance in top_features:
                print(f"  {feature}: {importance}")
            
            # 12. 保存预测结果
            df['预测分数线'] = predictions
            df['预测误差'] = np.abs(df['分数线'] - df['预测分数线'])
            
            # 输出一些示例预测结果
            print("\n示例预测结果:")
            sample_results = df[['地区', '年份', '分数线', '预测分数线', '预测误差']].sample(5)
            print(sample_results.to_string(index=False))
            
        except Exception as e:
            print(f"模型使用过程中出错: {e}")
            import traceback
            print(traceback.format_exc())
            
        print("\n=== 预测完成 ===")
    else:
        print("无法获取数据，程序终止")

if __name__ == "__main__":
    main() 