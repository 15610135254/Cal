from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_babelex import Babel
from flask_security import UserMixin, RoleMixin

app = Flask(__name__)
babel = Babel(app)

# 基础配置
app.config.update(
    BABEL_DEFAULT_LOCALE='zh_CN',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ECHO=False,
    SQLALCHEMY_COMMIT_ON_TEARDOWN=False,
    SECRET_KEY='',
    SECURITY_PASSWORD_SALT='123456789',
    SECURITY_PASSWORD_HASH='sha512_crypt'
)

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'xinxi'
}

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://{user}:{password}@{host}:3306/{database}".format(**DB_CONFIG)
app.secret_key = "fj"

db = SQLAlchemy(app)

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
    username = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users', lazy='dynamic'))

    @property
    def roles(self):
        return [self.role] if self.role else []

    def __repr__(self):
        return "<{} 用户>".format(self.username)

    def verify_password(self, password):
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
    职位资格条件和要求 = db.Column(db.Text)
    专业 = db.Column(db.String(124))
    学历 = db.Column(db.String(124))
    学位 = db.Column(db.String(124))
    年龄 = db.Column(db.String(124))
    经历要求 = db.Column(db.String(124))
    其他 = db.Column(db.String(124))
    申论类别 = db.Column(db.String(124))
    专业科目 = db.Column(db.Text)
    咨询电话 = db.Column(db.String(124))

def init_db():
    with app.app_context():
        db.create_all()

        # 初始化角色
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='管理员')
            db.session.add(admin_role)

        user_role = Role.query.filter_by(name='User').first()
        if not user_role:
            user_role = Role(name='User', description='普通用户')
            db.session.add(user_role)

        db.session.commit()

        # 初始化管理员账户
        admin_data = {
            'username': 'admin',
            'password': 'admin123',
            'email': 'admin@example.com'
        }

        admin_user = User.query.filter_by(username=admin_data['username']).first()
        if not admin_user:
            admin_user = User(
                username=admin_data['username'],
                password=admin_data['password'],
                email=admin_data['email'],
                active=True,
                role_id=admin_role.id
            )
            db.session.add(admin_user)
        elif admin_user.role_id != admin_role.id:
            admin_user.role_id = admin_role.id

        # 更新现有用户角色
        for user in User.query.filter(User.username != admin_data['username']).all():
            if user.role_id is None:
                user.role_id = user_role.id

        db.session.commit()

if __name__ == '__main__':
    init_db()

