# !/usr/bin/env python
# _*_ coding: utf-8 _*_
import random

from flask import Flask, request, render_template,jsonify,abort,session,redirect, url_for
import os
import models
from models import app
import time
from sqlalchemy import or_,and_
import pandas
import numpy as np
import datetime
from flask_security import Security, SQLAlchemySessionUserDatastore, \
    UserMixin, RoleMixin, login_required, auth_token_required, http_auth_required,current_user

user_datastore = SQLAlchemySessionUserDatastore(models.db.session, models.User, models.Role)
security = Security(app, user_datastore)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():#主页
    uuid = current_user.is_anonymous
    if uuid:
        return redirect(url_for('logins'))
    if request.method == 'GET':
        results = models.XinXi.query.all()[:1000]
        return render_template('index.html',**locals())

import jieba
import pandas as pd
@app.route('/keshihua', methods=['GET', 'POST'])
def keshihua():#主页
    uuid = current_user.is_anonymous
    if uuid:
        return redirect(url_for('logins'))
    if request.method == 'GET':
        sql_command = 'select * from XinXi'
        df = pd.read_sql(sql_command, models.db.engine)

        df.dropna(subset=['专业'], inplace=True)

        # 各专业平均分数线
        dys = df['分数线'].groupby(df['专业']).mean().head(20)
        fuzhuang_xiaoshou = []
        for i in range(len(dys.values.tolist())):
            fuzhuang_xiaoshou.append({"name":list(dys.index)[i],"value":round(dys.values.tolist()[i],10)})

        # #各专业报考人数
        fuzhuang_type2 = {key: value for key, value in df['报考人数'].groupby(df['专业']).mean().items()}
        fuzhuang_type2 = sorted(fuzhuang_type2.items(), key=lambda x: x[1], reverse=True)
        type2_name = []
        type2_count = []
        for resu in fuzhuang_type2[:10]:
            type2_name.append(resu[0])
            type2_count.append(round(resu[1]))

        # # 各专业招考人数
        fuzhuang_pinbai = {key: round(value, 2) for key, value in  df['招考人数'].groupby(df['专业']).mean().items()}
        fuzhuang_pinbai = sorted(fuzhuang_pinbai.items(), key=lambda x: x[1], reverse=True)
        num_name = []
        num_count = []
        for resu in fuzhuang_pinbai[:10]:
            num_name.append(resu[0])
            num_count.append(resu[1])

        # 词云图
        a = [da1[0] for da1 in df[['专业']].values.tolist()[:100]]
        b = ' '.join(a)
        c = jieba.lcut(b)
        values = []
        for key in c:
            if key.strip():
                values.append(key.strip())
        list11 = list(set(values))
        title_count1 = []
        for resu1 in list11:
            title_count1.append({"name": resu1, "value": values.count(resu1)})
        title_count1.sort(key=lambda xx: xx['value'], reverse=True)
        title_count1 = title_count1[:100]

        # 各地区招考人数
        title2_list = []
        title2_count = []
        datas11 = [i[0] for i in df[['地区']].values.tolist()]
        type1s = list(set(datas11))
        type1s.sort()
        li1 = []
        for type1 in type1s:
            li1.append((type1, df[df['地区']==type1]['招考人数'].sum()))
        title2_list = []
        title2_count = []
        for resu in li1:
            title2_list.append(resu[0])
            title2_count.append(resu[1])


        return render_template('daping/index.html', **locals())

from flask_security.utils import login_user, logout_user
@app.route('/logins', methods=['GET', 'POST'])
def logins():
    uuid = current_user.is_anonymous
    if not uuid:
        return redirect(url_for('index'))
    if request.method=='GET':
        return render_template('account/index.html')
    elif request.method=='POST':
        user = request.form.get('user')
        password = request.form.get('password')
        drone = request.form.get('drone')
        data = models.User.query.filter(and_(models.User.username==user,models.User.password==password)).first()
        if not data:
            return render_template('account/index.html',error='账号密码错误')
        else:
            if drone == '用户登陆':
                # 如果用户选择用户登录，则登录用户
                login_user(data, remember=True)
                return redirect(url_for('index'))
            for resu in models.User.query.get(data.id).roles:
                if resu.name == 'admin' and drone == '管理员登陆':
                    # 如果用户选择管理员登录且具有管理员权限，则登录用户
                    login_user(data, remember=True)
                    return redirect('/admin')
                else:
                    # 如果用户无管理员权限，返回错误信息
                    return render_template('login.html', error='用户无管理员权限')



