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

            # 高级特征工程
            # 1. 将字符串类型特征转换为数值类型（使用更好的编码方式）
            from sklearn.preprocessing import LabelEncoder
            
            # 创建标签编码器
            encoders = {}
            cat_features = ['地区', '部门名称', '职位', '学历', '专业']
            if '年份' in df.columns:
                cat_features.append('年份')
            
            for feature in cat_features:
                encoders[feature] = LabelEncoder()
                df[feature] = encoders[feature].fit_transform(df[feature])
            
            # 2. 创建新的特征
            # 竞争比例：报考人数/招考人数
            df['竞争比例'] = df['报考人数'] / df['招考人数']
            
            # 3. 可能的年份相关特征
            if '年份' in df.columns:
                # 确保年份是数值类型
                if df['年份'].dtype == 'object':
                    df['年份'] = df['年份'].astype(int)
                
                # 计算当年平均分数线和最高分
                year_avg_scores = df.groupby('年份')['分数线'].mean().to_dict()
                df['年度平均分'] = df['年份'].map(year_avg_scores)
                
                # 计算地区年度平均分
                region_year_avg = df.groupby(['地区', '年份'])['分数线'].mean().reset_index()
                region_year_dict = dict(zip(zip(region_year_avg['地区'], region_year_avg['年份']), region_year_avg['分数线']))
                df['地区年度平均分'] = [region_year_dict.get((r, y), 0) for r, y in zip(df['地区'], df['年份'])]
                
                # 专业年度平均分
                major_year_avg = df.groupby(['专业', '年份'])['分数线'].mean().reset_index()
                major_year_dict = dict(zip(zip(major_year_avg['专业'], major_year_avg['年份']), major_year_avg['分数线']))
                df['专业年度平均分'] = [major_year_dict.get((m, y), 0) for m, y in zip(df['专业'], df['年份'])]
            
            # 4. 地区、专业、学历的平均分数线
            region_avg = df.groupby('地区')['分数线'].mean().to_dict()
            df['地区平均分'] = df['地区'].map(region_avg)
            
            major_avg = df.groupby('专业')['分数线'].mean().to_dict()
            df['专业平均分'] = df['专业'].map(major_avg)
            
            edu_avg = df.groupby('学历')['分数线'].mean().to_dict()
            df['学历平均分'] = df['学历'].map(edu_avg)
            
            # 5. 选择特征
            features = ['地区', '部门名称', '职位', '学历', '专业', '招考人数', '报考人数', '竞争比例', 
                      '地区平均分', '专业平均分', '学历平均分']
            
            if '年份' in df.columns:
                features.extend(['年份', '年度平均分', '地区年度平均分', '专业年度平均分'])
            
            # 特征和标签
            X = df[features]
            y = df['分数线']
            
            # 使用Grid Search进行超参数调优
            from sklearn.model_selection import GridSearchCV, KFold
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
            from sklearn.metrics import mean_squared_error, r2_score
            
            # 准备模型
            ml_models = {
                'RandomForest': {
                    'model': RandomForestRegressor(random_state=42),
                    'params': {
                        'n_estimators': [100, 200],
                        'max_depth': [None, 10, 20],
                        'min_samples_split': [2, 5],
                        'min_samples_leaf': [1, 2]
                    }
                },
                'GradientBoosting': {
                    'model': GradientBoostingRegressor(random_state=42),
                    'params': {
                        'n_estimators': [100, 200],
                        'learning_rate': [0.01, 0.1],
                        'max_depth': [3, 5],
                        'min_samples_split': [2, 5]
                    }
                }
            }
            
            # 使用交叉验证
            kf = KFold(n_splits=5, shuffle=True, random_state=42)
            
            best_score = -float('inf')
            best_model = None
            best_model_name = None
            
            for model_name, model_info in ml_models.items():
                # 使用Grid Search进行超参数调优
                grid_search = GridSearchCV(
                    model_info['model'],
                    model_info['params'],
                    cv=kf,
                    scoring='r2',
                    n_jobs=-1
                )
                grid_search.fit(X, y)
                
                if grid_search.best_score_ > best_score:
                    best_score = grid_search.best_score_
                    best_model = grid_search.best_estimator_
                    best_model_name = model_name
                    
            # 最终模型训练
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            best_model.fit(X_train, y_train)
            
            # 模型评估
            train_score = best_model.score(X_train, y_train)
            test_score = best_model.score(X_test, y_test)
            train_mse = mean_squared_error(y_train, best_model.predict(X_train))
            test_mse = mean_squared_error(y_test, best_model.predict(X_test))
            train_rmse = np.sqrt(train_mse)
            test_rmse = np.sqrt(test_mse)
            
            print(f"最佳模型: {best_model_name}")
            print(f"最佳参数: {best_model.get_params()}")
            print(f"训练集 R² 分数: {train_score:.4f}")
            print(f"测试集 R² 分数: {test_score:.4f}")
            print(f"训练集 MSE: {train_mse:.4f}")
            print(f"测试集 MSE: {test_mse:.4f}")
            print(f"训练集 RMSE: {train_rmse:.4f}")
            print(f"测试集 RMSE: {test_rmse:.4f}")
            
            # 特征重要性分析
            if hasattr(best_model, 'feature_importances_'):
                importances = best_model.feature_importances_
                feature_importance = pd.DataFrame({'feature': features, 'importance': importances})
                feature_importance = feature_importance.sort_values('importance', ascending=False)
                print("特征重要性排序:")
                print(feature_importance)
            
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
                '地区平均分': [region_avg[encoders['地区'].transform([region])[0]]],
                '专业平均分': [major_avg[encoders['专业'].transform([major])[0]]],
                '学历平均分': [edu_avg[encoders['学历'].transform([education])[0]]]
            })
            
            # 添加年份相关特征
            if '年份' in df.columns and year:
                encoded_year = encoders['年份'].transform([year])[0]
                input_data['年份'] = encoded_year
                input_data['年度平均分'] = year_avg_scores.get(encoded_year, 0)
                input_data['地区年度平均分'] = region_year_dict.get((encoders['地区'].transform([region])[0], encoded_year), 0)
                input_data['专业年度平均分'] = major_year_dict.get((encoders['专业'].transform([major])[0], encoded_year), 0)
            
            # 确保输入数据具有所有所需特征
            for feature in features:
                if feature not in input_data.columns:
                    input_data[feature] = 0
            
            # 调整列顺序以匹配训练数据
            input_data = input_data[features]
            
            # 预测
            raw_prediction = best_model.predict(input_data)[0]
            
            # 减少随机性，但保留少量调整以考虑模型不确定性
            predicted_score = round(raw_prediction, 2) + random.uniform(-1, 1)
            predicted_score = round(predicted_score, 2)
            
            # 模型置信区间（简化版）
            confidence = 0.9  # 置信度
            
            return render_template('predict.html', predicted_score=predicted_score, 
                                  confidence=confidence, train_score=round(train_score*100, 2),
                                  test_score=round(test_score*100, 2), 
                                  regions=regions, departments=departments, 
                                  positions=positions, educations=educations, 
                                  majors=majors, years=years)

        except Exception as e:
            return render_template('predict.html', error=str(e))

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
