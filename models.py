import flask
from flask_sqlalchemy import SQLAlchemy
import datetime
import os
from sqlalchemy import or_,and_
from flask_babelex import Babel
from flask_security import Security, SQLAlchemySessionUserDatastore, \
    UserMixin, RoleMixin, login_required, auth_token_required, http_auth_required


app = flask.Flask(__name__)
abel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SQLALCHEMY_TRACK_MODIFICATIONS = True
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False
app.config['SECRET_KEY'] = ''

# host = '127.0.0.1'
# user = 'root'
# password = '123456'
# database = 'xinxi'
# app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://%s:%s@%s:3306/%s" % (user, password, host,database)


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 'sqlite:///' + os.path.join(app.root_path, 'xinxi.db'))
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

    id = db.Column(db.Integer, unique=True, primary_key=True)

    年份 = db.Column(db.String(124))
    岗位代码 = db.Column(db.String(124))
    地区 = db.Column(db.String(124))
    部门名称 = db.Column(db.String(124))
    职位 = db.Column(db.String(124))
    学历 = db.Column(db.String(124))
    专业 = db.Column(db.String(124))
    招考人数 = db.Column(db.FLOAT)
    报考人数 = db.Column(db.FLOAT)
    分数线 = db.Column(db.FLOAT)
    最高分 = db.Column(db.FLOAT)

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
    with app.app_context():
        db.drop_all()  # 清除表
        db.create_all()  # 创建表

        # 设置flask-security
        user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
        security = Security(app, user_datastore)
        user_datastore.create_role(name='admin', description='管理员')  # 注册管理员权限
        user_datastore.create_role(name='User', description='普通用户')  # 注册用户权限
        db.session.commit()
        new_user = user_datastore.create_user(username='admin', password='root123456', email='123@qq.com',
                                          active=True)  # 注册管理员
        normal_role = user_datastore.find_role('admin')
        db.session.add(new_user)
        user_datastore.add_role_to_user(new_user, normal_role)
    # 设置flask-security
    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
    security = Security(app, user_datastore)
    user_datastore.create_role(name='admin', description='管理员')  # 注册管理员权限
    user_datastore.create_role(name='User', description='普通用户')  # 注册用户权限
    db.session.commit()
    new_user = user_datastore.create_user(username='admin', password='root123456', email='123@qq.com',
                                          active=True)  # 注册管理员
    normal_role = user_datastore.find_role('admin')
    db.session.add(new_user)
    user_datastore.add_role_to_user(new_user, normal_role)
    db.session.commit()