@app.route('/loginsout', methods=['GET'])
def loginsout():
    if request.method=='GET':
        logout_user()
        return redirect(url_for('logins'))



@app.route('/signups', methods=['GET', 'POST'])
def signups():
    uuid = current_user.is_anonymous
    if not uuid:
        return redirect(url_for('index'))
    if request.method == 'GET':
        return render_template('account/register.html')
    elif request.method == 'POST':
        user = request.form.get('user')
        email = request.form.get('email')
        password = request.form.get('password')
        if models.User.query.filter(models.User.username == user).all():
            return render_template('account/register.html', error='账号名已被注册')
        elif user == '' or password == '' or email == '':
            return render_template('account/register.html', error='输入不能为空')
        else:
            new_user = user_datastore.create_user(username=user, email=email, password=password)
            normal_role = user_datastore.find_role('User')
            models.db.session.add(new_user)
            user_datastore.add_role_to_user(new_user, normal_role)
            models.db.session.commit()
            login_user(new_user, remember=True)

            return redirect(url_for('index'))


@app.route('/usercenter', methods=['GET'])
@login_required
def usercenter():
    return render_template('usercenter.html')

from models import db
@app.route('/update_password', methods=['POST'])
@login_required
def update_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # 验证旧密码是否正确
    if not current_user.verify_password(old_password):
        return render_template('usercenter.html', error='旧密码不正确')

    # 验证新密码和确认密码是否一致
    if new_password != confirm_password:
        return render_template('usercenter.html', error='新密码和确认密码不一致')

    # 更新密码
    current_user.password = new_password
    db.session.commit()

    return render_template('usercenter.html', success='密码修改成功')


