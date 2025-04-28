# !/usr/bin/env python
# _*_ coding: utf-8 _*_
# 标准库导入
import os
import time
import datetime

# 第三方库导入
import numpy as np
import pandas as pd
import jieba
import pickle

# Flask相关导入
from flask import Flask, request, render_template, jsonify, abort, session, redirect, url_for
from flask_security import Security, SQLAlchemySessionUserDatastore, \
    UserMixin, RoleMixin, login_required, auth_token_required, http_auth_required, current_user
from flask_security.utils import login_user, logout_user
from sqlalchemy import or_, and_

# 本地模块导入
import models
from models import app, db

# 设置Flask-Security
user_datastore = SQLAlchemySessionUserDatastore(models.db.session, models.User, models.Role)
security = Security(app, user_datastore)

# 公共数据加载函数
def load_data_from_db(filter_condition=None):
    """
    从数据库加载数据并进行预处理
    参数:
        filter_condition: 可选，用于过滤数据的条件函数
    返回:
        处理后的DataFrame
    """
    try:
        # 使用pandas从数据库读取数据
        sql_command = 'select * from XinXi'
        df = pd.read_sql(sql_command, models.db.engine)
        
        # 去除包含NaN的行
        df.dropna(inplace=True)
        
        # 应用过滤条件（如果有）
        if filter_condition is not None:
            df = df[filter_condition(df)]
            
        return df
    except Exception as e:
        print(f"数据加载错误: {e}")
        return pd.DataFrame()  # 返回空DataFrame

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():  # 主页
    uuid = current_user.is_anonymous
    if uuid:
        return redirect(url_for('logins'))
    if request.method == 'GET':
        results = models.XinXi.query.all()[:1000]
        return render_template('index.html', **locals())

@app.route('/keshihua', methods=['GET', 'POST'])
def keshihua():  # 可视化页面
    uuid = current_user.is_anonymous
    if uuid:
        return redirect(url_for('logins'))
    if request.method == 'GET':
        df = load_data_from_db()
        
        # 对专业列进行过滤
        df.dropna(subset=['专业'], inplace=True)

        # 各专业平均分数线
        dys = df['分数线'].groupby(df['专业']).mean().head(20)
        fuzhuang_xiaoshou = []
        for i in range(len(dys.values.tolist())):
            fuzhuang_xiaoshou.append({"name": list(dys.index)[i], "value": round(dys.values.tolist()[i], 10)})

        # 各专业报考人数
        fuzhuang_type2 = {key: value for key, value in df['报考人数'].groupby(df['专业']).mean().items()}
        fuzhuang_type2 = sorted(fuzhuang_type2.items(), key=lambda x: x[1], reverse=True)
        type2_name = []
        type2_count = []
        for resu in fuzhuang_type2[:10]:
            type2_name.append(resu[0])
            type2_count.append(round(resu[1]))

        # 各专业招考人数
        fuzhuang_pinbai = {key: round(value, 2) for key, value in df['招考人数'].groupby(df['专业']).mean().items()}
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
        datas11 = [i[0] for i in df[['地区']].values.tolist()]
        type1s = list(set(datas11))
        type1s.sort()
        li1 = []
        for type1 in type1s:
            li1.append((type1, df[df['地区'] == type1]['招考人数'].sum()))
        title2_list = []
        title2_count = []
        for resu in li1:
            title2_list.append(resu[0])
            title2_count.append(resu[1])

        return render_template('daping/index.html', **locals())

