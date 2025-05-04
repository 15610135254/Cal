import flask
from flask_sqlalchemy import SQLAlchemy
import datetime
import os
from sqlalchemy import or_,and_
from flask_babelex import Babel
from flask_security import Security, SQLAlchemySessionUserDatastore, \
    UserMixin, RoleMixin, login_required, auth_token_required, http_auth_required

# 修改为直接导入 Flask 
from flask import Flask

# 修改应用创建方式
app = Flask(__name__)
abel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SQLALCHEMY_TRACK_MODIFICATIONS = True
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False
app.config['SECRET_KEY'] = ''

# MySQL数据库配置
host = '127.0.0.1'
user = 'root'
password = ''  # 无密码
database = 'xinxi'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://%s:%s@%s:3306/%s" % (user, password, host, database)

# 安全配置
app.config['SECURITY_PASSWORD_SALT'] = '123456789'
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'

app.secret_key = "fj"

db = SQLAlchemy(app)

# 创建模型
class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column('role_id', db.Integer, db.ForeignKey('role.id'))

    def __repr__(self):
        return "<{} 用户 {} 权限>".format(self.user_id,self.role_id)

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return "<{} 权限>".format(self.name)




class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, unique=True, primary_key=True)
    username  = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary='roles_users',
                         backref=db.backref('user', lazy='dynamic'))

    def __repr__(self):
        return "<{} 用户>".format(self.username)
        
    def verify_password(self, password):
        """验证用户密码是否正确"""
        return self.password == password


class XinXi(db.Model):
    __tablename__ = 'XinXi'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    年份 = db.Column(db.String(10))
    岗位代码 = db.Column(db.String(20))
    地区 = db.Column(db.String(50))
    部门名称 = db.Column(db.String(100))
    职位 = db.Column(db.String(100))
    学历 = db.Column(db.String(50))
    专业 = db.Column(db.String(200))
    招考人数 = db.Column(db.Float)
    报考人数 = db.Column(db.Float)
    分数线 = db.Column(db.Float)
    最高分 = db.Column(db.Float)
    城市 = db.Column(db.String(50))

    def __str__(self):
        return '<XinXi {}>'.format(self.岗位代码)


class ShuJu(db.Model):
    __tablename__ = 'ShuJu'

    id = db.Column(db.Integer, unique=True, primary_key=True)
    招录机关 = db.Column(db.String(124))
    机构性质 = db.Column(db.String(124))
    机构层级 = db.Column(db.String(124))
    职位类别 = db.Column(db.String(124))
    职位名称 = db.Column(db.String(124))
    职级层次 = db.Column(db.String(124))
    报考人数 = db.Column(db.String(124))
    最低进面分 = db.Column(db.String(124))
    最高进面分 = db.Column(db.String(124))
    职位代码 = db.Column(db.String(124))
    招考人数 = db.Column(db.String(124))
    职位资格条件和要求 = db.Column(db.String(124))
    专业 = db.Column(db.String(124))
    学历 = db.Column(db.String(124))
    学位 = db.Column(db.String(124))
    年龄 = db.Column(db.String(124))
    经历要求 = db.Column(db.String(124))
    其他 = db.Column(db.String(124))
    申论类别 = db.Column(db.String(124))
    专业科目 = db.Column(db.String(124))
    咨询电话 = db.Column(db.String(124))




if __name__ == '__main__':
    print("正在检查并初始化数据库角色和默认管理员...")
    with app.app_context():
        # 仅创建尚不存在的表
        db.create_all()

        # 设置Flask-Security (需要在 app_context 内)
        user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
        # security = Security(app, user_datastore) # Security 实例通常在主应用创建

        # 确保 'admin' 和 'User' 角色存在
        admin_role = user_datastore.find_or_create_role(name='admin', description='管理员')
        user_role = user_datastore.find_or_create_role(name='User', description='普通用户')
        
        # 查找或创建 admin 用户
        admin_username = 'admin'
        admin_password = 'admin123'
        admin_email = 'admin@example.com'
        
        admin_user = user_datastore.find_user(username=admin_username)
        
        if not admin_user:
            print(f"正在创建管理员用户 '{admin_username}'...")
            admin_user = user_datastore.create_user(
                username=admin_username, 
                password=admin_password, 
                email=admin_email,
                active=True
            )
            # 为新创建的 admin 用户添加 admin 角色
            user_datastore.add_role_to_user(admin_user, admin_role)
            print(f"管理员用户 '{admin_username}' 创建成功。")
        else:
            print(f"管理员用户 '{admin_username}' 已存在。")
            # 可选：如果需要，可以在这里更新现有 admin 用户的密码或角色
            # admin_user.password = user_datastore.hash_password(admin_password) # 如果要更新密码
            # if admin_role not in admin_user.roles:
            #     user_datastore.add_role_to_user(admin_user, admin_role)
            #     print(f"已为现有用户 '{admin_username}' 添加 'admin' 角色。")

        # 提交所有更改
        db.session.commit()
        print("数据库检查与初始化完成。")