from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pandas as pd
import numpy as np


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    uuid = current_user.is_anonymous
    if uuid:
        return redirect(url_for('logins'))

    if request.method == 'GET':
        # 使用 pandas 读取数据
        sql_command = 'select * from XinXi'
        df = pd.read_sql(sql_command, models.db.engine)

        # 去除包含 NaN 的行
        df.dropna(inplace=True)

        # 获取去重后的字符串类型特征值
        regions = df['地区'].unique().tolist()
        departments = df['部门名称'].unique().tolist()
        positions = df['职位'].unique().tolist()
        educations = df['学历'].unique().tolist()
        majors = df['专业'].unique().tolist()
        years = df['年份'].unique().tolist() if '年份' in df.columns else []

        return render_template('predict.html', regions=regions, departments=departments, positions=positions,
                               educations=educations, majors=majors, years=years)

    elif request.method == 'POST':
        # 打印接收到的表单数据
        print("\n\n==================== 接收到表单数据 ====================")
        print("表单数据:", request.form)
        
        try:
            # 使用 pandas 读取数据
            sql_command = 'select * from XinXi'
            df = pd.read_sql(sql_command, models.db.engine)

            # 去除包含 NaN 的行
            df.dropna(inplace=True)

            # 获取去重后的字符串类型特征值
            regions = df['地区'].unique().tolist()
            departments = df['部门名称'].unique().tolist()
            positions = df['职位'].unique().tolist()
            educations = df['学历'].unique().tolist()
            majors = df['专业'].unique().tolist()
            years = df['年份'].unique().tolist() if '年份' in df.columns else []

            # 获取用户输入的特征值
            region = request.form.get('region')
            department = request.form.get('department')
            position = request.form.get('position')
            education = request.form.get('education')
            major = request.form.get('major')
            recruitment_num = float(request.form.get('recruitment_num'))
            application_num = float(request.form.get('application_num'))
            year = request.form.get('year') if '年份' in df.columns and request.form.get('year') else None
            
            print(f"接收到的特征值: region={region}, department={department}, position={position}, education={education}, major={major}, recruitment_num={recruitment_num}, application_num={application_num}, year={year}")

            # 更高级的特征工程和模型训练
            from sklearn.preprocessing import LabelEncoder, StandardScaler, PolynomialFeatures
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, StackingRegressor
            from sklearn.model_selection import train_test_split, cross_val_score, KFold
            from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
            from sklearn.linear_model import ElasticNet, Ridge, Lasso, HuberRegressor
            from sklearn.svm import SVR
            from sklearn.neighbors import KNeighborsRegressor
            
            # 尝试导入高级模型库，如果不存在则安装
            try:
                import xgboost as xgb
                from xgboost import XGBRegressor
            except ImportError:
                import subprocess
                subprocess.call(['pip', 'install', 'xgboost'])
                import xgboost as xgb
                from xgboost import XGBRegressor
            
            try:
                import lightgbm as lgb
                from lightgbm import LGBMRegressor
            except ImportError:
                import subprocess
                subprocess.call(['pip', 'install', 'lightgbm'])
                import lightgbm as lgb
                from lightgbm import LGBMRegressor
            
            try:
                import catboost as cb
                from catboost import CatBoostRegressor
            except ImportError:
                import subprocess
                subprocess.call(['pip', 'install', 'catboost'])
                import catboost as cb
                from catboost import CatBoostRegressor
            
            # 创建标签编码器
            encoders = {}
            cat_features = ['地区', '部门名称', '职位', '学历', '专业']
            if '年份' in df.columns and year:
                cat_features.append('年份')
            
            for feature in cat_features:
                encoders[feature] = LabelEncoder()
                df[feature] = encoders[feature].fit_transform(df[feature])
            
            # 创建高级特征
            # 1. 基础竞争比例
            df['竞争比例'] = df['报考人数'] / df['招考人数']
            df['竞争比例_对数'] = np.log1p(df['竞争比例'])  # 添加对数变换特征
            
            # 2. 专业相关特征
            major_avg = df.groupby('专业')['分数线'].mean().to_dict()
            major_max = df.groupby('专业')['分数线'].max().to_dict()
            major_min = df.groupby('专业')['分数线'].min().to_dict()
            major_std = df.groupby('专业')['分数线'].std().fillna(0).to_dict()
            major_median = df.groupby('专业')['分数线'].median().to_dict()  # 添加中位数特征
            
            df['专业_平均分'] = df['专业'].map(major_avg)
            df['专业_最高分'] = df['专业'].map(major_max)
            df['专业_最低分'] = df['专业'].map(major_min)
            df['专业_分差'] = df['专业_最高分'] - df['专业_最低分']
            df['专业_标准差'] = df['专业'].map(major_std)
            df['专业_中位数'] = df['专业'].map(major_median)
            df['专业_变异系数'] = df['专业_标准差'] / df['专业_平均分']  # 添加变异系数特征
            
            # 3. 地区相关特征
            region_avg = df.groupby('地区')['分数线'].mean().to_dict()
            region_max = df.groupby('地区')['分数线'].max().to_dict()
            region_competition = df.groupby('地区')['竞争比例'].mean().to_dict()
            region_median = df.groupby('地区')['分数线'].median().to_dict()  # 添加中位数特征
            
            df['地区_平均分'] = df['地区'].map(region_avg)
            df['地区_最高分'] = df['地区'].map(region_max)
            df['地区_平均竞争比'] = df['地区'].map(region_competition)
            df['地区_中位数'] = df['地区'].map(region_median)
            
            # 4. 教育程度特征
            edu_avg = df.groupby('学历')['分数线'].mean().to_dict()
            edu_max = df.groupby('学历')['分数线'].max().to_dict()  # 添加最高分
            edu_min = df.groupby('学历')['分数线'].min().to_dict()  # 添加最低分
            
            df['学历_平均分'] = df['学历'].map(edu_avg)
            df['学历_最高分'] = df['学历'].map(edu_max)
            df['学历_最低分'] = df['学历'].map(edu_min)
            
            # 5. 职位复合特征
            job_major_avg = df.groupby(['职位', '专业'])['分数线'].mean().to_dict()
            job_region_avg = df.groupby(['职位', '地区'])['分数线'].mean().to_dict()  # 添加职位-地区交叉特征
            
            df['职位专业_平均分'] = [job_major_avg.get((p, m), 0) for p, m in zip(df['职位'], df['专业'])]
            df['职位地区_平均分'] = [job_region_avg.get((p, r), 0) for p, r in zip(df['职位'], df['地区'])]
            
            # 6. 部门相关特征
            dept_avg = df.groupby('部门名称')['分数线'].mean().to_dict()
            dept_competition = df.groupby('部门名称')['竞争比例'].mean().to_dict()
            
            df['部门_平均分'] = df['部门名称'].map(dept_avg)
            df['部门_平均竞争比'] = df['部门名称'].map(dept_competition)
            
            # 7. 添加二次项特征
            df['招考人数_平方'] = df['招考人数'] ** 2
            df['报考人数_平方'] = df['报考人数'] ** 2
            
            # 8. 添加交互特征
            df['招报_乘积'] = df['招考人数'] * df['报考人数']
            
            # 选择最终特征集
            features = [
                '地区', '部门名称', '职位', '学历', '专业', '招考人数', '报考人数', '竞争比例',
                '竞争比例_对数', '专业_平均分', '专业_最高分', '专业_最低分', '专业_分差', 
                '专业_标准差', '专业_中位数', '专业_变异系数', '地区_平均分', '地区_最高分',
                '地区_平均竞争比', '地区_中位数', '学历_平均分', '学历_最高分', '学历_最低分',
                '职位专业_平均分', '职位地区_平均分', '部门_平均分', '部门_平均竞争比',
                '招考人数_平方', '报考人数_平方', '招报_乘积'
            ]
            
            if '年份' in df.columns and year:
                features.append('年份')
            
            # 准备训练数据
            X = df[features]
            y = df['分数线']
            
            # 使用多项式特征扩展
            poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
            X_poly = poly.fit_transform(X[['招考人数', '报考人数', '竞争比例']])
            
            # 将多项式特征添加到原始特征中
            poly_feature_names = [f'poly_{i}' for i in range(X_poly.shape[1])]
            X_poly_df = pd.DataFrame(X_poly, columns=poly_feature_names, index=X.index)
            X = pd.concat([X, X_poly_df], axis=1)
            features.extend(poly_feature_names)
            
            # 标准化数值特征(非分类特征)
            cat_indices = [X.columns.get_loc(col) for col in ['地区', '部门名称', '职位', '学历', '专业'] if col in X.columns]
            numeric_features = [col for col in X.columns if X.columns.get_loc(col) not in cat_indices]
            
            scaler = StandardScaler()
            X[numeric_features] = scaler.fit_transform(X[numeric_features])
            
            # 训练集测试集分割
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # 构建更强大的基础模型
            rf = RandomForestRegressor(n_estimators=200, max_depth=15, min_samples_split=5, 
                                     random_state=42, n_jobs=-1)
            
            gbm = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, 
                                          max_depth=5, subsample=0.8, random_state=42)
            
            xgb_model = XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=6, 
                                   gamma=0, subsample=0.8, colsample_bytree=0.8, 
                                   reg_alpha=0.1, reg_lambda=1, random_state=42, n_jobs=-1)
            
            lgb_model = LGBMRegressor(n_estimators=200, learning_rate=0.05, max_depth=6, 
                                    num_leaves=31, subsample=0.8, colsample_bytree=0.8, 
                                    reg_alpha=0.1, reg_lambda=1, random_state=42, n_jobs=-1)
            
            catboost_model = CatBoostRegressor(iterations=200, learning_rate=0.05, depth=6, 
                                            l2_leaf_reg=3, random_state=42, verbose=0,
                                            cat_features=cat_indices)
            
            # 创建第二层元模型
            meta_model = Ridge(alpha=1.0)
            
            # 创建Stacking回归器(高级集成模型)
            estimators = [
                ('rf', rf),
                ('gb', gbm),
                ('xgb', xgb_model),
                ('lgb', lgb_model),
                ('catboost', catboost_model)
            ]
            
            stack = StackingRegressor(
                estimators=estimators,
                final_estimator=meta_model,
                cv=5,
                n_jobs=-1
            )
            
            # 使用交叉验证评估模型
            kf = KFold(n_splits=5, shuffle=True, random_state=42)
            cv_scores = cross_val_score(stack, X, y, cv=kf, scoring='r2')
            print(f"交叉验证 R² 分数: {cv_scores.mean():.4f}")
            
            # 训练最终模型
            stack.fit(X_train, y_train)
            
            # 模型评估
            train_preds = stack.predict(X_train)
            test_preds = stack.predict(X_test)
            
            train_r2 = r2_score(y_train, train_preds)
            test_r2 = r2_score(y_test, test_preds)
            train_mae = mean_absolute_error(y_train, train_preds)
            test_mae = mean_absolute_error(y_test, test_preds)
            train_rmse = np.sqrt(mean_squared_error(y_train, train_preds))
            test_rmse = np.sqrt(mean_squared_error(y_test, test_preds))
            
            print(f"训练集 R² 分数: {train_r2:.4f}")
            print(f"测试集 R² 分数: {test_r2:.4f}")
            print(f"训练集 MAE: {train_mae:.4f}")
            print(f"训练集 RMSE: {train_rmse:.4f}")
            print(f"测试集 MAE: {test_mae:.4f}")
            print(f"测试集 RMSE: {test_rmse:.4f}")
            
            # 准备预测数据
            input_data = pd.DataFrame({
                '地区': [encoders['地区'].transform([region])[0]],
                '部门名称': [encoders['部门名称'].transform([department])[0]],
                '职位': [encoders['职位'].transform([position])[0]],
                '学历': [encoders['学历'].transform([education])[0]],
                '专业': [encoders['专业'].transform([major])[0]],
                '招考人数': [recruitment_num],
                '报考人数': [application_num],
                '竞争比例': [application_num / recruitment_num],
                '竞争比例_对数': [np.log1p(application_num / recruitment_num)]
            })
            
            # 添加高级特征到预测数据
            input_data['专业_平均分'] = major_avg.get(encoders['专业'].transform([major])[0], 0)
            input_data['专业_最高分'] = major_max.get(encoders['专业'].transform([major])[0], 0)
            input_data['专业_最低分'] = major_min.get(encoders['专业'].transform([major])[0], 0)
            input_data['专业_分差'] = input_data['专业_最高分'] - input_data['专业_最低分']
            input_data['专业_标准差'] = major_std.get(encoders['专业'].transform([major])[0], 0)
            input_data['专业_中位数'] = major_median.get(encoders['专业'].transform([major])[0], 0)
            input_data['专业_变异系数'] = input_data['专业_标准差'] / input_data['专业_平均分']
            
            input_data['地区_平均分'] = region_avg.get(encoders['地区'].transform([region])[0], 0)
            input_data['地区_最高分'] = region_max.get(encoders['地区'].transform([region])[0], 0)
            input_data['地区_平均竞争比'] = region_competition.get(encoders['地区'].transform([region])[0], 0)
            input_data['地区_中位数'] = region_median.get(encoders['地区'].transform([region])[0], 0)
            
            input_data['学历_平均分'] = edu_avg.get(encoders['学历'].transform([education])[0], 0)
            input_data['学历_最高分'] = edu_max.get(encoders['学历'].transform([education])[0], 0)
            input_data['学历_最低分'] = edu_min.get(encoders['学历'].transform([education])[0], 0)
            
            job_major_key = (encoders['职位'].transform([position])[0], encoders['专业'].transform([major])[0])
            input_data['职位专业_平均分'] = job_major_avg.get(job_major_key, 0)
            
            job_region_key = (encoders['职位'].transform([position])[0], encoders['地区'].transform([region])[0])
            input_data['职位地区_平均分'] = job_region_avg.get(job_region_key, 0)
            
            input_data['部门_平均分'] = dept_avg.get(encoders['部门名称'].transform([department])[0], 0)
            input_data['部门_平均竞争比'] = dept_competition.get(encoders['部门名称'].transform([department])[0], 0)
            
            input_data['招考人数_平方'] = input_data['招考人数'] ** 2
            input_data['报考人数_平方'] = input_data['报考人数'] ** 2
            input_data['招报_乘积'] = input_data['招考人数'] * input_data['报考人数']
            
            # 添加年份特征(如果存在)
            if '年份' in df.columns and year:
                input_data['年份'] = encoders['年份'].transform([year])[0]
            
            # 添加多项式特征
            input_poly = poly.transform(input_data[['招考人数', '报考人数', '竞争比例']])
            for i, col in enumerate(poly_feature_names):
                input_data[col] = input_poly[0, i]
            
            # 标准化预测数据的数值特征
            input_data[numeric_features] = scaler.transform(input_data[numeric_features])
            
            # 确保输入数据具有所有所需特征
            for feature in features:
                if feature not in input_data.columns:
                    input_data[feature] = 0
            
            # 重新排列特征列以匹配训练数据
            input_data = input_data[features]
            
            # 使用堆叠集成模型进行预测
            predicted_score = stack.predict(input_data)[0]
            predicted_score = round(predicted_score, 2)
            
            # 计算置信度
            # 基于测试集R²值计算置信度(R²取值范围为0-1，越接近1表示模型解释性越好)
            confidence = max(0.6, min(0.95, test_r2))  # 置信度范围限制在0.6-0.95之间
            
            return render_template('predict.html', predicted_score=predicted_score, 
                                  confidence=confidence, train_score=round(train_r2*100, 2),
                                  test_score=round(test_r2*100, 2), 
                                  regions=regions, departments=departments, 
                                  positions=positions, educations=educations, 
                                  majors=majors, years=years)

        except Exception as e:
            import traceback
            print(f"预测错误: {str(e)}")
            print(traceback.format_exc())
            return render_template('predict.html', error=f"预测错误: {str(e)}", 
                                  regions=regions, departments=departments, 
                                  positions=positions, educations=educations, 
                                  majors=majors, years=years)