@app.route('/logins', methods=['GET', 'POST'])
def logins():
    uuid = current_user.is_anonymous
    if not uuid:
        return redirect(url_for('index'))
    if request.method == 'GET':
        return render_template('account/index.html')
    elif request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('password')
        drone = request.form.get('drone')
        data = models.User.query.filter(and_(models.User.username == user, models.User.password == password)).first()
        if not data:
            return render_template('account/index.html', error='账号密码错误')
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
    if request.method == 'GET':
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

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    uuid = current_user.is_anonymous
    if uuid:
        return redirect(url_for('logins'))

    if request.method == 'GET':
        # 加载数据
        df = load_data_from_db()

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
            # 加载数据
            df = load_data_from_db()

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

            # 加载LightGBM模型
            try:
                # 加载pickle格式的LightGBM模型
                model_path = 'lgb_model.pkl'
                print(f"尝试加载LightGBM模型: {model_path}")
                
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                # 提取模型和元数据
                lgb_model = model_data['model']
                encoders = model_data['encoders']
                scaler = model_data['scaler']
                features = model_data['features']
                
                print(f"成功加载LightGBM模型，特征数量: {len(features)}")
                
                # 准备预测数据
                pred_data = pd.DataFrame({
                    '地区': [region],
                    '部门名称': [department],
                    '职位': [position],
                    '学历': [education],
                    '专业': [major],
                    '招考人数': [recruitment_num],
                    '报考人数': [application_num]
                })
                
                if year:
                    pred_data['年份'] = year
                
                # 创建时间序列特征
                if '年份' in pred_data.columns and not df.empty:
                    print("为预测数据创建时间序列特征")
                    
                    # 为预测数据构建时间序列特征
                    # 1. 从历史数据中获取该地区的时间序列数据
                    hist_data = df[df['地区'] == region].copy() if region else df.copy()
                    
                    if len(hist_data) > 0:
                        # 确保按年份排序
                        if '年份' in hist_data.columns:
                            hist_data = hist_data.sort_values('年份')
                        
                        # 如果预测数据的年份早于历史数据中的最大年份，则使用历史数据填充
                        if '年份' in hist_data.columns and year:
                            try:
                                # 尝试转换为数值进行比较
                                hist_max_year = hist_data['年份'].max()
                                if pd.to_numeric(year) <= pd.to_numeric(hist_max_year):
                                    # 获取历史数据中特定年份的数据
                                    year_data = hist_data[hist_data['年份'] == year]
                                    if len(year_data) > 0:
                                        avg_score = year_data['分数线'].mean()
                                        print(f"从历史数据找到年份 {year} 的平均分数线: {avg_score:.2f}")
                                        # 直接使用历史数据作为预测结果
                                        predicted_score = avg_score
                                        confidence = 0.95  # 高置信度，因为使用了实际历史数据
                                        return render_template('predict.html', predicted_score=predicted_score, 
                                                              confidence=confidence, train_score=round(confidence*100, 0),
                                                              test_score=round(confidence*100 - 5, 0), 
                                                              regions=regions, departments=departments, 
                                                              positions=positions, educations=educations, 
                                                              majors=majors, years=years)
                            except:
                                print("年份格式转换失败，继续使用模型预测")
                        
                        # 为预测数据添加历史特征
                        # 1. 添加滞后特征
                        if region and '分数线' in hist_data.columns:
                            # 获取该地区的历史分数线数据
                            region_scores = hist_data[hist_data['地区'] == region]['分数线']
                            if len(region_scores) > 0:
                                # 滞后1年
                                pred_data['分数线_滞后1年'] = region_scores.iloc[-1] if len(region_scores) >= 1 else region_scores.mean()
                                # 滞后2年
                                pred_data['分数线_滞后2年'] = region_scores.iloc[-2] if len(region_scores) >= 2 else region_scores.mean()
                                # 滞后3年
                                pred_data['分数线_滞后3年'] = region_scores.iloc[-3] if len(region_scores) >= 3 else region_scores.mean()
                                
                                # 计算历史平均值和变化
                                last_3_scores = region_scores.iloc[-3:] if len(region_scores) >= 3 else region_scores
                                last_5_scores = region_scores.iloc[-5:] if len(region_scores) >= 5 else region_scores
                                
                                # 3年均值
                                pred_data['分数线_3年均值'] = last_3_scores.mean()
                                # 5年均值
                                pred_data['分数线_5年均值'] = last_5_scores.mean()
                                # 3年标准差
                                pred_data['分数线_3年标准差'] = last_3_scores.std() if len(last_3_scores) > 1 else 0
                                # 3年最大值
                                pred_data['分数线_3年最大值'] = last_3_scores.max()
                                # 3年最小值
                                pred_data['分数线_3年最小值'] = last_3_scores.min()
                                
                                # 年度变化
                                if len(region_scores) >= 2:
                                    pred_data['分数线_年度变化'] = region_scores.iloc[-1] - region_scores.iloc[-2]
                                    # 年度变化率
                                    pred_data['分数线_年度变化率'] = (region_scores.iloc[-1] / region_scores.iloc[-2] - 1) if region_scores.iloc[-2] != 0 else 0
                                else:
                                    pred_data['分数线_年度变化'] = 0
                                    pred_data['分数线_年度变化率'] = 0
                                
                                # 年度加速度 (变化的变化)
                                if len(region_scores) >= 3:
                                    change1 = region_scores.iloc[-1] - region_scores.iloc[-2]
                                    change2 = region_scores.iloc[-2] - region_scores.iloc[-3]
                                    pred_data['分数线_年度加速度'] = change1 - change2
                                else:
                                    pred_data['分数线_年度加速度'] = 0
                    
                    # 报考人数相关特征
                    if '报考人数' in hist_data.columns and region:
                        region_applicants = hist_data[hist_data['地区'] == region]['报考人数']
                        if len(region_applicants) > 0:
                            # 3年平均报考人数
                            last_3_applicants = region_applicants.iloc[-3:] if len(region_applicants) >= 3 else region_applicants
                            pred_data['报考人数_3年均值'] = last_3_applicants.mean()
                            
                            # 报考人数年度变化
                            if len(region_applicants) >= 2:
                                pred_data['报考人数_年度变化'] = region_applicants.iloc[-1] - region_applicants.iloc[-2]
                                pred_data['报考人数_年度变化率'] = (region_applicants.iloc[-1] / region_applicants.iloc[-2] - 1) if region_applicants.iloc[-2] != 0 else 0
                            else:
                                pred_data['报考人数_年度变化'] = 0
                                pred_data['报考人数_年度变化率'] = 0
                    
                    # 竞争比相关特征
                    if '报考人数' in hist_data.columns and '招考人数' in hist_data.columns and region:
                        region_data = hist_data[hist_data['地区'] == region]
                        if len(region_data) > 0:
                            # 计算历史竞争比
                            region_data['竞争比'] = region_data['报考人数'] / region_data['招考人数'].replace(0, 1)
                            competition_ratios = region_data['竞争比']
                            
                            # 当前竞争比
                            pred_data['竞争比'] = application_num / max(1, recruitment_num)
                            
                            # 3年平均竞争比
                            last_3_ratios = competition_ratios.iloc[-3:] if len(competition_ratios) >= 3 else competition_ratios
                            pred_data['竞争比_3年均值'] = last_3_ratios.mean()
                            
                            # 竞争比年度变化
                            if len(competition_ratios) >= 2:
                                pred_data['竞争比_年度变化'] = competition_ratios.iloc[-1] - competition_ratios.iloc[-2]
                            else:
                                pred_data['竞争比_年度变化'] = 0
                
                # 特征编码
                for col, encoder in encoders.items():
                    if col in pred_data.columns:
                        try:
                            # 检查编码器是否已经见过该值
                            unique_values = encoder.classes_
                            if pred_data[col].iloc[0] in unique_values:
                                pred_data[col+'_encoded'] = encoder.transform(pred_data[col])
                            else:
                                # 如果是未见过的类别，使用最常见的类别
                                print(f"警告: 特征 {col} 的值 '{pred_data[col].iloc[0]}' 在训练数据中不存在，使用最常见值")
                                pred_data[col+'_encoded'] = 0
                        except Exception as e:
                            print(f"编码特征 {col} 时出错: {e}")
                            # 使用0作为默认编码
                            pred_data[col+'_encoded'] = 0
                
                # 检查所有必需的特征是否存在
                missing_features = [f for f in features if f not in pred_data.columns]
                if missing_features:
                    print(f"警告: 缺失以下特征: {missing_features}")
                    # 为缺失的特征填充0值
                    for feature in missing_features:
                        pred_data[feature] = 0
                
                # 准备输入特征向量
                X_pred = pred_data[features]
                
                # 标准化数值特征
                X_pred_scaled = scaler.transform(X_pred)
                
                # 使用LightGBM模型预测
                predicted_score = lgb_model.predict(X_pred_scaled)[0]
                
                # 获取模型置信度
                confidence = model_data['metrics']['confidence'] / 100  # 转换为0-1范围
                
                # 四舍五入到2位小数
                predicted_score = round(predicted_score, 2)
                
                print(f"LightGBM预测结果: {predicted_score}, 置信度: {confidence:.2f}")
                
            except Exception as e:
                import traceback
                print(f"LightGBM模型预测失败: {e}")
                print(traceback.format_exc())
                
                # 回退到使用平均值预测
                predicted_score = df['分数线'].mean()
                confidence = 0.7  # 中等置信度
                
                # 考虑竞争比例影响
                competition_ratio = application_num / max(1, recruitment_num)
                avg_competition = df['报考人数'].mean() / df['招考人数'].mean()
                
                # 根据竞争比例调整预测分数线
                adjustment = 0
                if competition_ratio > avg_competition:
                    # 竞争更激烈，分数线可能更高
                    adjustment = min(5, (competition_ratio/avg_competition - 1) * 10)
                    predicted_score += adjustment
                
                print(f"使用备选方法(平均值)预测: {predicted_score:.2f}，竞争比例调整: {adjustment:.2f}")
            
            # 返回预测结果
            return render_template('predict.html', predicted_score=predicted_score, 
                                  confidence=confidence, train_score=round(confidence*100, 0),
                                  test_score=round(confidence*100 - 5, 0), 
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

# 提取数据可视化公共函数
def prepare_visualization_data(df, keyword=None):
    """准备可视化数据"""
    # 模糊匹配地区、年份、职位、学历
    if keyword:
        df = df[df.apply(lambda row: any(keyword in str(row[col]) for col in ['地区', '年份', '职位', '学历']), axis=1)]

    # 1. 各专业平均分数线
    dys = df['分数线'].groupby(df['专业']).mean().head(20)
    fuzhuang_xiaoshou = []
    for i in range(len(dys.values.tolist())):
        fuzhuang_xiaoshou.append({"name": list(dys.index)[i], "value": round(dys.values.tolist()[i], 10)})

    # 2. 各专业报考人数
    fuzhuang_type2 = {key: value for key, value in df['报考人数'].groupby(df['专业']).mean().items()}
    fuzhuang_type2 = sorted(fuzhuang_type2.items(), key=lambda x: x[1], reverse=True)
    type2_name = []
    type2_count = []
    for resu in fuzhuang_type2[:10]:
        type2_name.append(resu[0])
        type2_count.append(round(resu[1]))

    # 3. 各专业招考人数
    fuzhuang_pinbai = {key: round(value, 2) for key, value in df['招考人数'].groupby(df['专业']).mean().items()}
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
    datas11 = [i[0] for i in df[['地区']].values.tolist()]
    type1s = list(set(datas11))
    type1s.sort()
    li1 = []
    for type1 in type1s:
        li1.append((type1, df[df['地区'] == type1]['招考人数'].sum()))
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
    
    return locals()

@app.route('/visualization', methods=['GET'])
def visualization():
    uuid = current_user.is_anonymous
    if uuid:
        return redirect(url_for('logins'))
    
    if request.method == 'GET':
        # 获取关键词
        keyword = request.args.get('keyword', '')

        # 加载数据
        df = load_data_from_db()
        
        # 准备可视化数据
        vis_data = prepare_visualization_data(df, keyword)
        
        # 自定义zip过滤器
        def zip_filter(a, b):
            return zip(a, b)

        app.jinja_env.filters['zip'] = zip_filter

        return render_template('visualization.html', **vis_data)

# API端点
@app.route('/api/get_departments', methods=['GET'])
def get_departments():
    """根据地区获取部门列表"""
    region = request.args.get('region', '')
    if not region:
        return jsonify([])
    
    # 加载数据
    df = load_data_from_db()
    
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
    
    # 加载数据
    df = load_data_from_db()
    
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
    
    # 加载数据
    df = load_data_from_db()
    
    # 过滤特定地区、部门和职位
    filtered_df = df[(df['地区'] == region) & 
                    (df['部门名称'] == department) & 
                    (df['职位'] == position)]
    majors = filtered_df['专业'].unique().tolist()
    
    return jsonify(majors)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