@app.route('/visualization', methods=['GET'])
def visualization():
    uuid = current_user.is_anonymous
    if uuid:
        return redirect(url_for('logins'))
    
    if request.method == 'GET':
        # 获取关键词
        keyword = request.args.get('keyword', '')

        # 使用 pandas 读取数据
        sql_command = 'select * from XinXi'
        df = pd.read_sql(sql_command, models.db.engine)

        # 去除包含 NaN 的行
        df.dropna(inplace=True)

        # 模糊匹配地区、年份、职位、学历
        if keyword:
            df = df[df.apply(lambda row: any(keyword in str(row[col]) for col in ['地区', '年份', '职位', '学历']), axis=1)]

        # 1. 各专业平均分数线
        dys = df['分数线'].groupby(df['专业']).mean().head(20)
        fuzhuang_xiaoshou = []
        for i in range(len(dys.values.tolist())):
            fuzhuang_xiaoshou.append({"name":list(dys.index)[i],"value":round(dys.values.tolist()[i],10)})

        # 2. 各专业报考人数
        fuzhuang_type2 = {key: value for key, value in df['报考人数'].groupby(df['专业']).mean().items()}
        fuzhuang_type2 = sorted(fuzhuang_type2.items(), key=lambda x: x[1], reverse=True)
        type2_name = []
        type2_count = []
        for resu in fuzhuang_type2[:10]:
            type2_name.append(resu[0])
            type2_count.append(round(resu[1]))

        # 3. 各专业招考人数
        fuzhuang_pinbai = {key: round(value, 2) for key, value in  df['招考人数'].groupby(df['专业']).mean().items()}
        fuzhuang_pinbai = sorted(fuzhuang_pinbai.items(), key=lambda x: x[1], reverse=True)
        num_name = []
        num_count = []
        for resu in fuzhuang_pinbai[:10]:
            num_name.append(resu[0])
            num_count.append(resu[1])

        # 4. 词云图
        a = [da1[0] for da1 in df[['专业']].values.tolist()[:100]]
        b = ' '.join(a)
        c = jieba.lcut(b)
        values = []
        for key in c:
            if key.strip():
                values.append(key.strip())
        list11 = list(set(values))
        title_count1 = []
        for resu1 in list11:
            title_count1.append({"name": resu1, "value": values.count(resu1)})
        title_count1.sort(key=lambda xx: xx['value'], reverse=True)
        title_count1 = title_count1[:100]

        # 5. 各地区招考人数
        title2_list = []
        title2_count = []
        datas11 = [i[0] for i in df[['地区']].values.tolist()]
        type1s = list(set(datas11))
        type1s.sort()
        li1 = []
        for type1 in type1s:
            li1.append((type1, df[df['地区']==type1]['招考人数'].sum()))
        title2_list = []
        title2_count = []
        for resu in li1:
            title2_list.append(resu[0])
            title2_count.append(resu[1])

        # 6. 各地区平均分数线
        region_avg_score = df['分数线'].groupby(df['地区']).mean()
        region_avg_score = region_avg_score.sort_values(ascending=False)
        region_avg_score_list = region_avg_score.index.tolist()
        region_avg_score_count = region_avg_score.values.tolist()

        # 7. 各学历平均分数线
        education_avg_score = df['分数线'].groupby(df['学历']).mean()
        education_avg_score = education_avg_score.sort_values(ascending=False)
        education_avg_score_list = education_avg_score.index.tolist()
        education_avg_score_count = education_avg_score.values.tolist()

        # 8. 各职位平均分数线
        position_avg_score = df['分数线'].groupby(df['职位']).mean()
        # 过滤掉可能的0值或异常值
        position_avg_score = position_avg_score[position_avg_score > 0]
        position_avg_score = position_avg_score.sort_values(ascending=False)
        position_avg_score_list = position_avg_score.index.tolist()
        position_avg_score_count = position_avg_score.values.tolist()

        # 9. 各专业最高分
        major_max_score = df['最高分'].groupby(df['专业']).max()
        major_max_score = major_max_score.sort_values(ascending=False)
        major_max_score_list = major_max_score.index.tolist()
        major_max_score_count = major_max_score.values.tolist()

        # 10. 各地区报考人数
        region_application_num = df['报考人数'].groupby(df['地区']).sum()
        region_application_num = region_application_num.sort_values(ascending=False)
        region_application_num_list = region_application_num.index.tolist()
        region_application_num_count = region_application_num.values.tolist()


        # 自定义zip过滤器
        def zip_filter(a, b):
            return zip(a, b)

        app.jinja_env.filters['zip'] = zip_filter

        return render_template('visualization.html', **locals())

@app.route('/api/get_departments', methods=['GET'])
def get_departments():
    """根据地区获取部门列表"""
    region = request.args.get('region', '')
    if not region:
        return jsonify([])
    
    # 查询指定地区的所有部门
    sql_command = 'select * from XinXi'
    df = pd.read_sql(sql_command, models.db.engine)
    
    # 过滤特定地区
    filtered_df = df[df['地区'] == region]
    departments = filtered_df['部门名称'].unique().tolist()
    
    return jsonify(departments)

@app.route('/api/get_positions', methods=['GET'])
def get_positions():
    """根据地区和部门获取职位列表"""
    region = request.args.get('region', '')
    department = request.args.get('department', '')
    if not region or not department:
        return jsonify([])
    
    # 查询指定地区和部门的所有职位
    sql_command = 'select * from XinXi'
    df = pd.read_sql(sql_command, models.db.engine)
    
    # 过滤特定地区和部门
    filtered_df = df[(df['地区'] == region) & (df['部门名称'] == department)]
    positions = filtered_df['职位'].unique().tolist()
    
    return jsonify(positions)

@app.route('/api/get_majors', methods=['GET'])
def get_majors():
    """根据地区、部门和职位获取专业列表"""
    region = request.args.get('region', '')
    department = request.args.get('department', '')
    position = request.args.get('position', '')
    if not region or not department or not position:
        return jsonify([])
    
    # 查询指定地区、部门和职位的所有专业
    sql_command = 'select * from XinXi'
    df = pd.read_sql(sql_command, models.db.engine)
    
    # 过滤特定地区、部门和职位
    filtered_df = df[(df['地区'] == region) & 
                    (df['部门名称'] == department) & 
                    (df['职位'] == position)]
    majors = filtered_df['专业'].unique().tolist()
    
    return jsonify(majors)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
